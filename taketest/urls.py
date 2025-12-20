from django.urls import path
from . import views

app_name = "taketest"

urlpatterns = [
	# Create your urlpatterns here.
	path('pretest/', views.pretest, name='pretest'),  # Example API view
	path('taketest/', views.taketest, name='taketest'),  # Another example API view
]
