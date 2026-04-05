from django.core.exceptions import ValidationError
from datetime import datetime
import uuid,logging
logger = logging.getLogger(__name__)

def validate_question_options(options, correct_answer=None):
	logger.info('validating options...')
	if not isinstance(options, (list, tuple)):
		raise ValidationError("Options must be a list.")
	if len(options) != 4:
		raise ValidationError("Each question must have exactly 4 options.")
	if correct_answer is not None:
		if correct_answer not in options:
			raise ValidationError("Correct answer must be one of the options.")
	logger.info('validation success.')

def generate_unique_id():
	"""
	Generates a unique quiz ID combining timestamp and a short UUID segment.
	Example: 20251012145530765432_a3f9
	"""
	timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")  # yyyymmddhhmmssµs
	random_part = uuid.uuid4().hex[:10]  # take first 10 hex chars of a UUID
	reference = f"{timestamp}_{random_part}"
	logger.info(f"Generated quiz ID: {reference} and length: {len(reference)}")
	return reference