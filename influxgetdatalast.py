from influxdb import InfluxDBClient
from flask import Flask, jsonify, abort, make_response
from flask import request
from flask import render_template
import flask_restful as restful
import pymongo, yaml, sys, json
import metricolumns
import commands
from user import requires_auth
from get_node import getnode
import re
import json

class Influxgetdatalast(restful.Resource):

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
                result = self.getinfluxdata()
                return result
                #return make_response(jsonify({"status": str(response)}), 200)
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
        default_query = "select %s from %s where host='%s' and time > now() - 1h " % (metricstr, metric, host)
        param_query = "select %s from %s where host='%s' and time > %s and time < %s " \
                      % (metricstr, metric, host, start_time, end_time )
        try:
            if not self.content['start_time'].encode('utf8') or not self.content['end_time'].encode('utf8'):
                data = self.client.query(default_query,epoch='s' )
                result = list(data.get_points())
                my_stats_1 = []
                my_stats_2 = []
                resultant = []
                j=0
                while j<len(result):
                  result[j]['time'] = result[j]['time'] + 19800
                  first = [result[j]['time']*1000, result[j]['usage_system']]
                  second = [result[j]['time']*1000, result[j]['usage_user']]
                  #return first
                  #return second
                  my_stats_1.append(first)
                  my_stats_2.append(second)
                  j=j+1
                row_value1 = json.dumps(my_stats_1)
                #return row_value1
                row_value2 = json.dumps(my_stats_2)
                final = dict([('cpu_user', row_value1), ('system_user', row_value2)])
            #return json.dumps(final)
            #return final           
            else:
                data = self.client.query(param_query,epoch='s')
                result = list(data.get_points())

                my_stats_1 = []
                my_stats_2 = []
                resultant = []
                j=0
                while j<len(result):
                  result[j]['time'] = result[j]['time'] + 19800
                  first = [result[j]['time']*1000, result[j]['usage_system']]
                  second = [result[j]['time']*1000, result[j]['usage_user']]
                  #return first
                  #return second
		  my_stats_1.append(first)
		  my_stats_2.append(second)
 		  j=j+1
                row_value1 = json.dumps(my_stats_1)
                #return row_value1
                row_value2 = json.dumps(my_stats_2)
                final = dict([('cpu_user', row_value1), ('system_user', row_value2)])
            #return json.dumps(final)
            return final
        except Exception as e:
            print e
