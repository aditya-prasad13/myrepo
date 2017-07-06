import os, sys
import flask_restful as restful
from flask import Flask, abort, request, jsonify, g, url_for, make_response
from models import User, db
from functools import wraps


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token_custom = request.headers.get('X-Token')
        if not User.verify_auth_token(token_custom):
            abort(401, 'Either your Token is Expired or Token is Bad')
        return f(*args, **kwargs)
    return decorated

class NewUser(restful.Resource):

    def post(self):
        self.username = request.json.get('username')
        self.password = request.json.get('password')
        if self.username is None or self.password is None:
            abort(400)  # missing arguments
        response = self.new_user()
        return make_response(jsonify({"username": str(response)}), 200)

    def new_user(self):
        if User.query.filter_by(username=self.username).first() is not None:
            abort(400)    # existing user
        user = User(username=self.username)
        user.hash_password(self.password)
        db.session.add(user)
        db.session.commit()
        return user.username


class Token(restful.Resource):

    def post(self):
        self.username = request.json.get('username')
        self.password = request.json.get('password')
        if self.username is None or self.password is None:
            abort(400)  # missing arguments
        response = self.get_auth_token()
        return make_response(jsonify({"token": str(response), "duration": 600}), 200)

    def verify_password(self, username_or_token, password):
        # first try to authenticate by token
        user = User.verify_auth_token(username_or_token)
        if not user:
            # try to authenticate with username/password
            user = User.query.filter_by(username=username_or_token).first()
            if not user or not user.verify_password(password):
                return False
        g.user = user
        return True

    def get_auth_token(self):
        result = self.verify_password(self.username, self.password)
        if result:
            token = g.user.generate_auth_token(600)
            return token.decode('ascii')
        else:
            abort(400)
