from flask import Flask, jsonify, abort, make_response
from flask import request
from flask import render_template
import flask_restful as restful
import sys
import socket
from urllib2 import urlopen, URLError, HTTPError
import urllib
class urlchk(restful.Resource):

    def get(self):
        args = request.args
        self.url=args['url']
        status=self.go()
        return status

    def go(self):

        if self.url.startswith('http://www.'):
                self.url='http://' + self.url[len('http://www.'):]
        if self.url.startswith('www.'):
                self.url='http://' + self.url[len('www.'):]
        if not self.url.startswith('http://'):
                self.url='http://' + self.url

        result={'status':''}
        try :
                response = urlopen(self.url)
        except HTTPError, e:
                result['status']="Failed"
                return result
        except URLError, e:
                #print 'We failed to reach a server.'
                result['status']="Failed"
                return result
        else :
                code=urllib.urlopen(self.url).getcode()
                if code == 200:
                        result['status']="Success"
                else:
                      result['status']="Failed"
                return result
