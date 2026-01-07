from django.urls import path
from . import views

app_name = "take_quiz"

urlpatterns = [
	# Create your urlpatterns here.
	path('pre-quiz/', views.pre_quiz, name='prequiz'),  # Example API view
	path('take-quiz/', views.take_quiz, name='takequiz'),  # Another example API view
	path('grade-quiz/', views.grade_quiz, name='gradequiz'),
	path('quiz-attempt/<str:session_id>/', views.send_time, name='send_time'),
]
