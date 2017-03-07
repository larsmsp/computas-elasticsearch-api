import os
import uuid

from elasticsearch_dsl.connections import connections
from error import JSONValidationError, NonExistingIndexError
from flask import Flask, jsonify, request, render_template
from model import DocumentIndex
from model.Document import make_document
from werkzeug.exceptions import BadRequest

ES_HOSTS_ENV = 'ELASTICSEARCH_HOSTS'
es_hosts = ['10.0.0.10'] if ES_HOSTS_ENV not in os.environ else str(os.environ[ES_HOSTS_ENV]).split(',')
connections.create_connection(hosts=es_hosts)
app = Flask(__name__)


@app.route('/')
def root():
    return 'Hello! Nothing to see here. :)'


@app.route('/index/create', methods=['GET'])
def create_index():
    index_name = str(uuid.uuid4())
    app.logger.info("Received request to create index %s", index_name)
    DocumentIndex.create(index_name)
    return jsonify(index=index_name)


@app.route('/index/put/<uuid:index_name>', methods=['POST'])
def index_document(index_name):
    if request.is_json:
        try:
            document_json = request.get_json()
            if __validate_document(document_json):
                if DocumentIndex.exists(index_name):
                    document = make_document(index_name,
                                             document_json['document']['id'],
                                             document_json['document']['title'],
                                             document_json['document']['contents'],
                                             document_json['document']['url'])
                    document.save()
                    return '', 201
                else:
                    raise NonExistingIndexError(index_name)
        except BadRequest:
            raise JSONValidationError(request.data)
    raise JSONValidationError(request.data)


def __validate_document(document):
    return 'document' in document and all(key in document['document'] for key in ('id', 'title', 'contents', 'url'))


@app.route('/search/<uuid:index_name>/<query>', methods=['GET'])
def search(index_name, query):
    return 'Searched for %s in %s' % (query, index_name)


@app.errorhandler(JSONValidationError)
def validation_error(error):
    return render_template('error.html', code=error.status_code, title='Error in JSON request',
                           description='There was an error parsing your JSON:\n%s' % error.json_payload), error.status_code


@app.errorhandler(NonExistingIndexError)
def non_existing_index(error):
    return render_template('error.html', code=error.status_code, title='Non-existing index',
                           description='Tried to reference non-existing index: %s' % error.index_name), error.status_code


if __name__ == '__main__':
    app.run()
