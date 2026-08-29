# render_orchestrator.py
# ==========================================================
# MY CREATION VIDEO GENERATOR  --  PHASE 2
# RENDER ORCHESTRATOR v1.0  --  Pipeline Coordinator
# ==========================================================
#
# PURPOSE:
# - Poori rendering pipeline ko coordinate karna
# - Phase 1 config → Phase 2 execution ka bridge
# - Clip scheduling with Variation Intelligence
# - Batch processing with RAM monitoring
# - Auto-pause/resume on resource constraints
# - Error recovery and retry logic
# - Progress tracking across all stages
# - Final video assembly (intro + clips + outro)
#
# PIPELINE STAGES:
# ┌─────────────────────────────────────────────────────────┐
# │                  RenderOrchestrator                      │
# │                                                         │
# │  Stage 1: PREPARE                                       │
# │  - Load Phase 1 config                                  │
# │  - Validate all source files                            │
# │  - Calculate durations & clip schedule                  │
# │  - Initialize Variation Engine                          │
# │                                                         │
# │  Stage 2: RENDER CLIPS                                  │
# │  - Submit clips to RenderWorker                         │
# │  - Monitor RAM & disk space                             │
# │  - Auto-pause if resources low                          │
# │  - Track progress with callbacks                        │
# │                                                         │
# │  Stage 3: ASSEMBLE                                      │
# │  - Concat intro + clips + outro                         │
# │  - Apply transitions between clips                      │
# │  - Burn captions onto video                             │
# │                                                         │
# │  Stage 4: POST-PRODUCTION                               │
# │  - Apply watermark                                      │
# │  - Apply subscribe overlay (mid-video)                  │
# │  - Add B-roll overlay                                   │
# │                                                         │
# │  Stage 5: AUDIO MIX                                     │
# │  - Mix voice + music + SFX                              │
# │  - Master audio (EQ, compression, loudnorm)             │
# │  - Output final video                                   │
# │                                                         │
# │  Stage 6: CLEANUP                                       │
# │  - Remove temp files                                    │
# │  - Save render report                                   │
# │  - Return final output path                             │
# └─────────────────────────────────────────────────────────┘
# ==========================================================

from __future__ import annotations

import os
import gc
import json
import time
import shutil
import logging
import tempfile
import traceback
import threading
from queue import Queue
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger("RenderOrchestrator")
logger.setLevel(logging.INFO)

if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.handlers.clear()
    logger.addHandler(_handler)


# ============================================================
# IMPORTS FROM OTHER PHASE 2 MODULES
# ============================================================

try:
    from batch_long_renderer import (
        render_clip_segment,
        normalize_video_asset,
        concat_files,
        concat_files_hard,
        burn_captions,
        apply_subscribe_overlay_mid,
        apply_niche_watermark,
        apply_broll_overlay,
        mux_audio_timeline,
        get_variation_engine,
        VariationIntelligence,
        duration_plan,
        chunked,
        probe_duration,
        probe_video_size,
        normalize_quality,
        quality_to_size,
        existing_files,
        first_existing,
        VIDEO_EXTS,
        AUDIO_EXTS,
        IMAGE_EXTS,
        DEFAULT_BATCH_SIZE,
        DEFAULT_FPS,
        INTRO_SECONDS,
        OUTRO_SECONDS,
        VOICE_START_OFFSET,
        FFMPEG,
        FFPROBE,
        log,
        fnum,
        inum,
        run_cmd,
    )
    HAS_RENDER_ENGINE = True
except ImportError as e:
    HAS_RENDER_ENGINE = False
    logger.warning(f"batch_long_renderer.py not available: {e}")

try:
    from render_worker import RenderWorker, TempFileManager, RenderProgress
    HAS_WORKER = True
except ImportError:
    HAS_WORKER = False
    logger.warning("render_worker.py not available")

try:
    from audio_mixer import AudioMixer, AudioMixConfig, mix_audio
    HAS_MIXER = True
except ImportError:
    HAS_MIXER = False
    logger.warning("audio_mixer.py not available")


