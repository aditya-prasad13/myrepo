#!/usr/bin/python

from flask import Flask, jsonify, abort, make_response
from flask import request
from flask import render_template
import flask_restful as restful
from get_srv_location import getloc
from get_node import getnode
from db_conn import DB_Connector
import MySQLdb
import commands
import json

class alert_stat(restful.Resource):


    def get(self):
        args = request.args
        self.hst = args['host']
        self.lmt = args['limit']
        self.ofst = args['offset']
        x=self.status()
        return x

    def status(self):
        hostmod = ''

        cmd = """mysql -h192.168.27.100 -P 3306 -uroot -pl0bstEr db_sysadmin -Bse "select concat(concat(private_ip,'_'),PROJECT) from tbl_infra where PRIVATE_IP='%s' " """ % (self.hst)
        hostmod = commands.getoutput(cmd)
        hostmod = hostmod.replace(".", "_")
        hostmod = hostmod.replace(" ", "")

        #dbconn = DB_Connector('192.168.27.100', 'dbchefrdonly', 'dbchefrdonly100', 'db_sysadmin')
        #sql = "select concat(replace(private_ip,'.','_'),'_',project) from tbl_infra where private_ip='% s'" % self.hst
        #hostmod = dbconn.Execute(sql)

        # check if ip address exists in infra table
        #if hostmod == "":
            #return ("The IP % s does not exist in the infra table") % self.hst
            #exit()

        # Format the result as per grafana
        #hostmod = hostmod.replace("/", "")
        #hostmod = hostmod.replace(" ", "")

        dc=getnode(self.hst)
        node=dc.loc()
    
        if node == 1:
           db = MySQLdb.connect('192.168.37.253', 'grafins', 'grafins@253', 'grafana')
        elif node == 2:
           db = MySQLdb.connect('192.169.35.253', 'grafins', 'grafins@253', 'grafana')
        elif node == 3:
           db = MySQLdb.connect('192.168.37.137', 'grafins', 'grafins@253', 'grafana')
        #elif node == 4:
           #db = MySQLdb.connect('172.26.102.12', 'grafins', 'grafins@253', 'grafana')

        
        cursor = db.cursor()

        sql1 = "select host,metric,status,thrshval,curval,ack,classification,tktno,unix_timestamp(alert_time),'%s' as ip,metric_variable from alert_log where host='%s' limit %s offset %s" % (self.hst,hostmod,self.lmt,self.ofst)
	cursor.execute(sql1)
	result1 = cursor.fetchall()
	
        sql2 = "select count(1) from alert_log where host='%s'" %(hostmod)
        cursor.execute(sql2)
        result2 = cursor.fetchone()[0]

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
      
        my_dict2 = {}
        my_dict2["Count"] = result2

        finl_lst =[]
        finl_lst.append(my_dict3)         
        finl_lst.append(list1)         
        finl_lst.append(my_dict2)         

        return finl_lst
