# your_app/utils/randomize.py
import os
import shutil
import zipfile
import random
import string
import uuid
import re
from datetime import datetime
from threading import Timer
from docx import Document
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.oxml.shared import OxmlElement, qn
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_SECTION
from docx.shared import Inches
# from docx2pdf import convert
from django.conf import settings
from .timestamp import get_timestamp
from .check_time import delete_time
from hooks.pretty_print import pretty_print_json

# # Ensure /public folder exists
# PUBLIC_DIR = os.path.join(settings.BASE_DIR, 'public')
# os.makedirs(PUBLIC_DIR, exist_ok=True)

def shuffle_array(arr):
	# print(f"shuffling array:")
	# pretty_print_json(arr)
	shuffled = arr[:]
	random.shuffle(shuffled)
	return shuffled

def generate_alphabets(n):
	return [chr(65 + i) for i in range(n)]  # A, B, C, D...

def schedule_deletion(zip_path, dir_path):
	def delete_files():
		timestamp = get_timestamp()
		try:
			if os.path.exists(zip_path):
				os.remove(zip_path)
				print(f"ZIP file {zip_path} deleted after 24 hours {timestamp}")
			if os.path.exists(dir_path):
				shutil.rmtree(dir_path)
				print(f"Directory {dir_path} deleted after 24 hours {timestamp}")

			# delete the links from models here

		except Exception as e:
			print(f"Error in scheduled cleanup {timestamp}: {e}")

	Timer(delete_time, delete_files).start()

