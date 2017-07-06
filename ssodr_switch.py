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


class sso_maxdrswitch(restful.Resource):

    def get(self):
        db = MySQLdb.connect("192.168.37.58","DBmonitor","DBmonitor@60","practices")
        cursor = db.cursor()

        sql = "select vip_address from drdbinfra where project_name='JSSO' and service_type='Maxscale' and current_status='prod_location'"
        cursor.execute(sql)
        maxscale_ip = cursor.fetchone()[0]

        sql2 = "select vip_address from drdbinfra where project_name='JSSO' and service_type='Maxscale' and current_status='dr_location'"
        cursor.execute(sql2)
        maxscale_dr_ip = cursor.fetchone()[0]

        connection = Ssh("192.168.34.185")
        command = "/usr/bin/maxadmin -h%s -pmariadb show servers|grep 'Server:'|awk '{print $2}'|paste -d, -s" % (maxscale_ip)
        prodserver_list = connection.sendcommand(command)
        prodserver_list = prodserver_list.rstrip()
        prodserver_list = prodserver_list.split(",")

        command = "/usr/bin/maxadmin -h%s -pmariadb show servers|grep 'Server:'|awk '{print $2}'|paste -d, -s" % (maxscale_dr_ip)
        drserver_list = connection.sendcommand(command)
        drserver_list = drserver_list.rstrip()
        drserver_list = drserver_list.split(",")

        full_list = prodserver_list + drserver_list
        clst = ''
        for i in full_list:
          clst = clst + i +':3309,'
        clst = re.sub(",$","",clst)
        
        # list of DR server cluster
        #clst = '192.168.43.94:3309,192.168.43.95:3309,192.168.43.96:3309,192.169.38.184:3309,192.169.38.185:3309,192.169.38.186:3309'
        #drlst = ['192.169.38.184', '192.169.38.185', '192.169.38.186']
 
        clst = clst
        drlst = drserver_list

        # ssh conn to 33.185 and run command to check lag
        lst = []
        for i in drlst:
            result = ''
            hlth_chk = ''
            my_dct = {}
            connection = Ssh("192.169.33.185")
            command = '/usr/bin/mysql -P 3309 -h%s -uDBmonitor -p"DBmonitor@60" -Bse "show slave status\G"|grep "Seconds_Behind_Master:"|awk "{print \$2}"' % i
            result = connection.sendcommand(command)[0]
            # call health check api to get OK
            url = 'http://192.168.42.112:5000/health?host=%s' % i
            try:
                hres = requests.get(url)
                hlth_chk = hres.json()
            except:
                hlth_chk = ''
            my_dct[i] = hlth_chk
            lst.append(my_dct)
            #if result == '0' and hlth_chk == 'Okay':
            if result == '0':
                drip = i
                # invoke replication manager with preferred master as DR ip
                try:
                    connection = Ssh(drip)
                except:
                    return "Connection to DR server %s failed" % drip
                    exit()
                command = '/usr/local/bin/replication-manager --user=maxusr:maxadminpwd --rpluser=replicausr:replicausr --hosts=%s --prefmaster=%s:3309 --readonly=true --switchover=keep --interactive=false --logfile=/tmp/repmgr.log' % (clst, drip)
                chkstr = "Master switch on %s:3309 complete" % drip
                out = ''
                try:
                    out = connection.sendcommand(command)
                    if chkstr in out:
                      db = MySQLdb.connect("192.168.37.58","DBmonitor","DBmonitor@60","practices")
                      cursor = db.cursor()
                      sql1="update drdbinfra set current_status='dr_location' where vip_address='%s'" % maxscale_ip
                      sql2="update drdbinfra set current_status='prod_location' where vip_address='%s'" % maxscale_dr_ip
                      cursor.execute(sql1)
                      cursor.execute(sql2)
                      db.commit()
                      return i + " set as dr master"
                except:
                    return "Error while issuing replication manager command"

        return lst
