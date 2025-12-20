from django.urls import path
from . import views

app_name = "contribute"

urlpatterns = [
	# Create your urlpatterns here.
	path('subjects/', views.create_or_update_subject, name='create_or_update_subject'),
]
