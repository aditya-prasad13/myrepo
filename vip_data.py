from influxdb import InfluxDBClient
from flask import Flask, jsonify, abort, make_response
from flask import request
from flask import render_template
import flask_restful as restful
import pymongo, yaml, sys, json
import metriallcolumns
import commands
from user import requires_auth
import re
import json
import itertools
from collections import defaultdict
from get_node import getnode
from get_srv_location import getloc
import itertools
from operator import itemgetter



class vipdata(restful.Resource):

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
	        self.ohost=self.content['Hostname']
                result = self.getvipdata()
                #result = dict(itertools.izip_longest(*[iter(result1)] * 2, fillvalue=""))
		return result
		exit()
		merged = {}
		for dict in result:
			for key,value in dict.items():
				if key not in merged:
					merged [key] = []
				merged [key].append(value)
		#merged.pop('time')
		result1=merged
		result = defaultdict(list)
		for key, value in result1.iteritems():
		   j = 0
		   if key != "time":
		       for item1 in value:
	           		result[key].append([result1["time"][j],item1])
		        	j = j + 1
				result=result
                #return make_response(jsonify({"status": str(result)}), 200)
                return result
        except Exception as e:
            print e

    def getvipdata(self):
         """ Gather Data """
         cmd = """mysql -uapi_user -pApIuser -h192.168.36.201 nagios -Bse "select distinct RIP from SNMP_MAP where VIP='%s' " """ % (self.ohost)
         host = commands.getoutput(cmd)
         list1=host.split()
	 final_list={}
         for i in list1:
		
	  	ohost=i
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

        	cmd = """mysql -h192.168.27.100 -P 3306 -uroot -pl0bstEr db_sysadmin -Bse "select concat(concat(private_ip,'_'),PROJECT) from tbl_infra where PRIVATE_IP='%s' " """ % (ohost)
	        host = commands.getoutput(cmd)
        	host = host.replace(".", "_")
	        host = host.replace(" ", "")
        	start_time = self.content['start_time']+"s".encode('utf8')
	        end_time = self.content['end_time']+"s".encode('utf8')
        	metric = self.content['metric']
	        """ Build Query """
        	metricstr = ','.join(getattr(metriallcolumns, metric+'_TABLE_COLUMNS'))
	        default_query = "select %s from %s where host='%s' and time > now() - 1h  limit 50" % (metricstr, metric, host)
        	param_query = "select %s from %s where host='%s' and time > %s and time < %s limit 50" \
                      % (metricstr, metric, host, start_time, end_time )
	        try:
        	    #if start_time is None or end_time is None:
	            if not self.content['start_time'].encode('utf8') or not self.content['end_time'].encode('utf8'):
                	data = self.client.query(default_query,epoch='s' )
	                result = list(data.get_points())
        	        j=0
	                while j<len(result):
                  		result[j]['time'] = (result[j]['time'] + 19800) * 1000
		                j=j+1
            	    else:
	                data = self.client.query(param_query,epoch='s')
        	        result = list(data.get_points())
                	j=0
	                while j<len(result):
        	          	result[j]['time'] = (result[j]['time'] + 19800) * 1000
	                	j=j+1
				if metric=='disk':
				   result = sorted(result, key=itemgetter('path'))
                                   final_list[ohost]=result
                    if metric!='disk':
		    	merged = {}
	                for dict in result:
                        	for key,value in dict.items():
                                	if key not in merged:
                                        	merged [key] = []
	                                merged [key].append(value)
                #merged.pop('time')
            	        result1=merged
                        result = defaultdict(list)
	                for key, value in result1.iteritems():
                   		j = 0
                   		if key != "time":
                       			for item1 in value:
                                		result[key].append([result1["time"][j],item1])
		                                j = j + 1
        		final_list[ohost] = result
	                #final_list=json.dump(final_list)
        	except Exception as e:
				print e
         return final_list
	
