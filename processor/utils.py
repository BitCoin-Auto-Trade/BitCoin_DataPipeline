import json
import time


def parse_json(value):
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def parse_redis_hash(data):
    if not data:
        return None
    for k, v in data.items():
        if isinstance(v, str) and v and v[0] in "[{":
            data[k] = parse_json(v)
    return data


def to_redis_hash(data):
    result = {}
    for k, v in data.items():
        if isinstance(v, (list, dict)):
            result[k] = json.dumps(v)
        elif isinstance(v, bool):
            result[k] = str(v).lower()
        elif v is None:
            result[k] = ""
        else:
            result[k] = str(v)
    return result


def now_ms():
    return int(time.time() * 1000)


def calc_change_percent(current, previous):
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100
