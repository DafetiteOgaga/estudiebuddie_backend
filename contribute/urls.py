from django.urls import path
from . import views

app_name = "contribute"

urlpatterns = [
	# Create your urlpatterns here.
	path('', views.contribute, name='contribute'),
	# path('subjects/', views.create_or_update_subject, name='create_or_update_subject'),
]
