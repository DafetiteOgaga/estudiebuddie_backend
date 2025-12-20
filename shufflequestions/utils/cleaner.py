# your_app/utils/cleaner.py
import os
import re
import shutil
from datetime import datetime, timezone
from .timestamp import get_timestamp
from .check_time import delete_time
from django.conf import settings


def clean_old_files_and_dirs(dir_path=None):
	# print("🧹 Running clean_old_files_and_dirs()")
	# print(f'dir_path1: {dir_path}')
	if dir_path is None:
		dir_path = os.path.join(settings.BASE_DIR, 'public')
	# print(f'dir_path2: {dir_path}')
	try:
		entries = os.listdir(dir_path)
		# print(f"Entries in directory {dir_path} {get_timestamp()}\n: {entries}")
	except Exception as e:
		# print(f"Error reading directory {get_timestamp()}: {e}")
		return

	for entry in entries:
		full_path = os.path.join(dir_path, entry)

		file_match = re.match(r"^estudiebuddie_(\d{8})_(\d{6})_", entry)
		dir_match = re.match(r"^(\d{8})_(\d{6})_", entry)

		file_timestamp_str = None
		if file_match:
			# print(f"File match found: {file_match.groups()} {get_timestamp()}")
			file_timestamp_str = file_match.group(1) + file_match.group(2)
		elif dir_match:
			# print(f"Directory match found: {dir_match.groups()} {get_timestamp()}")
			file_timestamp_str = dir_match.group(1) + dir_match.group(2)
		else:
			# print(f"Skipping entry: {entry} does not match expected pattern {get_timestamp()}")
			continue  # Not matching expected pattern

		try:
			dt = datetime.strptime(file_timestamp_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
		except ValueError:
			continue  # Invalid timestamp, skip

		age = (datetime.now(timezone.utc) - dt).total_seconds()

		# print(f"age > delete_time: {age > delete_time}")
		# print(f'age: {age}')
		# print(f'delete_time: {delete_time}')
		if age > delete_time:
			try:
				if os.path.isdir(full_path):
					shutil.rmtree(full_path)
					print(f"Deleted old directory: {entry} {get_timestamp()}")
				else:
					os.remove(full_path)
					print(f"Deleted old file: {entry} {get_timestamp()}")
			except Exception as e:
				print(f"Failed to delete {entry} {get_timestamp()}: {e}")
