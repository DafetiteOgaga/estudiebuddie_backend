from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from hooks.pretty_print import pretty_print_json
from root_utils.formDataToDict import print_formdata_content, cleanup_old_zips, parse_nested_formdata
from .models import ScrambleSession
from .serializers import ScrambleSessionReadSerializer, ScrambleSessionWriteSerializer, SchoolSerializer
from user.serializers import UserSerializer
import re, logging
from collections import defaultdict
from django.db import transaction
logger = logging.getLogger(__name__)

# def reconstruct_scramble_payload(flat_data):
# 	result = {}
# 	# questions = defaultdict(dict)
# 	questions = defaultdict(lambda: defaultdict(dict))

# 	# question_pattern = re.compile(r"questions\[(\d+)\]\[(.+?)\]")
# 	question_pattern = re.compile(
# 		r"questions\[(\d+)\]\[(\w+)\](?:\[(\d+)\])?(?:\[(\w+)\])?"
# 	)

# 	for key, value in flat_data.items():
# 		match = question_pattern.match(key)

# 		if match:
# 			# index, field = match.groups()
# 			# questions[int(index)][field] = value
# 			q_index, field, sub_index, sub_field = match.groups()

# 			q_index = int(q_index)

# 			if sub_index is None:
# 				questions[q_index][field] = value

# 			elif sub_field is None:
# 				questions[q_index].setdefault(field, [])
# 				idx = int(sub_index)

# 				while len(questions[q_index][field]) <= idx:
# 					questions[q_index][field].append(None)

# 				questions[q_index][field][idx] = value

# 			else:
# 				questions[q_index].setdefault(field, [])
# 				idx = int(sub_index)

# 				while len(questions[q_index][field]) <= idx:
# 					questions[q_index][field].append({})

# 				questions[q_index][field][idx][sub_field] = value
# 		else:
# 			result[key] = value

# 	# convert questions dict to ordered list
# 	result["questions"] = [
# 		questions[i] for i in sorted(questions.keys())
# 	]
# 	return result

# def reconstruct_scramble_payload(flat_data):
#     result = {}

#     for key, value in flat_data.items():

#         # split key into parts
#         parts = re.findall(r"[^\[\]]+", key)

#         current = result

#         for i, part in enumerate(parts):
#             is_last = i == len(parts) - 1

#             # convert numeric indexes
#             if part.isdigit():
#                 part = int(part)

#             if is_last:
#                 if isinstance(current, list):
#                     while len(current) <= part:
#                         current.append(None)
#                     current[part] = value
#                 else:
#                     current[part] = value
#             else:
#                 next_part = parts[i + 1]
#                 next_is_index = next_part.isdigit()

#                 if isinstance(current, list):
#                     while len(current) <= part:
#                         current.append({} if not next_is_index else [])

#                     if current[part] is None:
#                         current[part] = {} if not next_is_index else []

#                     current = current[part]

#                 else:
#                     if part not in current:
#                         current[part] = [] if next_is_index else {}

#                     current = current[part]

#     return result

KEY_SPLIT = re.compile(r'\[|\]')

def reconstruct_scramble_payload(flat_data):
    result = {}

    for key, value in flat_data.items():

        # Split and remove empty strings
        parts = [p for p in KEY_SPLIT.split(key) if p]

        current = result

        for i, part in enumerate(parts):
            last = i == len(parts) - 1
            next_part = parts[i + 1] if not last else None

            # detect numeric index
            if part.isdigit():
                part = int(part)

            if last:
                if isinstance(current, list):
                    if part >= len(current):
                        current.extend([None] * (part - len(current) + 1))
                    current[part] = value
                else:
                    current[part] = value
                continue

            # decide next container type
            next_container = [] if next_part and next_part.isdigit() else {}

            if isinstance(current, list):
                if part >= len(current):
                    current.extend([None] * (part - len(current) + 1))

                if current[part] is None:
                    current[part] = next_container

                current = current[part]

            else:
                current = current.setdefault(part, next_container)

    return result

