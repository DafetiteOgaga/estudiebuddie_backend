from django.contrib import admin
from .models import Category, Question, QuizSession, QuizAnswer

# Register your models here.
admin.site.register(Category)
admin.site.register(Question)
admin.site.register(QuizSession)
admin.site.register(QuizAnswer)