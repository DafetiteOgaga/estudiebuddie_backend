from rest_framework import serializers
from .models import *

# Create your serializers here.
class ScrambleLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrambleLinks
        fields = "__all__"
