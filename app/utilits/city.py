import asyncio
import re
import time
from math import radians, sin, cos, asin, sqrt

import aiohttp

from config import NOMINATIM_USER_AGENT
from store import Store

_LOCK = asyncio.Lock()
_LAST_REQUEST_AT = 0.0
_MIN_INTERVAL_SEC = 1.0


def _norm_city(value: str) -> str:
    value = value.lower().strip().replace("ё", "е")
    value = re.sub(r"[^a-z0-9а-я]+", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_city_key(value: str) -> str:
    if not value:
        return ""
    return _norm_city(value)


async def resolve_city(city: str) -> str:
    if not city:
        return city
    norm = _norm_city(city)
    if not norm:
        return city.strip()

    cached = Store.city.get_by_norm(norm) or Store.city.get_by_name(city.strip())
    if cached:
        return cached.name

    result = await _fetch_nominatim(city)
    if not result:
        return city.strip()

    name, lat, lon = result
    Store.city.upsert(norm=norm, name=name, lat=lat, lon=lon)
    return name


def get_nearest_cities(city: str, limit: int = 5) -> list[str]:
    if not city:
        return []
    norm = _norm_city(city)
    base = Store.city.get_by_norm(norm) or Store.city.get_by_name(city.strip())
    if not base:
        return []

    base_lat = float(base.lat)
    base_lon = float(base.lon)

    all_cities = Store.city.list(limit=10000)
    results: list[tuple[float, str]] = []
    for item in all_cities:
        if item.id == base.id:
            continue
        dist = _haversine_km(base_lat, base_lon, float(item.lat), float(item.lon))
        results.append((dist, item.name))
    results.sort(key=lambda item: item[0])
    return [name for _, name in results[:limit]]


async def _fetch_nominatim(query: str) -> tuple[str, float, float] | None:
    params = {
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 1,
        "accept-language": "ru",
        "q": query,
    }
    headers = {"User-Agent": NOMINATIM_USER_AGENT}

    async with _LOCK:
        now = time.monotonic()
        wait_for = _MIN_INTERVAL_SEC - (now - _LAST_REQUEST_AT)
        if wait_for > 0:
            await asyncio.sleep(wait_for)

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
            async with session.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

        globals()["_LAST_REQUEST_AT"] = time.monotonic()

    if not data:
        return None

    item = data[0]
    lat = float(item.get("lat"))
    lon = float(item.get("lon"))
    address = item.get("address", {})
    name = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("municipality")
        or address.get("county")
    )
    if not name:
        display = item.get("display_name", "")
        name = display.split(",")[0].strip() if display else query.strip()
    return name, lat, lon


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))
