import os
import uuid

from elasticsearch_dsl.connections import connections
from error import ValidationError, NonExistingIndexError
from flask import Flask, jsonify, request, render_template
from model import DataStore
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


@app.route('/index/register', methods=['POST'])
def register():
    __validate_register('name', 'email', 'repository_url')
    form_data = request.form
    if not DataStore.exists(form_data['name']):
        index_name = str(uuid.uuid4())
        app.logger.info("Received request to register %s", index_name)
        if DocumentIndex.create(index_name):
            DataStore.create(form_data['name'], form_data['email'], index_name, form_data['repository_url'])
            return index_name, 200
    return 'User exists', 409


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
        raise NonExistingIndexError(index_name)


@app.route('/search/<uuid:index_name>/<query>', methods=['GET'])
def search(index_name, query):
    app.logger.info('Searching for %s in %s' % (query, index_name))
    if DocumentIndex.exists(index_name):
        return DocumentIndex.search(index_name, query)
    else:
        raise NonExistingIndexError(index_name)


@app.errorhandler(ValidationError)
def validation_error(error):
    return render_template('error.html', code=error.status_code, title='Error in JSON request',
                           description=error.message), error.status_code


@app.errorhandler(NonExistingIndexError)
def non_existing_index(error):
    return render_template('error.html', code=error.status_code, title='Non-existing index',
                           description='Tried to reference non-existing index: %s' % error.index_name), error.status_code


def __validate_index_payload(*required_keys):
    if request.is_json:
        try:
            json_data = request.get_json()
            if not ('document' in json_data and all(key in json_data['document'] for key in required_keys)):
                raise ValidationError(request.data)
        except BadRequest:
            raise ValidationError('There was an error parsing your JSON:\n%s' % request.data)
    else:
        raise ValidationError('There was an error parsing your JSON:\n%s' % request.data)


def __validate_register(*required_fields):
    if not all(key in request.form for key in required_fields):
        raise ValidationError('Missing fields in form data. Need: %s. Found: %s' % (str(required_fields), str(request.form.keys)))


if __name__ == '__main__':
    app.run()
