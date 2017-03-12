from elasticsearch_dsl import Index, Search, analyzer
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
    s = Search(index=name).query('query_string', query=query, fields='title, contents')
    response = s.execute()
    return response
