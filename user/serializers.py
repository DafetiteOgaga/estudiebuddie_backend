from rest_framework import serializers
from django.utils.crypto import get_random_string
from .models import User
from school.serializers import SchoolSerializer
from school.models import School
import logging
logger = logging.getLogger(__name__)

# Create your serializers here.
class UserSerializer(serializers.ModelSerializer):
	password = serializers.CharField(write_only=True, required=False)
	is_super_admin = serializers.SerializerMethodField(read_only=True)
	# username = serializers.SerializerMethodField(read_only=True)
	school = SchoolSerializer(read_only=True) # read
	school_id = serializers.PrimaryKeyRelatedField( # write
		queryset=School.objects.all(),
		source='school',
		write_only=True,
		required=False,
		allow_null=True
	)
	class Meta:
		model = User
		fields = [
			'id', 'first_name', 'last_name', 'email',
			'mobile_no', 'username', 'is_staff',
			'image_url', 'fileId', 'role', 'about',
			'gender', 'avatar_code',
			'contributor', 'points', 'password',
			'school', 'school_id', 'is_super_admin',
			'must_change_password', 'theme_mode',
		]
		read_only_fields = [
			'id',
			'is_staff',
			# 'is_school_admin',
			# 'school',
		]

	def get_is_super_admin(self, obj):
		return obj.is_superuser

	def create(self, validated_data):
		logger.info('creating user...')
		password = validated_data.pop('password', None)
		username = validated_data.get('password', None)
		# update other fields
		user = User(**validated_data)
		creating_for = False
		if not password:
			creating_for = True
			password = get_random_string(8)
			username = validated_data.get('first_name')
			logger.info(f'validated_data: {validated_data}')
		logger.info('hashing password')
		user.set_password(password) # hash password
		if creating_for:
			user.username = password # f'{user.email[:10]}-{get_random_string(5)}'
			user.must_change_password = True
		user.save()
		return user

	def update(self, instance, validated_data):
		logger.info('updating user...')
		password = validated_data.pop('password', None)
		# update other fields
		for attr, value in validated_data.items():
			setattr(instance, attr, value)
		if password:
			logger.info('hashing password')
			instance.set_password(password)  # hash the password
		instance.save()
		return instance

class PulledUserSerializer(serializers.ModelSerializer):
	temp_password = serializers.SerializerMethodField(read_only=True)
	class Meta:
		model = User
		fields = [
			'id', 'first_name', 'last_name', 'email',
			'mobile_no', 'image_url', 'role', 'about',
			'gender', 'avatar_code', 'must_change_password',
			'temp_password',
		]
	def get_temp_password(self, obj):
		return obj.username if obj.must_change_password else None