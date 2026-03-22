from django.urls import path
from . import views

app_name = "user"

urlpatterns = [
	# Create your urlpatterns here.
	path('create/', views.create_user, name='create_user'),
	path('update/', views.update_user, name='update_user'),
	path('check-email/', views.check_email, name='check_email'),
	path('check-username/', views.check_username, name='check_username'),
	path('school-code/<str:code_type>/', views.get_school_code_link, name='get_school_code_link'),
	path('pull-staffs/', views.pull_users, name='pull_users'),
]
