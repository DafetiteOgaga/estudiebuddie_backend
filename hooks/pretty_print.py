import json
try:
    from .dont_push import mode
    print(f"Development mode 🔨")
except Exception as e:
    print(f"Production mode ☁")
    mode = 'prod'

def pretty_print_json(data):
    """
    Takes a JSON string or Python dict/list and prints it in.
    """
    # print(f"Pretty Print mode: {mode}")
    if mode == 'dev':
        if not isinstance(data, object):
            data = json.loads(data)

        print(json.dumps(data, indent=4, sort_keys=True, default=str))
    else:
        print(data)
    print("".rjust(40, '*'))
