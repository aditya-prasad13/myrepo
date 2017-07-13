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
from get_srv_location import getloc

class mon_install(restful.Resource):

  def get(self):
    args = request.args
    self.hst = args['host']
    self.usr = 'root'
    self.pwd= '112@$mcitY6'
    #self.pwd= 'tooroot'
    x=self.add_mon()
    return x

  def add_mon(self):
    uipprj = ''
    gipprj = ''
    #get server location.
    dc=getloc(self.hst)
    location=dc.loc()
    
    #check if IP is already in monitoring
    dbconn=DB_Connector('192.168.27.100','dbchefrdonly','dbchefrdonly100','db_sysadmin')
    sql="select concat(replace(private_ip,'.','_'),'_',project) from tbl_infra where private_ip='% s'" % self.hst
    uipprj = dbconn.Execute(sql)

    #check if ip address exists in infra table
    if uipprj == "":
        return("The IP % s does not exist in the infra table") % self.hst
        exit()
   
    #Format the result as per grafana 
    uipprj = uipprj.replace("/","")
    uipprj = uipprj.replace(" ","")

    if location == 'VSNL':
      dbconn=DB_Connector('192.168.37.137','grafins','grafins@253','grafana')
    elif location == 'NetMagic':
      dbconn=DB_Connector('172.26.102.12','grafins','grafins@253','grafana')  
      
    sql1="select slug from dashboard where org_id=2 and slug='% s'" % uipprj
    gipprj=dbconn.Execute(sql1)
    
    if uipprj.lower() == gipprj.lower():
        return "The IP % s is already added in monitoring." % self.hst
        exit()
    
    #add chef hostname in the hosts file
    connection = ssh(self.hst,self.usr,self.pwd)
    command='if [[ ! `cat /etc/hosts|grep "192.168.33.151"` ]];then echo "192.168.33.151 sysaddb33151.timesgroup.com" >> /etc/hosts;fi'
    connection.sendCommand(command)
    
    #run chef script to install telegraf and add to monitoring            
    connection = ssh("192.168.33.151", "root", "151##McitY6")
    command='knife cookbook upload -a && knife bootstrap %s --ssh-user %s --ssh-password \'%s\' --node-name %sPROD -r "recipe[telegraf]" -y' %(self.hst,self.usr,self.pwd,self.hst)
    connection.sendCommand(command)
    
    #check if insert in grafana table for monitoring
    sql2="select count(1) from dashboard where org_id=2 and slug='% s'" % uipprj
    chk=dbconn.Execute(sql2)
    
    if chk == 1:
      return "success"
    else:
      return "failed.Kindly check logs."
