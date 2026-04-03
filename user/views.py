from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from hooks.pretty_print import pretty_print_json
from root_utils.formDataToDict import generate_esb_code, cleanup_old_zips
from django.db import transaction
from django.contrib.auth import get_user_model
User = get_user_model()
from .serializers import UserSerializer, PulledUserSerializer
from school.models import School, ValidCode

# Create your views here.
@api_view(['POST'])
@permission_classes([AllowAny])
def create_user(request):
	cleanup_old_zips()
	if request.method == 'POST':
		payload = request.data.copy()
		esb_code = payload.get("esb_code", None)
		school = payload.get("school", None)
		acronym = payload.get("acronym", None)
		user_role = payload.get("role", None)
		password_provided = payload.get("password", None)
		print('payload:')
		pretty_print_json(payload)
		print(f'esb_code: {esb_code}')
		print(f'school: {school} - {acronym}')

		try:
			with transaction.atomic():
				if esb_code:
					print('got code')
					print(f'user is: {user_role}')

					validated_code = ValidCode.objects.filter(valid_code=esb_code).first()
					print(f'validated_code: {validated_code}')
					if not validated_code:
						expired_code_txt = 'code has been used.'
						print(expired_code_txt)
						raise ValueError(expired_code_txt)

					print('getting or creating school')
					school_to_use = None
					if school and acronym:
						print(f'got both: {school}\n{acronym}')
						school_to_use = School.objects.filter(
							code=validated_code.valid_code,
							name=school.strip().lower(),
							acronym=acronym.upper(),
						)
						print(f'school_to_use: {school_to_use}')
						if not school_to_use and user_role == "head":
							print(f'creating school: {school}')
							school_to_use = School.objects.create(
								code=validated_code.valid_code,
								name=school.strip().lower(),
								acronym=acronym.strip().upper(),
							)
					else:
						validated_code_str = validated_code.valid_code
						i_index = validated_code_str.rfind("l")
						found_school_id = None
						if i_index > 0:
							print(f'i_index: {i_index}')
							found_school_id = validated_code_str[(i_index+1):]
							print(f'found_school_id: {found_school_id}')
						print('got none, so using school id')
						school_to_use = School.objects.get(
							id=found_school_id
						)
					print('code validated')
					print(f'school found: {school_to_use}')

					print('adding school to payload')
					payload["school_id"] = school_to_use.id
					print('invalidating code')
					# print(f'payload 2222:')
					# pretty_print_json(payload)
					#################
					# return Response({"error": "done!"}, status=status.HTTP_400_BAD_REQUEST)
					validated_code.delete()
				else:
					print('got no code')
					print(f'user is: {request.user}')
					if request.user.is_authenticated and (request.user.role=="head" or request.user.role=="admin"):
						print(f'user is: {request.user.role}')
						print('adding school to payload')
						payload["school_id"] = request.user.school.id
					else:
						print('removing school from payload (not linked to any school)')
						payload.pop("school", None)
				print(f'payload 2222:')
				pretty_print_json(payload)
				# return Response({"error": "done!"}, status=status.HTTP_400_BAD_REQUEST)
				email = payload.get("email", None)
				username = payload.get("username", None)
				print(f'email: {email}\nusername: {username}')
				print(f'payload:')
				pretty_print_json(payload)
				email_check = User.objects.filter(email=email).exists()
				if username is None:
					username_check = False
				else:
					username_check = User.objects.filter(username=username).exists()
				print(f'email_check: {email_check}')
				print(f'username_check: {username_check}')
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
				if not serializer.is_valid():
					not_saved = "Unable to update information"
					user_serializer = serializer.errors
					print(f'user_serializer: {user_serializer}')
					print(f'error message: {serializer.error_messages}')
					raise ValueError(not_saved)

				print("Data that WILL be saved (not yet saved):")
				pretty_print_json(serializer.validated_data)
				# return Response({"error": "all good"}, status=status.HTTP_400_BAD_REQUEST)
				user = serializer.save()
		except ValueError as e:
			# Business logic / validation errors
			return Response(
				{"error": str(e)},
				status=status.HTTP_400_BAD_REQUEST
			)

		except Exception as e:
			print(f'account creation error: {str(e)}')
			return Response(
				{"error": "Oopsy! something went wrong duriing account creation"},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)

		data = {}
		serialized_user = UserSerializer(user).data
		print(f'serialized_user:')
		pretty_print_json(serialized_user)
		if not password_provided:
			temp_password = serialized_user["username"]
			print(f'created user with temprary password: {temp_password}')
			tmp_data = {**data, **serialized_user}
			tmp_data["temp_password"] = temp_password
			pretty_print_json(tmp_data)
			data["temp_password"] = temp_password
			# user.must_change_password = True
			# user.save()
			return Response(data, status=status.HTTP_201_CREATED)

		refresh = RefreshToken.for_user(user)

		data["user"] = serialized_user
		data["refresh"] = str(refresh),
		data["access"] = str(refresh.access_token),

		# user_serializer = serializer.data

		print('created user:')
		pretty_print_json(data)
		return Response(data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user(request):
	cleanup_old_zips()
	if request.method == 'POST':
		qp = request.query_params
		print(f'qp: {qp}')
		must_change_p = qp.get("must_change_password", None)
		print(f'must_change_p(raw): {must_change_p}')
		must_change_p = must_change_p == "true"
		print(f'must_change_p(bool): {must_change_p}')
		pk = request.user.id
		payload = request.data
		print(f'payload with id: {pk}')
		# print(f'request user: {request.user}')
		pretty_print_json(payload)
		# return Response({"ok": "all good"}, status=status.HTTP_400_BAD_REQUEST)
		user = User.objects.filter(id=pk).first()
		print(f'user: {user}')
		# return Response({"ok": "all good"}, status=status.HTTP_400_BAD_REQUEST)
		if not user:
			user_not_exist = "User does not exist."
			print(user_not_exist)
			return Response({"error": user_not_exist}, status=status.HTTP_400_BAD_REQUEST)
		payload["must_change_password"] = False
		if must_change_p:
			payload["username"] = None
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
		if must_change_p:
			user_serializer = {
				"must_change_password": user_serializer["must_change_password"],
				"username": "",
				"update_user_must_change_password": 1,
			}
		pretty_print_json(user_serializer)
		return Response(user_serializer, status=status.HTTP_200_OK)

# @api_view(['GET'])
# @permission_classes([AllowAny])
# def check_username(request):
# 	# Access query parameter
# 	username = request.GET.get('username') # ?username=johndoe
# 	print(f'username: {username}')

# 	response_data = "available"
# 	if User.objects.filter(username=username).exists():
# 		response_data = "not_available"
# 	print(f'response_data: {response_data}')

# 	return Response(response_data, status=status.HTTP_200_OK)

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_school_code_link(request, code_type):
	user = request.user
	user_id = user.id
	school = getattr(user, "school", None)
	print(f'user: {user}')
	print(f'school: {school}')
	if not school:
		print("Oopsy! no school is associated with this account")
		return Response({"Oopsy! no school is associated with this account"}, status=status.HTTP_400_BAD_REQUEST)
	# print(f'user: {user}')
	print(f'user_id: {user_id}')
	print(f'code_type: {code_type}')
	print(f'user school: {school.name} ({school.acronym})')
	if user.is_superuser and code_type == "school_code":
		print('is superuser')
		esb_code = generate_esb_code(school_id=school.id)
	elif user.role == "head" or user.role == "admin":
		print(f'not superuser and code_type: {code_type}')
		esb_code = generate_esb_code(school_id=school.id, code_type=code_type)
	else:
		print({"error": "You do not have permission for this request."})
		return Response({"error": "You do not have permission for this request."},
							status=status.HTTP_400_BAD_REQUEST)
	code = ValidCode.objects.create(
		valid_code=esb_code,
	)
	print(f'esb_code created: {code.valid_code}')
	return Response({"esb_code": esb_code}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pull_users(request):
	cleanup_old_zips()
	user = request.user
	exclude_list = ["head", "admin"]
	school = getattr(user, "school", None)
	if not school:
		not_school = "You do not have permission for this action"
		print(not_school)
		return Response({"error": not_school}, status=status.HTTP_400_BAD_REQUEST)
	if user.role not in exclude_list:
		not_admin = "You are not admin"
		print(not_admin)
		return Response({"error": not_admin}, status=status.HTTP_400_BAD_REQUEST)
	# exclude_list = ["head"]
	exclude_list = ["head"] if user.role == "admin" else []
	print(f'school: {school}\nschool.id: {school.id}')
	print(f'user: {user}')
	print(f'user is {user.role}')
	# if user.role == "head":
	# 	exclude_list = []
	print(f'school id: {school.id}')
	users = User.objects.filter(
		school=school,
	).exclude(role__in=exclude_list)
	print(f'users: {users}')
	serialized_users = PulledUserSerializer(users, many=True).data
	print(f'users:')
	pretty_print_json(serialized_users)
	return Response(serialized_users, status=status.HTTP_200_OK)
