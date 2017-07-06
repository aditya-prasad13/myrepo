from influxdb import InfluxDBClient
from flask import Flask, jsonify, abort, make_response
from flask import request
from flask import render_template
import flask_restful as restful
import pymongo, yaml, sys, json
from get_srv_location import getloc
from get_node import getnode
import metricolumns
import commands
from user import requires_auth
import re
import json

class Influxgetdatadisk(restful.Resource):

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

        """ Build Query """
        metricstr = ','.join(getattr(metricolumns, metric+'_TABLE_COLUMNS'))
        #return metric
        #return metricstr 
        #exit

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


        ####### Query disk values - /root   #######
        default_query_root = "select %s from %s where host='%s' and path='/' and time > now() - 1h " % (metricstr, metric, host)
        param_query_root = "select %s from %s where host='%s' and path='/' and time > %s and time < %s " \
                      % (metricstr, metric, host, start_time, end_time )
        #return param_query_root
        #exit
        try:
            if not self.content['start_time'].encode('utf8') or not self.content['end_time'].encode('utf8'):
                data_root = self.client.query(default_query_root,epoch='s' )
                result_root = list(data_root.get_points())
                my_stats_root = []
                j=0
                while j<len(result_root):
                  result_root[j]['time'] = result_root[j]['time'] + 19800
                  first_root = [result_root[j]['time']*1000, result_root[j]['used_percent']]
                  #return first_root
                  my_stats_root.append(first_root)
                  j=j+1
                row_value_root = json.dumps(my_stats_root)
                #return row_value_root
                #exit
                final_root = dict([('root', row_value_root)]) 
            else:
                data_root = self.client.query(param_query_root,epoch='s')
                result_root = list(data_root.get_points())
                my_stats_root = []
                j=0
                while j<len(result_root):
                  result_root[j]['time'] = result_root[j]['time'] + 19800
                  first_root = [result_root[j]['time']*1000, result_root[j]['used_percent']]
                  #return first_root
		  my_stats_root.append(first_root)
 		  j=j+1
                row_value_root = json.dumps(my_stats_root)
                #return row_value_root
                #exit
                final_root = dict([('root', row_value_root)])
            #return json.dumps(final_root)
            #return final_root
        except Exception as e:
            print e
        #############################################

        ####### Query disk values - /log   #######
        default_query_log = "select %s from %s where host='%s' and path='/log' and time > now() - 1h " % (metricstr, metric, host)
        param_query_log = "select %s from %s where host='%s' and path='/log' and time > %s and time < %s " \
                      % (metricstr, metric, host, start_time, end_time )
        #return param_query_log
        #exit
        try:
            if not self.content['start_time'].encode('utf8') or not self.content['end_time'].encode('utf8'):
                data_log = self.client.query(default_query_log,epoch='s' )
                result_log = list(data_log.get_points())
                my_stats_log = []
                j=0
                while j<len(result_log):
                  result_log[j]['time'] = result_log[j]['time'] + 19800
                  first_log = [result_log[j]['time']*1000, result_log[j]['used_percent']]
                  #return first_data
                  my_stats_log.append(first_log)
                  j=j+1
                row_value_log = json.dumps(my_stats_log)
                #return row_value_data
                #exit
                final_log = dict([('log', row_value_log)])
            else:
                data_log = self.client.query(param_query_log,epoch='s')
                result_log = list(data_log.get_points())
                my_stats_log = []
                j=0
                while j<len(result_log):
                  result_log[j]['time'] = result_log[j]['time'] + 19800
                  first_log = [result_log[j]['time']*1000, result_log[j]['used_percent']]
                  #return first_data
                  my_stats_log.append(first_log)
                  j=j+1
                row_value_log = json.dumps(my_stats_log)
                #return row_value_data
                #exit
                final_log = dict([('log', row_value_log)])
            #return json.dumps(final_log)
            #return final_log
        except Exception as e:
            print e
        #############################################
        
        #resultant = {}
        #resultant = final_data.final_log
        #resultant.append(final_data)
        #resultant.append(final_log)
        #resultant = dict([ (final_data), (final_log) ])
        #resultant = final_data + final_log
        #return resultant
        resultant = dict(final_root, **final_log)
        return resultant        

