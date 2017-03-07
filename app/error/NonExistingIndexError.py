class NonExistingIndexError(Exception):
    status_code = 404

    def __init__(self, _index_name):
        super(NonExistingIndexError, self).__init__()
        self.index_name = _index_name
