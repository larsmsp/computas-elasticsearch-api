from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Index, Search, analyzer
from elasticsearch_dsl.connections import connections
from .Document import Document


def create(name, analyzer_name='norwegian'):
    index = Index(name)
    index.settings(
        number_of_shards=1,
        number_of_replicas=0
    )
    index.doc_type(Document)
    index.analyzer(analyzer(analyzer_name))
    index.delete(ignore=404)
    index.create()
    return exists(name)


def exists(name):
    return Index(name).exists()


def search(name, query):
    s = Search(index=name).query('query_string', query=query)
    return s.execute()


def clear(name):
    return create(name)


def size(name):
    c = IndicesClient(connections.get_connection())
    return c.stats(index=name, metric='store', human=True)


def index(name, documents):
    conn = connections.get_connection()
    actions = ({
                   '_op_type': 'index',
                   '_index': name,
                   '_type': 'document',
                   '_id': d.meta.id,
                   '_source': d
               } for d in documents)
    return bulk(conn, actions)[0]



"""
'{"query": {"query_string": {"fields": ["title, contents"], "query": "this"}}}'
"""
