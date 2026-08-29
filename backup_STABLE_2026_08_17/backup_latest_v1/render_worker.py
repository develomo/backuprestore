# render_worker.py
# ==========================================================
# MY CREATION VIDEO GENERATOR  --  PHASE 2
# RENDER WORKER v1.0  --  Background Clip Processing Engine
# ==========================================================
#
# PURPOSE:
# - Har ek clip ko alag-alag thread/process mein render karna
# - Temp files manage karna (create, track, cleanup)
# - RAM monitoring ke saath safe rendering
# - Failed clips ko retry karna
# - Progress tracking with callbacks
# - Graceful shutdown support
#
# ARCHITECTURE:
# ┌─────────────────────────────────────────────────────────┐
# │                    RenderWorker                         │
# │                                                         │
# │  ┌──────────┐   ┌──────────┐   ┌──────────────────┐   │
# │  │Job Queue │──▶│ Clip     │──▶│ Temp File        │   │
# │  │(FIFO)    │   │ Renderer │   │ Manager          │   │
# │  └──────────┘   └──────────┘   └──────────────────┘   │
# │       │              │                  │               │
# │       ▼              ▼                  ▼               │
# │  ┌──────────────────────────────────────────────────┐  │
# │  │              Progress Tracker                     │  │
# │  │  - completed_count / total_count                  │  │
# │  │  - current_clip_index                             │  │
# │  │  - failed_clips list                              │  │
# │  │  - elapsed_time / estimated_remaining             │  │
# │  │  - callback triggers                              │  │
# │  └──────────────────────────────────────────────────┘  │
# └─────────────────────────────────────────────────────────┘
#
# DATA FLOW:
#   clip_configs → RenderWorker → render_clip_segment()
#   → temp_file.mp4 → track in registry → concat later
# ==========================================================

from __future__ import annotations

import os
import gc
import time
import json
import shutil
import signal
import hashlib
import logging
import threading
import tempfile
import traceback
from queue import Queue, Empty
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, Future, as_completed

# ============================================================
# IMPORT RENDER ENGINE (same directory)
# ============================================================

try:
    from batch_long_renderer import (
        render_clip_segment,
        get_variation_engine,
        VariationIntelligence,
        probe_duration,
        FFMPEG,
        log as engine_log,
    )
    HAS_RENDER_ENGINE = True
except ImportError:
    HAS_RENDER_ENGINE = False
    print("[WARN] batch_long_renderer.py not found. Worker will run in mock mode.")

# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger("RenderWorker")
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
# RAM MONITOR (lightweight, used by worker)
# ============================================================

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class RamMonitor:
    """
    Lightweight RAM monitor for the worker.
    
    Checks system RAM before processing each clip.
    If RAM exceeds threshold, pauses until it drops.
    """
    
    def __init__(self, max_ram_pct: float = 85.0, min_ram_pct: float = 60.0):
        self.max_ram_pct = max_ram_pct
        self.min_ram_pct = min_ram_pct
        self._paused = False
        self._pause_reason = ""
    
    @property
    def is_paused(self) -> bool:
        return self._paused
    
    @property
    def pause_reason(self) -> str:
        return self._pause_reason
    
    def check(self) -> bool:
        """
        Check RAM usage.
        Returns True if safe to continue processing.
        """
        if not HAS_PSUTIL:
            return True
        
        try:
            ram = psutil.virtual_memory()
            pct = ram.percent
            
            if self._paused:
                if pct <= self.min_ram_pct:
                    logger.info(f"RAM recovered to {pct:.1f}%  --  resuming")
                    self._paused = False
                    self._pause_reason = ""
                    return True
                return False
            
            if pct >= self.max_ram_pct:
                logger.warning(f"RAM at {pct:.1f}%  --  PAUSING worker "
                             f"(threshold: {self.max_ram_pct}%)")
                self._paused = True
                self._pause_reason = f"High RAM: {pct:.1f}%"
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"RAM check failed: {e}")
            return True  # Don't block on error
    
    def wait_until_safe(self, timeout: float = 300.0, check_interval: float = 2.0) -> bool:
        """
        Block until RAM drops below threshold.
        
        Args:
            timeout: Max seconds to wait
            check_interval: Seconds between checks
        
        Returns:
            True if safe, False if timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            if self.check():
                if self._paused:
                    # Extra cooldown after pause
                    time.sleep(5.0)
                return True
            time.sleep(check_interval)
        
        logger.error(f"RAM wait timeout after {timeout}s")
        return False


# ============================================================
# TEMP FILE MANAGER
# ============================================================

@dataclass
class TempFileEntry:
    """Track a single temp file."""
    path: str
    clip_index: int
    size_bytes: int = 0
    duration: float = 0.0
    created_at: str = ""
    status: str = "created"  # created, verified, failed, deleted


class TempFileManager:
    """
    Manages all temporary files created during rendering.
    
    Features:
    - Automatic cleanup on completion
    - Size tracking (warn if disk is filling up)
    - Registry persistence (for crash recovery)
    - Safe deletion with retry
    """
    
    def __init__(self, temp_root: Optional[str] = None, keep_temp: bool = False):
        self.temp_root = Path(temp_root) if temp_root else Path(tempfile.gettempdir()) / "video_render_temp"
        self.temp_root.mkdir(parents=True, exist_ok=True)
        self.keep_temp = keep_temp
        
        # Registry: clip_index → TempFileEntry
        self._registry: Dict[int, TempFileEntry] = {}
        self._registry_file = self.temp_root / "registry.json"
        
        # Load existing registry (crash recovery)
        self._load_registry()
        
        logger.info(f"TempFileManager: root={self.temp_root}, "
                    f"existing_files={len(self._registry)}")
    
    def _load_registry(self):
        """Load registry from disk (crash recovery)."""
        if self._registry_file.exists():
            try:
                data = json.loads(self._registry_file.read_text(encoding="utf-8"))
                for entry_data in data.get("entries", []):
                    entry = TempFileEntry(**entry_data)
                    self._registry[entry.clip_index] = entry
                logger.info(f"Loaded {len(self._registry)} entries from registry")
            except Exception as e:
                logger.warning(f"Failed to load registry: {e}")
    
    def _save_registry(self):
        """Save registry to disk."""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "temp_root": str(self.temp_root),
                "entries": [
                    {
                        "path": e.path,
                        "clip_index": e.clip_index,
                        "size_bytes": e.size_bytes,
                        "duration": e.duration,
                        "created_at": e.created_at,
                        "status": e.status,
                    }
                    for e in self._registry.values()
                ],
            }
            self._registry_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
    
    def allocate_path(self, clip_index: int, extension: str = ".mp4") -> Path:
        """
        Allocate a temp file path for a clip.
        
        Args:
            clip_index: Global clip index
            extension: File extension (default .mp4)
        
        Returns:
            Path object for the temp file
        """
        filename = f"clip_{clip_index:05d}_{hashlib.md5(str(clip_index).encode()).hexdigest()[:6]}{extension}"
        path = self.temp_root / filename
        return path
    
    def register(self, clip_index: int, file_path: Union[str, Path],
                 duration: float = 0.0):
        """
        Register a completed temp file.
        
        Args:
            clip_index: Global clip index
            file_path: Path to rendered file
            duration: Clip duration in seconds
        """
        path = Path(file_path)
        size = path.stat().st_size if path.exists() else 0
        
        entry = TempFileEntry(
            path=str(path),
            clip_index=clip_index,
            size_bytes=size,
            duration=duration,
            created_at=datetime.now().isoformat(),
            status="created",
        )
        
        self._registry[clip_index] = entry
        self._save_registry()
    
    def verify(self, clip_index: int) -> bool:
        """
        Verify that a registered temp file actually exists and is valid.
        
        Args:
            clip_index: Clip index to verify
        
        Returns:
            True if file exists and has size > 0
        """
        entry = self._registry.get(clip_index)
        if not entry:
            return False
        
        path = Path(entry.path)
        if not path.exists():
            entry.status = "failed"
            self._save_registry()
            return False
        
        if path.stat().st_size == 0:
            entry.status = "failed"
            self._save_registry()
            return False
        
        entry.status = "verified"
        entry.size_bytes = path.stat().st_size
        self._save_registry()
        return True
    
    def get_verified_files(self, sort: bool = True) -> List[Path]:
        """
        Get all verified temp files, optionally sorted by clip index.
        
        Returns:
            List of Path objects for verified files
        """
        verified = []
        for idx, entry in sorted(self._registry.items()):
            if entry.status == "verified":
                path = Path(entry.path)
                if path.exists():
                    verified.append(path)
        return verified
    
    def get_total_size_mb(self) -> float:
        """Get total size of all temp files in megabytes."""
        total = 0
        for entry in self._registry.values():
            if entry.status in ("created", "verified"):
                path = Path(entry.path)
                if path.exists():
                    total += path.stat().st_size
        return total / (1024 * 1024)
    
    def get_disk_free_gb(self) -> float:
        """Get free disk space on temp drive in gigabytes."""
        try:
            usage = shutil.disk_usage(self.temp_root)
            return usage.free / (1024 ** 3)
        except Exception:
            return 999.0
    
    def cleanup(self, keep_registry: bool = False):
        """
        Delete all temp files.
        
        Args:
            keep_registry: If True, keep registry file for debugging
        """
        if self.keep_temp:
            logger.info("keep_temp=True  --  skipping cleanup")
            return
        
        deleted = 0
        failed = 0
        
        for entry in list(self._registry.values()):
            path = Path(entry.path)
            if path.exists():
                try:
                    path.unlink()
                    deleted += 1
                except Exception as e:
                    logger.warning(f"Failed to delete {path.name}: {e}")
                    failed += 1
            entry.status = "deleted"
        
        logger.info(f"Cleanup: {deleted} deleted, {failed} failed")
        
        # Remove registry
        if not keep_registry:
            try:
                self._registry_file.unlink(missing_ok=True)
            except Exception:
                pass
        
        # Try to remove temp root if empty
        try:
            remaining = list(self.temp_root.iterdir())
            if not remaining:
                self.temp_root.rmdir()
        except Exception:
            pass
        
        self._registry.clear()


# ============================================================
# CLIP JOB
# ============================================================

@dataclass
class ClipJob:
    """A single clip rendering job."""
    clip_index: int
    source_path: str
    output_path: str
    duration: float
    size: Tuple[int, int] = (854, 480)
    fps: int = 24
    quality: str = "480p"
    niche: str = "default"
    variation_data: Optional[Dict] = None
    retry_count: int = 0
    max_retries: int = 2
    priority: int = 0  # Lower = higher priority
    
    @property
    def job_id(self) -> str:
        return f"clip_{self.clip_index:05d}"


# ============================================================
# PROGRESS TRACKER
# ============================================================

@dataclass
class RenderProgress:
    """Track overall rendering progress."""
    total_clips: int = 0
    completed_clips: int = 0
    failed_clips: List[int] = field(default_factory=list)
    retried_clips: List[int] = field(default_factory=list)
    current_clip: int = -1
    started_at: Optional[datetime] = None
    status: str = "idle"  # idle, running, paused, completed, failed, cancelled
    
    @property
    def progress_pct(self) -> float:
        if self.total_clips == 0:
            return 0.0
        return (self.completed_clips / self.total_clips) * 100
    
    @property
    def elapsed_seconds(self) -> float:
        if not self.started_at:
            return 0.0
        return (datetime.now() - self.started_at).total_seconds()
    
    def estimate_remaining_seconds(self) -> float:
        """Estimate remaining render time."""
        if self.completed_clips == 0:
            return float('inf')
        elapsed = self.elapsed_seconds
        rate = self.completed_clips / max(1, elapsed)
        remaining = self.total_clips - self.completed_clips
        if rate <= 0:
            return float('inf')
        return remaining / rate
    
    def to_dict(self) -> dict:
        return {
            "total_clips": self.total_clips,
            "completed_clips": self.completed_clips,
            "failed_clips": self.failed_clips,
            "retried_clips": self.retried_clips,
            "current_clip": self.current_clip,
            "status": self.status,
            "progress_pct": round(self.progress_pct, 1),
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "estimated_remaining_seconds": round(self.estimate_remaining_seconds(), 1),
        }


# ============================================================
# RENDER WORKER  --  MAIN CLASS
# ============================================================

class RenderWorker:
    """
    Background worker that processes clips one at a time.
    
    FEATURES:
    - Thread-safe job queue (FIFO)
    - Single-clip-at-a-time rendering (RAM safe)
    - Automatic retry for failed clips
    - Progress tracking with callbacks
    - RAM monitoring with auto-pause
    - Temp file registry for crash recovery
    - Graceful shutdown (finishes current clip)
    
    USAGE:
        worker = RenderWorker(temp_root="/tmp/renders")
        worker.on_progress(lambda p: print(f"{p.progress_pct}%"))
        worker.on_complete(lambda success, progress: print("Done!"))
        
        # Submit all jobs
        for clip in clips:
            worker.submit(clip_config, clip_index)
        
        # Start processing (blocking)
        worker.process_all()
        
        # Or start in background (non-blocking)
        worker.start_background()
        # ... do other things ...
        worker.wait()  # Block until done
    """
    
    def __init__(
        self,
        temp_root: Optional[str] = None,
        max_ram_pct: float = 85.0,
        min_ram_pct: float = 60.0,
        max_retries: int = 2,
        keep_temp: bool = False,
        variation_enabled: bool = True,
    ):
        """
        Initialize render worker.
        
        Args:
            temp_root: Directory for temp files (auto-created if None)
            max_ram_pct: Pause if RAM exceeds this percentage
            min_ram_pct: Resume when RAM drops below this
            max_retries: Max retry attempts per failed clip
            keep_temp: Keep temp files after completion
            variation_enabled: Enable Variation Intelligence
        """
        # Temp file management
        self.temp_manager = TempFileManager(temp_root=temp_root, keep_temp=keep_temp)
        
        # RAM monitoring
        self.ram_monitor = RamMonitor(max_ram_pct=max_ram_pct, min_ram_pct=min_ram_pct)
        
        # Job queue
        self._job_queue: Queue = Queue()
        self._pending_jobs: Dict[int, ClipJob] = {}
        
        # Progress tracking
        self.progress = RenderProgress()
        self._progress_lock = threading.Lock()
        
        # Settings
        self.max_retries = max_retries
        self.variation_enabled = variation_enabled
        
        # Control flags
        self._cancel_flag = threading.Event()
        self._pause_flag = threading.Event()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            "progress": [],
            "clip_start": [],
            "clip_done": [],
            "clip_error": [],
            "paused": [],
            "resumed": [],
            "complete": [],
        }
        
        logger.info(f"RenderWorker initialized | max_ram={max_ram_pct}% | "
                    f"retries={max_retries} | variation={variation_enabled}")
    
    # ================================================================
    # CALLBACK SYSTEM
    # ================================================================
    
    def on(self, event: str, callback: Callable):
        """Register an event callback."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
        else:
            logger.warning(f"Unknown event: {event}")
    
    def _fire(self, event: str, *args, **kwargs):
        """Fire all callbacks for an event."""
        for cb in self._callbacks.get(event, []):
            try:
                cb(*args, **kwargs)
            except Exception as e:
                logger.error(f"Callback error [{event}]: {e}")
    
    # ================================================================
    # JOB SUBMISSION
    # ================================================================
    
    def submit(
        self,
        clip_config: dict,
        clip_index: int,
        source_path: str,
        size: Tuple[int, int] = (854, 480),
        fps: int = 24,
        quality: str = "480p",
        niche: str = "default",
        priority: int = 0,
    ):
        """
        Submit a clip for rendering.
        
        Args:
            clip_config: Clip configuration dict (duration, effects, etc.)
            clip_index: Global clip index
            source_path: Path to source video
            size: (width, height) for output
            fps: Target frame rate
            quality: Quality preset
            niche: Niche name
            priority: Lower = higher priority (0 = normal)
        """
        # Allocate temp output path
        output_path = self.temp_manager.allocate_path(clip_index)
        
        # Get variation data if enabled
        variation_data = None
        if self.variation_enabled and HAS_RENDER_ENGINE:
            try:
                engine = get_variation_engine()
                variation_data = engine.get_clip_variation(
                    clip_index=clip_index,
                    clip_duration=clip_config.get("duration", 6.0),
                )
            except Exception as e:
                logger.warning(f"Variation engine failed for clip {clip_index}: {e}")
        
        # Determine actual duration
        duration = clip_config.get("duration", 6.0)
        if variation_data and "humanized_duration" in variation_data:
            duration = variation_data["humanized_duration"]
        
        # Create job
        job = ClipJob(
            clip_index=clip_index,
            source_path=source_path,
            output_path=str(output_path),
            duration=duration,
            size=size,
            fps=fps,
            quality=quality,
            niche=niche,
            variation_data=variation_data,
            priority=priority,
        )
        
        self._pending_jobs[clip_index] = job
        self._job_queue.put((priority, clip_index, job))
        
        with self._progress_lock:
            self.progress.total_clips = max(
                self.progress.total_clips, clip_index + 1
            )
    
    def submit_batch(
        self,
        clip_configs: List[dict],
        source_paths: List[str],
        **kwargs,
    ):
        """
        Submit multiple clips at once.
        
        Args:
            clip_configs: List of clip configuration dicts
            source_paths: List of source video paths (must match length)
            **kwargs: Passed to submit() for each clip
        """
        for i, (config, source) in enumerate(zip(clip_configs, source_paths)):
            self.submit(
                clip_config=config,
                clip_index=i,
                source_path=source,
                **kwargs,
            )
    
    # ================================================================
    # CLIP PROCESSING
    # ================================================================
    
    def _render_single_clip(self, job: ClipJob) -> Tuple[bool, str]:
        """
        Render a single clip.
        
        Returns:
            (success, error_message_or_empty_string)
        """
        try:
            if not HAS_RENDER_ENGINE:
                # Mock mode for testing
                logger.info(f"[MOCK] Rendering clip {job.clip_index}...")
                time.sleep(0.5)
                
                # Create empty file for testing
                Path(job.output_path).parent.mkdir(parents=True, exist_ok=True)
                Path(job.output_path).touch()
                
                self.temp_manager.register(
                    job.clip_index, job.output_path, job.duration
                )
                return True, ""
            
            # Real rendering
            logger.info(f"Rendering clip {job.clip_index}: "
                       f"dur={job.duration:.1f}s, "
                       f"motion={job.variation_data.get('motion_direction_name','?') if job.variation_data else '?'}")
            
            render_clip_segment(
                src=job.source_path,
                out=job.output_path,
                wanted=job.duration,
                index=job.clip_index,
                size=job.size,
                fps=job.fps,
                quality=job.quality,
                niche=job.niche,
                variation_data=job.variation_data,
            )
            
            # Verify output
            if not Path(job.output_path).exists():
                return False, "Output file not created"
            
            if Path(job.output_path).stat().st_size == 0:
                return False, "Output file is empty"
            
            # Register in temp manager
            self.temp_manager.register(
                job.clip_index, job.output_path, job.duration
            )
            
            return True, ""
            
        except Exception as e:
            error_msg = str(e)[-500:]
            logger.error(f"Clip {job.clip_index} render failed: {error_msg}")
            return False, error_msg
    
    def _process_job(self, job: ClipJob):
        """
        Process a single job with retry logic.
        """
        # Check cancel flag
        if self._cancel_flag.is_set():
            return
        
        # Check pause flag
        while self._pause_flag.is_set() and not self._cancel_flag.is_set():
            time.sleep(1.0)
        
        # Check RAM
        if not self.ram_monitor.check():
            self._fire("paused", self.ram_monitor.pause_reason)
            if not self.ram_monitor.wait_until_safe():
                logger.error("RAM timeout  --  skipping clip")
                return
            self._fire("resumed")
        
        # Update progress
        with self._progress_lock:
            self.progress.current_clip = job.clip_index
            self.progress.status = "running"
        
        self._fire("clip_start", job.clip_index, job)
        
        # Render with retry
        success = False
        error_msg = ""
        
        for attempt in range(self.max_retries + 1):
            if self._cancel_flag.is_set():
                break
            
            success, error_msg = self._render_single_clip(job)
            
            if success:
                break
            
            if attempt < self.max_retries:
                logger.warning(f"Retrying clip {job.clip_index} "
                             f"(attempt {attempt + 2}/{self.max_retries + 1})")
                job.retry_count = attempt + 1
                time.sleep(1.0)  # Brief pause before retry
        
        # Update progress
        with self._progress_lock:
            if success:
                self.progress.completed_clips += 1
                self._fire("clip_done", job.clip_index, job)
            else:
                self.progress.failed_clips.append(job.clip_index)
                if job.retry_count > 0:
                    self.progress.retried_clips.append(job.clip_index)
                self._fire("clip_error", job.clip_index, error_msg, job)
            
            self._fire("progress", self.progress)
        
        # Garbage collect after each clip
        gc.collect()
    
    # ================================================================
    # MAIN PROCESSING LOOP
    # ================================================================
    
    def _worker_loop(self):
        """
        Main worker loop  --  runs in background thread.
        Processes jobs from queue until empty or cancelled.
        """
        self._running = True
        
        with self._progress_lock:
            self.progress.started_at = datetime.now()
            self.progress.status = "running"
        
        logger.info(f"Worker started | {self.progress.total_clips} clips queued")
        
        while not self._cancel_flag.is_set():
            try:
                # Get next job (with timeout for cancel check)
                priority, clip_index, job = self._job_queue.get(timeout=1.0)
                
                # Process the job
                self._process_job(job)
                
                self._job_queue.task_done()
                
            except Empty:
                # Queue is empty  --  check if all done
                with self._progress_lock:
                    total_processed = (
                        self.progress.completed_clips +
                        len(self.progress.failed_clips)
                    )
                    if total_processed >= self.progress.total_clips:
                        break
                continue
        
        # Determine final status
        with self._progress_lock:
            if self._cancel_flag.is_set():
                self.progress.status = "cancelled"
            elif len(self.progress.failed_clips) > 0:
                self.progress.status = "completed"  # Completed with failures
            else:
                self.progress.status = "completed"
        
        self._running = False
        
        # Fire completion callback
        success = len(self.progress.failed_clips) == 0
        self._fire("complete", success, self.progress)
        
        logger.info(f"Worker finished | status={self.progress.status} | "
                    f"completed={self.progress.completed_clips}/"
                    f"{self.progress.total_clips} | "
                    f"failed={len(self.progress.failed_clips)} | "
                    f"elapsed={self.progress.elapsed_seconds:.1f}s")
    
    def process_all(self, blocking: bool = True):
        """
        Start processing all submitted jobs.
        
        Args:
            blocking: If True, blocks until all jobs are done.
                      If False, runs in background thread.
        """
        if blocking:
            self._worker_loop()
        else:
            self.start_background()
    
    def start_background(self):
        """Start processing in a background thread (non-blocking)."""
        if self._worker_thread and self._worker_thread.is_alive():
            logger.warning("Worker already running")
            return
        
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name="RenderWorker",
            daemon=True,
        )
        self._worker_thread.start()
    
    def wait(self, timeout: Optional[float] = None):
        """
        Wait for background processing to complete.
        
        Args:
            timeout: Max seconds to wait (None = forever)
        """
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=timeout)
    
    # ================================================================
    # CONTROL
    # ================================================================
    
    def pause(self):
        """Pause processing (finishes current clip first)."""
        logger.info("Pause requested")
        self._pause_flag.set()
        with self._progress_lock:
            self.progress.status = "paused"
    
    def resume(self):
        """Resume processing after pause."""
        logger.info("Resume requested")
        self._pause_flag.clear()
        with self._progress_lock:
            self.progress.status = "running"
    
    def cancel(self):
        """Cancel all processing."""
        logger.info("Cancel requested")
        self._cancel_flag.set()
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def is_paused(self) -> bool:
        return self._pause_flag.is_set()
    
    @property
    def is_cancelled(self) -> bool:
        return self._cancel_flag.is_set()
    
    # ================================================================
    # RESULTS
    # ================================================================
    
    def get_verified_files(self) -> List[Path]:
        """Get all successfully rendered temp files."""
        return self.temp_manager.get_verified_files()
    
    def get_failed_clips(self) -> List[int]:
        """Get list of failed clip indices."""
        with self._progress_lock:
            return list(self.progress.failed_clips)
    
    def get_progress_dict(self) -> dict:
        """Get current progress as dict."""
        with self._progress_lock:
            return {
                **self.progress.to_dict(),
                "is_paused": self.is_paused,
                "is_cancelled": self.is_cancelled,
                "ram_pct": psutil.virtual_memory().percent if HAS_PSUTIL else -1,
                "temp_size_mb": round(self.temp_manager.get_total_size_mb(), 1),
                "disk_free_gb": round(self.temp_manager.get_disk_free_gb(), 1),
            }
    
    def cleanup(self):
        """Clean up all temp files."""
        self.temp_manager.cleanup()


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def render_clips_parallel(
    clip_configs: List[dict],
    source_paths: List[str],
    output_dir: Optional[str] = None,
    on_progress: Optional[Callable] = None,
    on_complete: Optional[Callable] = None,
    **worker_kwargs,
) -> RenderWorker:
    """
    Convenience function: render multiple clips with one call.
    
    Args:
        clip_configs: List of clip configurations
        source_paths: List of source file paths
        output_dir: Directory for temp files
        on_progress: Callback(progress_dict)
        on_complete: Callback(success_bool, progress)
        **worker_kwargs: Passed to RenderWorker constructor
    
    Returns:
        RenderWorker instance (after completion if on_complete not set)
    """
    worker = RenderWorker(temp_root=output_dir, **worker_kwargs)
    
    if on_progress:
        worker.on("progress", lambda p: on_progress(p.to_dict()))
    
    worker.submit_batch(clip_configs, source_paths)
    
    if on_complete:
        worker.on("complete", on_complete)
        worker.start_background()
    else:
        worker.process_all(blocking=True)
    
    return worker


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("RENDER WORKER  --  SELF-TEST")
    print("=" * 60)
    
    # Test with mock clips
    test_configs = [
        {"duration": 3.0, "motion_direction": "center_push", "zoom_level": 1.04},
        {"duration": 5.0, "motion_direction": "left_sweep", "zoom_level": 1.06},
        {"duration": 4.0, "motion_direction": "diagonal", "zoom_level": 1.05},
        {"duration": 6.0, "motion_direction": "bottom_sweep", "zoom_level": 1.07},
        {"duration": 3.5, "motion_direction": "subtle_pulse", "zoom_level": 1.03},
    ]
    
    test_sources = ["test_source.mp4"] * 5
    
    print(f"\n[1] Creating worker with {len(test_configs)} test clips...")
    
    worker = RenderWorker(
        temp_root="/tmp/test_render_worker",
        variation_enabled=False,
    )
    
    def on_prog(p):
        print(f"    Progress: {p.completed_clips}/{p.total_clips} "
              f"({p.progress_pct:.0f}%) | ETA: {p.estimate_remaining_seconds():.0f}s")
    
    def on_done(success, p):
        status = "SUCCESS" if success else "COMPLETED WITH ERRORS"
        print(f"\n[2] Render {status}")
        print(f"    Clips: {p.completed_clips}/{p.total_clips}")
        print(f"    Failed: {p.failed_clips}")
        print(f"    Elapsed: {p.elapsed_seconds:.1f}s")
    
    worker.on("progress", on_prog)
    worker.on("complete", on_done)
    
    worker.submit_batch(test_configs, test_sources)
    worker.process_all(blocking=True)
    
    # Check results
    files = worker.get_
