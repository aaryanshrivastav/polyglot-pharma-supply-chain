"""
ETL Pipeline Scheduler / Runner.
Supports one-off execution (--once) or scheduled periodic daemon loop (--interval-minutes N).
Can also be plugged into crontab / systemd or Kubernetes cronjobs.
"""

import argparse
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from etl.rollup_job import RollupJob

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("ETLScheduler")

RUNNING = True


def signal_handler(signum, frame):
    global RUNNING
    logger.info("Termination signal received. Gracefully shutting down scheduler...")
    RUNNING = False


def run_single_job() -> int:
    """Instantiates and executes a single ETL rollup job."""
    t0 = time.time()
    logger.info("Starting scheduled RollupJob execution...")
    try:
        job = RollupJob()
        inserted = job.run_pipeline()
        job.close()
        elapsed = time.time() - t0
        logger.info(f"RollupJob completed in {elapsed:.2f}s. Inserted/updated {inserted:,} records.")
        return inserted
    except Exception as e:
        logger.error(f"RollupJob failed with exception: {e}", exc_info=True)
        return -1


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    parser = argparse.ArgumentParser(description="Pharmaceutical Supply Chain ETL Rollup Scheduler")
    parser.add_argument("--once", action="store_true", help="Run ETL job once and immediately exit")
    parser.add_argument("--interval-minutes", type=int, default=60, help="Interval in minutes between scheduled runs (default: 60)")
    args = parser.parse_args()

    if args.once:
        logger.info("Mode: Single run (--once)")
        status = run_single_job()
        sys.exit(0 if status >= 0 else 1)

    logger.info(f"Mode: Daemon loop running every {args.interval_minutes} minute(s). Press Ctrl+C to stop.")
    iteration = 1

    while RUNNING:
        logger.info(f"--- Triggering ETL Iteration #{iteration} at {datetime.now().isoformat()} ---")
        run_single_job()
        iteration += 1

        # Sleep in small slices to respond promptly to SIGINT
        sleep_seconds = args.interval_minutes * 60
        logger.info(f"Next run scheduled in {args.interval_minutes}m ({sleep_seconds}s)...")
        for _ in range(sleep_seconds):
            if not RUNNING:
                break
            time.sleep(1)

    logger.info("Scheduler shutdown complete.")


if __name__ == "__main__":
    main()