def save_docx(paragraphs, file_path, add_footer=True, image_map=None, logo=None):
	# #####################
	# print("data to use for file:")
	# pretty_print_json(paragraphs)
	# #####################
	if image_map is None:
		image_map = {}
	doc = Document()
	# ============================
	# PAGE SIZE & MARGINS (PUT IT HERE)
	# ============================
	from docx.shared import Inches

	for section in doc.sections:
		# section.page_width = Inches(11.69)   # A4 landscape
		# section.page_height = Inches(8.27)

		section.left_margin = Inches(0.7)
		section.right_margin = Inches(0.7)
		section.top_margin = Inches(0)
		section.bottom_margin = Inches(0.75)

	# ============================
	# SECTION 1 — PAGE 1 HEADER (applicable to only the first page)
	# ============================
	section1 = doc.sections[0]
	section1.different_first_page_header_footer = True

	header = section1.first_page_header

	# ============================
	# HEADER PARAGRAPH WITH RHS LOGO
	# ============================
	p = header.paragraphs[0]
	p.clear()

	# right-aligned tab stop at page margin
	pPr = p._p.get_or_add_pPr()
	tabs = OxmlElement('w:tabs')
	tab = OxmlElement('w:tab')
	tab.set(qn('w:val'), 'right')
	tab.set(qn('w:pos'), str(int(Inches(7.2).emu)))  # usable page width
	tabs.append(tab)
	pPr.append(tabs)

	# column widths
	# left_cell.width = Inches(5.5)
	# right_cell.width = Inches(1.5)

	# ============================
	# LOGO (HEADER - FIRST PAGE ONLY)
	# ============================
	if logo:
		logo_para = header.add_paragraph()
		logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

		run = logo_para.add_run()
		run.add_picture(
			logo,
			width=Inches(0.7)  # adjust if needed
		)

		logo_para.paragraph_format.space_before = Pt(0)
		logo_para.paragraph_format.space_after = Pt(1)
		# run = p.add_run("\t")
		# run.add_picture(
		# 	logo,
		# 	width=Inches(1.2)  # logo size ONLY
		# )
	# header_para = header.paragraphs[0]

	header_lines = []
	body_start_index = 0

	for i, line in enumerate(paragraphs):
		if line == "":
			body_start_index = i + 1
			break
		header_lines.append(line)

	# Clear default paragraph
	# header.paragraphs[0].clear()
	# header.paragraphs[0].clear()

	school, subject, clazz, term, duration, instruction, variant, qtype = header_lines

	# --- School name (centered & bold)
	p = header.add_paragraph(school)
	p.alignment = WD_ALIGN_PARAGRAPH.CENTER
	p.runs[0].bold = True
	p.runs[0].font.size = Pt(14)
	p.paragraph_format.space_before = Pt(0)
	p.paragraph_format.space_after = Pt(2)
	p.paragraph_format.line_spacing = 0.5
	p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

	# --- Subject (left)
	p = header.add_paragraph()
	p.add_run(subject).bold = True
	p.alignment = WD_ALIGN_PARAGRAPH.LEFT
	p.paragraph_format.space_before = Pt(0)
	p.paragraph_format.space_after = Pt(2)
	p.paragraph_format.line_spacing = 0.5
	p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

	# --- Term (left) | Class (right)
	p = header.add_paragraph()
	p.add_run(term)
	p.add_run("\t" * 8)
	p.add_run(clazz)
	p.alignment = WD_ALIGN_PARAGRAPH.LEFT
	p.paragraph_format.space_before = Pt(0)
	p.paragraph_format.space_after = Pt(2)
	p.paragraph_format.line_spacing = 0.5
	p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

	# --- Variant ID (left)
	p = header.add_paragraph()
	p.add_run(variant)
	p.paragraph_format.space_before = Pt(0)
	p.paragraph_format.space_after = Pt(2)
	p.paragraph_format.line_spacing = 0.5
	p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

	# --- Duration (left) | Type (center) | Instruction (right)
	p = header.add_paragraph()
	p.add_run(duration)
	p.add_run("\t" * 2)
	p.add_run(qtype)
	p.alignment = WD_ALIGN_PARAGRAPH.LEFT
	p.paragraph_format.space_before = Pt(0)
	p.paragraph_format.space_after = Pt(2)
	p.paragraph_format.line_spacing = 0.5
	p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
	p.add_run("\t" * 1)
	p.add_run(instruction).bold = True
	p.alignment = WD_ALIGN_PARAGRAPH.LEFT
	p.paragraph_format.space_before = Pt(0)
	p.paragraph_format.space_after = Pt(2)
	p.paragraph_format.line_spacing = 0.5
	p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

	# ============================
	# SECTION 2 — QUESTIONS (2 COLUMNS)
	# ============================
	section2 = doc.add_section(WD_SECTION.CONTINUOUS)
	sectPr = section2._sectPr

	cols = OxmlElement('w:cols')
	cols.set(qn('w:num'), '2')
	cols.set(qn('w:space'), '720')
	sectPr.append(cols)

	# --- Add question body content (flows across columns & pages)
	for para in paragraphs[body_start_index:]:
		# Detect image marker
		if para.startswith("__IMAGE__:"):
			q_index = int(para.split(":")[1])
			image = image_map.get(q_index)

			if image:
				img_paragraph = doc.add_paragraph()
				run = img_paragraph.add_run()

				# Add image (COLUMN-FRIENDLY SIZE)
				run.add_picture(
					image,
					width=Inches(2.5)  # fits 2-column layout
				)

				img_paragraph.paragraph_format.space_after = Pt(6)
				img_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT

			continue  # skip text rendering for marker

		# normal text
		p = doc.add_paragraph(para)
		p.style.font.size = Pt(12)

		# Detect options: A. B. C. D.
		if re.match(r'^[A-D]\.\s', para):
			p.paragraph_format.space_before = Pt(0)
			p.paragraph_format.space_after = Pt(2)
			p.paragraph_format.line_spacing = 0.5
			p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

	# ============================
	# SECTION 3 — LAST PAGE FOOTER (OPTIONAL)
	# ============================
	if add_footer:
		section3 = doc.add_section()
		section3.start_type = 2  # new page

		footer = section3.footer
		footer_para = footer.paragraphs[0]
		footer_para.text = "End of Examination"
		footer_para.style.font.size = Pt(10)
		footer_para.alignment = 1  # center

	doc.save(file_path)


