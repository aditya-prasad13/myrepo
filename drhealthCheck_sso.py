#!/usr/bin/python

from flask import Flask, jsonify, abort, make_response
from flask import request
from flask import render_template
import flask_restful as restful
import pymongo, yaml, sys, json
import requests
import MySQLdb
import re
from paramiko import client
from pymongo import MongoClient


# from db_conn import DB_Connector

class Ssh:
    client = None

    def __init__(self, address):
        username = 'root'
        # keyfile = '/root/.ssh/id_dsa.pub'
        # Create a new SSH client
        self.client = client.SSHClient()
        self.client.set_missing_host_key_policy(client.AutoAddPolicy())
        # Make the connection
        self.client.connect(address, username=username, password='185$#McitY7')

    def sendcommand(self, command):
        # Check if connection is made previously
        if self.client:
            stdin, stdout, stderr = self.client.exec_command(command)
            err = stderr.read()
            odata = stdout.read()
            if err:
                return err
            elif odata:
                return odata
        else:
            return "Connection not opened."


class CheckDRhealth_sso(restful.Resource):
    # @requires_auth
    def post(self):
        try:
            if 'Content-Type' not in request.headers:
                return make_response(jsonify(
                    {"status": "Header Content-Type is missing in request"}), 401)
            if request.headers['Content-Type'] != 'application/json':
                return make_response(jsonify(
                    {"status": "Your Content-Type is not set to application/json"}), 401)
            else:
                self.content = request.get_json(silent=True, force=True)
                # print self.content
                result = self.getDRhealth_sso()
                return result
        except Exception as e:
            print e

    def getDRhealth_sso(self):
        Health_All = []

        ## Check MariaDB Health

        db = MySQLdb.connect("192.168.37.58", "DBmonitor", "DBmonitor@60", "practices")
        cursor = db.cursor()

        sql_dr_MA = "select vip_address,location from drdbinfra where project_name='JSSO' and service_type='Maxscale' and current_status='dr_location'"
        cursor.execute(sql_dr_MA)
        getresult = cursor.fetchone()
        maxscale_dr_ip_MA = getresult[0]
        maxscale_dr_loc_MA = getresult[1]

        sql_dr_MO = "select vip_address,location from drdbinfra where project_name='JSSO' and service_type='MongoDB' and current_status='dr_location'"
        cursor.execute(sql_dr_MO)
        result = cursor.fetchone()
        mongo_dr_ip_MO = result[0]
        mongo_dr_loc_MO = result[1]

        re_lst = []
        sql_dr_RE = "select vip_address,location from drdbinfra where project_name='JSSO' and service_type='RedisDB' and current_status='dr_location'"
        cursor.execute(sql_dr_RE)
        result_re = cursor.fetchall()
        for row in result_re:
            re_lst.append(row[0])
            re_loc = row[1]

        connection = Ssh("192.168.34.185")

        command = "/usr/bin/maxadmin -h%s -pmariadb show servers|grep 'Server:'|awk '{print $2}'|paste -d, -s" % (
            maxscale_dr_ip_MA)
        drserver_list_MA = connection.sendcommand(command)
        drserver_list_MA = drserver_list_MA.rstrip()
        drserver_list_MA = drserver_list_MA.split(",")

        # ssh conn to 33.185 and run command to check lag
        lst = []
        for i in drserver_list_MA:
            result_MA = ''
            hlth_chk_MA = ''
            my_dct_MA = {}
            connection = Ssh("192.168.34.185")
            command = '/usr/bin/mysql -P 3309 -h%s -uDBmonitor -p"DBmonitor@60" -Bse "show slave status\G"|grep "Seconds_Behind_Master:"|awk "{print \$2}"' % i
            result_MA = connection.sendcommand(command)[0]
            # call health check api to get OK
            url = 'http://192.168.42.112:5000/health?host=%s' % i
            try:
                hres = requests.get(url)
                hlth_chk_MA = hres.json()
            except:
                hlth_chk_MA = ''
            my_dct_MA[i] = hlth_chk_MA
            lst.append(my_dct_MA)
            Health_MA = {}
            Health_MA['MariaDB DR Cluster'] = {}
            if result_MA != '0' or hlth_chk_MA != 'Okay':
                Health_MA['MariaDB DR Cluster'][
                    'Health'] = 'MariaDB Cluster'
                Health_MA['MariaDB DR Cluster']['Status'] = '1'
                break
            else:
                Health_MA['MariaDB DR Cluster'][
                    'Health'] = 'MariaDB Cluster'
                Health_MA['MariaDB DR Cluster']['Status'] = '0'

                ## End MariaDB Health

        Health_MA['MariaDB DR Cluster']['Location'] = maxscale_dr_loc_MA
        #Health_All.append(Health_MA)
        Health_All.append(Health_MA['MariaDB DR Cluster'])

        ## Check MongoDB Health
        client = MongoClient(mongo_dr_ip_MO)
        client.admin.authenticate('root', 'mongor00t')
        db = client.admin
        x = db.command("replSetGetStatus")
        mo_lst = []
        for i in x['members']:
            ip = i['name']
            ip = ip.split(":")[0]
            mo_lst.append(ip)

        ip_mongo = ', '.join('"{0}"'.format(w) for w in mo_lst)

        db = MySQLdb.connect("192.168.37.58", 'DBmonitor', 'DBmonitor@60', 'DBmonitor_NetMagic')
        cursor = db.cursor()

        f_mo_dr_lst = []

        sql = "select ip_address from DBmonitor_NetMagic.dbinfra where ip_address in (%s) and location='%s' union select ip_address from DBmonitor_VSNL.dbinfra where ip_address in ( % s) and location = '%s'" % (
        ip_mongo, mongo_dr_loc_MO, ip_mongo, mongo_dr_loc_MO)
        cursor.execute(sql)
        result = cursor.fetchall()
        for row in result:
            f_mo_dr_lst.append(row)

        hlth = 0
        for i in f_mo_dr_lst:
            url = 'http://192.168.42.112:5000/health?host=%s' % i
            try:
                hres = requests.get(url)
                hlth_chk = hres.json()
            except:
                hlth_chk = ''
            if hlth_chk != 'Okay':
                hlth = 1
                break

        Health_MO = {}
        Health_MO['MongoDB DR Cluster'] = {}
        if hlth == 0:
            Health_MO['MongoDB DR Cluster']['Health'] = 'MongoDB Cluster'
            Health_MO['MongoDB DR Cluster']['Status'] = '0'
        if hlth == 1:
            Health_MO['MongoDB DR Cluster'][
                'Health'] = 'MongoDB Cluster'
            Health_MO['MongoDB DR Cluster']['Status'] = '1'

        Health_MO['MongoDB DR Cluster']['Location'] = mongo_dr_loc_MO
        #Health_All.append(Health_MO)
        Health_All.append(Health_MO['MongoDB DR Cluster'])
        
        ## End MongoDB Health
        
        #Check Redis health
        hlth_re = 0
        for i in re_lst:
            url = 'http://192.168.42.112:5000/health?host=%s' % i
            try:
                hres = requests.get(url)
                hlth_chk = hres.json()
            except:
                hlth_chk = ''
            if hlth_chk != 'Okay':
                hlth_re = 1
                break

        Health_RE = {}
        Health_RE['Redis DR Cluster'] = {}
        if hlth_re == 0:
            Health_RE['Redis DR Cluster']['Health'] = 'Redis Cluster'
            Health_RE['Redis DR Cluster']['Status'] = '0'
        if hlth_re == 1:
            Health_RE['Redis DR Cluster']['Health'] = 'Redis Cluster'
            Health_RE['Redis DR Cluster']['Status'] = '1'

        Health_RE['Redis DR Cluster']['Location'] = re_loc
        #Health_All.append(Health_RE)
        Health_All.append(Health_RE['Redis DR Cluster'])
    

        # Health_All.append(Health_MO)

        # Health_All = Health_MA.update(Health_MO)

        return Health_All
        exit()


