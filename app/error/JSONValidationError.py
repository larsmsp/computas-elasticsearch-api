class JSONValidationError(Exception):
    status_code = 400

    def __init__(self, json_payload):
        super(JSONValidationError, self).__init__()
        self.json_payload = json_payload
