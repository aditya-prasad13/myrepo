#!/usr/bin/python

from flask import Flask, jsonify, abort, make_response
from flask import request
from flask import render_template
import flask_restful as restful
from get_srv_location import getloc
from db_conn import DB_Connector
import MySQLdb
import json

class dbBackup_stat(restful.Resource):


    def get(self):
        iplist = ''
        args = request.args
        self.usr = args['username']
        self.lmt = args['limit']
        self.ofst = args['offset']
        self.srtme = args['start_time']
        self.endtme = args['end_time']
        x=self.status()
        return x

    def status(self):

        dbconn = MySQLdb.connect('192.168.27.100', 'dbchefrdonly', 'dbchefrdonly100', 'db_sysadmin')
        sql_1 = "SELECT a.ip FROM PCLI_INFRA a, AD_ACCESS b WHERE a.PROJECT=b.PROJECT AND b.EMAIL='%s'" % (self.usr + "@timesinternet.in") 
        cursor_1 = dbconn.cursor()
        cursor_1.execute(sql_1)
        result_1 = cursor_1.fetchall()
        
        list_1 = []
        for row_1 in result_1:
            list_1.append(row_1[0])

        #return list_1
        #exit()

       
        if len(list_1) == 0:
           abort(400, 'INVALID USERNAME OR USERNAME DOES NOT HAVE REQUIRED ACCESS')  # No data found
           #raise BadRequest('My custom message')

        
	ip_list = str(list_1)[1:-1]        
        #return ip_list

        dbconn_2 = MySQLdb.connect('192.168.37.58', 'DBmonitor', 'DBmonitor@60', 'DBmonitor_VSNL')
        sql_2 = "SELECT * FROM (SELECT serverip, backuptype, fullbackupstatus, incrementalbackupstatus_1, incrementalbackupstatus_2, UNIX_TIMESTAMP(DateTime) as DT FROM DBmonitor_VSNL.dbbackupdata WHERE serverip IN (%s) AND UNIX_TIMESTAMP(DateTime) > '%s' AND UNIX_TIMESTAMP(DateTime) < '%s' UNION SELECT serverip, backuptype, fullbackupstatus, incrementalbackupstatus_1, incrementalbackupstatus_2, UNIX_TIMESTAMP(DateTime) as DT FROM DBmonitor_NetMagic.dbbackupdata WHERE serverip IN (%s) AND UNIX_TIMESTAMP(DateTime) > '%s' AND UNIX_TIMESTAMP(DateTime) < '%s') AS Ux GROUP BY Ux.DT ORDER BY Ux.DT DESC limit %s offset %s" % (ip_list,self.srtme,self.endtme,ip_list,self.srtme,self.endtme,self.lmt,self.ofst)

        #return sql_2
        #exit() 

        cursor_2 = dbconn_2.cursor()
        cursor_2.execute(sql_2)
        result_2 = cursor_2.fetchall()


        #return result_2
        #exit()
        
        list_t = []
        for row in result_2:
            my_dict = {}
            my_dict["serverip"] = row[0]
            my_dict["backuptype"] = row[1]
            my_dict["fullbackupstatus"] = row[2]
            my_dict["incrementalbackupstatus_1"] = row[3]
            my_dict["incrementalbackupstatus_2"] = row[4]
            my_dict["DateTime"] = row[5]
            my_dict["Status"] = 'OK'
            list_t.append(my_dict)
      
        #return list_t
        #exit()
       
        my_dict2 = {}
        #db = MySQLdb.connect('192.169.35.253', 'grafins', 'grafins@253', 'grafana')
        sql_3 = "SELECT count(1) FROM DBmonitor_VSNL.dbbackupdata WHERE serverip IN (%s) AND UNIX_TIMESTAMP(DateTime) > '%s' AND UNIX_TIMESTAMP(DateTime) < '%s'" % (ip_list,self.srtme,self.endtme)
        

        #return sql_3
        #exit()

        cursor_2.execute(sql_3)
        result_3 = cursor_2.fetchone()[0]


        my_dict2["Count"] = result_3

        my_dict3 = {}
        if len(result_2) == 0:
          my_dict3["status"] = 1
        elif len(result_2) > 0:
          my_dict3["status"] = 0 

        finl_lst =[]
        finl_lst.append(my_dict3)         
        finl_lst.append(list_t)         
        finl_lst.append(my_dict2)         

        return finl_lst 
