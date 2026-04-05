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
import logging
logger = logging.getLogger(__name__)

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
		logger.info('payload:')
		pretty_print_json(payload)
		logger.info(f'esb_code: {esb_code}')
		logger.info(f'school: {school} - {acronym}')

		try:
			with transaction.atomic():
				if esb_code:
					logger.info('got code')
					logger.info(f'user is: {user_role}')

					validated_code = ValidCode.objects.filter(valid_code=esb_code).first()
					logger.info(f'validated_code: {validated_code}')
					if not validated_code:
						expired_code_txt = 'code has been used.'
						logger.info(expired_code_txt)
						raise ValueError(expired_code_txt)

					logger.info('getting or creating school')
					school_to_use = None
					if school and acronym:
						logger.info(f'got both: {school}\n{acronym}')
						school_to_use = School.objects.filter(
							code=validated_code.valid_code,
							name=school.strip().lower(),
							acronym=acronym.upper(),
						)
						logger.info(f'school_to_use: {school_to_use}')
						if not school_to_use and user_role == "head":
							logger.info(f'creating school: {school}')
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
							logger.info(f'i_index: {i_index}')
							found_school_id = validated_code_str[(i_index+1):]
							logger.info(f'found_school_id: {found_school_id}')
						logger.info('got none, so using school id')
						school_to_use = School.objects.get(
							id=found_school_id
						)
					logger.info('code validated')
					logger.info(f'school found: {school_to_use}')

					logger.info('adding school to payload')
					payload["school_id"] = school_to_use.id
					logger.info('invalidating code')
					# logger.info(f'payload 2222:')
					# pretty_print_json(payload)
					#################
					# return Response({"error": "done!"}, status=status.HTTP_400_BAD_REQUEST)
					validated_code.delete()
				else:
					logger.info('got no code')
					logger.info(f'user is: {request.user}')
					if request.user.is_authenticated and (request.user.role=="head" or request.user.role=="admin"):
						logger.info(f'user is: {request.user.role}')
						logger.info('adding school to payload')
						payload["school_id"] = request.user.school.id
					else:
						logger.info('removing school from payload (not linked to any school)')
						payload.pop("school", None)
				logger.info(f'payload 2222:')
				pretty_print_json(payload)
				# return Response({"error": "done!"}, status=status.HTTP_400_BAD_REQUEST)
				email = payload.get("email", None)
				username = payload.get("username", None)
				logger.info(f'email: {email}\nusername: {username}')
				logger.info(f'payload:')
				pretty_print_json(payload)
				email_check = User.objects.filter(email=email).exists()
				if username is None:
					username_check = False
				else:
					username_check = User.objects.filter(username=username).exists()
				logger.info(f'email_check: {email_check}')
				logger.info(f'username_check: {username_check}')
				if email_check:
					email_exist = "This email has been taken. Please, use another one."
					logger.info(email_exist)
					return Response({"error": email_exist}, status=status.HTTP_400_BAD_REQUEST)
				if username_check:
					username_exist = "This username has been taken. Please, use another one."
					logger.info(username_exist)
					return Response({"error": username_exist}, status=status.HTTP_400_BAD_REQUEST)
				# return Response({"ok": "all good"}, status=status.HTTP_200_OK)
				serializer = UserSerializer(data=payload)
				if not serializer.is_valid():
					not_saved = "Unable to update information"
					user_serializer = serializer.errors
					logger.info(f'user_serializer: {user_serializer}')
					logger.info(f'error message: {serializer.error_messages}')
					raise ValueError(not_saved)

				logger.info("Data that WILL be saved (not yet saved):")
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
			logger.info(f'account creation error: {str(e)}')
			return Response(
				{"error": "Oopsy! something went wrong duriing account creation"},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)

		data = {}
		serialized_user = UserSerializer(user).data
		logger.info(f'serialized_user:')
		pretty_print_json(serialized_user)
		if not password_provided:
			temp_password = serialized_user["username"]
			logger.info(f'created user with temprary password: {temp_password}')
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

		logger.info('created user:')
		pretty_print_json(data)
		return Response(data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user(request):
	cleanup_old_zips()
	if request.method == 'POST':
		qp = request.query_params
		logger.info(f'qp: {qp}')
		must_change_p = qp.get("must_change_password", None)
		logger.info(f'must_change_p(raw): {must_change_p}')
		must_change_p = must_change_p == "true"
		logger.info(f'must_change_p(bool): {must_change_p}')
		pk = request.user.id
		payload = request.data
		logger.info(f'payload with id: {pk}')
		# logger.info(f'request user: {request.user}')
		pretty_print_json(payload)
		# return Response({"ok": "all good"}, status=status.HTTP_400_BAD_REQUEST)
		user = User.objects.filter(id=pk).first()
		logger.info(f'user: {user}')
		# return Response({"ok": "all good"}, status=status.HTTP_400_BAD_REQUEST)
		if not user:
			user_not_exist = "User does not exist."
			logger.info(user_not_exist)
			return Response({"error": user_not_exist}, status=status.HTTP_400_BAD_REQUEST)
		payload["must_change_password"] = False
		if must_change_p:
			payload["username"] = None
		serializer = UserSerializer(user, data=payload, partial=True)
		if serializer.is_valid():
			logger.info("Data that WILL be saved (not yet saved):")
			pretty_print_json(serializer.validated_data)
			# return Response({"ok": "all good"}, status=status.HTTP_200_OK)
			serializer.save()
			user_serializer = serializer.data
		else:
			not_saved = "Unable to update information"
			user_serializer = serializer.errors
			logger.info(f'user_serializer: {user_serializer}')
			logger.info(f'error message: {serializer.error_messages}')
			return Response({"error": not_saved}, status=status.HTTP_400_BAD_REQUEST)
		logger.info('updated user:')
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
# 	logger.info(f'username: {username}')

# 	response_data = "available"
# 	if User.objects.filter(username=username).exists():
# 		response_data = "not_available"
# 	logger.info(f'response_data: {response_data}')

# 	return Response(response_data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def check_email(request):
	# Access query parameter
	email = request.GET.get('email') # ?email=someone@example.com
	logger.info(f'email: {email}')

	response_data = "available"
	if User.objects.filter(email=email).exists():
		response_data = "not_available"
	logger.info(f'response_data: {response_data}')

	return Response(response_data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_school_code_link(request, code_type):
	user = request.user
	user_id = user.id
	school = getattr(user, "school", None)
	logger.info(f'user: {user}')
	logger.info(f'school: {school}')
	if not school:
		logger.info("Oopsy! no school is associated with this account")
		return Response({"Oopsy! no school is associated with this account"}, status=status.HTTP_400_BAD_REQUEST)
	# logger.info(f'user: {user}')
	logger.info(f'user_id: {user_id}')
	logger.info(f'code_type: {code_type}')
	logger.info(f'user school: {school.name} ({school.acronym})')
	if user.is_superuser and code_type == "school_code":
		logger.info('is superuser')
		esb_code = generate_esb_code(school_id=school.id)
	elif user.role == "head" or user.role == "admin":
		logger.info(f'not superuser and code_type: {code_type}')
		esb_code = generate_esb_code(school_id=school.id, code_type=code_type)
	else:
		logger.info({"error": "You do not have permission for this request."})
		return Response({"error": "You do not have permission for this request."},
							status=status.HTTP_400_BAD_REQUEST)
	code = ValidCode.objects.create(
		valid_code=esb_code,
	)
	logger.info(f'esb_code created: {code.valid_code}')
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
		logger.info(not_school)
		return Response({"error": not_school}, status=status.HTTP_400_BAD_REQUEST)
	if user.role not in exclude_list:
		not_admin = "You are not admin"
		logger.info(not_admin)
		return Response({"error": not_admin}, status=status.HTTP_400_BAD_REQUEST)
	# exclude_list = ["head"]
	exclude_list = ["head"] if user.role == "admin" else []
	logger.info(f'school: {school}\nschool.id: {school.id}')
	logger.info(f'user: {user}')
	logger.info(f'user is {user.role}')
	# if user.role == "head":
	# 	exclude_list = []
	logger.info(f'school id: {school.id}')
	users = User.objects.filter(
		school=school,
	).exclude(role__in=exclude_list)
	logger.info(f'users: {users}')
	serialized_users = PulledUserSerializer(users, many=True).data
	logger.info(f'users:')
	pretty_print_json(serialized_users)
	return Response(serialized_users, status=status.HTTP_200_OK)
