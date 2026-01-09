from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from contribute.models import Question, Category, QuizSession, QuizAnswer
from contribute.serializers import QuestionReadSerializer
from hooks.pretty_print import pretty_print_json
import random
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

sample_questions = [
	{
		"question": "What is the capital of Nigeria?",
		"image_url": "https://pub-d26aede9a41940d48b0db48bc6422d34.r2.dev/test/placeholder.jpeg",
		"options": ["Abuja", "Lagos", "Kano", "Port Harcourt"],
		"correct_answer": "Abuja",
		"explanation": "Abuja became Nigeria's capital in 1991, replacing Lagos."
	},
	{
		"question": "Solve: 15 ÷ 3",
		"image_url": None,
		"options": ["3", "5", "6", "9"],
		"correct_answer": "5",
		"explanation": "15 divided by 3 equals 5."
	},
	{
		"question": "Which of these is not a programming language?",
		"image_url": "https://pub-d26aede9a41940d48b0db48bc6422d34.r2.dev/test/placeholder.jpeg",
		"options": ["Python", "Java", "Banana", "C++"],
		"correct_answer": "Banana",
		"explanation": "Banana is a fruit, not a programming language."
	},
	{
		"question": "Which gas do plants absorb from the atmosphere?",
		"image_url": None,
		"options": ["Oxygen", "Carbon Dioxide", "Hydrogen", "Nitrogen"],
		"correct_answer": "Carbon Dioxide",
		"explanation": "Plants absorb carbon dioxide for photosynthesis."
	},
	{
		"question": "What is the boiling point of water at sea level?",
		"image_url": None,
		"options": ["90°C", "100°C", "110°C", "120°C"],
		"correct_answer": "100°C",
		"explanation": "At sea level, water boils at 100 degrees Celsius."
	},
	{
		"question": "What is the next number in the sequence: 2, 4, 6, 8, ...?",
		"image_url": None,
		"options": ["9", "10", "12", "14"],
		"correct_answer": "10",
		"explanation": "It's an arithmetic sequence increasing by 2."
	},
	{
		"question": "Who wrote *Things Fall Apart*?",
		"image_url": "https://pub-d26aede9a41940d48b0db48bc6422d34.r2.dev/test/placeholder.jpeg",
		"options": ["Wole Soyinka", "Chimamanda Ngozi Adichie", "Chinua Achebe", "Ben Okri"],
		"correct_answer": "Chinua Achebe",
		"explanation": "Chinua Achebe authored *Things Fall Apart* in 1958."
	},
	{
		"question": "Which planet is closest to the sun?",
		"image_url": None,
		"options": ["Earth", "Venus", "Mercury", "Mars"],
		"correct_answer": "Mercury",
		"explanation": "Mercury is the closest planet to the sun."
	},
	{
		"question": "What is the chemical symbol for Gold?",
		"image_url": None,
		"options": ["Go", "G", "Au", "Ag"],
		"correct_answer": "Au",
		"explanation": "The symbol 'Au' comes from the Latin word 'Aurum'."
	},
	{
		"question": "How many continents are there on Earth?",
		"image_url": None,
		"options": ["5", "6", "7", "8"],
		"correct_answer": "7",
		"explanation": "The seven continents are Africa, Antarctica, Asia, Australia, Europe, North America, and South America."
	},
]