# Create your views here.
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def remember_sessions(request, detailed_resp):
	cleanup_old_zips()
	qp = request.query_params
	logger.info(f'qp: {qp}')
	d_all = qp.get("delete_all")
	raw_ids = qp.get("allIDs")
	logger.info(f'd_all: {d_all}\nraw_ids: {raw_ids}')
	if d_all and not raw_ids:
		logger.info('nothing to delete')
		return Response({"error": "Nothing to delete."}, status=status.HTTP_400_BAD_REQUEST)
	cleaned_ids = None

	teacher = request.user
	# if not teacher.school:
	# 	return Response({"error": "Oopsy! You have no school assigned to you, contact your admin."},
	# 						status=status.HTTP_400_BAD_REQUEST)
	# school = teacher.school
	school = getattr(teacher, "school", None)
	if not school:
		return Response({"error": "school not found"}, status=status.HTTP_400_BAD_REQUEST)
	logger.info('school info:')
	user_info = {
		"teacher": teacher,
		"school": school,
	}
	pretty_print_json(user_info)

	if d_all:
		cleaned_ids = raw_ids.split(',')
		cleaned_ids = [int(i) for i in cleaned_ids]
		logger.info(f'cleaned_ids: {cleaned_ids}')
		# return Response({
		# 		"success": "good"},
		# 		status=status.HTTP_400_BAD_REQUEST)
		with transaction.atomic():
			ScrambleSession.objects.filter(
				teacher=teacher,
				school=school,
				id__in=cleaned_ids
			).delete()
		return Response({
				"success": "Saved item deleted Successfully" if len(cleaned_ids)==1 else "All saved items deleted successfully"},
				status=status.HTTP_200_OK)

	if request.method == 'POST':
		scramble_session_data = parse_nested_formdata(request.data, request.FILES)
		print_formdata_content(scramble_session_data)
		# return Response({"all": "good"}, status=status.HTTP_400_BAD_REQUEST)

		# saved_id = scramble_session_data.get("savedID", None)
		session_class = scramble_session_data.get("class", None)
		session_term = scramble_session_data.get("term", None)
		session_subject = scramble_session_data.get("subject", None)
		# logger.info(f'saved_id: {saved_id}')
		logger.info(f'session_class: {session_class}\nsession_term: {session_term}\nsession_subject: {session_subject}')
		found_session_by_category = None
		is_update = False

		# if saved_id:
		# 	try:
		# 		saved_id = int(saved_id)
		# 	except (TypeError, ValueError):
		# 		return Response(
		# 					{"error": "Invalid: Session cannot be saved"},
		# 					status=status.HTTP_400_BAD_REQUEST
		# 				)
		# 	logger.info('updating existing session')
		# 	session = ScrambleSession.objects.filter(
		# 		id=saved_id,
		# 		teacher=teacher,
		# 		school=school,
		# 	).first()

		# 	if not session:
		# 		no_session_txt = "Oopsy! Session does not exist"
		# 		return Response({"error": no_session_txt}, status=status.HTTP_400_BAD_REQUEST)

		# 	post_serializer = ScrambleSessionWriteSerializer(
		# 		session,
		# 		data={
		# 			"scramble_session_data": scramble_session_data,
		# 			"session_class": session_class,
		# 			"session_term": session_term,
		# 			"session_subject": session_subject,
		# 		},
		# 		partial=True,
		# 		context={'request': request}
		# 	)
		# 	is_update = True
		# else:
		logger.info('checking session by category')
		found_session_by_category = ScrambleSession.objects.filter(
			teacher=teacher,
			school=school,
			session_class=session_class,
			session_term=session_term,
			session_subject=session_subject,
		).first()

		if found_session_by_category:
			logger.info("found session by category")
			logger.info('updating existing session')
			post_serializer = ScrambleSessionWriteSerializer(
				found_session_by_category,
				data={
					"scramble_session_data": scramble_session_data,
					"session_class": session_class,
					"session_term": session_term,
					"session_subject": session_subject,
				},
				partial=True,
				context={'request': request}
			)
			is_update = True
		else:
			logger.info('creating new session')
			post_serializer = ScrambleSessionWriteSerializer(
				data={
					"scramble_session_data": scramble_session_data,
					"session_class": session_class,
					"session_term": session_term,
					"session_subject": session_subject,
				},
				context={'request': request}
			)
			# is_update = False

		# is_update = saved_id is not None or found_session_by_category is not None
		status_code = status.HTTP_200_OK if is_update else status.HTTP_201_CREATED
		if post_serializer.is_valid():
			logger.info('serialized data is valid')
			post_serializer.save()
			logger.info('serialized data saved:')
			pretty_print_json(post_serializer)
			response_text = "Progress updated" if is_update else "Progress saved"
			logger.info(response_text)
			return Response({"success": response_text},
								status=status_code)

		logger.info(f'post_serializer.errors: {post_serializer.errors}')
		return Response({"error": "Could not save."}, status=status.HTTP_400_BAD_REQUEST)

	if detailed_resp and detailed_resp.isdigit():
		session = ScrambleSession.objects.filter(
			teacher=teacher,
			school=school,
			id=int(detailed_resp),
		).first()

		detailed_data = ScrambleSessionReadSerializer(session).data
		# detailed_data = serializer.data
		if "questions[0][correct_answer]" in detailed_data["scramble_session_data"].keys() or \
			"postQuestions[0][correct_answer]" in detailed_data["scramble_session_data"].keys():
			logger.info('being processed')
			detailed_data["scramble_session_data"] = reconstruct_scramble_payload(detailed_data["scramble_session_data"])

		# detailed_data["scramble_session_data"] = reconstruct_scramble_payload(
		# 	detailed_data["scramble_session_data"]
		# )
		if "postQuestions" in detailed_data["scramble_session_data"].keys():
			logger.info('yeah, it has postQuestions and not questions')
			logger.info('renaming postQuestions to questions')
			detailed_data["scramble_session_data"]["questions"] = detailed_data["scramble_session_data"]["postQuestions"]
			detailed_data["scramble_session_data"].pop("postQuestions")
		logger.info('detailed_data:')
		pretty_print_json(detailed_data)

		return Response(detailed_data, status=status.HTTP_200_OK)

	sessions = ScrambleSession.objects.filter(
		teacher=teacher,
		school=school
	).order_by('-updated_at')
	logger.info('fetched saved sessions')

	get_session_serializer = ScrambleSessionReadSerializer(
		sessions, many=True
	).data

	# logger.info(f'get_session_serializer:')
	# pretty_print_json(get_session_serializer)

	list_of_data = []
	for session in get_session_serializer:
		# logger.info('session start')
		# pretty_print_json(session)
		# logger.info('session end')
		new_form_questions = session["scramble_session_data"].get("questions") or session["scramble_session_data"].get("postQuestions") or None

		# remove reconstruct_scramble_payload() now
		reconstructed = reconstruct_scramble_payload(
			session["scramble_session_data"]
		)
		# logger.info(f'session question:')
		# pretty_print_json(session["scramble_session_data"]["questions"])
		logger.info(f'reconstructed:')
		pretty_print_json(reconstructed)
		# session["scramble_session_data"] = reconstructed

		objective_questions = reconstructed.get("questions") or reconstructed.get("postQuestions") or []
		theory_questions = reconstructed.get("theory", None)
		logger.info(f'new_form_questions: {bool(new_form_questions)}')
		logger.info(f'objective_questions: {bool(objective_questions)}')
		if objective_questions == [] and new_form_questions:
			logger.info('using new_form_questions')
			objective_questions = new_form_questions
		logger.info(f'objective_questions:')
		pretty_print_json(objective_questions)
		logger.info(f'theory_questions:')
		pretty_print_json(theory_questions)

		list_of_data.append({
			"id": session.get("id"),
			"has_submitted": session.get("has_submitted"),
			"class": reconstructed.get("class"),
			"subject": reconstructed.get("subject"),
			"term": reconstructed.get("term"),
			"objective_questions": len(objective_questions) if objective_questions else None,
			"theory_questions": len(theory_questions) if theory_questions else None,
		})
	logger.info('whats being returned:')
	pretty_print_json(list_of_data)
	return Response(list_of_data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_school(request):
	cleanup_old_zips()
	if request.method == 'POST':
		head = request.user
		logger.info(f'user: {head}')
		logger.info(f'role: {head.role}')
		update_payload = request.data
		logger.info(f'update_payload:')
		pretty_print_json(update_payload)
		if head.role != "head":
			logger.info("You do not have permission for this action.")
			return Response({"erreo": "You do not have permission for this action."}, status=status.HTTP_400_BAD_REQUEST)
		school = getattr(head, "school", None)
		if not school:
			logger.info("Oopsy! No school found.")
			return Response({"error": "Oopsy! No school found."}, status=status.HTTP_400_BAD_REQUEST)
		logger.info(f'school: {school}')
		serialized_school = SchoolSerializer(
			school,
			data=update_payload,
			partial=True)
		if serialized_school.is_valid():
			logger.info("Data that WILL be saved (not yet saved):")
			pretty_print_json(serialized_school.validated_data)
			# return Response({"ok": "all good"}, status=status.HTTP_200_OK)
			serialized_school.save()
			# head.school = serialized_school.data
			head_serializer = UserSerializer(head).data
			logger.info('head_serializer')
			pretty_print_json(head_serializer)
		else:
			not_saved = "Unable to update school information"
			logger.info(f'serialized_school error: {serialized_school.errors}')
			logger.info(f'error message: {serialized_school.error_messages}')
			return Response({"error": not_saved}, status=status.HTTP_400_BAD_REQUEST)
		return Response(head_serializer, status=status.HTTP_200_OK)
