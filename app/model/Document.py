from datetime import datetime
from elasticsearch_dsl import DocType, Text, Date


class Document(DocType):

    title = Text()
    contents = Text()
    url = Text()
    created_at = Date()

    def __init__(self, _index, _document_id, **kwargs):
        super(Document, self).__init__(meta={'id': _document_id, 'index': _index}, **kwargs)

    def save(self, **kwargs):
        self.created_at = datetime.now()
        return super(Document, self).save(**kwargs)


def make_document(index, document_id, title, contents, url):
    document = Document(index, document_id)
    document.title = title
    document.contents = contents
    document.url = url
    return document
