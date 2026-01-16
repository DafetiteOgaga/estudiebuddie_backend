from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .utils.randomize import Randomize
from .models import ScrambleLinks
from .serializers import ScrambleLinksSerializer
from root_utils.formDataToDict import parse_nested_formdata, print_formdata_content
from hooks.pretty_print import pretty_print_json
# from ../root_utils.formDataToDict import parse_nested_formdata
import json

# Create your views here.

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_exam_bundle(request):
	if request.method == 'POST':
		print_formdata_content(request.data)
		# try:
		parsed_data = parse_nested_formdata(request.data, request.FILES)
		# print(f"Parsed form data: {json.dumps(parsed_data, indent=2)}")
		file_url = Randomize(parsed_data)
		print("Generated file URL:", file_url)

		# save link for future downloads
		ScrambleLinks.objects.create(
			user=request.user,
			link=file_url,
		)
		return Response({"success": "Success", "downloadLink": file_url})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_links(request):
	if request.method == 'GET':
		user = request.user
		print(f'user: {user}')

		links = ScrambleLinks.objects.filter(user=user).order_by('-created_at')[:5]
		# print(f'links: {links}')
		serialized_links = ScrambleLinksSerializer(links, many=True).data
		print(f'serialized_links:')
		pretty_print_json(serialized_links)
		return Response(serialized_links, status=status.HTTP_200_OK)