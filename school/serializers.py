from rest_framework import serializers
from .models import *

# Create your serializers here.
class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['name', 'acronym']

class ScrambleSessionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrambleSession
        fields = [
            'scramble_session_data',
            'session_class',
            'session_term',
            'session_subject',
            'has_submitted',
        ]

    def create(self, validated_data):
        print('in create method in serializer')
        request = self.context['request']
        teacher = request.user
        school = teacher.school
        
        # print(f'validated_data: {validated_data}')

        return ScrambleSession.objects.create(
            teacher=teacher,
            school=school,
            **validated_data
        )

    def update(self, instance, validated_data):
        print('in update method in serializer')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class ScrambleSessionReadSerializer(serializers.ModelSerializer):
    school = SchoolSerializer(read_only=True)
    # teacher = serializers.StringRelatedField()

    class Meta:
        model = ScrambleSession
        fields = [
            'id',
            'teacher',
            'school',
            'scramble_session_data',
            'has_submitted',
            'updated_at',
        ]

class SubmittedQuestionsWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmitedQuestions
        fields = ['submitted_session_data']

    def create(self, validated_data):
        print('in create method in serializer')
        request = self.context['request']
        teacher = request.user
        school = teacher.school

        submitted_data = validated_data["submitted_session_data"].dict()
        validated_data["session_class"] = submitted_data.get("class")
        validated_data["session_term"] = submitted_data.get("term")
        validated_data["session_subject"] = submitted_data.get("subject")
        # print(f'validated_data: {validated_data}')

        return SubmitedQuestions.objects.create(
            teacher=teacher,
            school=school,
            **validated_data
        )

    def update(self, instance, validated_data):
        print('in update method in serializer')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def replace_submitted_session(self, instance, new_data):
        """
        Completely replace submitted_session_data
        """
        instance.submitted_session_data = new_data
        instance.save()
        return instance

class SubmittedQuestionsReadSerializer(serializers.ModelSerializer):
    # school = SchoolSerializer(read_only=True)
    # teacher = serializers.StringRelatedField()

    class Meta:
        model = SubmitedQuestions
        fields = [
            'id',
            # 'teacher',
            # 'school',
            # 'submitted_session_data',
            'session_class',
            'session_term',
            'session_subject',
            'updated_at',
        ]
