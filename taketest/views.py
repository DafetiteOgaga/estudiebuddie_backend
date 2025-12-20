from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

sample_questions = [
    {
        "question": "What is the capital of Nigeria?",
        "image": None,
        "options": ["Abuja", "Lagos", "Kano", "Port Harcourt"],
        "correct_answer": "Abuja",
        "explanation": "Abuja became Nigeria's capital in 1991, replacing Lagos."
    },
    {
        "question": "Solve: 15 ÷ 3",
        "image": None,
        "options": ["3", "5", "6", "9"],
        "correct_answer": "5",
        "explanation": "15 divided by 3 equals 5."
    },
    {
        "question": "Which of these is not a programming language?",
        "image": None,
        "options": ["Python", "Java", "Banana", "C++"],
        "correct_answer": "Banana",
        "explanation": "Banana is a fruit, not a programming language."
    },
    {
        "question": "Which gas do plants absorb from the atmosphere?",
        "image": None,
        "options": ["Oxygen", "Carbon Dioxide", "Hydrogen", "Nitrogen"],
        "correct_answer": "Carbon Dioxide",
        "explanation": "Plants absorb carbon dioxide for photosynthesis."
    },
    {
        "question": "What is the boiling point of water at sea level?",
        "image": None,
        "options": ["90°C", "100°C", "110°C", "120°C"],
        "correct_answer": "100°C",
        "explanation": "At sea level, water boils at 100 degrees Celsius."
    },
    {
        "question": "What is the next number in the sequence: 2, 4, 6, 8, ...?",
        "image": None,
        "options": ["9", "10", "12", "14"],
        "correct_answer": "10",
        "explanation": "It's an arithmetic sequence increasing by 2."
    },
    {
        "question": "Who wrote *Things Fall Apart*?",
        "image": None,
        "options": ["Wole Soyinka", "Chimamanda Ngozi Adichie", "Chinua Achebe", "Ben Okri"],
        "correct_answer": "Chinua Achebe",
        "explanation": "Chinua Achebe authored *Things Fall Apart* in 1958."
    },
    {
        "question": "Which planet is closest to the sun?",
        "image": None,
        "options": ["Earth", "Venus", "Mercury", "Mars"],
        "correct_answer": "Mercury",
        "explanation": "Mercury is the closest planet to the sun."
    },
    {
        "question": "What is the chemical symbol for Gold?",
        "image": None,
        "options": ["Go", "G", "Au", "Ag"],
        "correct_answer": "Au",
        "explanation": "The symbol 'Au' comes from the Latin word 'Aurum'."
    },
    {
        "question": "How many continents are there on Earth?",
        "image": None,
        "options": ["5", "6", "7", "8"],
        "correct_answer": "7",
        "explanation": "The seven continents are Africa, Antarctica, Asia, Australia, Europe, North America, and South America."
    },
]

# Create your views here.
@api_view(['GET', 'POST'])
def pretest(request):
	if request.method == 'POST':
		# Handle POST request
		payload = request.data
		print('pretest:', payload)
	return Response({
					'success': 'Success',
					'goto': 'taketest/taketest',
					'info': payload,
    })

@api_view(['GET', 'POST'])
def taketest(request):
	if request.method == 'POST':
		# Handle POST request
		payload = request.data
		print('taketest:', payload)
	return Response({
				'questions': sample_questions,
				'info': payload,
				'duration': payload['duration']
    })
