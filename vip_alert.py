#!/usr/bin/python

from flask import Flask, jsonify, abort, make_response
from flask import request
from flask import render_template
import flask_restful as restful
from get_srv_location import getloc
import commands
from db_conn import DB_Connector
from get_node import getnode
import MySQLdb
import json

class vip_alert_stat(restful.Resource):


    def get(self):
        args = request.args
        self.hst = args['host']
        self.lmt = args['limit']
        self.ofst = args['offset']
        x=self.status()
        return x

    def status(self):
        hostmod = ''
        cmd = """mysql -uapi_user -pApIuser -h192.168.36.201 nagios -Bse "select exists (select distinct RIP from SNMP_MAP where VIP='%s') " """ % (self.hst)
        status1 = commands.getoutput(cmd)
	if status1 == '1':
		cmd = """mysql -uapi_user -pApIuser -h192.168.36.201 nagios -Bse "select distinct RIP from SNMP_MAP where VIP= '%s' " """ % (self.hst)
		host = commands.getoutput(cmd)
		list=host.split()
		j=0
                my_dict2 = {}
		alertlist=[]
		for i in list:
		        dbconn = DB_Connector('192.168.27.100', 'dbchefrdonly', 'dbchefrdonly100', 'db_sysadmin')
		        sql = "select concat(replace(private_ip,'.','_'),'_',project) from tbl_infra where private_ip='% s'" % i
		        hostmod = dbconn.Execute(sql)
		        # check if ip address exists in infra table
		        if hostmod == "":
		 	       return ("The IP % s does not exist in the infra table") % i
			       exit()

		        # Format the result as per grafana
		        hostmod = hostmod.replace("/", "")
		        hostmod = hostmod.replace(" ", "")
			dc=getnode(i)
	                node=dc.loc()
        	        if node == 1:
			        db = MySQLdb.connect('192.168.37.253', 'grafins', 'grafins@253', 'grafana')
	                elif node == 2:
			        db = MySQLdb.connect('192.169.35.253', 'grafins', 'grafins@253', 'grafana')
                	elif node == 3:
                                db = MySQLdb.connect('192.168.37.137', 'grafins', 'grafins@253', 'grafana')
		        cursor = db.cursor()
		        sql1 = "select host,metric,status,thrshval,curval,ack,classification,tktno,unix_timestamp(alert_time),'%s' as ip,metric_variable from alert_log where host='%s' limit %s offset %s" % (i,hostmod,self.lmt,self.ofst)
			cursor.execute(sql1)
			result1 = cursor.fetchall()
		        sql2 = "select count(1) from alert_log where host='%s'" %(hostmod)
		        cursor.execute(sql2)
		        result2 = cursor.fetchone()[0]
			j=result2+j
        		my_dict3 = {}
		        if result2 == 0:
		          my_dict3["status"] = 1
		        elif result2 > 0:
		          my_dict3["status"] = 0

		        list1 = []
		        for row in result1:
		            my_dict = {}
		            my_dict["host"] = row[0]
		            my_dict["metric"] = row[1]
		            my_dict["status"] = row[2]
		            my_dict["thrshval"] = row[3]
		            my_dict["curval"] = row[4]
		            my_dict["ack"] = row[5]
		            my_dict["classification"] = row[6]
		            my_dict["tktno"] = row[7]
		            my_dict["alert_time"] = row[8]
		            my_dict["ip"]=row[9]
		            my_dict["metric_variable"]=row[10]
		            list1.append(my_dict)
        	 	my_dict2["Count"] = j
                alertlist.append(my_dict2)
                alertlist.append(my_dict3)
                alertlist.append(list1)
		alertlist.reverse()	
		return alertlist
	else:
        	return ("The VIP % s does not exist in the infra table") % self.hst
		exit()
