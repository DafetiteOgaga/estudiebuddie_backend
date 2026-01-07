import json, logging
try:
    from .dont_push import mode
    print(f"Development mode 🔨")
except Exception as e:
    print(f"Production mode ☁")
    mode = 'prod'

logger = logging.getLogger(__name__)

def pretty_print_json(data):
    """
    Pretty prints JSON-like data.
    Handles str, dict, list, int, float, bool, None, and nested structures.
    """

    stars_line = "*" * 40
    if mode != 'dev':
        print(data)
        print(stars_line)
        return

    # If it's a JSON string, try to parse it
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            # Not JSON, print as-is
            print(data)
            print(stars_line)
            return

    # dict or list → pretty print
    if isinstance(data, (dict, list)):
        print(json.dumps(data, indent=4, sort_keys=True, default=str))
    else:
        # int, float, bool, None, etc.
        print(data)

    print(stars_line)

def log_pretty(data, level=logging.DEBUG):
    """
    Developer-friendly pretty logger for JSON-like data.
    """
    try:
        if isinstance(data, str):
            data = json.loads(data)

        message = json.dumps(
            data,
            indent=4,
            sort_keys=True,
            default=str
        )

    except Exception:
        message = str(data)

    logger.log(level, f"\n{message}\n{'*' * 40}")