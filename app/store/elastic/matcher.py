from typing import Optional
from datetime import datetime


from config import ELASTIC_INDEX
from store import Store
from store.models import UsersTable
from store.elastic.client import get_client
from store.elastic.indexer import ensure_index
from config import FREE_VIEW_LIMIT
from utilits.city import get_nearest_cities, normalize_city_key


def _swiped_keys(viewer_id: int) -> set[tuple[int, int]]:
    swipes = Store.swipe.list(user_id=viewer_id, limit=1000)
    return {(s.target_user_id, s.target_version) for s in swipes}


def _build_city_filter(cities: list[str]) -> dict:
    norms = [normalize_city_key(city) for city in cities if normalize_city_key(city)]
    if len(norms) == 1:
        return {"term": {"city_norm": norms[0]}}
    if norms:
        return {"terms": {"city_norm": norms}}
    if len(cities) == 1:
        return {"term": {"city": cities[0]}}
    return {"terms": {"city": cities}}


def _search_candidates(viewer, min_age: int, max_age: int, cities: list[str] | None = None) -> list[dict]:
    cities = cities or [viewer.city]
    city_filter = _build_city_filter(cities)
    must_filters = [
        city_filter,
        {"term": {"is_approved": True}},
        {"term": {"is_enabled": True}},
        {"range": {"age": {"gte": min_age, "lte": max_age}}},
    ]
    must_filters.append({"term": {"sex": not viewer.sex}})

    body = {
        "size": 50,
        "query": {
            "bool": {
                "must": must_filters,
                "must_not": [{"term": {"user_id": viewer.user_id}}],
            }
        },
        "sort": [{"user_id": "asc"}],
    }

    client = get_client()
    resp = client.search(index=ELASTIC_INDEX, body=body)
    return resp.get("hits", {}).get("hits", [])


def _search_nearest_by_age(viewer, cities: list[str] | None = None) -> list[dict]:
    cities = cities or [viewer.city]
    city_filter = _build_city_filter(cities)
    must_filters = [
        city_filter,
        {"term": {"is_approved": True}},
        {"term": {"is_enabled": True}},
    ]
    must_filters.append({"term": {"sex": not viewer.sex}})

    body = {
        "size": 50,
        "query": {
            "bool": {
                "must": must_filters,
                "must_not": [{"term": {"user_id": viewer.user_id}}],
            }
        },
        "sort": [
            {
                "_script": {
                    "type": "number",
                    "script": {
                        "source": "Math.abs(doc['age'].value - params.age)",
                        "params": {"age": viewer.age},
                    },
                    "order": "asc",
                }
            }
        ],
    }

    client = get_client()
    resp = client.search(index=ELASTIC_INDEX, body=body)
    return resp.get("hits", {}).get("hits", [])


def _search_with_age_range(viewer, cities: list[str], max_delta: int = 3) -> list[dict] | None:
    base_min = max(0, viewer.age - 2)
    base_max = viewer.age + 2
    for delta in range(0, max_delta + 1):
        min_age = max(0, base_min - delta)
        max_age = base_max + delta
        try:
            hits = _search_candidates(viewer, min_age, max_age, cities)
        except Exception:
            return None
        if hits:
            return hits
    return []


def _has_active_subscription(user) -> bool:
    expires = user.expire_subscription_date
    return bool(expires and expires > datetime.utcnow())


def _utc_day_start() -> datetime:
    now = datetime.utcnow()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _can_show_profile(candidate) -> bool:
    if _has_active_subscription(candidate):
        return True
    # Free limit resets daily. If user exhausted it, hide profile.
    return Store.swipe.count_by_user_since(candidate.user_id, _utc_day_start()) < FREE_VIEW_LIMIT


def find_next_profile(viewer_id: int) -> Optional[UsersTable]:
    viewer = Store.user.get_by_user_id(viewer_id)
    if not viewer:
        return None

    ensure_index()

    swiped = _swiped_keys(viewer_id)
    hits: list[dict] | None = _search_with_age_range(viewer, [viewer.city], max_delta=3)
    if hits is None:
        return None

    if not hits:
        nearest_cities = get_nearest_cities(viewer.city, limit=5)
        for city in nearest_cities:
            hits = _search_with_age_range(viewer, [city], max_delta=3)
            if hits is None:
                return None
            if hits:
                break

    for hit in hits:
        source = hit.get("_source", {})
        candidate_user_id = int(source.get("user_id", 0))
        candidate_version = int(source.get("profile_version", 1))
        candidate_age = int(source.get("age", 0))

        if (candidate_user_id, candidate_version) in swiped:
            continue

        candidate = Store.user.get_by_user_id(candidate_user_id)
        if candidate and _can_show_profile(candidate):
            return candidate

    return None
