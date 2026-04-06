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
import json, logging
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponse
from urllib.parse import quote
logger = logging.getLogger(__name__)

def handle_shuffle_record(data):
	logger.info('checking for existing scramble')

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
	logger.info(f'saved_question: {saved_question}')
	if not saved_question:
		if post_payload and request:
			logger.info('creating ScrambleSession')
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
				logger.info('saved_question is valid')
				saved_question = saved_question.save()
				logger.info(saved_question)
				logger.info('created new session')
	else:
		if post_payload and request:
			saved_question.scramble_session_data = post_payload
			logger.info('updated session')
	if shuffle_record:
		logger.info('ready to take shuffle_record!')
		pretty_print_json(shuffle_record)
		saved_question.shuffle_record = shuffle_record
		logger.info('shuffle record saved!')
	saved_question.save()

def pushDownloadFromBuffer(zip_buffer, zip_name):
	zip_buffer.seek(0)
	response = HttpResponse(
		zip_buffer.read(),
		content_type="application/zip"
	)
	response["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(zip_name)}"
	response["Content-Length"] = zip_buffer.getbuffer().nbytes
	logger.info(f"response:")
	pretty_print_json(response.items())
	return response

# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_exam_bundle(request):
	cleanup_old_zips()
	user = request.user
	logger.info(f'user: {user}')
	school = getattr(user, "school", None)
	# logger.info(f'school: {school}')
	if request.method == 'POST':
		saved_question = None

		post_payload = request.data
		parsed_data = parse_nested_formdata(post_payload, request.FILES)
		logger.info(f'parsed_data:')
		pretty_print_json(parsed_data)
		# return Response({"success": "Success", "downloadLink": "file_url"}, status=status.HTTP_400_BAD_REQUEST)
		db_category = {
			"teacher_id": user.id,
			"school_id": school.id,
			"session_subject": parsed_data["subject"],
			"session_term": parsed_data["term"],
			"session_class": parsed_data["class"],
		}
		# file_url, shuffle_record = Randomize(parsed_data, db_category=db_category)
		zip_buffer, zip_name, shuffle_record = Randomize(parsed_data, db_category=db_category)
		logger.info(f"Generated file URL: {zip_name}")
		logger.info('free usage')

		logger.info(f'user: {user}')
		logger.info(f'school: {school}')
		logger.info(f'shuffle_record: {shuffle_record}')
		if school:
			handle_shuffle_record({
				"user": user,
				"school": school,
				"parsed_data": parsed_data,
				"post_payload": post_payload,
				"request": request,
				"shuffle_record": shuffle_record
			})

		# save link to disk or cloud for future downloads
		# ScrambleLinks.objects.create(
		# 	user=request.user,
		# 	link=file_url,
		# )
		# return Response({"success": "Success", "downloadLink": file_url})
		return pushDownloadFromBuffer(zip_buffer, zip_name)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def generate_exam_bundle_for_school(request):
	cleanup_old_zips()
	qp = request.query_params
	logger.info(f'qp: {qp}')
	d_all = qp.get("submit_all")
	raw_ids = qp.get("allIDs")
	logger.info(f'd_all: {d_all}\nraw_ids: {raw_ids}')
	if d_all and not raw_ids:
		logger.info('nothing to delete')
		return Response({"error": "Nothing to delete."}, status=status.HTTP_400_BAD_REQUEST)
	cleaned_ids = None

	user = request.user
	logger.info(f'user: {user}')
	school = getattr(user, "school", None)
	# logger.info(f'school: {school.name}')
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

	logger.info(f'school: {school.name}')

	if d_all:
		cleaned_ids = raw_ids.split(',')
		cleaned_ids = [int(i) for i in cleaned_ids]
		logger.info(f'cleaned_ids: {cleaned_ids}')
		with transaction.atomic():
			saved_questions = ScrambleSession.objects.filter(
				teacher=user,
				school=school,
				id__in=cleaned_ids
			)

			logger.info(f'saved_questions: {saved_questions}')

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

			# logger.info(f'saved_list: {saved_list}')

			query = Q()
			for item in saved_list:
				# logger.info('item in saved list:')
				# pretty_print_json(item)
				query |= Q(
					session_class=item["session_class"],
					session_term=item["session_term"],
					session_subject=item["session_subject"],
					teacher=user,
					school=school
				)

			existing = SubmitedQuestions.objects.filter(query)

			logger.info(f'existing in submitted: {existing}')

			# map existing by class/term/subject for quick lookup
			existing_map = {
				(obj.session_class, obj.session_term, obj.session_subject): obj
				for obj in existing
			}

			logger.info(f'existing_map: {existing_map}')

			to_update = []
			to_create = []

			for item in saved_list:
				logger.info(f'item:')
				pretty_print_json(item)
				key = (item["session_class"], item["session_term"], item["session_subject"])
				if key in existing_map:
					logger.info(f'append to update list')
					logger.info(f'key: {key}')
					obj = existing_map[key]
					obj.submitted_session_data = item["submitted_session_data"]
					obj.submitted_session_data = item["submitted_session_data"]
					obj.updated_at = timezone.now()
					to_update.append(obj)
				else:
					logger.info(f'append to create list')
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
				logger.info(f'updating: {to_update}')
				SubmitedQuestions.objects.bulk_update(to_update, ["submitted_session_data", "updated_at"])

			if to_create:
				logger.info(f'creating: {to_create}')
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
			logger.info(f'qp: {qp}')
			q_all = qp.get("all")
			raw_ids = qp.get("allIDs")
			logger.info(f'q_all: {q_all}\nraw_ids: {raw_ids}')
			if q_all and not raw_ids:
				logger.info('nothing to download')
				return Response({"error": "Nothing to download."}, status=status.HTTP_400_BAD_REQUEST)
			cleaned_ids = raw_ids.split(',')
			logger.info(f'cleaned_ids: {cleaned_ids}')

			many_payloads = []
			many_folder_names = []
			shuffle_record_dict = {}
			for _id in cleaned_ids:
				# return Response({"error": "all good"})
				submitted_obj_m = SubmitedQuestions.objects.filter(
							id=_id,
							school=school,
				).first()
				logger.info(f'submitted_obj_m: {submitted_obj_m}')
				if not submitted_obj_m:
					logger.info('skipping...')
					continue
				parsed_data_m = parse_nested_formdata(submitted_obj_m.submitted_session_data, request.FILES)
				db_category["session_subject"] = parsed_data_m["subject"]
				db_category["session_term"] = parsed_data_m["term"]
				db_category["session_class"] = parsed_data_m["class"]
				result, shuffle_record = Randomize(parsed_data_m, multiple=True, db_category=db_category)
				many_payloads.append(result["doc_files"])
				many_folder_names.append(result["folder_name"])
				if shuffle_record:
					handle_shuffle_record_arg["parsed_data"] = parsed_data_m
					handle_shuffle_record_arg["shuffle_record"] = shuffle_record
					handle_shuffle_record(handle_shuffle_record_arg)
				shuffle_record_dict.setdefault(_id, shuffle_record)

			logger.info(f'cleaned_ids: {cleaned_ids}')
			logger.info(f'many_payloads:')
			pretty_print_json(many_payloads)
			logger.info(f'many_folder_names:')
			pretty_print_json(many_folder_names)
			# zip all dirs once
			zip_buffer_m, zip_name_m = zip_all(many_payloads, folder_names=many_folder_names)
			logger.info(f"Generated file URL: {zip_name_m}")
			logger.info('multiple usage (authenticated)')
			logger.info(f'shuffle_record_dict:')
			pretty_print_json(shuffle_record_dict)
			# return Response({"downloadLink": file_url_m}, status=status.HTTP_200_OK)
			return pushDownloadFromBuffer(zip_buffer_m, zip_name_m)

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
		logger.info(f'submitted_obj: {submitted_obj}')
		logger.info('submitted_session_data:')
		# pretty_print_json(submitted_obj.submitted_session_data)
		print_formdata_content(submitted_obj.submitted_session_data)
		# return Response({"success": "Success", "downloadLink": "file_url"})

		parsed_data = parse_nested_formdata(submitted_obj.submitted_session_data, request.FILES)
		# # logger.info(f"Parsed form data: {json.dumps(parsed_data, indent=2)}")
		db_category["session_subject"] = parsed_data["subject"]
		db_category["session_term"] = parsed_data["term"]
		db_category["session_class"] = parsed_data["class"]
		# file_url, shuffle_record = Randomize(parsed_data, db_category=db_category)
		zip_buffer, zip_name, shuffle_record = Randomize(parsed_data, db_category=db_category)

		logger.info(f"Generated file URL: {zip_name}")
		logger.info('single usage (authenticated)')

		# # save link for future downloads
		# ScrambleLinks.objects.create(
		# 	user=request.user,
		# 	link=file_url,
		# )
		if shuffle_record:
			handle_shuffle_record_arg["parsed_data"] = parsed_data
			handle_shuffle_record_arg["shuffle_record"] = shuffle_record
			handle_shuffle_record(handle_shuffle_record_arg)

		# return Response({"success": "Success", "downloadLink": file_url})
		return pushDownloadFromBuffer(zip_buffer, zip_name)

	if request.method == 'POST':
		logger.info(f'in post:')
		post_payload = request.data
		saved_Id = post_payload.get("savedID")
		logger.info(f'saved_id: {saved_Id}')
		session_class = post_payload.get("class", None)
		if not session_class:
			logger.info(f'class is required')
			return Response({"error": "class not found"}, status=status.HTTP_400_BAD_REQUEST)
		session_term = post_payload.get("term", None)
		if not session_term:
			logger.info(f'term is required')
			return Response({"error": "term not found"}, status=status.HTTP_400_BAD_REQUEST)
		session_subject = post_payload.get("subject", None)
		if not session_subject:
			logger.info(f'subject is required')
			return Response({"error": "subject not found"}, status=status.HTTP_400_BAD_REQUEST)
		pretty_print_json(post_payload)
		submitted_session = SubmitedQuestions.objects.filter(
			teacher=user,
			school=school,
			session_class=session_class,
			session_term=session_term,
			session_subject=session_subject
		).first()
		logger.info(f'submitted_session: {submitted_session}')
		# if submitted_session:
		# 	serialized_submitted_session = SubmittedQuestionsReadSerializer(submitted_session).data
		# 	logger.info('serialized_submitted_session:')
		# 	pretty_print_json(serialized_submitted_session)
		is_update = bool(submitted_session)

		# return Response({"error": "all good"})
		if submitted_session:
			logger.info('updating existing session')
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
			logger.info('creating new session')
			post_serializer = SubmittedQuestionsWriteSerializer(
				data={"submitted_session_data": post_payload},
				context={'request': request}
			)

		if post_serializer.is_valid():
			logger.info('serialized data is valid')
			post_serializer.save()
		else:
			logger.info(f'post_serializer.errors: {post_serializer.errors}')
			return Response({"error": "Could not submit."}, status=status.HTTP_400_BAD_REQUEST)

		if saved_Id:
			logger.info('checking by id')
			saved_question = ScrambleSession.objects.filter(id=saved_Id).first()
		else:
			logger.info('checking by category')
			saved_question = ScrambleSession.objects.filter(
				teacher=user,
				school=school,
				session_class=session_class,
				session_term=session_term,
				session_subject=session_subject
			).first()
		logger.info(f'saved_question: {saved_question}')
		if saved_question:
			logger.info('updating ScrambleSession')
			saved_question.scramble_session_data = post_payload
			if saved_question.has_submitted == False:
				saved_question.has_submitted = True
			saved_question.save()
		else:
			logger.info('creating ScrambleSession')
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
				logger.info('saved_question is valid')
				saved_question = saved_question.save()
				logger.info(saved_question)
			else:
				logger.info(f'saved_question.errors: {saved_question.errors}')
			# logger.info('serialized data saved:')
			# pretty_print_json(post_serializer)
		logger.info(f'has_submitted: {saved_question.has_submitted}')
		return Response({
					"success": "Submit updated" if is_update else "Submit success",
					"has_submitted": saved_question.has_submitted,
				}, status=status.HTTP_200_OK if is_update else status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_links(request):
	cleanup_old_zips()
	if request.method == 'GET':
		user = request.user
		logger.info(f'user: {user}')

		links = ScrambleLinks.objects.filter(user=user).order_by('-created_at')[:5]
		# logger.info(f'links: {links}')
		serialized_links = ScrambleLinksSerializer(links, many=True).data
		logger.info(f'serialized_links:')
		pretty_print_json(serialized_links)
		return Response(serialized_links, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_submitted(request):
	cleanup_old_zips()
	user = request.user
	school = user.school
	qp = request.query_params
	logger.info(f'qp: {qp}')
	teacher_id = qp.get("teacherID", None)
	if teacher_id:
		try:
			teacher_id = int(teacher_id)
		except:
			logger.info("Oopsy! Teacher/Admin not specified.")
			return Response({"error": "Oopsy! Teacher/Admin not specified."})
	logger.info(f'teacher_id: {teacher_id}')
	logger.info(f'user: {user}\nschool: {school}')
	if user.role not in ["admin", "head"]:
		logger.info('you have no permision to view this')
		return Response({"error": "you do not have permission for this action."})
	submitted_objs = SubmitedQuestions.objects.filter(
		school=school,
		teacher_id=teacher_id
	).order_by('-updated_at')
	serialized_objs = SubmittedQuestionsReadSerializer(
		submitted_objs, many=True
	).data
	logger.info('checked response:')
	pretty_print_json(serialized_objs)
	return Response(serialized_objs, status=status.HTTP_200_OK)
