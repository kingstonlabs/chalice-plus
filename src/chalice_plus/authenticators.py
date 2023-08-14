import base64
import binascii
import json

from functools import cached_property

from chalice.app import UnauthorizedError


class CognitoAuthenticator:
    def __init__(self, request, session):
        self.request = request
        self.session = session

    @cached_property
    def jwt_payload(self):
        token = self.request.headers.get("authorization")
        if not token:
            token = self.request.headers.get("Authorization")
        if token:
            return self._decode_jwt_payload(token)

    def _decode_jwt_payload(self, jwt):
        try:
            payload_segment = jwt.split(".", 2)[1]
            payload = base64.urlsafe_b64decode(self._base64_pad(payload_segment))
            return json.loads(payload)
        except (IndexError, binascii.Error, json.decoder.JSONDecodeError):
            raise UnauthorizedError("Unauthorized")

    def _base64_pad(self, value):
        rem = len(value) % 4
        if rem > 0:
            value += "=" * (4 - rem)
        return value

    def get_user(self):
        raise NotImplementedError

    @cached_property
    def user(self):
        return self.get_user()

    def get_user_id(self):
        if self.jwt_payload:
            return self.jwt_payload.get("sub")

    @cached_property
    def user_id(self):
        return self.get_user_id()
