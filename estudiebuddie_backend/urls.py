"""
URL configuration for estudiebuddie_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('school/', include('school.urls')),     # For school configuration
    path('user/', include('user.urls')),     # For user configuration
    path('', include('auth_app.urls')),     # For auth_app configuration
    path('shufflequestions/', include('shufflequestions.urls')),     # For shufflequestions configuration
    path('', include('defaultpage.urls')),     # For defaultpage configuration
    path('contribute/', include('contribute.urls')),     # For contribute configuration
    path('take-quiz/', include('take_quiz.urls')),     # For take_quiz configuration
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)