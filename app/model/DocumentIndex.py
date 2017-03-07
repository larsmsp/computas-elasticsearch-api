from elasticsearch_dsl import Index, analyzer
from .Document import Document


def create(_name, _analyzer='norwegian'):
    index = Index(_name)
    index.settings(
        number_of_shards=1,
        number_of_replicas=0
    )
    index.doc_type(Document)
    index.analyzer(analyzer(_analyzer))
    index.delete(ignore=404)
    index.create()


def exists(_name):
    return Index(_name).exists()
