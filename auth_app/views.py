# from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.contrib.auth import get_user_model, authenticate
import base64, hmac, hashlib, time, json, uuid, logging
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from user.serializers import UserSerializer
from hooks.pretty_print import pretty_print_json
logger = logging.getLogger(__name__)

# @permission_classes([AllowAny])
# @permission_classes([IsAuthenticated])
# @permission_classes([IsAdminUser]) # is_staff=True
# @permission_classes([IsAuthenticatedOrReadOnly])

User = get_user_model()

mock_data = {
    "total_participants": 6,
    "leaderboard": [
        {
            "rank": 1,
            "user": {
                "id": 12,
                "name": "Ogaga 🤡",
                "username": "ogaga_dev",
                "avatar_code": "🤡",
                "image_url": "null",
                "points": 19,
            },
            "score": 18,
            "total_questions": 20,
            "accuracy": 90,
            "duration_used": 840,
            "submitted_at": "2026-01-02T18:42:11Z"
        },
        {
            "rank": 2,
            "user": {
                "id": 7,
                "name": "Aisha Bello",
                "username": "aisha_b",
                "avatar_code": "😎",
                "image_url": "null",
                "points": 13,
            },
            "score": 17,
            "total_questions": 20,
            "accuracy": 85,
            "duration_used": 790,
            "submitted_at": "2026-01-02T18:39:02Z"
        },
        {
            "rank": 3,
            "user": {
                "id": 9,
                "name": "Chinedu Okafor",
                "username": "chine",
                "avatar_code": "🧠",
                "image_url": "null",
                "points": 64,
            },
            "score": 16,
            "total_questions": 20,
            "accuracy": 80,
            "duration_used": 910,
            "submitted_at": "2026-01-02T18:50:21Z"
        },
        {
            "rank": 4,
            "user": {
                "id": 19,
                "name": "Zainab Musa",
                "username": "zainab_m",
                "avatar_code": "✨",
                "image_url": "https://ik.imagekit.io/demo/zainab.jpg",
                "points": 9,
            },
            "score": 15,
            "total_questions": 20,
            "accuracy": 75,
            "duration_used": 880,
            "submitted_at": "2026-01-02T18:47:09Z"
        },
        {
            "rank": 5,
            "user": {
                "id": 23,
                "name": "Anonymous",
                "username": "anon",
                "avatar_code": "👻",
                "image_url": "null",
                "points": 433,
            },
            "score": 12,
            "total_questions": 20,
            "accuracy": 60,
            "duration_used": 1020,
            "submitted_at": "2026-01-02T19:01:44Z"
        }
    ]
}

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def imagekit_auth(request):
    logger.info("Generating ImageKit auth token (imagekit_auth)...")
    token = uuid.uuid4().hex # str(int(time.time()))
    expire = str(int(time.time()) + 2400)  # 40 minutes (more reasonable)

    # Fix: The signature should be generated from token + expire only
    # NOT including the private key in the hash
    signature = hmac.new(
        settings.IMAGEKIT_PRIVATE_KEY.encode('utf-8'),
        f"{token}{expire}".encode('utf-8'),
        hashlib.sha1
    ).hexdigest()

    logger.info(f"Generated ImageKit auth")
    pretty_print_json({f"token": token, f"expire": expire, f"signature": signature})

    return JsonResponse({
        "token": token,
        "expire": int(expire),  # Should be integer, not string
        "signature": signature
    }, status=status.HTTP_200_OK)

# @permission_classes([AllowAny])
class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        logger.info("REFRESH ENDPOINT HIT")  # log added

        # optional: inspect incoming data
        logger.info("Request data:", request.data)

        response = super().post(request, *args, **kwargs)

        # optional: log response
        logger.info("Refresh response:", response.data)

        return response

# @permission_classes([AllowAny])
class CookieTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        logger.info(f'email: {email}\npassword: {password}')

        # 1. Check if email was provided
        if not email or not password:
            logger.info("Email and password are required.")
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.info("No account found for this email.")
            return Response({"error": "No account found for this email."}, status=status.HTTP_404_NOT_FOUND)

        # 3. Authenticate user (checks password)
        user = authenticate(request, username=email, password=password)
        logger.info(f'authenticate user: {user}')
        if not user:
            logger.info("Incorrect password.")
            return Response({"error": "Incorrect password."}, status=status.HTTP_404_NOT_FOUND)
        logger.info('user authenticated...')

        # 4. If authentication passes, use normal JWT process
        response = super().post(request, *args, **kwargs)
        data = response.data

        # add user info to response
        data["user"] = UserSerializer(user).data

        logger.info(f'response.data:')
        pretty_print_json(data)
        return response

@api_view(['GET', 'POST'])
@permission_classes({AllowAny})
def test_view(request):
    logger.info(f'request data')
    pretty_print_json(request.data)
    return Response({'data': 'all good'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def leaderboard_mock(request):
    # logger.debug("DEBUG: Refresh called")
    logger.info("INFO: Refresh endpoint hit")
    # logger.warning("WARNING: Example warning")
    # logger.error("ERROR: Example error")
    # logger.critical("CRITICAL: Example critical")
    logger.info(f'request data')
    pretty_print_json(request.data)
    return Response({'data': mock_data}, status=status.HTTP_200_OK)

keys = f"""
    "private": {settings.IMAGEKIT_PRIVATE_KEY},<br/>
    "public": {settings.IMAGEKIT_PUBLIC_KEY},<br/>
    "url": {settings.IMAGEKIT_URL_ENDPOINT},<br/>
"""
def test_keys(request):
    return HttpResponse(keys)