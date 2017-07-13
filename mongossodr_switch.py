#!/usr/bin/python

import flask_restful as restful
import paramiko
import pymysql
import os
from pymongo import MongoClient


class sso_mongodrswitch(restful.Resource):
    def get(self):
        try:
            mysqldb = pymysql.connect("192.168.37.58", "DBmonitor", "DBmonitor@60", "practices")
        except:
            return "Unable to connect to mysql db on 192.168.37.58"
        cursor = mysqldb.cursor()
        sql_dr_mo = "select vip_address,location from drdbinfra where project_name='JSSO' and " \
                    "service_type='MongoDB' and current_status='dr_location'"
        cursor.execute(sql_dr_mo)
        result = cursor.fetchone()
        mongo_dr_ip_mo = result[0]
        mongo_dr_loc_mo = result[1]

        try:
            client = MongoClient(mongo_dr_ip_mo)
            client.admin.authenticate('root', 'mongor00t')
        except:
            return "Unable to connect to mongodb on %s" % mongo_dr_ip_mo
        mongodb = client.admin
        x = mongodb.command("replSetGetStatus")
        mo_lst = []
        prm = "none"
        for i in x['members']:
            ip = i['name']
            ip = ip.split(":")[0]
            # Get primary node
            if i['state'] == 1:
                prm = ip
            # Get all ips in the cluster
            mo_lst.append(ip)

        # retrun error if primary server variable is not set
        if prm == "none":
            return "Primary server could not be located"

        # Convert mongo ip list to usable format for sql input
        ip_mongo_all = ', '.join('"{0}"'.format(w) for w in mo_lst)

        mysqldb = pymysql.connect("192.168.37.58", 'DBmonitor', 'DBmonitor@60', 'DBmonitor_NetMagic')
        cursor = mysqldb.cursor()

        # Filter out the DR ips from the list
        f_mo_dr_lst = []
        sql = "select ip_address from DBmonitor_NetMagic.dbinfra where ip_address in (%s) and location='%s' " \
              "union select ip_address from DBmonitor_VSNL.dbinfra where ip_address in ( % s) and location = '%s'" \
              % (ip_mongo_all, mongo_dr_loc_mo, ip_mongo_all, mongo_dr_loc_mo)
        cursor.execute(sql)
        result = cursor.fetchall()
        for row in result:
            f_mo_dr_lst.append(row[0])

        client = MongoClient(mongo_dr_ip_mo)
        client.admin.authenticate('root', 'mongor00t')

        # Get array position for reconfig
        mongodb = client.admin
        y = mongodb.command("replSetGetConfig", 1)

        mmbr_lst = []
        for i in y['config']['members']:
            host_ip = i['host'].split(":")[0]
            mmbr_lst.append(host_ip)

        # create reconfig file
        f = open("/tmp/drconf_change.json", "w+")
        f.write("cfg = rs.conf()\r\n")

        cnt_dr = len(f_mo_dr_lst)
        for position, item in enumerate(mmbr_lst):
            if item in f_mo_dr_lst:
                if cnt_dr != 1:
                    priority = "cfg.members[%s].priority = 1\r\n" % position
                    hidden = "cfg.members[%s].hidden = 0\r\n" % position
                    votes = "cfg.members[%s].votes = 1\r\n" % position
                    f.write(priority)
                    f.write(hidden)
                    f.write(votes)
                    cnt_dr = cnt_dr - 1
                else:
                    priority = "cfg.members[%s].priority = 0\r\n" % position
                    hidden = "cfg.members[%s].hidden = 1\r\n" % position
                    votes = "cfg.members[%s].votes = 1\r\n" % position
                    f.write(priority)
                    f.write(hidden)
                    f.write(votes)

            else:
                if item == prm:
                    priority = "cfg.members[%s].priority = 0.8\r\n" % position
                    hidden = "cfg.members[%s].hidden = 0\r\n" % position
                    votes = "cfg.members[%s].votes = 1\r\n" % position
                    f.write(priority)
                    f.write(hidden)
                    f.write(votes)
                else:
                    priority = "cfg.members[%s].priority = 0\r\n" % position
                    hidden = "cfg.members[%s].hidden = 1\r\n" % position
                    votes = "cfg.members[%s].votes = 1\r\n" % position
                    f.write(priority)
                    f.write(hidden)
                    f.write(votes)

        f.write("rs.reconfig(cfg)")
        f.close()

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(prm, key_filename='/root/.ssh/112_rsa.pub')
        except:
            return "Connection to Primary server %s failed" % prm

        transfer = ssh.open_sftp()
        transfer.put('/tmp/drconf_change.json', '/tmp/drconf_change.json')
        transfer.close()

        command = 'mongo admin -uroot -pmongor00t < /tmp/drconf_change.json && rm -f /tmp/drconf_change.json'
        stdin, stdout, stderr = ssh.exec_command(command)
        os.remove("/tmp/drconf_change.json")
        output = stdout.readlines()
        for res in output:
            if res.rstrip() == '{ "ok" : 1 }':
                try:
                    mysqldb = pymysql.connect("192.168.37.58", "DBmonitor", "DBmonitor@60", "practices")
                except:
                    return "DR Successful.Connect to 192.168.37.58 failed,unable to update current prod " \
                           "and dr locations."
                cursor = mysqldb.cursor()
                sql1 = "update drdbinfra set current_status='dr_location' where project_name='JSSO' " \
                       "and service_type='MongoDB' and location!='%s'" % mongo_dr_loc_mo
                sql2 = "update drdbinfra set current_status='prod_location' where vip_address='%s'" % mongo_dr_ip_mo
                try:
                    cursor.execute(sql1)
                    cursor.execute(sql2)
                    mysqldb.commit()
                except:
                    return "DR Successful,Update table on monitoring for current production and DR failed."
                return "DR Successful.%s is now PROD." % mongo_dr_loc_mo
        return "DR failed."
