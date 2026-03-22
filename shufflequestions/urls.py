from django.urls import path
from . import views

app_name = "shufflequestions"

urlpatterns = [
	# Create your urlpatterns here.
	path('shuffle/', views.generate_exam_bundle, name='shuffle_questions'),
	path('get-links/', views.get_links, name='get_links'),
	path('exam-questions/', views.generate_exam_bundle_for_school, name='generate_exam_bundle_for_school'),
	path('check-submitted/', views.get_submitted, name='get_submitted'),
]
