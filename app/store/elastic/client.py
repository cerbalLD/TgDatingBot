from elasticsearch import Elasticsearch

from config import ELASTIC_URL

_client = None


def get_client() -> Elasticsearch:
    global _client
    if _client is None:
        _client = Elasticsearch(ELASTIC_URL)
    return _client
