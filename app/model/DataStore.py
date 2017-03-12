from google.cloud import datastore

NAMESPACE = 'Abakus'
ENTITY_KEY = 'Entrant'


def exists(name):
    ds = __get_ds_client()
    entrants = ds.query(kind=ENTITY_KEY).fetch()
    return any(e['name'] == name for e in entrants)


def create(name, email, index, repository_url):
    ds = __get_ds_client()
    entrant = datastore.Entity(key=ds.key(ENTITY_KEY, index))
    entrant.update({
        'name': name,
        'email': email,
        'repository_url': repository_url
    })
    ds.put(entrant)


def get_by_name(name):
    return get('name', name)


def get(key, value):
    ds = __get_ds_client()
    entrants = ds.query(kind=ENTITY_KEY).fetch()
    return next((e for e in entrants if e[key] == value), None)


def __get_ds_client():
    return datastore.Client(namespace=NAMESPACE)

