from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .utils.randomize import Randomize, zip_all
from .models import ScrambleLinks
from .serializers import ScrambleLinksSerializer
from root_utils.formDataToDict import parse_nested_formdata, print_formdata_content, cleanup_old_zips
from hooks.pretty_print import pretty_print_json
from school.models import SubmitedQuestions, ScrambleSession
from school.serializers import SubmittedQuestionsReadSerializer, SubmittedQuestionsWriteSerializer
from school.serializers import ScrambleSessionWriteSerializer
# from ../root_utils.formDataToDict import parse_nested_formdata
import json
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

def handle_shuffle_record(data):
	print('checking for existing scramble')

	user = data["user"]
	school = data["school"]
	parsed_data = data["parsed_data"]
	shuffle_record = data["shuffle_record"]

	post_payload = data["post_payload"]
	request = data["request"]

	saved_question = ScrambleSession.objects.filter(
		teacher=user,
		school=school,
		session_subject=parsed_data["subject"],
		session_term=parsed_data["term"],
		session_class=parsed_data["class"],
		# "level": parsed_data["level"]
	).first()
	print(f'saved_question: {saved_question}')
	if not saved_question:
		if post_payload and request:
			print('creating ScrambleSession')
			saved_question = ScrambleSessionWriteSerializer(
				data={
					"scramble_session_data": post_payload,
					"session_class": parsed_data["class"],
					"session_term": parsed_data["term"],
					"session_subject": parsed_data["subject"],
				},
				context={'request': request}
			)
			if saved_question.is_valid():
				print('saved_question is valid')
				saved_question = saved_question.save()
				print(saved_question)
	# if saved_question:
	print('ready to take shuffle_record!')
	pretty_print_json(shuffle_record)
	saved_question.shuffle_record = shuffle_record
	saved_question.save()

# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_exam_bundle(request):
	cleanup_old_zips()
	user = request.user
	print(f'user: {user}')
	school = getattr(user, "school", None)
	# print(f'school: {school}')
	if request.method == 'POST':
		saved_question = None

		post_payload = request.data
		parsed_data = parse_nested_formdata(post_payload, request.FILES)
		print(f'parsed_data:')
		pretty_print_json(parsed_data)
		# return Response({"success": "Success", "downloadLink": "file_url"})
		db_category = {
			"teacher_id": user.id,
			"school_id": school.id,
			"session_subject": parsed_data["subject"],
			"session_term": parsed_data["term"],
			"session_class": parsed_data["class"],
		}
		file_url, shuffle_record = Randomize(parsed_data, db_category=db_category)
		print("Generated file URL:", file_url)
		print('free usage')

		print(f'user: {user}')
		print(f'school: {school}')
		if school and shuffle_record:
			handle_shuffle_record({
				"user": user,
				"school": school,
				"parsed_data": parsed_data,
				"post_payload": post_payload,
				"request": request,
				"shuffle_record": shuffle_record
			})

		# save link for future downloads
		ScrambleLinks.objects.create(
			user=request.user,
			link=file_url,
		)
		return Response({"success": "Success", "downloadLink": file_url})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_links(request):
	cleanup_old_zips()
	if request.method == 'GET':
		user = request.user
		print(f'user: {user}')

		links = ScrambleLinks.objects.filter(user=user).order_by('-created_at')[:5]
		# print(f'links: {links}')
		serialized_links = ScrambleLinksSerializer(links, many=True).data
		print(f'serialized_links:')
		pretty_print_json(serialized_links)
		return Response(serialized_links, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_submitted(request):
	cleanup_old_zips()
	user = request.user
	school = user.school
	qp = request.query_params
	print(f'qp: {qp}')
	teacher_id = qp.get("teacherID", None)
	if teacher_id:
		try:
			teacher_id = int(teacher_id)
		except:
			print("Oopsy! Teacher/Admin not specified.")
			return Response({"error": "Oopsy! Teacher/Admin not specified."})
	print(f'teacher_id: {teacher_id}')
	print(f'user: {user}\nschool: {school}')
	if user.role not in ["admin", "head"]:
		print('you have no permision to view this')
		return Response({"error": "you do not have permission for this action."})
	submitted_objs = SubmitedQuestions.objects.filter(
		school=school,
		teacher_id=teacher_id
	).order_by('-updated_at')
	serialized_objs = SubmittedQuestionsReadSerializer(
		submitted_objs, many=True
	).data
	print('checked response:')
	pretty_print_json(serialized_objs)
	return Response(serialized_objs, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def generate_exam_bundle_for_school(request):
	cleanup_old_zips()
	qp = request.query_params
	print(f'qp: {qp}')
	d_all = qp.get("submit_all")
	raw_ids = qp.get("allIDs")
	print(f'd_all: {d_all}\nraw_ids: {raw_ids}')
	if d_all and not raw_ids:
		print('nothing to delete')
		return Response({"error": "Nothing to delete."}, status=status.HTTP_400_BAD_REQUEST)
	cleaned_ids = None

	user = request.user
	print(f'user: {user}')
	school = getattr(user, "school", None)
	# print(f'school: {school.name}')
	handle_shuffle_record_arg = {
		"user": user,
		"school": school,
		"post_payload": None,
		"request": None,
	}
	db_category = {
			"teacher_id": user.id,
			"school_id": school.id,
		}

	if not school:
		return Response({"error": "you do not have the authorization for this action."})

	print(f'school: {school.name}')

	if d_all:
		cleaned_ids = raw_ids.split(',')
		cleaned_ids = [int(i) for i in cleaned_ids]
		print(f'cleaned_ids: {cleaned_ids}')
		with transaction.atomic():
			saved_questions = ScrambleSession.objects.filter(
				teacher=user,
				school=school,
				id__in=cleaned_ids
			)

			print(f'saved_questions: {saved_questions}')

			saved_list = [
				{
					"scramble_id": obj.id,
					"session_class": obj.session_class,
					"session_term": obj.session_term,
					"session_subject": obj.session_subject,
					"submitted_session_data": obj.scramble_session_data
				}
				for obj in saved_questions
			]

			# print(f'saved_list: {saved_list}')

			query = Q()
			for item in saved_list:
				# print('item in saved list:')
				# pretty_print_json(item)
				query |= Q(
					session_class=item["session_class"],
					session_term=item["session_term"],
					session_subject=item["session_subject"],
					teacher=user,
					school=school
				)

			existing = SubmitedQuestions.objects.filter(query)

			print(f'existing in submitted: {existing}')

			# map existing by class/term/subject for quick lookup
			existing_map = {
				(obj.session_class, obj.session_term, obj.session_subject): obj
				for obj in existing
			}

			print(f'existing_map: {existing_map}')

			to_update = []
			to_create = []

			for item in saved_list:
				print(f'item:')
				pretty_print_json(item)
				key = (item["session_class"], item["session_term"], item["session_subject"])
				if key in existing_map:
					print(f'append to update list')
					print(f'key: {key}')
					obj = existing_map[key]
					obj.submitted_session_data = item["submitted_session_data"]
					obj.submitted_session_data = item["submitted_session_data"]
					obj.updated_at = timezone.now()
					to_update.append(obj)
				else:
					print(f'append to create list')
					to_create.append(
						SubmitedQuestions(
							teacher=user,
							school=school,
							session_class=item["session_class"],
							session_term=item["session_term"],
							session_subject=item["session_subject"],
							submitted_session_data=item["submitted_session_data"],
						)
					)

			if to_update:
				print(f'updating: {to_update}')
				SubmitedQuestions.objects.bulk_update(to_update, ["submitted_session_data", "updated_at"])

			if to_create:
				print(f'creating: {to_create}')
				SubmitedQuestions.objects.bulk_create(to_create)

			saved_questions.update(has_submitted=True, updated_at=timezone.now())

		return Response({
				"success": "Successfully"
				}, status=status.HTTP_200_OK)
	# return Response({"error": "all good"})
	# if not school:
	# 	return Response({"error": "you do not have the authorization for this action."})
	if request.method == 'GET':
		submitted_id = request.query_params.get("id")
		if not submitted_id:
			qp = request.query_params
			print(f'qp: {qp}')
			q_all = qp.get("all")
			raw_ids = qp.get("allIDs")
			print(f'q_all: {q_all}\nraw_ids: {raw_ids}')
			if q_all and not raw_ids:
				print('nothing to download')
				return Response({"error": "Nothing to download."}, status=status.HTTP_400_BAD_REQUEST)
			cleaned_ids = raw_ids.split(',')
			print(f'cleaned_ids: {cleaned_ids}')

			many_payloads = []
			shuffle_record_dict = {}
			for _id in cleaned_ids:
				# return Response({"error": "all good"})
				submitted_obj_m = SubmitedQuestions.objects.filter(
							id=_id,
							school=school,
				).first()
				print(f'submitted_obj_m: {submitted_obj_m}')
				if not submitted_obj_m:
					print('skipping...')
					continue
				parsed_data_m = parse_nested_formdata(submitted_obj_m.submitted_session_data, request.FILES)
				db_category["session_subject"] = parsed_data_m["subject"]
				db_category["session_term"] = parsed_data_m["term"]
				db_category["session_class"] = parsed_data_m["class"]
				result, shuffle_record = Randomize(parsed_data_m, multiple=True, db_category=db_category)
				many_payloads.append(result["dir_path"])
				if shuffle_record:
					handle_shuffle_record_arg["parsed_data"] = parsed_data_m
					handle_shuffle_record_arg["shuffle_record"] = shuffle_record
					handle_shuffle_record(handle_shuffle_record_arg)
				shuffle_record_dict.setdefault(_id, shuffle_record)

			print(f'cleaned_ids: {cleaned_ids}')
			print(f'many_payloads: {many_payloads}')
			# zip all dirs once
			file_url_m = zip_all(many_payloads)
			print("Generated file URL:", file_url_m)
			print('multiple usage (authenticated)')
			print(f'shuffle_record_dict:')
			pretty_print_json(shuffle_record_dict)
			return Response({"downloadLink": file_url_m}, status=status.HTTP_200_OK)

		if not submitted_id:
			return Response(
				{"error": "id query parameter is required"},
				status=status.HTTP_400_BAD_REQUEST
			)
		try:
			submitted_id = int(submitted_id)
		except ValueError:
			return Response(
				{"detail": "id must be an integer"},
				status=status.HTTP_400_BAD_REQUEST
			)
		submitted_obj = SubmitedQuestions.objects.filter(
			id=submitted_id,
			school=school,
		).first()
		print(f'submitted_obj: {submitted_obj}')
		print('submitted_session_data:')
		# pretty_print_json(submitted_obj.submitted_session_data)
		print_formdata_content(submitted_obj.submitted_session_data)
		# return Response({"success": "Success", "downloadLink": "file_url"})

		parsed_data = parse_nested_formdata(submitted_obj.submitted_session_data, request.FILES)
		# # print(f"Parsed form data: {json.dumps(parsed_data, indent=2)}")
		db_category["session_subject"] = parsed_data["subject"]
		db_category["session_term"] = parsed_data["term"]
		db_category["session_class"] = parsed_data["class"]
		file_url, shuffle_record = Randomize(parsed_data, db_category=db_category)

		print("Generated file URL:", file_url)
		print('single usage (authenticated)')

		# # save link for future downloads
		# ScrambleLinks.objects.create(
		# 	user=request.user,
		# 	link=file_url,
		# )
		if shuffle_record:
			handle_shuffle_record_arg["parsed_data"] = parsed_data
			handle_shuffle_record_arg["shuffle_record"] = shuffle_record
			handle_shuffle_record(handle_shuffle_record_arg)

		return Response({"success": "Success", "downloadLink": file_url})

	if request.method == 'POST':
		print(f'in post:')
		post_payload = request.data
		saved_Id = post_payload.get("savedID")
		print(f'saved_id: {saved_Id}')
		session_class = post_payload.get("class", None)
		if not session_class:
			print(f'class is required')
			return Response({"error": "class not found"}, status=status.HTTP_400_BAD_REQUEST)
		session_term = post_payload.get("term", None)
		if not session_term:
			print(f'term is required')
			return Response({"error": "term not found"}, status=status.HTTP_400_BAD_REQUEST)
		session_subject = post_payload.get("subject", None)
		if not session_subject:
			print(f'subject is required')
			return Response({"error": "subject not found"}, status=status.HTTP_400_BAD_REQUEST)
		pretty_print_json(post_payload)
		submitted_session = SubmitedQuestions.objects.filter(
			teacher=user,
			school=school,
			session_class=session_class,
			session_term=session_term,
			session_subject=session_subject
		).first()
		print(f'submitted_session: {submitted_session}')
		# if submitted_session:
		# 	serialized_submitted_session = SubmittedQuestionsReadSerializer(submitted_session).data
		# 	print('serialized_submitted_session:')
		# 	pretty_print_json(serialized_submitted_session)
		is_update = bool(submitted_session)

		# return Response({"error": "all good"})
		if submitted_session:
			print('updating existing session')
			post_serializer = SubmittedQuestionsWriteSerializer(
				submitted_session,
				data={"submitted_session_data": post_payload},
				partial=True,
				context={'request': request}
			)
			# post_serializer = SubmittedQuestionsWriteSerializer(
			# 	submitted_session,
			# 	context={'request': request}
			# )

			# post_serializer.replace_submitted_session(
			# 	submitted_session,
			# 	post_payload
			# )
		else:
			print('creating new session')
			post_serializer = SubmittedQuestionsWriteSerializer(
				data={"submitted_session_data": post_payload},
				context={'request': request}
			)

		if post_serializer.is_valid():
			print('serialized data is valid')
			post_serializer.save()
		else:
			print(f'post_serializer.errors: {post_serializer.errors}')
			return Response({"error": "Could not submit."}, status=status.HTTP_400_BAD_REQUEST)

		if saved_Id:
			print('checking by id')
			saved_question = ScrambleSession.objects.filter(id=saved_Id).first()
		else:
			print('checking by category')
			saved_question = ScrambleSession.objects.filter(
				teacher=user,
				school=school,
				session_class=session_class,
				session_term=session_term,
				session_subject=session_subject
			).first()
		print(f'saved_question: {saved_question}')
		if saved_question:
			print('updating ScrambleSession')
			saved_question.scramble_session_data = post_payload
			if saved_question.has_submitted == False:
				saved_question.has_submitted = True
			saved_question.save()
		else:
			print('creating ScrambleSession')
			saved_question = ScrambleSessionWriteSerializer(
				data={
					"scramble_session_data": post_payload,
					"session_class": session_class,
					"session_term": session_term,
					"session_subject": session_subject,
					"has_submitted": True,
				},
				context={'request': request}
			)
			if saved_question.is_valid():
				print('saved_question is valid')
				saved_question = saved_question.save()
				print(saved_question)
			else:
				print(f'saved_question.errors: {saved_question.errors}')
			# print('serialized data saved:')
			# pretty_print_json(post_serializer)
		print(f'has_submitted: {saved_question.has_submitted}')
		return Response({
					"success": "Submit updated" if is_update else "Submit success",
					"has_submitted": saved_question.has_submitted,
				}, status=status.HTTP_200_OK if is_update else status.HTTP_201_CREATED)
