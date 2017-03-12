class ValidationError(Exception):
    status_code = 400

    def __init__(self, message):
        super(ValidationError, self).__init__()
        self.message = message
