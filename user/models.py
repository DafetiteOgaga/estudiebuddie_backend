from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models import F

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
	email = models.EmailField(max_length=200, unique=True, db_index=True)
	mobile_no = models.CharField(max_length=20, blank=True, null=True)

	# profile picture fields
	image_url = models.URLField(blank=True, null=True)  # only store ImageKit URL
	fileId = models.CharField(max_length=200, null=True, blank=True)  # store ImageKit fileId
	avatar_code = models.CharField(max_length=100, null=True, blank=True)
	points = models.PositiveIntegerField(default=0)

	gender = models.CharField(max_length=20, null=True, blank=True)
	role = models.CharField(max_length=20, null=True, blank=True)
	about = models.TextField(null=True, blank=True)
	username = models.CharField(max_length=30, unique=True, null=True, blank=True)
	# password = models.CharField(max_length=128, null=True, blank=True)
	contributor = models.BooleanField(default=False)
	is_deleted = models.BooleanField(default=False)
	must_change_password = models.BooleanField(default=False)

	# school details
	# is_school_admin = models.BooleanField(default=False)
	school = models.ForeignKey(
        'school.School',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rn_users_school"
    )

	class Meta:
		ordering = ['id']

	objects = UserManager() # custom manager

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []

	# Fields that should always be lowercase
	LOWERCASE_FIELDS = [
		"gender", "role", "first_name",
		"last_name",
	]
	def __str__(self):
		return f'user: {self.email}' # ({self.first_name}) - {self.role} for {self.location} in {self.region}' if self.first_name else self.email

	def delete(self):
		self.is_deleted = True
		self.save()

	# usage in view logic
	# if quiz_passed:
	# 	user.add_points(10)

	# if cheated:
	# 	user.remove_points(5)

	def add_points(self, amount):
		if amount <= 0:
			return

		self.__class__.objects.filter(
			id=self.id
		).update(points=F('points') + amount)

	def remove_points(self, amount):
		if amount <= 0:
			return

		qs = self.__class__.objects.filter(
			id=self.id)

		# subtract if possible or skip if not
		updated = qs.filter(
			points__gte=amount
		).update(points=F('points') - amount)

		# if subtraction is skipped
		if updated == 0:
			qs.update(points=0)

	def save(self, *args, **kwargs):
		if self.points < 0:
			self.points = 0

		for field_name in self.LOWERCASE_FIELDS:
			value = getattr(self, field_name, None)
			if value:
				setattr(self, field_name, value.lower())
		super().save(*args, **kwargs)
