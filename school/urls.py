from django.urls import path
from . import views

app_name = "school"

urlpatterns = [
	# Create your urlpatterns here.
	path('save/<str:detailed_resp>/', views.remember_sessions, name="remember_sessions"),
	path('update/', views.update_school, name="update_school"),
]
