from rest_framework import serializers
from .models import *

# Create your serializers here.
class QuestionReadSerializer(serializers.ModelSerializer):
    # category = serializers.StringRelatedField()
    class Meta:
        model = Question
        fields = [
			"id",
            "question",
            "image_url",
            "fileId",
            "options",
            # "correct_answer",
            "explanation",
        ]