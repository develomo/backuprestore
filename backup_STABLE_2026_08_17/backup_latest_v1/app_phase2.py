# app_phase2.py
# ==========================================================
# MY CREATION VIDEO GENERATOR  --  PHASE 2
# GRADIO UI v1.0  --  Render Interface & Control Panel
# ==========================================================
#
# PURPOSE:
# - Phase 1 config → Phase 2 render ka bridge
# - Live progress tracking with progress bars
# - Job queue management UI
# - Render preview & download
# - Error logs & diagnostics
# - Pause/Resume/Cancel controls
# - Niche selector with presets
# - Advanced settings panel
# - Batch render support
#
# UI LAYOUT:
# ┌─────────────────────────────────────────────────────────┐
# │  🎬 MY CREATION  --  Phase 2 Render Studio                 │
# │                                                         │
# │  ┌─────────────────┐  ┌─────────────────────────────┐  │
# │  │ 📁 Project      │  │ ⚙️ Render Settings          │  │
# │  │ - Voice file    │  │ - Quality: 480p/720p        │  │
# │  │ - Clip folder   │  │ - Niche: Luxury/Finance...  │  │
# │  │ - Music file    │  │ - Captions: ON/OFF          │  │
# │  │ - Intro/Outro   │  │ - Watermark opacity         │  │
# │  │ - SFX files     │  │ - Variation Engine: ON/OFF  │  │
# │  └─────────────────┘  └─────────────────────────────┘  │
# │                                                         │
# │  ┌─────────────────────────────────────────────────┐   │
# │  │ 🎯 Render Queue                                 │   │
# │  │ ┌───────────────────────────────────────────┐   │   │
# │  │ │ Job 1: Luxury Video │ Rendering... 67%    │   │   │
# │  │ │ ⏸️ Pause  ⏹️ Cancel                       │   │   │
# │  │ └───────────────────────────────────────────┘   │   │
# │  │ ┌───────────────────────────────────────────┐   │   │
# │  │ │ Job 2: Finance │ Queued...                │   │   │
# │  │ │ ❌ Remove                                  │   │   │
# │  │ └───────────────────────────────────────────┘   │   │
# │  └─────────────────────────────────────────────────┘   │
# │                                                         │
# │  ┌─────────────────────────────────────────────────┐   │
# │  │ 📊 Live Progress                               │   │
# │  │ [████████████████████░░░░░░░░] 67%              │   │
# │  │ Stage: Rendering Clips | ETA: 2m 35s           │   │
# │  │ Clips: 8/12 rendered | RAM: 67% | Disk: 12GB   │   │
# │  └─────────────────────────────────────────────────┘   │
# │                                                         │
# │  [▶️ START RENDER]  [⏸️ PAUSE ALL]  [🔄 RESET]      │
# └─────────────────────────────────────────────────────────┘
# ==========================================================

from __future__ import annotations

import os
import gc
import json
import time
import shutil
import logging
import traceback
import threading
from pathlib import Path
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger("AppPhase2")
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
# IMPORTS  --  Phase 2 Modules
# ============================================================

try:
    from render_orchestrator import (
        RenderOrchestrator,
        RenderJobConfig,
        PipelineStage,
    )
    HAS_ORCHESTRATOR = True
except ImportError:
    HAS_ORCHESTRATOR = False
    logger.warning("render_orchestrator.py not found")

try:
    from task_manager import (
        TaskManager,
        RenderJob,
        JobStatus,
        JobPriority,
        create_default_manager,
    )
    HAS_TASK_MANAGER = True
except ImportError:
    HAS_TASK_MANAGER = False
    logger.warning("task_manager.py not found")

try:
    from batch_long_renderer import (
        probe_duration,
        existing_files,
        VIDEO_EXTS,
        AUDIO_EXTS,
        IMAGE_EXTS,
    )
    HAS_UTILS = True
except ImportError:
    HAS_UTILS = False
    logger.warning("batch_long_renderer.py not found")


# ============================================================
# GRADIO IMPORT
# ============================================================

try:
    import gradio as gr
    HAS_GRADIO = True
