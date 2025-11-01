import unreal
import os

# --- SETTINGS ---
QUEUE_ASSET_PATH = "/Game/Sequencers/EditorMoviePipelineQueue.EditorMoviePipelineQueue"
SHUTDOWN_DELAY_SECONDS = 60  # seconds before shutdown (use /a in CMD to cancel)
SHUTDOWN_ON_FAILURE = False  # shutdown even if render fails

def log(msg):
    unreal.log(f"[shutdown_after_mrq] {msg}")

# --- CALLBACK ---
def on_executor_finished(executor, success):
    """Called when the Movie Render Queue finishes all jobs."""
    log(f"Render queue finished. Success = {success}")

    if success or SHUTDOWN_ON_FAILURE:
        shutdown_cmd = f"shutdown /s /t {int(SHUTDOWN_DELAY_SECONDS)}"
        log(f"Executing OS shutdown command: {shutdown_cmd}")
        try:
            os.system(shutdown_cmd)
        except Exception as e:
            log(f"Failed to issue shutdown: {e}")

        # Quit Unreal cleanly after scheduling shutdown
        try:
            unreal.SystemLibrary.execute_console_command(None, "quit")
        except Exception as e:
            log(f"Failed to quit Unreal: {e}")
    else:
        log("Render failed. Skipping shutdown.")

# --- MAIN EXECUTION ---
def execute_current_queue_and_watch():
    queue_subsys = unreal.get_engine_subsystem(unreal.MoviePipelineQueueEngineSubsystem)
    if not queue_subsys:
        log("ERROR: Could not access MoviePipelineQueueEngineSubsystem. Is MRQ enabled?")
        return

    # ✅ Load your queue asset directly
    queue_asset = unreal.load_asset(QUEUE_ASSET_PATH)
    if not queue_asset:
        log(f"ERROR: Could not load queue asset at {QUEUE_ASSET_PATH}")
        return

    # --- Check for jobs safely ---
    jobs = queue_asset.get_jobs()
    if not jobs or len(jobs) == 0:
        log(f"ERROR: No jobs found in queue {QUEUE_ASSET_PATH}. Aborting render.")
        return

    log(f"Found {len(jobs)} job(s) in queue. Starting Movie Render Queue...")

    # ✅ Use the queue asset directly with the executor
    executor = unreal.MoviePipelinePIEExecutor()
    executor.on_executor_finished_delegate.add_callable(on_executor_finished)
    queue_subsys.render_queue_with_executor_instance(executor, queue_asset)

# --- ENTRY POINT ---
if __name__ == "__main__":
    execute_current_queue_and_watch()