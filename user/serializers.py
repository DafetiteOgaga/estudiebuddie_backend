from rest_framework import serializers
from .models import User

# Create your serializers here.
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'email',
            'mobile_no', 'username', 'is_staff',
			'image_url','fileId', 'role', 'about',
			'gender', 'avatar_code', 'is_superuser',
            'contributor', 'points', 'password',
		]
        read_only_fields = ['is_staff', 'is_superuser', 'id']

    def create(self, validated_data):
        print('creating user...')
        password = validated_data.pop('password', None)
        # update other fields
        user = User(**validated_data)
        if password:
            print('hashing password')
            user.set_password(password) # hash password
        user.save()
        return user

    def update(self, instance, validated_data):
        print('updating user...')
        password = validated_data.pop('password', None)
        # update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            print('hashing password')
            instance.set_password(password)  # hash the password
        instance.save()
        return instance