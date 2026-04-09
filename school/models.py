from django.db import models
import logging
logger = logging.getLogger(__name__)

# Create your models here.
class ScrambleSession(models.Model):
	school = models.ForeignKey(
		'School',
		on_delete=models.CASCADE,
		related_name='rn_scramble_session_school'
	)
	teacher = models.ForeignKey(
		'user.User',
		on_delete=models.CASCADE,
		related_name='rn_scramble_session_teacher'
	)
	session_class = models.CharField(max_length=100, null=True, blank=True)
	session_term = models.CharField(max_length=100, null=True, blank=True)
	session_subject = models.CharField(max_length=100, null=True, blank=True)
	has_submitted = models.BooleanField(default=False)
	scramble_session_data = models.JSONField()
	shuffle_record = models.JSONField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

class School(models.Model):
	name = models.CharField(
		max_length=200,
		null=True,
		blank=True,)
	acronym = models.CharField(
		max_length=50,
		null=True,
		blank=True,
	)
	school_email = models.EmailField(max_length=200, null=True, blank=True)
	school_address = models.CharField(max_length=500, null=True, blank=True)
	school_logo_url = models.URLField(blank=True, null=True)  # only store ImageKit URL
	school_logo_fileId = models.CharField(max_length=200, null=True, blank=True)  # store ImageKit fileId
	code = models.CharField(max_length=100, unique=True, db_index=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def save(self, *args, **kwargs):
		if self.acronym is not None:
			self.acronym = self.acronym.upper()
			logger.info(f'acronym: {self.acronym}')
		if self.name is not None:
			self.name = self.name.strip().lower()
			logger.info(f'name: {self.name}')
		super().save(*args, **kwargs)

	def __str__(self):
		return f'{self.name} ({self.acronym})'

class SubmitedQuestions(models.Model):
	school = models.ForeignKey(
		'School',
		on_delete=models.CASCADE,
		related_name='rn_submitted_questions_school'
	)
	teacher = models.ForeignKey(
		'user.User',
		on_delete=models.CASCADE,
		related_name='rn_submitted_questions_teacher'
	)
	submitted_session_data = models.JSONField()
	session_class = models.CharField(max_length=100, null=True, blank=True)
	session_term = models.CharField(max_length=100, null=True, blank=True)
	session_subject = models.CharField(max_length=100, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f'{self.session_subject} for {self.session_term} term - submitted by {self.teacher.first_name}'

class ValidCode(models.Model):
	valid_code = models.CharField(max_length=50, db_index=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f'{self.valid_code}'