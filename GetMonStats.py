#!/usr/bin/python

import sys
from flask import Flask, jsonify, abort, make_response
from flask import request
from flask import render_template
import flask_restful as restful
import pymongo, yaml, sys, json
from user import requires_auth
from db_conn import DB_Connector
from ssh_conn import ssh
import commands
import metricolumns
from influxdb import InfluxDBClient


class GetMonStats(restful.Resource):

  def __init__(self):
    self.client = InfluxDBClient('192.168.37.253', 8086, '', '', 'telegraf')

  def get(self):
    list=[]
    args = request.args
    self.hst = args['Hostname']
    self.srttime = args['Start_time']
    self.endtime = args['End_time']
    self.metric = args['Metric']
    #self.usr = 'root'
    #self.pwd= '112@$mcitY6'
    #self.pwd= 'tooroot'
    self.GetStats()

  def GetStats(self):
    #Check if Hostname is empty
    if self.hst is None:
       return make_response(jsonify(
                    {"status": "Hostname is missing in request"}), 401)
    if self.srttime is None:
       return make_response(jsonify(
                    {"status": "Start time is missing in request"}), 401)
    if self.endtime is None:
       return make_response(jsonify(
                    {"status": "End time is missing in request"}), 401)    
    
    cmd = """mysql -h192.168.27.100 -P 3306 -uroot -pl0bstEr db_sysadmin -Bse "select concat(concat(private_ip,'_'),PROJECT) from tbl_infra where PRIVATE_IP='%s' " """ % (self.hst)
    #print cmd
    host = commands.getoutput(cmd)
    host = host.replace(".", "_")
    #start_time = self.content['start_time']+'s'
    #start_time = request.args.get('start_time')+'s'
    #end_time = request.args.get('end_time')+'s'
    #metric = request.args.get('metric')

    """ Build Query """
    metricstr = ','.join(getattr(metricolumns, self.metric+'_TABLE_COLUMNS'))
    default_query = "select %s from %s where host='%s' and time > now() - 1h limit 12" % (metricstr, self.metric, self.hst)
    param_query = "select %s from %s where host='%s' and time > %s and time < %s" \
                      % (metricstr, self.metric, self.hst, self.srttime, self.endtime )
    try:
         if self.srttime or self.endtime is None:
            data = self.client.query(default_query)
            result = list(data.get_points())
         else:
            data = self.client.query(param_query)
            result = list(data.get_points())
            return result
    except Exception as e:
    	print e    


