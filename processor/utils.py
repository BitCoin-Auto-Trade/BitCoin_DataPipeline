import json
import time


def parse_json(value):
    """JSON 문자열 안전하게 파싱"""
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def parse_redis_hash(data):
    """Redis Hash 데이터의 JSON 필드 파싱"""
    if not data:
        return None
    for k, v in data.items():
        if isinstance(v, str) and v and v[0] in "[{":
            data[k] = parse_json(v)
    return data


def to_redis_hash(data):
    """dict를 Redis Hash 저장 가능한 형태로 변환"""
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
    """현재 시간 밀리초"""
    return int(time.time() * 1000)


def calc_change_percent(current, previous):
    """변화율(%) 계산"""
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100
