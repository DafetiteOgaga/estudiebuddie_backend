from django.contrib import admin
from .models import School, ScrambleSession, ValidCode, SubmitedQuestions

# Register your models here.
admin.site.register(School)
admin.site.register(ScrambleSession)
admin.site.register(ValidCode)
admin.site.register(SubmitedQuestions)
