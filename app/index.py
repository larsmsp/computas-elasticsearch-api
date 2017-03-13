import logging
import os
import uuid

from elasticsearch_dsl.connections import connections
from error import RequestError
from flask import Flask, request
from flask_cors import CORS
from model import DataStore
from model import DocumentIndex
from model.Document import make_document
from werkzeug.exceptions import BadRequest

ES_HOSTS_ENV = 'ELASTICSEARCH_HOSTS'
es_hosts = ['10.0.0.10'] if ES_HOSTS_ENV not in os.environ else str(os.environ[ES_HOSTS_ENV]).split(',')
connections.create_connection(hosts=es_hosts)
app = Flask(__name__)
CORS(app)


@app.route('/')
def root():
    return 'Hello! Nothing to see here. :)'


@app.route('/index/register', methods=['POST'])
def register():
    logging.info("Incoming registration: %s" % request.form)
    __validate_register('name', 'email', 'repository_url')
    form_data = request.form
    if not DataStore.exists(form_data['name']):
        index_name = str(uuid.uuid4())
        logging.info("Received request to register %s", index_name)
        if DocumentIndex.create(index_name):
            DataStore.create(form_data['name'], form_data['email'], index_name, form_data['repository_url'])
            return index_name, 200
    raise RequestError('User %s exists!' % form_data['name'], 409)


@app.route('/index/put/<uuid:index_name>', methods=['POST'])
def index_document(index_name):
    __validate_index_payload('id', 'title', 'contents', 'url')
    document_json = request.get_json()
    if DocumentIndex.exists(index_name):
        document = make_document(index_name,
                                 document_json['document']['id'],
                                 document_json['document']['title'],
                                 document_json['document']['contents'],
                                 document_json['document']['url'])
        document.save()
        return '', 200
    else:
        raise __index_not_found(index_name)


@app.route('/search/<uuid:index_name>/<query>', methods=['GET'])
def search(index_name, query):
    logging.info('Searching for %s in %s' % (query, index_name))
    if DocumentIndex.exists(index_name):
        return DocumentIndex.search(index_name, query)
    else:
        raise __index_not_found(index_name)


@app.errorhandler(RequestError)
def handle_error(error):
    logging.exception(error.message)
    return error.message, error.status_code


def __validate_index_payload(*required_keys):
    if request.is_json:
        try:
            json_data = request.get_json()
            if not ('document' in json_data and all(key in json_data['document'] for key in required_keys)):
                raise RequestError(request.data)
        except BadRequest:
            raise __error_in_json()
    else:
        raise __error_in_json()


def __error_in_json():
    return RequestError('There was an error parsing your JSON:\n%s' % request.data)


def __index_not_found(index_name):
    return RequestError('Tried to reference non-existing index: %s' % index_name, 404)


def __validate_register(*required_fields):
    if not all(key in request.form for key in required_fields):
        raise RequestError('Missing fields in form data. Need: %s. Found: %s' % (str(required_fields), str(request.form.keys)))


if __name__ == '__main__':
    app.run()
