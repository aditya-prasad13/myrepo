from influxdb import InfluxDBClient
from flask import Flask, jsonify, abort, make_response
from flask import request
from flask import render_template
import flask_restful as restful
import pymongo, yaml, sys, json
import metricolumns
import commands
from user import requires_auth
import re
import json
from get_srv_location import getloc
from get_node import getnode


class Influxgetdata(restful.Resource):

    def __init__(self):
	        self.client = InfluxDBClient('192.168.37.253', 8086, '', '', 'telegraf')

    #@requires_auth
    def post(self):
        try:
            if 'Content-Type' not in request.headers:
                return make_response(jsonify(
                    {"status": "Header Content-Type is missing in request"}), 401)
            if request.headers['Content-Type'] != 'application/json' :
                return make_response(jsonify(
                    {"status": "Your Content-Type is not set to application/json"}), 401)
            else:
                self.content = request.get_json(silent=True, force=True)
                print self.content
                #response = self.getinfluxdata()
                result = self.getinfluxdata()
		merged = {}
                for dict in result:
                        for key,value in dict.items():
                                if key not in merged:
                                        merged [key] = []
                                merged [key].append(value)
                result=merged
                #lk=x[0].keys()
                #count=len(lk)
                #result="count : " +str(count) + ":"
                #result=""
                #for j in lk:
                #        quotes = ","
                #        lst = ""
                #        for i in x:
                #                lst+="[" + str(i['time']) + ',' + str(i[j]) + "]" + ","
                #        	z= "[" + re.sub( ",$","",lst) + "]"  
               	#	result+=  j  + ":" +z  
               	#result= '{' + result + '}'
                #response=json.dumps(result)
                return result
                #return jsonify(response)
                #return response
        except Exception as e:
            print e

    def getinfluxdata(self):
        """ Gather Data """
        ohost = self.content['Hostname']
        cmd = """mysql -h192.168.27.100 -P 3306 -uroot -pl0bstEr db_sysadmin -Bse "select concat(concat(private_ip,'_'),PROJECT) from tbl_infra where
PRIVATE_IP='%s' " """ % (ohost)
        host = commands.getoutput(cmd)
        host = host.replace(".", "_")
        host = host.replace(" ", "")
        start_time = self.content['start_time']+"s".encode('utf8')
        end_time = self.content['end_time']+"s".encode('utf8')
        metric = self.content['metric']

        dc=getnode(ohost)
        node=dc.loc()
        if node == 1:
           self.client = InfluxDBClient('192.168.37.253', 8086, '', '', 'telegraf')
        elif node == 2:
           self.client = InfluxDBClient('192.169.35.253', 8086, '', '', 'telegraf')
        elif node == 3:
           self.client = InfluxDBClient('192.168.37.137', 8086, '', '', 'telegraf')
        elif node == 4:
           self.client = InfluxDBClient('172.26.102.12', 8086, '', '', 'telegraf')

        """ Build Query """
        metricstr = ','.join(getattr(metricolumns, metric+'_TABLE_COLUMNS'))
        default_query = "select %s from %s where host='%s' and time > now() - 1h limit 5 " % (metricstr, metric, host)
        param_query = "select %s from %s where host='%s' and time > %s and time < %s  limit 5" \
                      % (metricstr, metric, host, start_time, end_time )
        try:
            if start_time is None or end_time is None:
                data = self.client.query(default_query,epoch='ms' )
                result = list(data.get_points())
                j=0
                while j<len(result):
                  result[j]['time'] = result[j]['time'] + 19800
                  j=j+1
            else:
                data = self.client.query(param_query,epoch='ms')
                result = list(data.get_points())
                j=0
                while j<len(result):
                  result[j]['time'] = result[j]['time'] + 19800000
                  j=j+1
		#result={"count":"12", "time": "16:10,16:20,16:30,16:40,16:50,16:59,15:10,15:20,15:30,15:40,15:50,15:59","usage_system": "1.062,1.063,1.064,1.065,5.656,6.598,9.569,1.064,1.065,5.656,6.598,9.569","usage_user": "6.326,6.365,9.568,8.364,9.365,1.236,3.236,9.568,8.364,9.365,1.236,3.236"}
            return result
        except Exception as e:
            print e
