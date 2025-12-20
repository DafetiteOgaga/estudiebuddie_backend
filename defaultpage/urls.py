from django.urls import path
from . import views

app_name = "defaultpage"

urlpatterns = [
	# Create your urlpatterns here.
	path('', views.defaultpage, name='defaultpage'),  # Default page view
]
