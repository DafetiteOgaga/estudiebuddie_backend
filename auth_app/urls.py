from django.urls import path
from . import views
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import (
    # TokenObtainPairView,
    TokenRefreshView,
)

app_name = "auth_app"

urlpatterns = [
	# Create your urlpatterns here.
	# path("api/auth/google/", views.google_login, name="google_login"),
	# path("api/authenticate/", views.generate_signature, name="generate_signature"),
	path("imagekit-auth/", views.imagekit_auth, name="imagekit_auth"),
	# path("products/", views.products, name="product_list_create"),
	# path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # login
    path(
        'api/token/refresh/',
        TokenRefreshView.as_view(permission_classes=[AllowAny]),
        name='token_refresh'
	),  # refresh
    path("api/token/", views.CookieTokenObtainPairView.as_view(), name="token_obtain_pair"),
    # path('secret-data/', views.secret_data, name='secret_data'),  # Example protected route
    path('test-view/', views.test_view, name='test-view'),
    path('test-keys/', views.test_keys, name='test-keys'),
    path('test-leaderboard/', views.leaderboard_mock, name='test-leaderboard'),
]