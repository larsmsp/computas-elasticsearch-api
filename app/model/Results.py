def get_results(response):
    results = {
        'index': '',
        'results': [],
        'total': 0
    }
    for hit in response:
        document = {
            'id': hit.meta.id,
            'score': hit.meta.score,
            'title': hit.title,
            'contents': hit.contents,
            'url': hit.url,
            'created_at': hit.created_at
        }
        results['index'] = hit.meta.index
        results['results'].append(document)
        results['total'] += 1
    return results