# Create your views here.
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def pre_quiz(request):
	if request.method == 'POST':
		# Handle POST request
		payload = request.data
		print('pre-quiz:', payload)
	return Response({
					'success': 'Success',
					'goto': 'take-quiz/take-quiz',
					'info': payload,
	}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def take_quiz(request):
	if request.method == 'POST':
		# number_of_questions = 5
		# Handle POST request

		# check user
		user = request.user
		authenticated = user.is_authenticated
		print(f'user: {user}')
		print(f'user is authenticated: {authenticated}')

		payload = request.data
		print('take-quiz:')
		pretty_print_json(payload)

		# Extract category info
		type_category = payload.get("type").lower()
		class_category = payload.get("class").lower()
		subject_category = payload.get("subject").lower()
		email = payload.get("email", None)
		number_of_questions = int(payload.get("noOfQs", 60))
		duration = float(payload.get("duration"))
		name = payload.get("name")

		# print(f'type: {type_category}')
		# print(f'class: {class_category}')
		# print(f'subject: {subject_category}')
		# print(f'email: {email}')
		# print(f'duration: {duration}')
		# print(f'name: {name}')

		try:
			category = Category.objects.get(
				type_category=type_category,
				class_category=class_category,
				subject_category=subject_category,
			)
		except Category.DoesNotExist:
			print("Invalid selection, no question exist in this category yet.")
			return Response(
				{"error": "Invalid selection, no question exist in this category yet."},
				status=status.HTTP_400_BAD_REQUEST
			)
		print(f'category: {category}')
		questions_qs = Question.objects.filter(
			category=category,
			# approved=True
		)
		questions_list = list(questions_qs)

		# RE-ENABLE TO PREVENT SENDING QUESTIONS BELOW THE NUMBER REQUESTED
		# if len(questions_list) < number_of_questions:
		# 	return Response(
		# 		{"error": "Not enough questions available for the selected category"},
		# 		status=status.HTTP_400_BAD_REQUEST
		# 	)


		# print('questions:')
		# print(questions)

		random.shuffle(questions_list)

		selected_questions = questions_list[:number_of_questions]

		with transaction.atomic():
			quiz_session = QuizSession.objects.create(
				email=email,
				name=name,
				duration=duration,
				user=user if authenticated else None
			)
			quiz_session.questions.set(selected_questions)

		print(f'started_at: {quiz_session.started_at}\ncreated_at: {quiz_session.created_at}')
		serialized_questions = QuestionReadSerializer(selected_questions, many=True).data
		print('serialized questions:')
		pretty_print_json(serialized_questions)

	return Response({
				'session_id': quiz_session.session_id,
				'questions': serialized_questions,
				'info': payload,
				'duration': payload['duration']
	}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def grade_quiz(request):
	payload = request.data
	print('grade test:')
	pretty_print_json(payload)
	# return Response({'resp': 'all good'})
	session_id = payload.get("session_id")
	answers = payload.get("answers", [])
	session = None

	# validate session exists
	try:
		session = QuizSession.objects.get(session_id=session_id)
	except QuizSession.DoesNotExist:
		return Response({"error": "Invalid session"}, status=status.HTTP_400_BAD_REQUEST)

	# prevent multiple submissions
	if session.is_submitted:
		print(f"User tried to resubmit session {session_id}")
		return Response({"error": "You cannot submit multiple sessions"}, status=status.HTTP_400_BAD_REQUEST)
	session.is_submitted = True
	session.save()

	# Convert list → dict for O(1) lookup
	submitted_map = {
		item["questionId"]: item["answer"]
		for item in answers
	}

	print('dict version:')
	pretty_print_json(submitted_map)
	# return Response({'resp': 'all good'})

	# Fetch all questions in ONE query
	questions = Question.objects.filter(id__in=submitted_map.keys())

	print(f'questions: {questions}')
	# return Response({'resp': 'all good'})

	score = 0
	results = []
	quiz_answers = []

	for q in questions:
		selected_answer = submitted_map[q.id]
		is_correct = selected_answer == q.correct_answer
		print(f'{q.correct_answer} = {selected_answer} ? {is_correct}')
		# print(f'is_correct: {is_correct}')
		if is_correct:
			score += 1

		# Store the answer
		quiz_answers.append(
			QuizAnswer(
				session=session,
				question=q,
				selected_option=selected_answer,
				is_correct=is_correct
			)
		)

		results.append({
			"question_id": q.id,
			"correct": is_correct,
			"correct_answer": q.correct_answer,
			"explanation": q.explanation
		})

	with transaction.atomic():
		QuizAnswer.objects.bulk_create(quiz_answers)

	response = {
		"score": score,
		"total": len(questions),
		"results": results
	}
	print(f'response:')
	pretty_print_json(response)
	# return Response({'resp': 'all good'})

	return Response(response, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def question_stats(request, question_id):
    stats = get_question_stats(question_id)
    return Response(stats, status=200)

def get_question_stats(question_ids):
    """
    Returns per-question stats including total attempts, correct answers,
    success rate, and option-level breakdown.
    """
    questions = Question.objects.filter(id__in=question_ids)
    stats = []

    for q in questions:
        # All answers for this question
        answers_qs = QuizAnswer.objects.filter(question=q)

        total_attempts = answers_qs.count()
        correct_count = answers_qs.filter(is_correct=True).count()
        success_rate = (correct_count / total_attempts * 100) if total_attempts else 0

        # Option-level breakdown
        option_stats = answers_qs.values('selected_option').annotate(
            count=Count('selected_option')
        ).order_by('-count')

        stats.append({
            "question_id": q.id,
            "question": q.question,
            "total_attempts": total_attempts,
            "correct_count": correct_count,
            "success_rate": round(success_rate, 2),
            "option_stats": list(option_stats)
        })

    return stats

@api_view(['GET'])
@permission_classes([AllowAny])
def send_time(request, session_id):
	if request.method == 'GET':
		# Handle GET request
		new_session = request.GET.get("session")
		print(f'new_session: {new_session}')
		print('session_id:', session_id)
		quiz_session = QuizSession.objects.filter(session_id=session_id).first()
		if not quiz_session:
			invalid_session = "Invalid Session."
			print(invalid_session)
			return Response({"error": invalid_session}, status=status.HTTP_400_BAD_REQUEST)
		if new_session == "true":
			quiz_session.started_at = timezone.now()
			quiz_session.save()
		start_time = quiz_session.started_at
		print(f'start_time: {start_time}')

		return Response(start_time, status=status.HTTP_200_OK)