# ============================================================
# RAM MONITOR (for orchestrator)
# ============================================================

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class ResourceMonitor:
    """
    Monitor system resources during rendering.
    
    Tracks:
    - RAM usage percentage
    - Free disk space
    - CPU temperature (if available)
    """
    
    def __init__(self, max_ram_pct: float = 85.0, min_disk_gb: float = 1.0):
        self.max_ram_pct = max_ram_pct
        self.min_disk_gb = min_disk_gb
        self._warnings: List[str] = []
    
    def check_ram(self) -> Tuple[bool, float]:
        """Check RAM. Returns (safe, percentage)."""
        if not HAS_PSUTIL:
            return True, 0.0
        try:
            pct = psutil.virtual_memory().percent
            return pct < self.max_ram_pct, pct
        except Exception:
            return True, 0.0
    
    def check_disk(self, path: str = ".") -> Tuple[bool, float]:
        """Check disk. Returns (safe, free_gb)."""
        try:
            usage = shutil.disk_usage(path)
            free_gb = usage.free / (1024 ** 3)
            return free_gb >= self.min_disk_gb, free_gb
        except Exception:
            return True, 999.0
    
    def check_all(self, path: str = ".") -> Dict[str, Any]:
        """Run all resource checks."""
        ram_ok, ram_pct = self.check_ram()
        disk_ok, disk_gb = self.check_disk(path)
        
        status = {
            "ram_pct": round(ram_pct, 1),
            "ram_ok": ram_ok,
            "disk_free_gb": round(disk_gb, 1),
            "disk_ok": disk_ok,
            "all_ok": ram_ok and disk_ok,
            "warnings": [],
        }
        
        if not ram_ok:
            status["warnings"].append(f"High RAM: {ram_pct:.1f}%")
        if not disk_ok:
            status["warnings"].append(f"Low disk: {disk_gb:.1f}GB free")
        
        return status


# ============================================================
# PIPELINE STAGE ENUM
# ============================================================

class PipelineStage(Enum):
    """Stages of the rendering pipeline."""
    IDLE = "idle"
    PREPARING = "preparing"
    RENDERING_CLIPS = "rendering_clips"
    ASSEMBLING = "assembling"
    POST_PRODUCTION = "post_production"
    AUDIO_MIXING = "audio_mixing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================
# RENDER JOB CONFIG
# ============================================================

@dataclass
class RenderJobConfig:
    """
    Complete configuration for one render job.
    
    This is what the orchestrator receives from Phase 1 UI.
    """
    # Required
    voice_path: str
    clip_paths: List[str]
    output_path: str
    
    # Optional assets
    intro_path: Optional[str] = None
    outro_path: Optional[str] = None
    music_path: Optional[str] = None
    sfx_paths: Optional[List[str]] = None
    subscribe_overlay: Optional[str] = None
    custom_logo_path: Optional[str] = None
    
    # Quality settings
    quality: str = "480p"
    fps: int = 24
    batch_size: int = 8
    
    # Caption settings
    add_captions: bool = True
    caption_mode: str = "phrase"  # "phrase" or "word"
    caption_style_id: Optional[str] = None
    words_data: Optional[List] = None
    words_path: Optional[str] = None
    transcript_text: Optional[str] = None
    
    # Niche & presets
    niche: str = "default"
    preset_overrides: Optional[Dict] = None
    
    # Timing
    intro_seconds: float = 2.0
    outro_seconds: float = 2.0
    voice_start_offset: Optional[float] = None
    
    # Post-production
    watermark_opacity: float = 0.6
    enable_broll: bool = False
    
    # Advanced
    temp_root: Optional[str] = None
    keep_temp: bool = False
    variation_enabled: bool = True
    use_transitions: bool = True
    
    # Callbacks
    progress_callback: Optional[Callable] = None
    stage_callback: Optional[Callable] = None
    
    def validate(self) -> List[str]:
        """
        Validate configuration. Returns list of error messages.
        Empty list = valid.
        """
        errors = []
        
        if not self.voice_path or not Path(self.voice_path).exists():
            errors.append(f"Voice file not found: {self.voice_path}")
        
        if not self.clip_paths:
            errors.append("No clip paths provided")
        else:
            missing = [c for c in self.clip_paths if not Path(c).exists()]
            if missing:
                errors.append(f"{len(missing)} clip(s) not found: {missing[:3]}...")
        
        if self.music_path and not Path(self.music_path).exists():
            errors.append(f"Music file not found: {self.music_path}")
        
        if self.intro_path and not Path(self.intro_path).exists():
            errors.append(f"Intro file not found: {self.intro_path}")
        
        if self.outro_path and not Path(self.outro_path).exists():
            errors.append(f"Outro file not found: {self.outro_path}")
        
        return errors


