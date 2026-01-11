from django.db import models
from django.core.exceptions import ValidationError
from .utils.hooks import validate_question_options, generate_unique_id
from django.utils import timezone

# Create your models here.
class Category(models.Model):
    type_category = models.CharField(max_length=100)
    class_category = models.CharField(max_length=100)
    subject_category = models.CharField(max_length=100)
    class Meta:
        unique_together = (
            "type_category",
            "class_category",
            "subject_category",
        )

    def __str__(self):
        return f"{self.type_category} ({self.class_category} - {self.subject_category})"


class Question(models.Model):
    category = models.ForeignKey(
        "Category",
        on_delete=models.CASCADE,
        related_name="rn_questions"
    )
    question = models.TextField(max_length=255)
    image_url = models.CharField(max_length=255, null=True, blank=True)
    fileId = models.CharField(max_length=225, null=True, blank=True)
    options = models.JSONField(validators=[validate_question_options])
    correct_answer = models.CharField(max_length=255)
    explanation = models.TextField()
    approved = models.BooleanField(default=False)

    def clean(self):
        """Ensure the correct answer is one of the options."""
        super().clean()
        validate_question_options(self.options, self.correct_answer)

    def save(self, *args, **kwargs):
        self.full_clean()  # ensures clean() runs
        super().save(*args, **kwargs)

    def __str__(self):
        return self.question[:60]

class QuizSession(models.Model):
    session_id = models.CharField(
		max_length=100,
		default=generate_unique_id,
		db_index=True,
		# editable=False,
		unique=True
	)
    is_submitted = models.BooleanField(default=False)
    email = models.EmailField()
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="rn_quiz_sessions",
        null=True, blank=True,
    )
    name = models.CharField(max_length=100, blank=True)
    duration = models.PositiveIntegerField()
    questions = models.ManyToManyField(Question, related_name="rn_quiz_sessions")
    started_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # def save(self, *args, **kwargs):
    #     if not self.session_id:
    #         self.session_id = generate_unique_id()
    #     super().save(*args, **kwargs)

class QuizAnswer(models.Model):
    session = models.ForeignKey(
        "QuizSession",
        on_delete=models.CASCADE,
        related_name="rn_session_answers"
    )
    question = models.ForeignKey(
        "Question",
        on_delete=models.CASCADE,
        related_name="rn_question_answers"
    )
    response_duration = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True
    )
    selected_option = models.CharField(max_length=255)
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)
