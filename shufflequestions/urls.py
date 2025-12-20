from django.urls import path
from . import views

app_name = "shufflequestions"

urlpatterns = [
	# Create your urlpatterns here.
	path('shuffle/', views.generate_exam_bundle, name='shuffle_questions'),  # API to shuffle questions.
]