# ============================================================
# RENDER ORCHESTRATOR  --  MAIN CLASS
# ============================================================

@dataclass
class OrchestratorProgress:
    """Overall orchestrator progress."""
    stage: PipelineStage = PipelineStage.IDLE
    stage_progress_pct: float = 0.0
    total_clips: int = 0
    clips_rendered: int = 0
    clips_failed: List[int] = field(default_factory=list)
    started_at: Optional[datetime] = None
    estimated_remaining_seconds: float = float('inf')
    current_operation: str = ""
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "stage": self.stage.value,
            "stage_progress_pct": round(self.stage_progress_pct, 1),
            "total_clips": self.total_clips,
            "clips_rendered": self.clips_rendered,
            "clips_failed": len(self.clips_failed),
            "elapsed_seconds": round(
                (datetime.now() - self.started_at).total_seconds() if self.started_at else 0, 1
            ),
            "estimated_remaining_seconds": round(self.estimated_remaining_seconds, 1),
            "current_operation": self.current_operation,
        }


class RenderOrchestrator:
    """
    THE MAIN PIPELINE COORDINATOR.
    
    This class orchestrates the ENTIRE rendering pipeline:
    1. Validate & prepare
    2. Render individual clips (via RenderWorker)
    3. Assemble with transitions
    4. Post-production (captions, watermark, overlay, b-roll)
    5. Audio mixing
    6. Final output & cleanup
    
    USAGE:
        config = RenderJobConfig(
            voice_path="voice.wav",
            clip_paths=["clip1.mp4", "clip2.mp4", ...],
            output_path="final.mp4",
            niche="luxury",
            music_path="bg.mp3",
            add_captions=True,
        )
        
        orch = RenderOrchestrator()
        orch.on_progress(lambda p: print(f"Stage: {p.stage}, {p.stage_progress_pct}%"))
        
        result = orch.render(config)
        print(f"Done! Output: {result}")
    """
    
    def __init__(self):
        # Progress tracking
        self.progress = OrchestratorProgress()
        self._cancel_flag = threading.Event()
        
        # Resource monitoring
        self.resource_monitor = ResourceMonitor()
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            "progress": [],
            "stage_change": [],
            "warning": [],
            "error": [],
            "complete": [],
        }
        
        # Worker & mixer (created per render)
        self._worker: Optional[RenderWorker] = None
        self._mixer: Optional[AudioMixer] = None
        
        logger.info("RenderOrchestrator initialized")
    
    # ================================================================
    # CALLBACK SYSTEM
    # ================================================================
    
    def on_progress(self, callback: Callable):
        """Register progress callback. Called with OrchestratorProgress."""
        self._callbacks["progress"].append(callback)
    
    def on_stage_change(self, callback: Callable):
        """Register stage change callback. Called with PipelineStage."""
        self._callbacks["stage_change"].append(callback)
    
    def on_complete(self, callback: Callable):
        """Register completion callback. Called with (success, output_path, report)."""
        self._callbacks["complete"].append(callback)
    
    def _fire(self, event: str, *args, **kwargs):
        """Fire all callbacks for an event."""
        for cb in self._callbacks.get(event, []):
            try:
                cb(*args, **kwargs)
            except Exception as e:
                logger.error(f"Callback error [{event}]: {e}")
    
    def _set_stage(self, stage: PipelineStage, operation: str = ""):
        """Set current pipeline stage and notify callbacks."""
        self.progress.stage = stage
        self.progress.current_operation = operation
        self.progress.stage_progress_pct = 0.0
        self._fire("stage_change", stage)
        self._fire("progress", self.progress)
        logger.info(f"[STAGE] {stage.value} | {operation}")
    
    def _update_progress(self, stage_pct: float, operation: str = ""):
        """Update stage progress percentage."""
        self.progress.stage_progress_pct = min(99.9, stage_pct)
        if operation:
            self.progress.current_operation = operation
        self._fire("progress", self.progress)
    
    # ================================================================
    # MAIN RENDER METHOD
    # ================================================================
    
    def render(self, config: RenderJobConfig) -> Dict[str, Any]:
        """
        Execute the complete rendering pipeline.
        
        Args:
            config: RenderJobConfig with all settings
        
        Returns:
            {
                "success": bool,
                "output_path": str,
                "report": dict,
                "elapsed_seconds": float,
                "errors": list,
            }
        """
        start_time = time.time()
        self.progress.started_at = datetime.now()
        errors = []
        
        try:
            # ---- STAGE 0: VALIDATE ----
            self._set_stage(PipelineStage.PREPARING, "Validating configuration")
            validation_errors = config.validate()
            if validation_errors:
                for e in validation_errors:
                    logger.error(f"Validation: {e}")
                return {
                    "success": False,
                    "output_path": "",
                    "report": {},
                    "elapsed_seconds": time.time() - start_time,
                    "errors": validation_errors,
                }
            
            # ---- STAGE 1: PREPARE ----
            self._set_stage(PipelineStage.PREPARING, "Loading source files")
            
            # Prepare paths
            output = Path(config.output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            
            temp_root = config.temp_root or str(output.parent / f"_render_temp_{int(time.time())}")
            temp_dir = Path(temp_root)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            seg_dir = temp_dir / "segments"
            batch_dir = temp_dir / "batches"
            seg_dir.mkdir(parents=True, exist_ok=True)
            batch_dir.mkdir(parents=True, exist_ok=True)
            
            # Load clips
            clip_paths = existing_files(config.clip_paths, VIDEO_EXTS)
            if not clip_paths:
                raise FileNotFoundError("No valid clip files found")
            
            # Validate voice
            voice_path = Path(config.voice_path)
            if not voice_path.exists():
                raise FileNotFoundError(f"Voice not found: {voice_path}")
            
            # Calculate timing
            voice_duration = probe_duration(str(voice_path))
            intro_sec = fnum(config.intro_seconds, INTRO_SECONDS)
            outro_sec = fnum(config.outro_seconds, OUTRO_SECONDS)
            voice_offset = fnum(config.voice_start_offset, intro_sec) if config.voice_start_offset else intro_sec
            body_duration = voice_duration
            total_duration = intro_sec + body_duration + outro_sec
            
            # Initialize variation engine
            if config.variation_enabled and HAS_RENDER_ENGINE:
                var_engine = get_variation_engine(reset=True)
                logger.info("Variation Intelligence Engine: ACTIVE")
            else:
                logger.info("Variation Intelligence Engine: DISABLED")
            
            # Calculate clip durations
            size = quality_to_size(config.quality)
            quality = normalize_quality(config.quality)
            fps = min(max(12, int(config.fps or DEFAULT_FPS)), 24)
            batch_size = max(2, min(16, int(config.batch_size or DEFAULT_BATCH_SIZE)))
            
            scene_durations = duration_plan(body_duration, len(clip_paths))
            
            logger.info(f"Prepared: {len(clip_paths)} clips | "
                       f"voice={voice_duration:.1f}s | total={total_duration:.1f}s | "
                       f"intro={intro_sec}s | outro={outro_sec}s | "
                       f"quality={config.quality} | size={size}")
            
            self.progress.total_clips = len(clip_paths)
            
            # ---- STAGE 2: RENDER CLIPS ----
            self._set_stage(PipelineStage.RENDERING_CLIPS,
                          f"Rendering {len(clip_paths)} clips")
            
            rendered_segments = []
            corrupt_clips = []
            
            # Render intro if provided
            if config.intro_path and Path(config.intro_path).exists():
                intro_out = batch_dir / "intro_normalized.mp4"
                normalize_video_asset(config.intro_path, intro_out, size, fps, intro_sec, quality)
                rendered_segments.append(intro_out)
                logger.info(f"Intro normalized: {intro_sec}s")
            
            # Render clips in batches
            for batch_start, batch_clips in chunked(clip_paths, batch_size):
                if self._cancel_flag.is_set():
                    raise InterruptedError("Render cancelled by user")
                
                batch_num = batch_start // batch_size + 1
                self._update_progress(
                    (batch_start / len(clip_paths)) * 100,
                    f"Batch {batch_num}: clips {batch_start+1}-{batch_start+len(batch_clips)}"
                )
                
                # Check resources before each batch
                resources = self.resource_monitor.check_all(str(temp_dir))
                if not resources["all_ok"]:
                    for w in resources["warnings"]:
                        logger.warning(f"Resource warning: {w}")
                        self.progress.warnings.append(w)
                
                batch_segments = []
                for local_i, clip_src in enumerate(batch_clips):
                    global_i = batch_start + local_i
                    seg_out = seg_dir / f"seg_{global_i+1:05d}.mp4"
                    
                    # Get variation data for this clip
                    variation_data = None
                    if config.variation_enabled and HAS_RENDER_ENGINE:
                        try:
                            variation_data = get_variation_engine().get_clip_variation(
                                clip_index=global_i,
                                clip_duration=scene_durations[global_i],
                                base_niche=config.niche,
                            )
                        except Exception as e:
                            logger.warning(f"Variation failed for clip {global_i}: {e}")
                    
                    # Render the clip
                    try:
                        if config.progress_callback:
                            try:
                                config.progress_callback(global_i + 1, len(clip_paths), str(clip_src))
                            except Exception:
                                pass
                        
                        render_clip_segment(
                            src=str(clip_src),
                            out=str(seg_out),
                            wanted=scene_durations[global_i],
                            index=global_i,
                            size=size,
                            fps=fps,
                            quality=quality,
                            niche=config.niche,
                            variation_data=variation_data,
                        )
                        
                        batch_segments.append(seg_out)
                        self.progress.clips_rendered += 1
                        
                    except Exception as e:
                        error_msg = str(e)[-300:]
                        logger.error(f"Clip {global_i} failed: {error_msg}")
                        corrupt_clips.append({
                            "clip_index": global_i,
                            "clip_path": str(clip_src),
                            "error": error_msg,
                        })
                        self.progress.clips_failed.append(global_i)
                    
                    gc.collect()
                
                # Concat batch segments
                if batch_segments:
                    batch_out = batch_dir / f"batch_{batch_num:04d}.mp4"
                    concat_files(
                        batch_segments, batch_out,
                        niche=config.niche,
                        use_transitions=config.use_transitions,
                        global_index_offset=batch_start,
                    )
                    rendered_segments.append(batch_out)
                
                # Cleanup individual segments (keep batch output)
                for s in batch_segments:
                    try:
                        s.unlink(missing_ok=True)
                    except Exception:
                        pass
                
                gc.collect()
            
            if not rendered_segments:
                raise RuntimeError("No clips were successfully rendered")
            
            logger.info(f"Clips rendered: {self.progress.clips_rendered}/{len(clip_paths)} "
                       f"| failed: {len(corrupt_clips)}")
            
            # ---- STAGE 3: ASSEMBLE ----
            self._set_stage(PipelineStage.ASSEMBLING, "Assembling video with transitions")
            
            # Render outro if provided
            outro_out = None
            if config.outro_path and Path(config.outro_path).exists():
                outro_out = batch_dir / "outro_normalized.mp4"
                normalize_video_asset(config.outro_path, outro_out, size, fps, outro_sec, quality)
                logger.info(f"Outro normalized: {outro_sec}s")
            
            # Concat all segments into body
            body_raw = temp_dir / "video_body_raw.mp4"
            concat_files(
                rendered_segments, body_raw,
                niche=config.niche,
                use_transitions=config.use_transitions,
                global_index_offset=0,
            )
            
            # BUG 1 FIX: Separate body and outro
            body_target = (total_duration - outro_sec) if outro_out else total_duration
            body_fixed = self._fit_body_duration(body_raw, body_target, temp_dir, size, fps, quality)
            
            if outro_out:
                video_raw = temp_dir / "video_raw.mp4"
                concat_files(
                    [body_fixed, outro_out], video_raw,
                    niche=config.niche,
                    use_transitions=False,
                    global_index_offset=0,
                )
                logger.info(f"Outro appended at {body_target:.1f}s "
                           f"(occupies last {outro_sec}s)")
            else:
                video_raw = body_fixed
            
            self._update_progress(50, "Video assembled")
            current_video = video_raw
            
            # ---- STAGE 4: POST-PRODUCTION ----
            self._set_stage(PipelineStage.POST_PRODUCTION, "Applying post-production effects")
            
            # Subscribe overlay
            if config.subscribe_overlay and Path(config.subscribe_overlay).exists():
                self._update_progress(60, "Applying subscribe overlay")
                sub_out = temp_dir / "video_subscribed.mp4"
                current_video, shown, sub_start, sub_dur = apply_subscribe_overlay_mid(
                    str(current_video), str(config.subscribe_overlay),
                    str(sub_out), intro_sec, voice_duration, total_duration
                )
                if shown:
                    logger.info(f"Subscribe overlay: {sub_start:.1f}s-{sub_start+sub_dur:.1f}s")
                current_video = Path(current_video)
            
            # B-Roll overlay
            if config.enable_broll:
                self._update_progress(65, "Applying B-roll overlay")
                broll_out = temp_dir / "video_broll.mp4"
                current_video = apply_broll_overlay(
                    str(current_video), str(broll_out), total_duration
                )
                current_video = Path(current_video)
            
            # Captions
            if config.add_captions:
                self._update_progress(70, "Burning captions")
                captioned = temp_dir / "video_captioned.mp4"
                current_video = burn_captions(
                    video=str(current_video),
                    out=str(captioned),
                    voice_path=str(voice_path),
                    words=config.words_data,
                    words_path=config.words_path,
                    transcript_text=config.transcript_text,
                    caption_mode=config.caption_mode,
                    style_id=config.caption_style_id,
                    size=size,
                    caption_offset=voice_offset,
                    niche=config.niche,
                )
                current_video = Path(current_video)
            else:
                logger.info("Captions: SKIPPED (add_captions=False)")
            
            # Watermark
            self._update_progress(80, "Applying watermark")
            wm_out = temp_dir / "video_watermarked.mp4"
            current_video = apply_niche_watermark(
                v=str(current_video),
                o=str(wm_out),
                n=config.niche,
                custom_logo_path=config.custom_logo_path,
                opacity=config.watermark_opacity,
            )
            current_video = Path(current_video)
            
            # ---- STAGE 5: AUDIO MIX ----
            self._set_stage(PipelineStage.AUDIO_MIXING, "Mixing audio")
            
            music_file = config.music_path if config.music_path and Path(config.music_path).exists() else None
            sfx_file = first_existing(config.sfx_paths, AUDIO_EXTS) if config.sfx_paths else None
            
            final_output = output
            
            if HAS_MIXER:
                mixer = AudioMixer()
                audio_config = AudioMixConfig(
                    video_path=str(current_video),
                    voice_path=str(voice_path),
                    output_path=str(final_output),
                    music_path=str(music_file) if music_file else None,
                    sfx_path=str(sfx_file) if sfx_file else None,
                    niche=config.niche,
                    total_duration=total_duration,
                    intro_seconds=voice_offset,
                    voice_duration=voice_duration,
                    outro_seconds=outro_sec,
                )
                mixer.mix(audio_config)
                
                if config.preset_overrides and "audio_profile" in config.preset_overrides:
                    # Custom audio profile was used
                    logger.info("Custom audio profile applied")
            elif HAS_RENDER_ENGINE:
                # Fallback: use batch_long_renderer's audio function
                mux_audio_timeline(
                    video=str(current_video),
                    voice=str(voice_path),
                    out=str(final_output),
                    music=str(music_file) if music_file else None,
                    sfx=str(sfx_file) if sfx_file else None,
                    total_duration=total_duration,
                    intro_sec=voice_offset,
                    voice_duration=voice_duration,
                    niche=config.niche,
                    audio_profile=config.preset_overrides.get("audio_profile") if config.preset_overrides else None,
                )
            else:
                # No mixer available  --  just copy video with original audio
                shutil.copy2(str(current_video), str(final_output))
                logger.warning("No audio mixer available  --  video has no audio")
            
            # ---- STAGE 6: FINALIZE ----
            self._set_stage(PipelineStage.FINALIZING, "Saving render report")
            
            # Build report
            report = {
                "engine": "render_orchestrator_v1.0",
                "clips_input": len(clip_paths),
                "clips_rendered": self.progress.clips_rendered,
                "corrupt_skipped": corrupt_clips,
                "quality": quality,
                "size": {"width": size[0], "height": size[1]},
                "fps": fps,
                "batch_size": batch_size,
                "voice_duration": voice_duration,
                "intro_seconds": intro_sec,
                "voice_start_offset": voice_offset,
                "outro_seconds": outro_sec,
                "total_duration": total_duration,
                "intro_used": bool(config.intro_path and Path(config.intro_path).exists()),
                "outro_used": bool(config.outro_path and Path(config.outro_path).exists()),
                "captions_enabled": config.add_captions,
                "music_used": bool(music_file),
                "sfx_used": bool(sfx_file),
                "watermark_applied": True,
                "subscribe_overlay_used": bool(
                    config.subscribe_overlay and Path(config.subscribe_overlay).exists()
                ),
                "variation_engine": config.variation_enabled,
                "niche": config.niche,
                "output": str(final_output),
                "elapsed_seconds": round(time.time() - start_time, 2),
                "pipeline_stages_completed": 6,
            }
            
            # Save report
            try:
                report_path = final_output.with_suffix(".render_report.json")
                report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            except Exception as e:
                logger.warning(f"Failed to save report: {e}")
            
            # Save corrupt clips log
            if corrupt_clips:
                try:
                    corrupt_path = final_output.parent / "corrupt_clips.json"
                    corrupt_path.write_text(json.dumps(corrupt_clips, indent=2), encoding="utf-8")
                except Exception:
                    pass
            
            # ---- CLEANUP ----
            if not config.keep_temp:
                self._update_progress(99, "Cleaning up temp files")
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info("Temp files cleaned up")
                except Exception as e:
                    logger.warning(f"Cleanup failed: {e}")
            
            self._set_stage(PipelineStage.COMPLETED, "Render complete!")
            
            elapsed = time.time() - start_time
            logger.info(f"RENDER COMPLETE | {elapsed:.1f}s | output={final_output}")
            
            result = {
                "success": True,
                "output_path": str(final_output),
                "report": report,
                "elapsed_seconds": round(elapsed, 2),
                "errors": [],
            }
            
            self._fire("complete", True, str(final_output), report)
            return result
            
        except InterruptedError:
            self._set_stage(PipelineStage.CANCELLED, "Render cancelled")
            elapsed = time.time() - start_time
            self._fire("complete", False, "", {"error": "cancelled"})
            return {
                "success": False,
                "output_path": "",
                "report": {"error": "cancelled"},
                "elapsed_seconds": round(elapsed, 2),
                "errors": ["Render cancelled by user"],
            }
            
        except Exception as e:
            self._set_stage(PipelineStage.FAILED, f"Error: {str(e)[:100]}")
            elapsed = time.time() - start_time
            
            error_detail = traceback.format_exc()
            logger.error(f"RENDER FAILED: {e}\n{error_detail}")
            
            result = {
                "success": False,
                "output_path": "",
                "report": {"error": str(e)},
                "elapsed_seconds": round(elapsed, 2),
                "errors": [str(e)],
            }
            
            self._fire("complete", False, "", {"error": str(e)})
            return result
    
    # ================================================================
    # BODY DURATION FITTER (BUG 1 FIX)
    # ================================================================
    
    def _fit_body_duration(self, body_raw: Path, target_duration: float,
                           temp_dir: Path, size: Tuple[int, int],
                           fps: int, quality: str) -> Path:
        """
        Pad or trim body video to exact target duration.
        
        This ensures outro always lands at the correct position.
        BUG 1 FIX: Outro is NEVER included in this operation.
        """
        body_raw = Path(body_raw)
        actual = probe_duration(str(body_raw))
        
        if actual < target_duration - 0.5:
            # Extend by cloning last frame
            fixed = temp_dir / "video_body_fixed.mp4"
            pad = max(0.1, target_duration - actual)
            logger.info(f"Body too short ({actual:.1f}s < {target_duration:.1f}s)  --  "
                       f"extending by {pad:.1f}s (last frame clone)")
            run_cmd([
                FFMPEG, "-y", "-i", str(body_raw),
                "-vf", f"tpad=stop_mode=clone:stop_duration={pad:.3f},"
                       f"trim=0:{target_duration:.3f},setpts=PTS-STARTPTS",
                "-c:v", "libx264", "-preset", "ultrafast",
                "-crf", "30", "-pix_fmt", "yuv420p",
                str(fixed),
            ])
            return fixed
            
        elif actual > target_duration + 0.5:
            # Trim
            fixed = temp_dir / "video_body_fixed.mp4"
            logger.info(f"Body too long ({actual:.1f}s > {target_duration:.1f}s)  --  "
                       f"trimming")
            run_cmd([
                FFMPEG, "-y", "-i", str(body_raw),
                "-t", f"{target_duration:.3f}",
                "-c:v", "libx264", "-preset", "ultrafast",
                "-crf", "30", "-pix_fmt", "yuv420p",
                str(fixed),
            ])
            return fixed
        
        return body_raw
    
    # ================================================================
    # CONTROL
    # ================================================================
    
    def cancel(self):
        """Cancel the current render."""
        logger.info("Cancel requested")
        self._cancel_flag.set()
    
    def get_progress(self) -> dict:
        """Get current progress as dict."""
        return self.progress.to_dict()


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

