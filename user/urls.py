from django.urls import path
from . import views

app_name = "user"

urlpatterns = [
	# Create your urlpatterns here.
	path('create/', views.create_user, name='create_user'),
	path('update/', views.update_user, name='update_user'),
	path('check-email/', views.check_email, name='check_email'),
	path('check-username/', views.check_username, name='check_username'),
]
