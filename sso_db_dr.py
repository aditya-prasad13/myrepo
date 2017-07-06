#!/usr/bin/python
import requests
import flask_restful as restful

class sso_full_dr(restful.Resource):
    def get(self):
        mxs_url = "http://192.168.42.112:5000/api/v0.1/sso_maxdrswitch"
        mng_url = "http://192.168.42.112:5000/api/v0.1/sso_mongodrswitch"

        mx_rslt = requests.get(mxs_url)
        mx_log = mx_rslt.json()

        mn_rslt = requests.get(mng_url)
        mn_log =  mn_rslt.json()

        return(mx_log + mn_log)
