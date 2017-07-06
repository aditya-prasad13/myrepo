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
from collections import defaultdict
from get_srv_location import getloc
from get_node import getnode
import MySQLdb

class healthstats(restful.Resource):

    #@requires_auth
    def get(self):
        args = request.args
        self.ohost=args['host']
        nodeno = getnode(self.ohost).loc()
        if nodeno == 1:
          self.client = InfluxDBClient('192.168.37.253', 8086, '', '', 'telegraf')
        elif nodeno == 2:
          self.client = InfluxDBClient('192.169.35.253', 8086, '', '', 'telegraf')
        elif nodeno == 3:
          self.client = InfluxDBClient('192.168.37.137', 8086, '', '', 'telegraf')
        elif nodeno == 4:
          self.client = InfluxDBClient('172.26.102.12', 8086, '', '', 'telegraf')
        
        result = self.serverhealth()
        #return make_response(jsonify({"status": str(result)}), 200)
        return result

    def serverhealth(self):
        """ Gather Data """
        cmd = """mysql -h192.168.27.100 -P 3306 -uroot -pl0bstEr db_sysadmin -Bse "select concat(concat(private_ip,'_'),PROJECT) from tbl_infra where PRIVATE_IP='%s' " """ % (self.ohost)
        host = commands.getoutput(cmd)
        host = host.replace(".", "_")
        cpu_query = "select mean(usage_system) +  mean(usage_user) as cpu from cpu where  host='%s' and time > now() - 5m"  % (host)
        mem_query = "select mean(used_percent)  as mem from mem where  host='%s' and time > now() - 5m" % (host)
        swap_query= "select mean(used_percent)  as swap from swap where  host='%s' and time > now() - 5m" % (host)
        load_query= "select mean(load5)  as load from system where  host='%s' and time > now() - 5m" % (host)
        cpu_stat = self.client.query(cpu_query,epoch='s' )
        mem_stat = self.client.query(mem_query,epoch='s' ) 
        swap_stat= self.client.query(swap_query )
        load_stat= self.client.query(load_query,epoch='s' )
        cpu = list(cpu_stat.get_points())
        mem = list(mem_stat.get_points())
        swap = list(swap_stat.get_points())
        load = list(load_stat.get_points())
        cpu=cpu[0]['cpu']
        mem=mem[0]['mem']
        swap=swap[0]['swap']
        load=load[0]['load']
        if cpu > 80:
                result="CPU Not Okay"
        elif mem > 80 :
                result="Memory Not Okay"	
        elif swap > 0 :
                result="Swap is being used !!! Not Okay"
        elif load > 1 :
                result="Load is there !!!! So, health is not Okay"
        else:
                result="Okay"
        return result