except ImportError:
    HAS_GRADIO = False
    logger.error("gradio not installed! Install with: pip install gradio")


# ============================================================
# CONSTANTS
# ============================================================

APP_TITLE = "🎬 MY CREATION  --  Phase 2 Render Studio"
APP_DESCRIPTION = """
## Professional Video Render Pipeline

Upload your Phase 1 assets and render professional-quality videos with:
- 🎯 **Variation Intelligence**  --  every clip unique
- 🎵 **Auto Audio Mixing**  --  voice + music + SFX
- 📝 **Smart Captions**  --  word-level or phrase mode
- 🎨 **12 Niche Presets**  --  Luxury, Finance, AI, Mystery...
- ⚡ **Batch Processing**  --  render multiple videos
"""

NICHE_CHOICES = [
    "default", "luxury", "luxury_lifestyle", "mystery",
    "ai", "quantum_future", "finance", "finance_simulation",
    "islamic", "home_design", "interior_design", "stoic",
]

QUALITY_CHOICES = ["480p", "720p", "360p"]

CAPTION_MODES = ["phrase", "word"]

PRIORITY_CHOICES = ["normal", "high", "urgent", "low", "background"]


# ============================================================
# GLOBAL STATE
# ============================================================

class AppState:
    """
    Global application state.
    
    Holds references to:
    - TaskManager instance
    - Current job tracking
    - UI update callbacks
    """
    def __init__(self):
        self.task_manager: Optional[TaskManager] = None
        self.current_job_id: Optional[str] = None
        self.output_files: List[str] = []
        self.logs: List[str] = []
        self._lock = threading.Lock()
    
    def add_log(self, msg: str):
        """Add a log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {msg}"
        with self._lock:
            self.logs.append(log_line)
            if len(self.logs) > 500:
                self.logs = self.logs[-500:]
        logger.info(msg)
    
    def clear_logs(self):
        """Clear all logs."""
        with self._lock:
            self.logs.clear()
    
    def get_logs(self) -> str:
        """Get all logs as string."""
        with self._lock:
            return "\n".join(self.logs[-100:])


app_state = AppState()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def scan_directory_for_media(directory: str) -> Dict[str, List[str]]:
    """
    Scan a directory and categorize media files.
    
    Returns:
        {
            "videos": [...],
            "audio": [...],
            "images": [...],
            "total": int,
        }
    """
    result = {"videos": [], "audio": [], "images": [], "total": 0}
    
    if not directory or not Path(directory).exists():
        return result
    
    dir_path = Path(directory)
    
    for f in sorted(dir_path.iterdir()):
        if not f.is_file():
            continue
        suffix = f.suffix.lower()
        if suffix in VIDEO_EXTS:
            result["videos"].append(str(f))
        elif suffix in AUDIO_EXTS:
            result["audio"].append(str(f))
        elif suffix in IMAGE_EXTS:
            result["images"].append(str(f))
    
    result["total"] = len(result["videos"]) + len(result["audio"]) + len(result["images"])
    return result


def validate_phase2_inputs(
    voice_file: str,
    clip_dir: str,
    output_name: str,
) -> Tuple[bool, str]:
    """
    Validate user inputs before starting render.
    
    Returns:
        (is_valid, error_message)
    """
    if not voice_file:
        return False, "❌ Voice file is required"
    
    voice_path = Path(voice_file)
    if not voice_path.exists():
        return False, f"❌ Voice file not found: {voice_file}"
    
    if not voice_path.suffix.lower() in AUDIO_EXTS:
        return False, f"❌ Voice file must be audio: {voice_file}"
    
    if not clip_dir:
        return False, "❌ Clip directory is required"
    
    clip_path = Path(clip_dir)
    if not clip_path.exists():
        return False, f"❌ Clip directory not found: {clip_dir}"
    
    if not clip_path.is_dir():
        return False, f"❌ Clip path must be a directory: {clip_dir}"
    
    # Check for video files
    scan = scan_directory_for_media(clip_dir)
    if scan["total"] == 0:
        return False, f"❌ No media files found in: {clip_dir}"
    if not scan["videos"]:
        return False, f"❌ No video files found in: {clip_dir}"
    
    if not output_name:
        return False, "❌ Output name is required"
    
    return True, "✅ Inputs valid"


def create_render_config(
    voice_file: str,
    clip_dir: str,
    output_name: str,
    niche: str,
    quality: str,
    add_captions: bool,
    caption_mode: str,
    music_file: Optional[str],
    sfx_dir: Optional[str],
    intro_file: Optional[str],
    outro_file: Optional[str],
    use_transitions: bool,
    variation_enabled: bool,
    watermark_opacity: float,
    batch_size: int,
    output_dir: str = "outputs",
) -> RenderJobConfig:
    """
    Create a RenderJobConfig from UI inputs.
    
    Args:
        voice_file: Path to voice-over audio
        clip_dir: Directory containing source clips
        output_name: Base name for output file
        niche: Niche selection
        quality: Quality preset
        add_captions: Enable captions
        caption_mode: "phrase" or "word"
        music_file: Optional background music
        sfx_dir: Optional SFX directory
        intro_file: Optional intro video
        outro_file: Optional outro video
        use_transitions: Enable transitions
        variation_enabled: Enable Variation Intelligence
        watermark_opacity: 0.0-1.0
        batch_size: Clip batch size
        output_dir: Output directory
    
    Returns:
        RenderJobConfig object
    """
    # Scan clip directory
    scan = scan_directory_for_media(clip_dir)
    
    # Find SFX files
    sfx_paths = None
    if sfx_dir and Path(sfx_dir).exists():
        sfx_scan = scan_directory_for_media(sfx_dir)
        if sfx_scan["audio"]:
            sfx_paths = sfx_scan["audio"]
            app_state.add_log(f"Found {len(sfx_paths)} SFX files")
    
    # Create output directory
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = str(out_dir / f"{output_name}_{niche}_{timestamp}.mp4")
    
    # Probe voice duration
    voice_duration = 60.0
    if HAS_UTILS and Path(voice_file).exists():
        try:
            voice_duration = probe_duration(voice_file)
            app_state.add_log(f"Voice duration: {voice_duration:.1f}s")
        except Exception:
            pass
    
    # Create config
    config = RenderJobConfig(
        voice_path=voice_file,
        clip_paths=scan["videos"],
        output_path=output_path,
        intro_path=intro_file if intro_file else None,
        outro_path=outro_file if outro_file else None,
        music_path=music_file if music_file else None,
        sfx_paths=sfx_paths,
        quality=quality,
        batch_size=batch_size,
        add_captions=add_captions,
        caption_mode=caption_mode,
        niche=niche,
        watermark_opacity=watermark_opacity / 100.0,  # Convert from percentage
        variation_enabled=variation_enabled,
        use_transitions=use_transitions,
        intro_seconds=2.0,
        outro_seconds=2.0,
    )
    
    app_state.add_log(f"Config created: {len(scan['videos'])} clips | "
                     f"voice={voice_duration:.1f}s | niche={niche}")
    
    return config


# ============================================================
# RENDER HANDLER
# ============================================================

def start_render(
    voice_file: str,
    clip_dir: str,
    output_name: str,
    niche: str,
    quality: str,
    add_captions: bool,
    caption_mode: str,
    music_file: Optional[str],
    sfx_dir: Optional[str],
    intro_file: Optional[str],
    outro_file: Optional[str],
    use_transitions: bool,
    variation_enabled: bool,
    watermark_opacity: float,
    batch_size: int,
    priority: str,
    progress=gr.Progress(),
) -> Tuple[str, str, str, str]:
    """
    Start a render job from UI inputs.
    
    Returns:
        (status_html, progress_bar_update, logs, output_file)
    """
    # Validate
    is_valid, msg = validate_phase2_inputs(voice_file, clip_dir, output_name)
    if not is_valid:
        app_state.add_log(msg)
        return (
            f"<div style='color:red;font-weight:bold'>{msg}</div>",
            gr.update(value=0),
            app_state.get_logs(),
            "",
        )
    
    # Create config
    try:
        config = create_render_config(
            voice_file=voice_file,
            clip_dir=clip_dir,
            output_name=output_name,
            niche=niche,
            quality=quality,
            add_captions=add_captions,
            caption_mode=caption_mode,
            music_file=music_file,
            sfx_dir=sfx_dir,
            intro_file=intro_file,
            outro_file=outro_file,
            use_transitions=use_transitions,
            variation_enabled=variation_enabled,
            watermark_opacity=watermark_opacity,
            batch_size=int(batch_size),
        )
    except Exception as e:
        error_msg = f"Failed to create config: {e}"
        app_state.add_log(error_msg)
        return (
            f"<div style='color:red;font-weight:bold'>❌ {error_msg}</div>",
            gr.update(value=0),
            app_state.get_logs(),
            "",
        )
    
    # Initialize task manager if needed
    if app_state.task_manager is None:
        app_state.task_manager = create_default_manager(max_concurrent=1)
        app_state.task_manager.on("job_completed", _on_job_completed)
        app_state.task_manager.on("job_failed", _on_job_failed)
        app_state.task_manager.on("job_progress", _on_job_progress)
        app_state.task_manager.start()
    
    # Add job
    job_name = f"{output_name} [{niche}]"
    job_id = app_state.task_manager.add_job(
        config=config,
        name=job_name,
        priority=priority,
    )
    
    app_state.current_job_id = job_id
    app_state.add_log(f"🚀 Render started: {job_name} (ID: {job_id})")
    
    status_html = f"""
    <div style='background:#e8f5e9;padding:12px;border-radius:8px;border-left:4px solid #4caf50'>
        <b>✅ Render Queued!</b><br/>
        <small>Job: {job_name}</small><br/>
        <small>Niche: {niche} | Quality: {quality}</small><br/>
        <small>Clips: {len(config.clip_paths)} | Captions: {'ON' if add_captions else 'OFF'}</small><br/>
        <small>Output: {config.output_path}</small>
    </div>
    """
    
    return (
        status_html,
        gr.update(value=5),  # Initial progress
        app_state.get_logs(),
        config.output_path,
    )


def _on_job_completed(job: RenderJob):
    """Callback: job completed successfully."""
    app_state.add_log(f"✅ COMPLETED: {job.name} | output={job.output_path}")
    app_state.output_files.append(job.output_path)


def _on_job_failed(job: RenderJob):
    """Callback: job failed."""
    app_state.add_log(f"❌ FAILED: {job.name} | error={job.error_message}")


def _on_job_progress(job: RenderJob):
    """Callback: job progress update."""
    pass  # Progress is polled by UI, not pushed


# ============================================================
# PROGRESS POLLER
# ============================================================

def poll_progress() -> Tuple[float, str, str]:
    """
    Poll current job progress for UI updates.
    
    Returns:
        (progress_pct, status_html, logs)
    """
    if not app_state.task_manager or not app_state.current_job_id:
        return 0.0, "<div style='color:#888'>No active job</div>", app_state.get_logs()
    
    job = app_state.task_manager.get_job(app_state.current_job_id)
    
    if not job:
        return 0.0, "<div style='color:#888'>Job not found</div>", app_state.get_logs()
    
    progress = job.progress_pct
    status = job.status.value
    
    # Status color
    color_map = {
        "completed": "#4caf50",
        "failed": "#f44336",
        "cancelled": "#ff9800",
        "paused": "#2196f3",
        "queued": "#9e9e9e",
        "preparing": "#2196f3",
        "rendering": "#2196f3",
        "assembling": "#9c27b0",
        "post_processing": "#9c27b0",
        "audio_mixing": "#ff5722",
        "finalizing": "#009688",
    }
    color = color_map.get(status, "#888")
    
    # ETA
    eta_str = ""
    if job.estimated_remaining_seconds and job.estimated_remaining_seconds != float('inf'):
        eta_mins = int(job.estimated_remaining_seconds // 60)
        eta_secs = int(job.estimated_remaining_seconds % 60)
        eta_str = f"ETA: {eta_mins}m {eta_secs}s | "
    
    status_html = f"""
    <div style='background:#f5f5f5;padding:10px;border-radius:8px;border-left:4px solid {color}'>
        <b>Status:</b> {status.upper()}<br/>
        <small>{eta_str}Clips: {job.clips_completed}/{job.total_clips}</small><br/>
        <small>Stage: {job.current_stage}</small>
    </div>
    """
    
    return progress, status_html, app_state.get_logs()


# ============================================================
# CONTROL HANDLERS
# ============================================================

def pause_current_job() -> str:
    """Pause the current render job."""
    if not app_state.task_manager or not app_state.current_job_id:
        return "No active job to pause"
    
    success = app_state.task_manager.pause_job(app_state.current_job_id)
    if success:
        app_state.add_log("⏸️ Render PAUSED")
        return "⏸️ Render paused"
    return "Could not pause job"


def resume_current_job() -> str:
    """Resume the current render job."""
    if not app_state.task_manager or not app_state.current_job_id:
        return "No paused job to resume"
    
    success = app_state.task_manager.resume_job(app_state.current_job_id)
    if success:
        app_state.add_log("▶️ Render RESUMED")
        return "▶️ Render resumed"
    return "Could not resume job"


def cancel_current_job() -> str:
    """Cancel the current render job."""
    if not app_state.task_manager or not app_state.current_job_id:
        return "No active job to cancel"
    
    success = app_state.task_manager.cancel_job(app_state.current_job_id)
    if success:
        app_state.add_log("⏹️ Render CANCELLED")
        return "⏹️ Render cancelled"
    return "Could not cancel job"


def reset_all() -> Tuple[str, str, str, float]:
    """Reset all state."""
    if app_state.task_manager:
        app_state.task_manager.shutdown(wait=False)
    
    app_state.task_manager = None
    app_state.current_job_id = None
    app_state.output_files.clear()
    app_state.clear_logs()
    
    return (
        "<div style='color:#888'>Ready for new render</div>",
        app_state.get_logs(),
        "",
        0.0,
    )


# ============================================================
# Niche Info
# ============================================================

def get_niche_info(niche: str) -> str:
    """Get descriptive info about a niche."""
    info = {
        "default": "📋 **Default**  --  Balanced. Works for any content type.",
        "luxury": "💎 **Luxury**  --  Rich, warm tones. Zoom 1.075-1.115. Elegant feel.",
        "luxury_lifestyle": "💎 **Luxury Lifestyle**  --  Same as Luxury. Premium aesthetic.",
        "mystery": "🌑 **Mystery**  --  Dark, atmospheric. Zoom 1.085-1.125. Tension.",
        "ai": "🤖 **AI / Tech**  --  Bright, futuristic. Zoom 1.090-1.130. High-energy.",
        "quantum_future": "🔮 **Quantum Future**  --  Same as AI. Sci-fi aesthetic.",
        "finance": "📊 **Finance**  --  Clean, authoritative. Zoom 1.045-1.075. Professional.",
        "finance_simulation": "📊 **Finance Simulation**  --  Same as Finance.",
        "islamic": "🕌 **Islamic**  --  Soft, respectful. Zoom 1.040-1.070. Minimal music.",
        "home_design": "🏠 **Home Design**  --  Warm, inviting. Zoom 1.060-1.095. Cozy.",
        "interior_design": "🏠 **Interior Design**  --  Same as Home Design.",
        "stoic": "🧘 **Stoic**  --  Minimal, meditative. Zoom 1.040-1.075. Very subtle.",
    }
    return info.get(niche, info["default"])


# ============================================================
# BUILD GRADIO UI
# ============================================================

def build_ui() -> gr.Blocks:
    """
    Build the complete Gradio UI for Phase 2.
    
    Returns:
        gr.Blocks instance ready for launch
    """
    if not HAS_GRADIO:
        raise ImportError("Gradio is not installed")
    
    css = """
    .render-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: bold !important;
        font-size: 16px !important;
        border: none !important;
        padding: 12px 24px !important;
    }
    .control-btn {
        font-size: 14px !important;
        padding: 8px 16px !important;
    }
    .status-box {
        min-height: 60px;
    }
    .log-box textarea {
        font-family: 'Consolas', 'Monaco', monospace !important;
        font-size: 12px !important;
        background: #1a1a2e !important;
        color: #00ff88 !important;
    }
    """
    
    with gr.Blocks(
        title=APP_TITLE,
        theme=gr.themes.Soft(),
        css=css,
    ) as app:
        
        # Header
        gr.Markdown(f"# {APP_TITLE}")
        gr.Markdown(APP_DESCRIPTION)
        
        # ============================================================
        # ROW 1: Project Files + Render Settings
        # ============================================================
        
        with gr.Row():
            # ---- LEFT: Project Files ----
            with gr.Column(scale=1):
                gr.Markdown("### 📁 Project Files")
                
                voice_file = gr.File(
                    label="🎤 Voice-Over Audio",
                    file_types=[".mp3", ".wav", ".m4a", ".aac", ".flac"],
                    type="filepath",
                )
                
                clip_dir = gr.Textbox(
                    label="🎬 Clips Directory",
                    placeholder="/path/to/your/clips/folder",
                    info="Folder containing all source video clips",
                )
                
                music_file = gr.File(
                    label="🎵 Background Music (optional)",
                    file_types=[".mp3", ".wav", ".m4a"],
                    type="filepath",
                )
                
                sfx_dir = gr.Textbox(
                    label="🔊 SFX Directory (optional)",
                    placeholder="/path/to/sfx/folder",
                    info="Sound effects for burst playback",
                )
                
                with gr.Row():
                    intro_file = gr.File(
                        label="🎞️ Intro Video (optional)",
                        file_types=[".mp4", ".mov"],
                        type="filepath",
                    )
                    outro_file = gr.File(
                        label="🎞️ Outro Video (optional)",
                        file_types=[".mp4", ".mov"],
                        type="filepath",
                    )
                
                output_name = gr.Textbox(
                    label="📝 Output Name",
                    placeholder="my_amazing_video",
                    value="my_video",
                )
            
            # ---- RIGHT: Render Settings ----
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ Render Settings")
                
                niche = gr.Dropdown(
                    label="🎨 Niche / Style",
                    choices=NICHE_CHOICES,
                    value="default",
                    interactive=True,
                )
                
                niche_info = gr.Markdown(get_niche_info("default"))
                
                quality = gr.Dropdown(
                    label="📐 Quality",
                    choices=QUALITY_CHOICES,
                    value="480p",
                    interactive=True,
                )
                
                with gr.Row():
                    add_captions = gr.Checkbox(
                        label="📝 Enable Captions",
                        value=True,
                    )
                    caption_mode = gr.Dropdown(
                        label="Caption Mode",
                        choices=CAPTION_MODES,
                        value="phrase",
                        interactive=True,
                    )
                
                with gr.Row():
                    use_transitions = gr.Checkbox(
                        label="🎬 Smooth Transitions",
                        value=True,
                    )
                    variation_enabled = gr.Checkbox(
                        label="🎯 Variation Intelligence",
                        value=True,
                        info="Every clip gets unique motion/color/animation",
                    )
                
                watermark_opacity = gr.Slider(
                    label="💧 Watermark Opacity",
                    minimum=0,
                    maximum=100,
                    value=60,
                    step=5,
                    info="0 = invisible, 100 = solid",
                )
                
                batch_size = gr.Slider(
                    label="📦 Batch Size",
                    minimum=2,
                    maximum=16,
                    value=8,
                    step=1,
                    info="Clips per batch (lower = less RAM)",
                )
                
                priority = gr.Dropdown(
                    label="⚡ Priority",
                    choices=PRIORITY_CHOICES,
                    value="normal",
                    interactive=True,
                )
        
        # ============================================================
        # ROW 2: Action Buttons
        # ============================================================
        
        with gr.Row():
            start_btn = gr.Button(
                "▶️ START RENDER",
                variant="primary",
                elem_classes=["render-btn"],
                scale=2,
            )
            pause_btn = gr.Button(
                "⏸️ Pause",
                variant="secondary",
                elem_classes=["control-btn"],
                scale=1,
            )
            resume_btn = gr.Button(
                "▶️ Resume",
                variant="secondary",
                elem_classes=["control-btn"],
                scale=1,
            )
            cancel_btn = gr.Button(
                "⏹️ Cancel",
                variant="stop",
                elem_classes=["control-btn"],
                scale=1,
            )
            reset_btn = gr.Button(
                "🔄 Reset",
                variant="secondary",
                elem_classes=["control-btn"],
                scale=1,
            )
        
        # ============================================================
        # ROW 3: Status & Progress
        # ============================================================
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📊 Progress")
                
                progress_bar = gr.Slider(
                    label="Render Progress",
                    minimum=0,
                    maximum=100,
                    value=0,
                    interactive=False,
                )
                
                status_html = gr.HTML(
                    value="<div style='color:#888'>Ready  --  upload files and start render</div>",
                    elem_classes=["status-box"],
                )
                
                output_file = gr.Textbox(
                    label="📁 Output File",
                    interactive=False,
                    placeholder="Output path will appear here...",
                )
        
        # ============================================================
        # ROW 4: Logs
        # ============================================================
        
        with gr.Row():
            gr.Markdown("### 📋 Logs")
        
        logs_output = gr.Textbox(
            label="",
            lines=12,
            max_lines=20,
            interactive=False,
            elem_classes=["log-box"],
            value="Ready...\n",
            autoscroll=True,
        )
        
        # ============================================================
        # EVENT HANDLERS
        # ============================================================
        
        # Niche change → show info
        niche.change(
            fn=get_niche_info,
            inputs=[niche],
            outputs=[niche_info],
        )
        
        # Start render
        start_btn.click(
            fn=start_render,
            inputs=[
                voice_file, clip_dir, output_name,
                niche, quality, add_captions, caption_mode,
                music_file, sfx_dir, intro_file, outro_file,
                use_transitions, variation_enabled,
                watermark_opacity, batch_size, priority,
            ],
            outputs=[status_html, progress_bar, logs_output, output_file],
        )
        
        # Control buttons
        pause_btn.click(
            fn=pause_current_job,
            inputs=[],
            outputs=[status_html],
        )
        
        resume_btn.click(
            fn=resume_current_job,
            inputs=[],
            outputs=[status_html],
        )
        
        cancel_btn.click(
            fn=cancel_current_job,
            inputs=[],
            outputs=[status_html],
        )
        
        reset_btn.click(
            fn=reset_all,
            inputs=[],
            outputs=[status_html, logs_output, output_file, progress_bar],
        )
        
        # Auto-poll progress (every 2 seconds)
        app.load(
            fn=poll_progress,
            inputs=[],
            outputs=[progress_bar, status_html, logs_output],
            every=2,
        )
    
    return app


# ============================================================
# LAUNCH
# ============================================================

def launch_phase2(
    server_name: str = "0.0.0.0",
    server_port: int = 7861,
    share: bool = False,
    debug: bool = False,
):
    """
    Launch the Phase 2 Gradio UI.
    
    Args:
        server_name: Host to bind to
        server_port: Port to listen on
        share: Create public link
        debug: Enable debug mode
    """
    if not HAS_GRADIO:
        print("=" * 60)
        print("ERROR: Gradio is not installed!")
        print("Install it with: pip install gradio")
        print("=" * 60)
        return
    
    app = build_ui()
    
    print("=" * 60)
    print(f"🚀 Phase 2 Render Studio")
    print(f"   Local:  http://{server_name}:{server_port}")
    print(f"   Share:  {'Enabled' if share else 'Disabled'}")
    print("=" * 60)
    
    app.queue(default_concurrency_limit=2)
    app.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        debug=debug,
    )


# ============================================================
# CLI ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 2 Render Studio")
    parser.add_argument("--port", type=int, default=7861, help="Server port")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Server host")
    parser.add_argument("--share", action="store_true", help="Create public link")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    
    args = parser.parse_args()
    
    launch_phase2(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        debug=args.debug,
    )