def Randomize(data):
	try:
		# random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
		# variant_id = f"{uuid.uuid4().hex[:8]}_{random_str}"
		# Generate 4 random lowercase alphanumeric characters
		random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
		print("Generated random string for variant ID:")
		pretty_print_json(random_str)

		# Get current time
		now = datetime.now()
		year = now.year
		month = f"{now.month:02d}"
		date = f"{now.day:02d}"
		hours = f"{now.hour:02d}"
		minutes = f"{now.minute:02d}"
		seconds = f"{now.second:02d}"

		# get subject
		subject = data['subject'].lower()

		# Combine to form variantId
		variant_id = f"{subject}_{year}{month}{date}_{hours}{minutes}{seconds}_{random_str}"
		print("Generated variant ID:")
		pretty_print_json(variant_id)

		# Create directories and files names
		zip_filename = f"estudiebuddie_{variant_id}.zip"
		print("ZIP filename will be:")
		pretty_print_json(zip_filename)
		public_dir = os.path.join(settings.BASE_DIR, 'public')
		dir_path = os.path.join(public_dir, variant_id)
		os.makedirs(dir_path, exist_ok=True)
		os.chmod(public_dir, 0o777)
		os.chmod(dir_path, 0o777)

		# Generate question types (A-Z)
		types = generate_alphabets(int(data['noOfTypes']))
		print(f"Generated question types:")
		pretty_print_json(types)

		# Generate question and answer files for each type
		for i, type_code in enumerate(types):
			print(f"Generating files for question type: {type_code}")
			# print(f"data: {data}")
			# print(f"postQuestions: {data['postQuestions']}")
			# Shuffle questions
			questions = shuffle_array(data['postQuestions'])
			answer_key = [
				f"variant: {variant_id}",
				f"Type: {type_code}",
				""
			]
			print(f"Initialized answer key for type {type_code}")
			pretty_print_json(answer_key)
			print(f"Shuffled questions for type {type_code}")
			print(f"Shuffled Questions:")
			pretty_print_json(questions)

			# Prepare header here
			duration = data['duration']
			try:
				print(f"Processing duration: {duration}")
				num = float(duration)
				print(f"Converted duration to float: {num}")
				if num > 1:
					print(f"Duration is plural hours: {num}")
					# plural: keep as hours
					duration_str = f"{num:g} hours"   # :g removes trailing .0 for whole numbers
				elif num == 1:
					print(f"Duration is singular one hour")
					# singular
					duration_str = f"{num:g} hour"
				elif 0 < num < 1:
					print(f"Duration is fractional hours: {num}")
					# convert fractional hours to minutes
					minutes = round(num * 60)
					print(f"Converted fractional hours to minutes: {minutes}")
					duration_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
				else:
					print(f"Duration is zero or negative: {num}")
					# for 0 or negative values, just leave as-is or customize
					duration_str = str(duration)
			except (ValueError, TypeError, OverflowError):
				print(f"Duration is non-numeric: {duration}")
				duration_str = duration
			header_lines = [
				data['school'].upper(),
				f"Subject: {data['subject'].title()}",
				f"Class: {data['class'].upper()}",
				f"{data['term'].title()} Term",
				f"Duration: {duration_str}",
				f"Instruction: {data['instruction'].title()}",
				f"variant: {variant_id}",
				f"Type: {type_code}",
				""
			]
			print(f"Prepared header for type {type_code}")
			print(f"Header Lines:")
			pretty_print_json(header_lines)

			# Prepare questions with shuffled options
			question_lines = header_lines[:]
			print(f"Starting to process questions for type {type_code}")
			print(f"Initial Question Lines:")
			pretty_print_json(question_lines)

			# Process each question
			for idx, q in enumerate(questions):
				print(f"Processing question {idx + 1} for type {type_code}")
				print(f"Question Data:")
				pretty_print_json(q)
				# Shuffle options
				opts = shuffle_array([
					{"text": q["correct_answer"], "isCorrect": True},
					{"text": q["wrong_answer1"], "isCorrect": False},
					{"text": q["wrong_answer2"], "isCorrect": False},
					{"text": q["wrong_answer3"], "isCorrect": False},
				])
				print(f"Shuffled options for question {idx + 1}:")
				pretty_print_json(opts)
				# Label options A, B, C, D
				for j, opt in enumerate(opts):
					print(f"Labeling option {j + 1} for question {idx + 1}")
					print(f"Option Data Before Labeling:")
					pretty_print_json(opt)
					opt['label'] = chr(65 + j)
					print(f"Option Data After Labeling:")
					pretty_print_json(opt)

				# Find correct option for answer key
				correct = next(o for o in opts if o["isCorrect"])
				print(f"Correct option for question {idx + 1}:")
				pretty_print_json(correct)
				# Append to answer key
				answer_key.append(f"{idx + 1}. {correct['label']}")
				print(f"Updated answer key:")
				pretty_print_json(answer_key)

				# append image (if it exists)
				if q.get("image"):
					question_lines.append(f"__IMAGE__:{idx}")
				# Append question and options to question lines
				question_lines.append(f"{idx + 1}. {q['question']}")
				print(f"Added question {idx + 1} to question lines.")
				print(f"Current Question Lines:")
				pretty_print_json(question_lines)
				# Loop and append options
				for opt in opts:
					print(f"Adding option for question {idx + 1}")
					pretty_print_json(opt)
					# append option label and text
					question_lines.append(f"{opt['label']}. {opt['text']}")
					print(f"Added option`s label to question lines.")
					pretty_print_json(opt["label"])
				# Add a blank line after each question
				question_lines.append("")
				print(f"Finished processing question {idx + 1}. Current Question Lines:")
				pretty_print_json(question_lines)

			# Save Question and Answer Files
			quest_dir = os.path.join(dir_path, 'questions')
			print(f"Creating directories for type {type_code}")
			ans_dir = os.path.join(dir_path, 'answers')
			print(f"Creating answer directories for type {type_code}")
			os.makedirs(quest_dir, exist_ok=True)
			os.makedirs(ans_dir, exist_ok=True)
			question_path_for_docx = os.path.join(quest_dir, f"Question_type_{type_code}.docx")
			# question_path_for_pdf = os.path.join(quest_dir, f"Exam_type_{type_code}.pdf")

			# build image map
			image_map = {}
			for i, q in enumerate(questions):
				if q.get("image"):
					image_map[i] = q["image"]

			save_docx(
				question_lines,
				question_path_for_docx,
				add_footer=False,
				image_map=image_map,
				logo=data.get("logo", None),
			)

			# # pdf creation
			# try:
			# 	convert(question_path_for_docx, question_path_for_pdf)
			# 	print(f"PDF generated successfully: {question_path_for_pdf}")
			# except Exception as e:
			# 	print(f"PDF generation failed for {question_path_for_docx}: {e}")

			# with open(os.path.join(quest_dir, f"Exam_type_{type_code}.txt"), "w") as f:
			# 	print(f"Saving question text file for type {type_code}")
			# 	f.write("\n".join(question_lines))

			with open(os.path.join(ans_dir, f"Answers_type_{type_code}.txt"), "w") as f:
				print(f"Saving answer key text file for type {type_code}")
				f.write("\n".join(answer_key))

		# Zip the directory
		zip_path = os.path.join(public_dir, zip_filename)
		print(f"Creating ZIP archive at: {zip_path}")
		with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as archive:
			print(f"Adding files to ZIP archive: {zip_path}")
			for foldername, _, filenames in os.walk(dir_path):
				print(f"Walking through folder: {foldername}")
				for filename in filenames:
					print(f"Adding file to archive: {filename}")
					file_path = os.path.join(foldername, filename)
					arcname = os.path.relpath(file_path, os.path.join(dir_path, '..'))
					archive.write(file_path, arcname)

		# schedule_deletion(zip_path, dir_path)

		return f"/public/{zip_filename}"

	except Exception as e:
		print(f"Error generating exam bundle: {get_timestamp()} =>", e)
		raise Exception("Failed to generate exam bundle")
