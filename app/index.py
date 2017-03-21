import logging
import os
import urllib2
import uuid

from elasticsearch_dsl.connections import connections
from error import RequestError
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from model import DataStore
from model import DocumentIndex
from model.Document import make_document
from model import Results
from werkzeug.exceptions import BadRequest

logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(logging.INFO)

ES_HOSTS_ENV = 'ELASTICSEARCH_HOSTS'
es_hosts = ['10.0.0.10'] if ES_HOSTS_ENV not in os.environ else str(os.environ[ES_HOSTS_ENV]).split(',')

try:
    logging.info("Verifying connection to Elasticsearch hosts...")
    for h in es_hosts:
        urllib2.urlopen('http://%s' % h, timeout=1)
    logging.info("All good!")
except urllib2.URLError as err:
    raise RuntimeError('Unable to to connect to Elasticsearch host %s' % h)

connections.create_connection(hosts=es_hosts)
app = Flask(__name__)
CORS(app)


@app.route('/')
def root():
    if 'API_DOC_LOCATION' not in os.environ:
        return 'Hello! Nothing to see here.:)'
    else:
        return redirect(os.environ['API_DOC_LOCATION'], 302)


@app.route('/register', methods=['POST'])
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


@app.route('/<uuid:index_name>/put', methods=['POST'])
def index_document(index_name):
    __validate_index_payload('id', 'title', 'contents', 'url')
    data = request.get_json()
    if DocumentIndex.exists(index_name):
        documents = [make_document(index_name, d['id'], d['title'], d['contents'], d['url']) for d in data]
        indexed_documents = DocumentIndex.index(index_name, documents)
        return jsonify({'indexed_documents': indexed_documents}), 200
    else:
        raise __index_not_found(index_name)


@app.route('/<uuid:index_name>/search', methods=['POST'])
def search(index_name):
    __validate_search_request()
    query = request.get_json()['query']
    str_index_name = str(index_name)
    logging.info('Searching for %s in %s' % (query, str_index_name))
    if DocumentIndex.exists(str_index_name):
        response = DocumentIndex.search(str_index_name, query)
        return jsonify(Results.get_results(response)), 200
    else:
        raise __index_not_found(index_name)


@app.route('/public/search', methods=['POST'])
def search_public():
    return search('public')


@app.route('/<uuid:index_name>/clear', methods=['POST'])
def clear(index_name):
    str_index_name = str(index_name)
    if DocumentIndex.exists(str_index_name):
        DocumentIndex.clear(str_index_name)
        return '', 200
    raise __index_not_found(str_index_name)


@app.errorhandler(RequestError)
def handle_error(error):
    logging.exception(error.message)
    return jsonify(error=error.status_code, description=error.message), error.status_code


def __validate_index_payload(*required_keys):
    if request.is_json:
        try:
            data = request.get_json()
            if not type(data) is list:
                raise __error_in_json()
            for document in data:
                for key in required_keys:
                    if key not in document or not document[key]:
                        raise RequestError('Missing required field in request: %s' % key, 400)
        except BadRequest:
            raise __error_in_json()
    else:
        raise __error_in_json()


def __validate_search_request():
    if request.is_json:
        try:
            json_data = request.get_json()
            if 'query' not in json_data or not json_data['query']:
                raise RequestError(request.data)
        except BadRequest:
            raise __error_in_json()
    else:
        raise __error_in_json()


def __error_in_json():
    return RequestError('There was an error parsing your JSON: %s' % request.data)


def __index_not_found(index_name):
    return RequestError('Tried to reference non-existing index: %s' % index_name, 404)


def __validate_register(*required_fields):
    for key in required_fields:
        if key not in request.form or not request.form[key]:
            raise RequestError('Missing field %s in form data.' % key, 400)


if __name__ == '__main__':
    app.run()
