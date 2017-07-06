#!/usr/bin/python

import flask_restful as restful
import requests
import paramiko
import MySQLdb
import os
from pymongo import MongoClient


class sso_mongodrswitch(restful.Resource):
    def get(self):
        # list of DR server cluster
        # clst='192.168.43.97,192.168.43.98,192.168.43.99,192.169.38.187,192.169.38.188,192.169.38.189'
        #drlst = ['192.169.38.187', '192.169.38.188', '192.169.38.189']

        db = MySQLdb.connect("192.168.37.58", "DBmonitor", "DBmonitor@60", "practices")
        cursor = db.cursor()
        sql_dr_MO = "select vip_address,location from drdbinfra where project_name='JSSO' and service_type='MongoDB' and current_status='dr_location'"
        cursor.execute(sql_dr_MO)
        result = cursor.fetchone()
        mongo_dr_ip_MO = result[0]
        mongo_dr_loc_MO = result[1]
        
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
        sql = "select ip_address from DBmonitor_NetMagic.dbinfra where ip_address in (%s) and location='%s' union select ip_address from DBmonitor_VSNL.dbinfra where ip_address in ( % s) and location = '%s'" %(ip_mongo,mongo_dr_loc_MO,ip_mongo,mongo_dr_loc_MO)
        cursor.execute(sql)
        result = cursor.fetchall()
        for row in result:
          f_mo_dr_lst.append(row)

        drlst = f_mo_dr_lst
        drip = ''
        prm = ''
        for i in drlst:
            url = 'http://192.168.42.112:5000/health?host=%s' % i
            try:
                hres = requests.get(url)
                hlth_chk = hres.json()
            except:
                hlth_chk = ''
            if hlth_chk == 'Okay':
                drip = i

        # find primary node
        client = MongoClient(drip)
        client.admin.authenticate('root', 'mongor00t')
        db = client.admin
        x = db.command("replSetGetStatus")
        for i in x['members']:
            if i['state'] == 1:
                prm = i['name']
        prm = prm.split(":")[0]

        # create reconfig file
        f = open("/tmp/drconf_change.json", "w+")
        f.write("cfg = rs.conf()\r\n")
        f.write("cfg.members[0].priority = 0\r\n")
        f.write("cfg.members[0].hidden = 1\r\n")
        f.write("cfg.members[0].votes = 1\r\n")
        f.write("cfg.members[1].priority = 0.8\r\n")
        f.write("cfg.members[1].hidden = 0\r\n")
        f.write("cfg.members[1].votes = 1\r\n")
        f.write("cfg.members[2].priority = 0\r\n")
        f.write("cfg.members[2].hidden = 1\r\n")
        f.write("cfg.members[2].votes = 1\r\n")
        f.write("cfg.members[3].priority = 1\r\n")
        f.write("cfg.members[3].hidden = 0\r\n")
        f.write("cfg.members[3].votes = 1\r\n")
        f.write("cfg.members[4].priority = 1\r\n")
        f.write("cfg.members[4].hidden = 0\r\n")
        f.write("cfg.members[4].votes = 1\r\n")
        f.write("cfg.members[5].priority = 0\r\n")
        f.write("cfg.members[5].hidden = 1\r\n")
        f.write("cfg.members[5].votes = 1\r\n")
        f.write("rs.reconfig(cfg)")
        f.close()

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(prm, key_filename='/root/.ssh/112_rsa.pub')
        except:
            return "Connection to Primary server %s failed" % prm
            exit()

        transfer = ssh.open_sftp()
        transfer.put('/tmp/drconf_change.json', '/tmp/drconf_change.json')
        transfer.close()

        command = 'mongo admin -uroot -pmongor00t < /tmp/drconf_change.json && rm -f /tmp/drconf_change.json'
        try:
            stdin, stdout, stderr = ssh.exec_command(command)
            os.remove("/tmp/drconf_change.json")
            return stdout.readlines()
            #return stderr.readlines()
        except:
            return "Error"

