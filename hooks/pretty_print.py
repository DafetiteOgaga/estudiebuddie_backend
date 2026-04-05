import json, logging
logger = logging.getLogger(__name__)
try:
    from .dont_push import mode
    logger.info(f"Development mode 🔨")
except Exception as e:
    logger.info(f"Production mode ☁")
    mode = 'prod'

def pretty_print_json(data):
    """
    Pretty prints JSON-like data.
    Handles str, dict, list, int, float, bool, None, and nested structures.
    """

    stars_line = "*" * 40
    if mode != 'dev':
        logger.info(data)
        logger.info(stars_line)
        return

    # If it's a JSON string, try to parse it
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            # Not JSON, print as-is
            logger.info(data)
            logger.info(stars_line)
            return

    # dict or list → pretty print
    if isinstance(data, (dict, list)):
        logger.info(json.dumps(data, indent=4, sort_keys=True, default=str))
    else:
        # int, float, bool, None, etc.
        logger.info(data)

    logger.info(stars_line)

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