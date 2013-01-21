from functools import wraps
from flask import request, jsonify
import authdigest
from SpaceAPI.settings import *

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

    def requires_admin(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not self.isAuthenticated(request, role = 'admin'):
                return self.challenge()
                #return jsonify(value=False, error='Invalid Role', status=403)

            return f(*args, **kwargs)

        return decorated


#Initialise Auth DB with Test Value for now.
authDB = FlaskRealmDigestDB('SpaceAPI', file='/opt/SpaceAPI/auth.json')
