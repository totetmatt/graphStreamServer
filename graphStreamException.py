# -*- coding: utf-8 -*-
from flask import jsonify

# Basic Exception Handler for WebService
class WebServiceException(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = str(message)
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['errorMessage'] = self.message
        return rv