from django.shortcuts import render
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .utils.randomize import Randomize
from root_utils.formDataToDict import parse_nested_formdata, print_formdata_content
# from ../root_utils.formDataToDict import parse_nested_formdata
import json

# Create your views here.

@api_view(['POST'])
def generate_exam_bundle(request):
	if request.method == 'POST':
		print_formdata_content(request.data)
		# try:
		parsed_data = parse_nested_formdata(request.data, request.FILES)
		# print(f"Parsed form data: {json.dumps(parsed_data, indent=2)}")
		file_url = Randomize(parsed_data)
		print("Generated file URL:", file_url)
		return Response({"success": "Success", "downloadLink": file_url})
		# except Exception as e:
		# 	return Response({"error": str(e)}, status=500)
