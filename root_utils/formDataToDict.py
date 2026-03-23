import re, json, string, secrets, os, time
from pathlib import Path
from django.conf import settings
from collections import defaultdict
from shufflequestions.models import ScrambleLinks

def parse_nested_formdata(flat_data, files):
    """
    Convert flat keys like postQuestions[0][question]
    and preserve uploaded files.
    """

    # handles case of no request files (images)
    if not files:
        files = {}

    result = {}
    pattern = re.compile(r'^([^\[]+)((?:\[\w*\])*)$')

    # handles normal fields
    for flat_key, value in flat_data.items():
        match = pattern.match(flat_key)
        if not match:
            result[flat_key] = value
            continue

        key, path = match.groups()
        path = re.findall(r'\[(\w*)\]', path)

        cursor = result
        for i, p in enumerate([key] + path):
            is_last = (i == len([key] + path) - 1)
            # if p.isdigit():
            #     p = int(p)
            #     if not isinstance(cursor, list):
            #         cursor = []  # create a new list if not exists
            #         result[key] = cursor
            if p.isdigit():
                p = int(p)
                if not isinstance(cursor.get(p) if isinstance(cursor, dict) else None, list):
                    if isinstance(cursor, dict):
                        cursor[p] = []
                cursor = cursor[p]
                # if key not in result or not isinstance(result[key], list):
                #     result[key] = []
                # cursor = result[key]
                while len(cursor) <= p:
                    cursor.append({})
                if is_last:
                    cursor[p] = value
                else:
                    if not isinstance(cursor[p], dict):
                        cursor[p] = {}
                    cursor = cursor[p]
            else:
                if is_last:
                    cursor.setdefault(p, value)
                else:
                    cursor = cursor.setdefault(p, {})

    # inject files
    for file_key, file_obj in files.items():
        # Example: postQuestions[1][image]
        match = pattern.match(file_key)
        if not match:
            continue

        key, path = match.groups()
        path = re.findall(r'\[(\w*)\]', path)

        cursor = result
        for i, p in enumerate([key] + path):
            is_last = (i == len([key] + path) - 1)

            # if p.isdigit():
            #     p = int(p)
            #     cursor.setdefault(key, [])
            #     while len(cursor[key]) <= p:
            #         cursor[key].append({})
            #     if is_last:
            #         cursor[key][p]['image'] = file_obj
            #     else:
            #         cursor = cursor[key][p]
            if p.isdigit():
                p = int(p)

                if not isinstance(cursor.get(p) if isinstance(cursor, dict) else None, list):
                    if isinstance(cursor, dict):
                        cursor[p] = []
                cursor = cursor[p]
                # if key not in result or not isinstance(result[key], list):
                #     result[key] = []

                # cursor = result[key]

                while len(cursor) <= p:
                    cursor.append({})

                if is_last:
                    cursor[p]['image'] = file_obj
                else:
                    cursor = cursor[p]
            else:
                if is_last:
                    cursor[p] = file_obj
                else:
                    cursor = cursor.setdefault(p, {})

    def clean_empty(obj):
        if isinstance(obj, dict):
            return {k: clean_empty(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_empty(item) for item in obj if item]  # removes empty {}
        return obj

    return clean_empty(result)
    # return result

def serialize(value):
    if hasattr(value, 'read') and hasattr(value, 'name'):
        return f"<file: {value.name}>"
    elif isinstance(value, list):
        return [serialize(v) for v in value]
    elif isinstance(value, dict):
        return {k: serialize(v) for k, v in value.items()}
    return value

def print_formdata_content(formdata, files=None):
    """
    Use parse_nested_formdata() to convert flat FormData,
    serialize it, and print as valid JSON.
    Files are shown by filename to avoid JSON errors.
    """
    if not formdata:
        print("No form data provided.")
        return

    # Step 1: Reconstruct nested dict from flat keys
    nested_data = parse_nested_formdata(formdata, files)

    # Step 2: Safely serialize any file objects
    safe_data = serialize(nested_data)

    # Step 3: Print as pretty JSON
    print("Form Data Content:")
    print(json.dumps(safe_data, indent=2))

def generate_esb_code(user_id, code_type='school'):
    """
    Generates a unique school/admin/teacher codes like:
    ESB-8F3K2Q/ESBA-8F3K2Q/ESBT-8F3K2Q
    """
    from school.models import School  # local import to avoid circular imports

    PREFIX = "ESB"
    LENGTH = 6  # adjustable (6 = ~2.1B combinations)
    if code_type == "admin" or code_type == "teacher":
        if code_type == "admin":
            PREFIX = "ESBA"
        elif code_type == "teacher":
            PREFIX = "ESBT"
        # print(f'LENGTH: {LENGTH}')
        # print(f'len(user_id): {len(str(user_id))}')
        # print(f'user_id: {user_id}')
        # LENGTH = LENGTH - (len(str(user_id)) + 1)
        # print(f'LENGTH: {LENGTH}')

    alphabet = string.ascii_uppercase + string.digits

    while True:
        random_part = ''.join(secrets.choice(alphabet) for _ in range(LENGTH))
        code = f"{PREFIX}-{random_part}"
        if code_type == "admin" or code_type == "teacher":
            code = f"{PREFIX}-{random_part}l{user_id}"
        print(f'generated code: {code}')

        if not School.objects.filter(code=code).exists():
            return code

# def cleanup_old_zips():
#     public_dir = os.path.join(settings.BASE_DIR, "public")
#     now = time.time()

#     saved_links = ScrambleLinks.objects.all()

#     for file in os.listdir(public_dir):
#         if file.endswith(".zip"):
#             path = os.path.join(public_dir, file)
#             print(f'found: {file}')
#             if now - os.path.getmtime(path) > EXPIRY_SECONDS:
#                 try:
#                     # delete expired archive
#                     print(f'deleting: {file}')
#                     os.remove(path)

#                     # deletes corresponding saved record
#                     link_path = f"/public/{file}"
#                     deleted_saved_obj, _ = saved_links.filter(link=link_path).delete()
#                     print(f'deleted: {file} link record')
#                 except FileNotFoundError:
#                     print(f'no zip file to delete')
#                     pass

def cleanup_old_zips():
    EXPIRY_SECONDS = 60 * 30
    print(f'scanning for expired zip and links')
    public_dir = os.path.join(settings.BASE_DIR, "public")
    now = time.time()

    saved_links = ScrambleLinks.objects.all()
    # print(f'saved_links:')
    # for i in saved_links:
    #     print(i)

    # ---- collect zip files on disk in a set (set comprehension) ----
    if not os.path.isdir(public_dir):
        zip_files_on_disk = set()
    else:
        zip_files_on_disk = {
            file for file in os.listdir(public_dir) if file.endswith(".zip")
        }
    # print(f'zip_files_on_disk:')
    # for i in zip_files_on_disk:
    #     print(i)

    # ---- delete expired zip files + DB records ----
    for file in zip_files_on_disk.copy():
        path = os.path.join(public_dir, file)
        print(f'found: {file}')

        if now - os.path.getmtime(path) > EXPIRY_SECONDS:
            try:
                print(f"deleting expired zip: {file}")
                os.remove(path)

                link_path = f"/public/{file}"
                saved_links.filter(link=link_path).delete()
                print(f'deleted: {file} link record')

                zip_files_on_disk.remove(file)
            except FileNotFoundError:
                print(f'no zip file to delete')
                pass

    # ---- delete orphaned DB records (no file exists) ----
    for link in saved_links:
        print(f'link::::: {link}')
        filename = os.path.basename(link.link)
        print(f'filename::::: {filename}')
        print(''.rjust(20, '-'))

        if filename not in zip_files_on_disk:
            print(f"orphaned DB link removed: {link.link}")
            link.delete()
