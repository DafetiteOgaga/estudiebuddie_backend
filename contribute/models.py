from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.
def validate_four_options(value):
    """Ensure the options list contains exactly 4 items."""
    if not isinstance(value, list) or len(value) != 4:
        raise ValidationError("Each question must have exactly 4 options.")

class Subject(models.Model):
    typeCategory = models.CharField(max_length=100)
    classCategory = models.CharField(max_length=100)
    name = models.CharField(max_length=100)  # formerly 'subject'

    def __str__(self):
        return f"{self.name} ({self.classCategory} - {self.typeCategory})"


class Question(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions')
    question = models.CharField(max_length=255)
    image = models.URLField(blank=True, null=True)
    options = models.JSONField(validators=[validate_four_options])
    correct_answer = models.CharField(max_length=255)
    explanation = models.TextField(blank=True)

    def clean(self):
        """Ensure the correct answer is one of the options."""
        super().clean()
        if self.correct_answer not in self.options:
            raise ValidationError("Correct answer must be one of the 4 options.")

    def __str__(self):
        return self.question