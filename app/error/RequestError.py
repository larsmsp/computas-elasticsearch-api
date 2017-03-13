class RequestError(Exception):

    def __init__(self, message, status_code=400):
        super(RequestError, self).__init__()
        self.message = message
        self.status_code = status_code
