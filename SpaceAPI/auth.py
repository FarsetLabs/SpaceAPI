from functools import wraps
from flask import request
import authdigest
class FlaskRealmDigestDB(authdigest.RealmDigestDB):
    """
    Flask Authentication DB for HTTP Digest Authentication
    """
    def requires_auth(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not self.isAuthenticated(request):
                return self.challenge()

            return f(*args, **kwargs)

        return decorated

#Initialise Auth DB with Test Value for now.
authDB = FlaskRealmDigestDB('MyAuthRealm')
authDB.add_user('farbot', 'testing')

