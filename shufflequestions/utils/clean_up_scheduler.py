import os
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from .cleaner import clean_old_files_and_dirs

def start_scheduler():
	scheduler = BackgroundScheduler(
		jobstores={'default': MemoryJobStore()},
		executors={'default': ThreadPoolExecutor(1)},
		timezone='UTC',
	)

	scheduler.add_job(
		clean_old_files_and_dirs,
		trigger='interval',
		days=1,
		id='cleanup_job',
		replace_existing=True,
	)

	if os.environ.get('RUN_MAIN') == 'true':
		scheduler.start()
		# print("✅ APScheduler scheduler started.")
		# print("📅 Scheduled jobs:", scheduler.get_jobs())
		atexit.register(lambda: scheduler.shutdown())
		# print("✅ APScheduler started.")
