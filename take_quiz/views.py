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

mock_questions = [
    {
		"id": 1,
		"question": "What color is the sky during the day?",
		"options": ["Blue", "Green", "Red", "Black"],
		"explanation": "The sky appears blue due to sunlight scattering.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Blue",
	},
    {
		"id": 2,
		"question": "How many legs does a dog have?",
		"options": ["Two", "Three", "Four", "Five"],
		"explanation": "Dogs have four legs.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Four",
	},
    {
		"id": 3,
		"question": "Which of these is a fruit?",
		"options": ["Carrot", "Apple", "Onion", "Pepper"],
		"explanation": "Apple is a fruit.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Apple",
	},
    {
		"id": 4,
		"question": "Which number comes after 9?",
		"options": ["7", "8", "10", "11"],
		"explanation": "10 comes after 9.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "10",
	},
    {
		"id": 5,
		"question": "What part of the body is used for seeing?",
		"options": ["Ear", "Eye", "Nose", "Mouth"],
		"explanation": "We use our eyes to see.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Eye",
	},
    {
		"id": 6,
		"question": "How many days are there in a week?",
		"options": ["5", "6", "7", "8"],
		"explanation": "There are 7 days in a week.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "7",
	},
    {
		"id": 7,
		"question": "Which animal lives in water?",
		"options": ["Dog", "Goat", "Fish", "Cat"],
		"explanation": "Fish live in water.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Fish",
	},
    {
		"id": 8,
		"question": "What is 5 + 3?",
		"options": ["6", "7", "8", "9"],
		"explanation": "5 + 3 equals 8.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "8",
	},
    {
		"id": 9,
		"question": "Which shape has three sides?",
		"options": ["Square", "Triangle", "Circle", "Rectangle"],
		"explanation": "A triangle has three sides.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Triangle",
	},
    {
		"id": 10,
		"question": "Which of these is a source of light?",
		"options": ["Moon", "Sun", "Book", "Chair"],
		"explanation": "The sun produces light.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Sun",
	},
    {
		"id": 11,
		"question": "Which part of a plant makes food?",
		"options": ["Root", "Stem", "Leaf", "Flower"],
		"explanation": "Leaves make food by photosynthesis.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Leaf",
	},
    {
		"id": 12,
		"question": "What is the capital of Nigeria?",
		"options": ["Lagos", "Ibadan", "Abuja", "Benin"],
		"explanation": "Abuja is the capital of Nigeria.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Abuja",
	},
    {
		"id": 13,
		"question": "Which gas do humans breathe in?",
		"options": ["Carbon dioxide", "Oxygen", "Nitrogen", "Hydrogen"],
		"explanation": "Humans breathe in oxygen.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Oxygen",
	},
    {
		"id": 14,
		"question": "What is the boiling point of water?",
		"options": ["50°C", "75°C", "100°C", "150°C"],
		"explanation": "Water boils at 100°C.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "100°C",
	},
    {
		"id": 15,
		"question": "Which of these is a noun?",
		"options": ["Run", "Blue", "Happiness", "Quickly"],
		"explanation": "Happiness is a noun.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Happiness",
	},
    {
		"id": 16,
		"question": "Which organ pumps blood in the body?",
		"options": ["Liver", "Brain", "Heart", "Kidney"],
		"explanation": "The heart pumps blood.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Heart",
	},
    {
		"id": 17,
		"question": "What is the square root of 16?",
		"options": ["2", "3", "4", "5"],
		"explanation": "The square root of 16 is 4.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "4",
	},
    {
		"id": 18,
		"question": "Which device is used to input text into a computer?",
		"options": ["Monitor", "Printer", "Keyboard", "Speaker"],
		"explanation": "A keyboard is an input device.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Keyboard",
	},
    {
		"id": 19,
		"question": "What is the chemical symbol for oxygen?",
		"options": ["Ox", "O", "Og", "Oy"],
		"explanation": "O is the symbol for oxygen.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "O",
	},
    {
		"id": 20,
		"question": "Which law relates voltage, current, and resistance?",
		"options": ["Newton's Law", "Ohm's Law", "Boyle's Law", "Faraday's Law"],
		"explanation": "Ohm's Law explains the relationship.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Ohm's Law",
	},
    {
		"id": 21,
		"question": "What is the formula for speed?",
		"options": ["Distance × Time", "Distance ÷ Time", "Time ÷ Distance", "Mass × Acceleration"],
		"explanation": "Speed equals distance divided by time.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Distance ÷ Time",
	},
    {
		"id": 22,
		"question": "Which blood group is the universal donor?",
		"options": ["A", "B", "AB", "O"],
		"explanation": "Blood group O is the universal donor.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "O",
	},
    {
		"id": 23,
		"question": "What type of bond involves sharing electrons?",
		"options": ["Ionic", "Covalent", "Metallic", "Hydrogen"],
		"explanation": "Covalent bonds share electrons.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Covalent",
	},
    {
		"id": 24,
		"question": "Which part of the brain controls balance?",
		"options": ["Cerebrum", "Cerebellum", "Medulla", "Hypothalamus"],
		"explanation": "The cerebellum controls balance.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Cerebellum",
	},
    {
		"id": 25,
		"question": "What is acceleration?",
		"options": ["Change in distance", "Change in speed", "Change in velocity per time", "Change in mass"],
		"explanation": "Acceleration is the rate of change of velocity.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Change in velocity per time",
	},
    {
		"id": 26,
		"question": "Which gas is released during photosynthesis?",
		"options": ["Carbon dioxide", "Oxygen", "Nitrogen", "Hydrogen"],
		"explanation": "Oxygen is released.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Oxygen",
	},
    {
		"id": 27,
		"question": "What is the SI unit of force?",
		"options": ["Joule", "Newton", "Watt", "Pascal"],
		"explanation": "Newton is the SI unit of force.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Newton",
	},
    {
		"id": 28,
		"question": "What is the pH value of a neutral solution?",
		"options": ["0", "7", "10", "14"],
		"explanation": "Neutral solutions have pH 7.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "7",
	},
    {
		"id": 29,
		"question": "Which scientist proposed the theory of evolution?",
		"options": ["Newton", "Einstein", "Darwin", "Galileo"],
		"explanation": "Charles Darwin proposed evolution.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Darwin",
	},
    {
		"id": 30,
		"question": "Which organ is responsible for detoxification?",
		"options": ["Heart", "Kidney", "Liver", "Lungs"],
		"explanation": "The liver detoxifies harmful substances.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Liver",
	},
    {
		"id": 31,
		"question": "Which of these is used for hearing?",
		"options": ["Eye", "Nose", "Ear", "Skin"],
		"explanation": "The ear is used for hearing.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Ear",
	},
    {
		"id": 32,
		"question": "Which of these animals can fly?",
		"options": ["Dog", "Cat", "Bird", "Goat"],
		"explanation": "Birds can fly.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Bird",
	},
    {
		"id": 33,
		"question": "How many hours make one day?",
		"options": ["12", "18", "24", "36"],
		"explanation": "There are 24 hours in a day.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "24",
	},
	{
		"id": 34, "question": "Which of these is a means of transport?",
		"options": ["Chair", "Car", "Plate", "Cup"],
		"explanation": "A car is used for transportation.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Car"
	},
	{
		"id": 35,
		"question": "What do we call animals that eat only plants?",
		"options": ["Carnivores", "Herbivores", "Omnivores", "Scavengers"],
		"explanation": "Herbivores eat only plants.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Herbivores",
	},
    {
		"id": 36,
		"question": "Which of these is a non-living thing?",
		"options": ["Tree", "Dog", "Stone", "Man"],
		"explanation": "Stone is non-living.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Stone",
	},
    {
		"id": 37,
		"question": "Which fraction is equal to one half?",
		"options": ["2/4", "3/4", "1/4", "4/4"],
		"explanation": "2/4 is equal to 1/2.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "2/4",
	},
    {
		"id": 38,
		"question": "What is the function of the lungs?",
		"options": ["Pump blood", "Digest food", "Exchange gases", "Filter waste"],
		"explanation": "The lungs exchange gases.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Exchange gases",
	},
    {
		"id": 39,
		"question": "Which vitamin is obtained from sunlight?",
		"options": ["Vitamin A", "Vitamin B", "Vitamin C", "Vitamin D"],
		"explanation": "Vitamin D is obtained from sunlight.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Vitamin D",
	},
    {
		"id": 40,
		"question": "Which of these materials conducts electricity?",
		"options": ["Plastic", "Rubber", "Copper", "Wood"],
		"explanation": "Copper is a good conductor of electricity.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Copper",
	},
    {
		"id": 41,
		"question": "Which planet is the largest in the solar system?",
		"options": ["Earth", "Mars", "Jupiter", "Venus"],
		"explanation": "Jupiter is the largest planet.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Jupiter",
	},
    {
		"id": 42,
		"question": "What is the SI unit of force?",
		"options": ["Joule", "Newton", "Watt", "Pascal"],
		"explanation": "Newton is the SI unit of force.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Newton",
	},
    {
		"id": 43,
		"question": "Which process converts sugar to alcohol?",
		"options": ["Respiration", "Fermentation", "Photosynthesis", "Evaporation"],
		"explanation": "Fermentation converts sugar to alcohol.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Fermentation",
	},
    {
		"id": 44,
		"question": "What is the main function of red blood cells?",
		"options": ["Fight infection", "Carry oxygen", "Clot blood", "Digest food"],
		"explanation": "Red blood cells carry oxygen.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Carry oxygen",
	},
    {
		"id": 45,
		"question": "Which of these is a vector quantity?",
		"options": ["Speed", "Mass", "Velocity", "Time"],
		"explanation": "Velocity has magnitude and direction.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Velocity",
	},
    {
		"id": 46,
		"question": "What is the SI unit of electric current?",
		"options": ["Volt", "Ohm", "Ampere", "Watt"],
		"explanation": "Ampere is the SI unit of current.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Ampere",
	},
    {
		"id": 47,
		"question": "Which gas supports combustion?",
		"options": ["Carbon dioxide", "Oxygen", "Nitrogen", "Helium"],
		"explanation": "Oxygen supports burning.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Oxygen",
	},
    {
		"id": 48,
		"question": "Which branch of biology studies plants?",
		"options": ["Zoology", "Botany", "Ecology", "Genetics"],
		"explanation": "Botany is the study of plants.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Botany",
	},
    {
		"id": 49,
		"question": "What is the value of pi to two decimal places?",
		"options": ["3.12", "3.14", "3.16", "3.18"],
		"explanation": "Pi is approximately 3.14.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "3.14",
	},
    {
		"id": 50,
		"question": "Which organ removes waste from the blood?",
		"options": ["Heart", "Lungs", "Kidney", "Stomach"],
		"explanation": "The kidneys remove waste from the blood.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Kidney",
	},
    {
		"id": 51,
		"question": "What is the main source of energy for the Earth?",
		"options": ["Moon", "Stars", "Sun", "Wind"],
		"explanation": "The sun is the main source of energy.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Sun",
	},
    {
		"id": 52,
		"question": "Which metal is liquid at room temperature?",
		"options": ["Iron", "Mercury", "Aluminium", "Copper"],
		"explanation": "Mercury is liquid at room temperature.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Mercury",
	},
    {
		"id": 53,
		"question": "What is the process by which plants lose water?",
		"options": ["Respiration", "Transpiration", "Evaporation", "Condensation"],
		"explanation": "Plants lose water through transpiration.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Transpiration",
	},
    {
		"id": 54,
		"question": "Which gas is most abundant in the air?",
		"options": ["Oxygen", "Carbon dioxide", "Nitrogen", "Hydrogen"],
		"explanation": "Nitrogen is the most abundant gas in air.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Nitrogen",
	},
    {
		"id": 55,
		"question": "What does DNA stand for?",
		"options": ["Deoxyribonucleic Acid", "Dynamic Nuclear Acid", "Double Nitric Acid", "Deoxynitric Agent"],
		"explanation": "DNA stands for Deoxyribonucleic Acid.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Deoxyribonucleic Acid",
	},
    {
		"id": 56,
		"question": "Which instrument is used to measure temperature?",
		"options": ["Barometer", "Thermometer", "Hygrometer", "Anemometer"],
		"explanation": "A thermometer measures temperature.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Thermometer",
	},
    {
		"id": 57,
		"question": "What type of energy is stored in food?",
		"options": ["Kinetic", "Thermal", "Chemical", "Electrical"],
		"explanation": "Food stores chemical energy.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Chemical",
	},
    {
		"id": 58,
		"question": "Which law explains action and reaction?",
		"options": ["Ohm's Law", "Newton's First Law", "Newton's Third Law", "Boyle's Law"],
		"explanation": "Newton's Third Law explains action and reaction.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Newton's Third Law",
	},
    {
		"id": 59,
		"question": "Which part of the eye controls the amount of light entering?",
		"options": ["Cornea", "Iris", "Lens", "Retina"],
		"explanation": "The iris controls light entering the eye.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Iris",
	},
    {
		"id": 60,
		"question": "Which planet is known as the Red Planet?",
		"options": ["Venus", "Mars", "Jupiter", "Saturn"],
		"explanation": "Mars is called the Red Planet.",
		"fileId": None,
		"image_url": None,
		"correct_answer": "Mars",
	}
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

		go_test = True
		try:
			if go_test: # test development
				category = Category.objects.get(
					id=1
				)
			else:
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
   
		if go_test: # test development
			questions_list = mock_questions # remove mock in full production
		else:
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
			if not go_test:
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
	# if session.is_submitted:
	# 	print(f"User tried to resubmit session {session_id}")
	# 	return Response({"error": "You cannot submit multiple sessions"}, status=status.HTTP_400_BAD_REQUEST)
	# session.is_submitted = True
	# session.save()

	now = timezone.now()
	quiz_duration = round((now - session.started_at).total_seconds(), 4)
	print(f'started_at: {session.started_at}\nnow: {now}\nquiz_duration: {quiz_duration}')

	# Convert list → dict for O(1) lookup
	submitted_map = {
		item["questionId"]: {
			"answer": item.get("answer"),
			"response_duration": item.get("response_duration"),
		}
		for item in answers
	}

	print('dict version:')
	pretty_print_json(submitted_map)
	# return Response({'resp': 'all good'})

	# Fetch all questions in ONE query
	go_test = True
	if go_test: # test development
		questions = [item for item in mock_questions if item["id"] in submitted_map.keys()] # remove mock in full production
		print('Questions:')
		pretty_print_json(questions)
	else:
		questions = Question.objects.filter(id__in=submitted_map.keys())

		print(f'questions: {questions}')
	# return Response({'resp': 'all good'})

	score = 0
	results = []
	quiz_answers = []

	for q in questions:
		print(f'q: {q}')
		if go_test: # test development
			submitted = submitted_map[q["id"]]
		else:
			submitted = submitted_map[q.id]
		print(f'submitted: {submitted}')
		selected_answer = submitted["answer"]
		response_duration = submitted["response_duration"]
		if go_test: # test development
			is_correct = selected_answer == q["correct_answer"]
		else:
			is_correct = selected_answer == q.correct_answer
			print(f'{q.correct_answer} = {selected_answer} ? {is_correct}')
		# print(f'is_correct: {is_correct}')
		if is_correct:
			score += 1

		if not go_test: # test development
			# Store the answer
			quiz_answers.append(
				QuizAnswer(
					session=session,
					question=q,
					selected_option=selected_answer,
					is_correct=is_correct,
					response_duration=response_duration,
				)
			)

		if go_test: # test development
			results.append({
				"question_id": q["id"],
				"correct": is_correct,
				"correct_answer": q["correct_answer"],
				"explanation": q["explanation"],
				"response_duration": response_duration,
			})
		else:
			results.append({
				"question_id": q.id,
				"correct": is_correct,
				"correct_answer": q.correct_answer,
				"explanation": q.explanation,
				"response_duration": response_duration,
			})

	with transaction.atomic():
		if not go_test: # test development
			QuizAnswer.objects.bulk_create(quiz_answers)

	response = {
		"quiz_score": score,
		"quiz_attempted": len(questions),
		"quiz_result": results,
		"quiz_duration": quiz_duration,
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
