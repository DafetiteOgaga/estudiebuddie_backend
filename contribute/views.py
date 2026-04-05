from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
import json, logging
from hooks.pretty_print import pretty_print_json
from .models import Category, Question
from .utils.hooks import validate_question_options
from django.core.exceptions import ValidationError
logger = logging.getLogger(__name__)

# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def contribute(request):
	if request.method == 'POST':
		# Handle POST request
		try:
			payload = request.data
		except:
			return Response({"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
		# logger.info(json.dumps(payload, indent=4))
		logger.info('contribute:')
		pretty_print_json(payload)

		# Extract category info
		type_category = payload.get("type_category").lower()
		class_category = payload.get("class_category").lower()
		subject_category = payload.get("subject_category").lower()
		questions_data = payload.get("questions", [])

		logger.info('questions:')
		pretty_print_json(questions_data)
		logger.info(f'type: {type_category}')
		logger.info(f'class: {class_category}')
		logger.info(f'subject: {subject_category}')

		# return Response({"good": "all good"}, status=status.HTTP_200_OK)

		if not (type_category and class_category and subject_category and questions_data):
			logger.info({"error": "Missing fields"})
			return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)

		# Get or create category
		category, created = Category.objects.get_or_create(
			type_category=type_category,
			class_category=class_category,
			subject_category=subject_category
		)
		logger.info(f'category: {category.id}')
		logger.info(f'newly created: {created}')

		# Prepare bulk questions
		bulk_questions = []
		duplicate_questions = []

		logger.info('performing bulk op')
		for idx, q in enumerate(questions_data):
			logger.info(f'for question: {idx+1}')
			question_text = q.get("question")
			options = q.get("options")
			correct_answer = q.get("correct_answer")
			explanation = q.get("explanation")
			image_url = q.get("image_url", None)
			fileId = q.get("fileId", None)

			# Prevent duplicate questions across all categories
			logger.info('checking if its a duplicate...')
			if Question.objects.filter(question=question_text).exists():
				logger.info(f'duplicate found: {question_text}')
				duplicate_questions.append(question_text)
				continue

			# Validate options
			try:
				validate_question_options(options, correct_answer)
			except ValidationError as e:
				return Response({"error": str(e)}, status=status.HTTP_406_NOT_ACCEPTABLE)

			bulk_questions.append(
				Question(
					category=category,
					question=question_text,
					options=options,
					correct_answer=correct_answer,
					explanation=explanation,
					image_url=image_url,
					fileId=fileId
				)
			)

		# Use transaction to ensure atomic insert
		try:
			with transaction.atomic():
				logger.info('creating bulk questions...')
				Question.objects.bulk_create(bulk_questions)
				logger.info('bulk questions created.')
		except Exception as e:
			logger.info({"error": str(e)})
			return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		logger.info('success.')
		response = {
			"saved": f"{len(bulk_questions)} questions",
			"skipped_duplicates": len(duplicate_questions)
		}
		more_details = {**response, "skipped_duplicates_details": duplicate_questions}
		pretty_print_json(more_details)
		return Response(response, status=status.HTTP_201_CREATED)
