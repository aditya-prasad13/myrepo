#!/usr/bin/python

import flask_restful as restful
from paramiko import client
import requests
import re
import MySQLdb


class Ssh:
    client = None

    def __init__(self, address):
        username = 'root'
        keyfile = '/root/.ssh/112_rsa.pub'
        # Create a new SSH client
        self.client = client.SSHClient()
        self.client.set_missing_host_key_policy(client.AutoAddPolicy())
        # Make the connection
        self.client.connect(address, username=username, key_filename=keyfile)

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


class sso_redisdrswitch(restful.Resource):

    def get(self):
        db = MySQLdb.connect("192.168.37.58","DBmonitor","DBmonitor@60","practices")
        cursor = db.cursor()

        re_lst = []
        sql_dr_RE = "select vip_address from drdbinfra where project_name='JSSO' and service_type='RedisDB' and current_status='dr_location'"
        cursor.execute(sql_dr_RE)
        result_re = cursor.fetchall()
        for row in result_re:
            re_lst.append(row[0])

        # Check Redis health
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

        if hlth_re == 0:
            for i in re_lst:
                connection = Ssh(i)
                command = 'sed -i "s,^slaveof,#slaveof," /etc/redis.conf'
                out = connection.sendcommand(command)
                
            return "Redis DR completed."
        
        return "Redis DR failed,check server health"
