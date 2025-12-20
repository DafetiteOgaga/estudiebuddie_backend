from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import Subject, Question
import json

# Create your views here.
@api_view(['GET', 'POST'])
def contribute(request):
	if request.method == 'POST':
		# Handle POST request
		payload = request.data
		print('contribute:', payload)
		return Response({
			'success': 'Success',
			'message': 'Contribution received successfully!',
			'info': payload
		})
	return render(request, 'contribute/contribute.html')


########################################################
@api_view(['POST'])
def create_or_update_subject(request):
	if request.method == 'POST':
		# print("Received request data:", request.data
		print("Received request data:", json.dumps(request.data, indent=2))
		return Response({
			'success': 'Success',
			'message': 'This endpoint is for creating or updating subjects and questions.',
			'info': request.data
		}, status=status.HTTP_200_OK)
		try:
			print("Trying to create or update subject...")
			print("Received request body:", request.data)

			info = request.data.get("info", {})
			questions = request.data.get("questions", [])

			name = info.get("subject")
			typeCategory = info.get("typeCategory")
			classCategory = info.get("classCategory")

			print("Formatting new questions...")
			formatted_questions = []
			for q in questions:
				options = q.get("options", [])
				correct_answer = q.get("correct_answer")

				if not isinstance(options, list) or len(options) != 4:
					return Response({"error": "Each question must have exactly 4 options."}, status=status.HTTP_400_BAD_REQUEST)

				if correct_answer not in options:
					return Response({"error": f"Correct answer '{correct_answer}' must be one of the 4 options."}, status=status.HTTP_400_BAD_REQUEST)

				formatted_questions.append({
					"question": q.get("question"),
					"options": options,
					"correct_answer": correct_answer,
					"image": q.get("image") or None,
					"explanation": q.get("explanation") or "",
				})

			print("Checking if subject exists...")
			existing_subject = Subject.objects.filter(name=name, typeCategory=typeCategory, classCategory=classCategory).first()

			if existing_subject:
				print("Found existing subject:", existing_subject.id)
				existing_question_texts = set(existing_subject.questions.values_list("question", flat=True))

				non_duplicate_questions = [
					fq for fq in formatted_questions if fq["question"] not in existing_question_texts
				]
				duplicate_count = len(formatted_questions) - len(non_duplicate_questions)
				print(f"Found {duplicate_count} duplicate questions.")
				print("Non-duplicate questions:", non_duplicate_questions)

				if non_duplicate_questions:
					print("Appending new questions to existing subject...")
					with transaction.atomic():
						for fq in non_duplicate_questions:
							Question.objects.create(subject=existing_subject, **fq)

					return Response({
						"success": "success",
						"message": "Questions appended to subject",
						"subjectId": existing_subject.id
					}, status=status.HTTP_200_OK)
				else:
					print("No new questions to append.")
					return Response({
						"success": "success",
						"message": "No new questions to append to subject",
						"subjectId": existing_subject.id
					}, status=status.HTTP_200_OK)

			else:
				print("Creating new subject...")
				with transaction.atomic():
					new_subject = Subject.objects.create(
						name=name,
						typeCategory=typeCategory,
						classCategory=classCategory
					)
					for fq in formatted_questions:
						Question.objects.create(subject=new_subject, **fq)

				print("Created new subject:", new_subject.id)
				return Response({
					"success": "success",
					"message": "New subject created with questions",
					"subjectId": new_subject.id
				}, status=status.HTTP_201_CREATED)

		except Exception as e:
			print("Error creating or updating subject:", e)
			return Response({
				"error": "Failed to create or update subject and questions."
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
