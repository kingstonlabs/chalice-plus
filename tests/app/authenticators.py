from chalice_plus.authenticators import CognitoAuthenticator

from .models import User


class CustomCognitoAuthenticator(CognitoAuthenticator):
    def get_user(self):
        if self.user_id:
            return self.session.get(User, self.user_id)
