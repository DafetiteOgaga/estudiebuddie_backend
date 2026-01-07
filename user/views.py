from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from hooks.pretty_print import pretty_print_json
from django.contrib.auth import get_user_model
User = get_user_model()
from .serializers import UserSerializer

# Create your views here.
@api_view(['POST'])
@permission_classes([AllowAny])
def create_user(request):
	if request.method == 'POST':
		payload = request.data
		email = payload.get("email", None)
		username = payload.get("username", None)
		print(f'email: {email}\nusername: {username}')
		print(f'payload:')
		pretty_print_json(payload)
		email_check = User.objects.filter(email=email).exists()
		username_check = User.objects.filter(username=username).exists()
		if email_check:
			email_exist = "This email has been taken. Please, use another one."
			print(email_exist)
			return Response({"error": email_exist}, status=status.HTTP_400_BAD_REQUEST)
		if username_check:
			username_exist = "This username has been taken. Please, use another one."
			print(username_exist)
			return Response({"error": username_exist}, status=status.HTTP_400_BAD_REQUEST)
		# return Response({"ok": "all good"}, status=status.HTTP_200_OK)
		serializer = UserSerializer(data=payload)
		if serializer.is_valid():
			print("Data that WILL be saved (not yet saved):")
			pretty_print_json(serializer.validated_data)
			# return Response({"ok": "all good"}, status=status.HTTP_200_OK)
			serializer.save()
			user_serializer = serializer.data
		else:
			not_saved = "Unable to update information"
			user_serializer = serializer.errors
			print(f'user_serializer: {user_serializer}')
			print(f'error message: {serializer.error_messages}')
			return Response({"error": not_saved}, status=status.HTTP_400_BAD_REQUEST)
		print('created user:')
		pretty_print_json(user_serializer)
		return Response(user_serializer, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user(request):
	if request.method == 'POST':
		pk = request.user.id
		payload = request.data
		print(f'payload with id: {pk}')
		# print(f'request user: {request.user}')
		pretty_print_json(payload)
		# return Response({"ok": "all good"}, status=status.HTTP_200_OK)
		user = User.objects.filter(id=pk).first()
		print(f'user: {user}')
		if not user:
			user_not_exist = "User does not exist."
			print(user_not_exist)
			return Response({"error": user_not_exist}, status=status.HTTP_400_BAD_REQUEST)
		serializer = UserSerializer(user, data=payload, partial=True)
		if serializer.is_valid():
			print("Data that WILL be saved (not yet saved):")
			pretty_print_json(serializer.validated_data)
			# return Response({"ok": "all good"}, status=status.HTTP_200_OK)
			serializer.save()
			user_serializer = serializer.data
		else:
			not_saved = "Unable to update information"
			user_serializer = serializer.errors
			print(f'user_serializer: {user_serializer}')
			print(f'error message: {serializer.error_messages}')
			return Response({"error": not_saved}, status=status.HTTP_400_BAD_REQUEST)
		print('updated user:')
		pretty_print_json(user_serializer)
		return Response(user_serializer, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def check_username(request):
	# Access query parameter
    username = request.GET.get('username') # ?username=johndoe
    print(f'username: {username}')

    response_data = "available"
    if User.objects.filter(username=username).exists():
        response_data = "not_available"
    print(f'response_data: {response_data}')

    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def check_email(request):
	# Access query parameter
    email = request.GET.get('email') # ?email=someone@example.com
    print(f'email: {email}')

    response_data = "available"
    if User.objects.filter(email=email).exists():
        response_data = "not_available"
    print(f'response_data: {response_data}')

    return Response(response_data, status=status.HTTP_200_OK)