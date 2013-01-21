# -*- coding: utf-8 -*-
"""
    werkzeug.contrib.authdigest
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The authdigest module contains classes to support
    digest authentication compliant with RFC 2617.


    Usage
    =====

    ::

        from werkzeug.contrib.authdigest import RealmDigestDB

        authDB = RealmDigestDB('test-realm')
        authDB.add_user('admin', 'test')

        def protectedResource(environ, start_reponse):
            request = Request(environ)
            if not authDB.isAuthenticated(request):
                return authDB.challenge()

            return get_protected_response(request)

    :copyright: (c) 2010 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Imports
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import os
import weakref
import hashlib
import werkzeug
import json
from SpaceAPI import app
import MySQLdb
log = app.logger

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Realm Digest Credentials Database
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class DigestDBConnection(object):
   """Database connection

    Passwords are hashed using realm key, and specified
    digest algorithm.

    :param realm: string identifing the hashing realm
    :param algorthm: string identifying hash algorithm to use,
                     default is 'md5'
    """

    def __init__(self, db_dict):
        import getpass
        log.error("Executing as %s"%getpass.getuser())
        try:
            self.tables = self.multi_query("show tables")
            if 'user' not in tables:
                raise Error("Cannot Query Database")
        except:
            log.error("Cannot Connect to DB")

    def connect():
        return MySQLdb.connect(
            self.db_dict['host'],
            self.db_dict['user'],
            self.db_dict['pass'],
            self.db_dict['name']
        }

    def multi_query( qry ):
        c = self.connect()
        #Todo input sanitation
        c.execute( qry )
        return c.fetchall()

    def existance_check( value, qry):
        for candidate in self.multi_query(qry):
            if value in candidate:
                return True
        return False

    def user_list(self):
        return multi_query(
        "select member.cid, username, firstName, middleName, lastName, email, role.name, hash
        from member
        left join contact on member.cid = contact.cid
        left join user on member.cid = user.cid
        left join membership on (member.cid = membership.cid and membership.end is NULL)
        left join plan on plan.pid = membership.pid
        left join user_role on user_role.cid = member.cid
        left join role on role.rid = user_role.rid
        where 1")

    def get(self, user, default=None):
        return 

    def __contains__(self, user):
        return self.existance_check(user, "select username from user")
    def __getitem__(self, user):
        return self.db.get(user)
    def __setitem__(self, user, password):
        return self.add_user(user, password)
    def __delitem__(self, user):
        return self.db.pop(user, None)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def newDB(self):
        if self.file is False:
            return dict()
        else:
            str_data = open(self.file,'r+')
            try:
                data = json.load(str_data)
                self.alg = self.newAlgorithm(data['cfg']['algorithm'])
                self.realm = data['cfg']['realm']
                db = dict(data['db'])
                roles = dict(data['roles'])
            except ValueError as e:
                log.error("Failed on Data Import, launching with no auth data: %s" %e )
                db = dict()
                roles = dict()
            finally:
                str_data.close()
        return (db, roles)


    def newAlgorithm(self, algorithm):
        return DigestAuthentication(algorithm)

    def isAuthenticated(self, request, role = None, **kw):
        authResult = AuthenticationResult(self)
        request.authentication = authResult

        authorization = request.authorization
        if authorization is None or authorization.response is None:
            return authResult.deny('initial', None)
        authorization.result = authResult

        hashPass = self[authorization.username]
        rolesPass = self.roles.get(authorization.username)
        if hashPass is None:
            return authResult.deny('unknown_user:%s' % authorization.username)
        elif not self.alg.verify(authorization, hashPass, request.method, **kw):
            return authResult.deny('invalid_password:%s' % authorization.username)
        # If a specific role is requested, check it
        elif role is not None:
            if rolesPass is None or role not in rolesPass:
                return authResult.deny('invalid_role:%s' % authorization.username)
            else:
                return authResult.approve('role_success:%s' % authorization.username)
        else:
            return authResult.approve('success:%s' % authorization.username)

    challenge_class = werkzeug.Response
    def challenge(self, response=None, status=401):
        try:
            authReq = response.www_authenticate
        except AttributeError:
            response = self.challenge_class(response, status)
            authReq = response.www_authenticate
        else:
            if isinstance(status, (int, long)):
                response.status_code = status
            else: response.status = status

        authReq.set_digest(self.realm, os.urandom(8).encode('hex'))
        return response


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Authentication Result
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class AuthenticationResult(object):
    """Authentication Result object

    Created by RealmDigestDB.isAuthenticated to operate as a boolean result,
    and storage of authentication information."""

    authenticated = None
    reason = None
    status = 500

    def __init__(self, authDB):
        self.authDB = weakref.ref(authDB)

    def __repr__(self):
        return '<authenticated: %r reason: %r>' % (
            self.authenticated, self.reason)
    def __nonzero__(self):
        return bool(self.authenticated)

    def deny(self, reason, authenticated=False):
        if bool(authenticated):
            raise ValueError("Denied authenticated parameter must evaluate as False")
        self.authenticated = authenticated
        self.reason = reason
        self.status = 401
        log.error(self)
        return self

    def approve(self, reason, authenticated=True):
        if not bool(authenticated):
            raise ValueError("Approved authenticated parameter must evaluate as True")
        self.authenticated = authenticated
        self.reason = reason
        self.status = 200
        log.error(self)
        return self

    def challenge(self, response=None, force=False):
        if force or not self:
            return self.authDB().challenge(response, self.status)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Digest Authentication Algorithm
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class DigestAuthentication(object):
    """Digest Authentication implementation.

    references:
        "HTTP Authentication: Basic and Digest Access Authentication". RFC 2617.
            http://tools.ietf.org/html/rfc2617

        "Digest access authentication"
            http://en.wikipedia.org/wiki/Digest_access_authentication
    """

    def __init__(self, algorithm='md5'):
        self.algorithm = algorithm.lower()
        self.H = self.hashAlgorithms[self.algorithm]

    def verify(self, authorization, hashPass=None, method='GET', **kw):
        reqResponse = self.digest(authorization, hashPass, method, **kw)
        if reqResponse:
            return (authorization.response.lower() == reqResponse.lower())

    def digest(self, authorization, hashPass=None, method='GET', **kw):
        if authorization is None:
            return None

        if hashPass is None:
            hA1 = self._compute_hA1(authorization, kw['password'])
        else: hA1 = hashPass

        hA2 = self._compute_hA2(authorization, method)

        if 'auth' in authorization.qop:
            res = self._compute_qop_auth(authorization, hA1, hA2)
        elif not authorization.qop:
            res = self._compute_qop_empty(authorization, hA1, hA2)
        else:
            raise ValueError("Unsupported qop: %r" % (authorization.qop,))
        return res

    def hashPassword(self, username, realm, password):
        return self.H(username, realm, password)

    def _compute_hA1(self, auth, password=None):
        return self.hashPassword(auth.username, auth.realm, password or auth.password)
    def _compute_hA2(self, auth, method='GET'):
        return self.H(method, auth.uri)
    def _compute_qop_auth(self, auth, hA1, hA2):
        return self.H(hA1, auth.nonce, auth.nc, auth.cnonce, auth.qop, hA2)
    def _compute_qop_empty(self, auth, hA1, hA2):
        return self.H(hA1, auth.nonce, hA2)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    hashAlgorithms = {}

    @classmethod
    def addDigestHashAlg(klass, key, hashObj):
        key = key.lower()
        def H(*args):
            x = ':'.join(map(str, args))
            return hashObj(x).hexdigest()

        H.__name__ = "H_"+key
        klass.hashAlgorithms[key] = H
        return H

DigestAuthentication.addDigestHashAlg('md5', hashlib.md5)
DigestAuthentication.addDigestHashAlg('sha', hashlib.sha1)
DigestAuthentication.addDigestHashAlg('sha256', hashlib.sha256)


