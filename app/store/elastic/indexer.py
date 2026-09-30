from datetime import datetime

from config import ELASTIC_INDEX
from store.elastic.client import get_client
from utilits.city import normalize_city_key


def ensure_index() -> None:
    client = get_client()
    if client.indices.exists(index=ELASTIC_INDEX):
        mapping = client.indices.get_mapping(index=ELASTIC_INDEX)
        properties = mapping.get(ELASTIC_INDEX, {}).get("mappings", {}).get("properties", {})
        user_id_type = properties.get("user_id", {}).get("type")
        city_norm_type = properties.get("city_norm", {}).get("type")
        if user_id_type != "long" or city_norm_type != "keyword":
            client.indices.delete(index=ELASTIC_INDEX)
        else:
            return
    client.indices.create(
        index=ELASTIC_INDEX,
        mappings={
            "properties": {
                "user_id": {"type": "long"},
                "name": {"type": "text"},
                "age": {"type": "integer"},
                "city": {"type": "keyword"},
                "city_norm": {"type": "keyword"},
                "sex": {"type": "boolean"},
                "text": {"type": "text"},
                "is_approved": {"type": "boolean"},
                "is_enabled": {"type": "boolean"},
                "profile_version": {"type": "integer"},
                "updated_at": {"type": "date"},
            }
        },
    )
from store.models import UsersTable


def index_profile(user: UsersTable) -> None:
    ensure_index()
    doc = {
        "user_id": int(user.user_id),
        "name": user.name,
        "age": user.age,
        "city": user.city,
        "city_norm": normalize_city_key(user.city),
        "sex": bool(user.sex),
        "text": user.text,
        "is_approved": bool(user.is_approved),
        "is_enabled": bool(user.is_enabled),
        "profile_version": user.profile_version or 1,
        "updated_at": datetime.utcnow().isoformat(),
    }
    client = get_client()
    client.index(index=ELASTIC_INDEX, id=user.user_id, document=doc)
