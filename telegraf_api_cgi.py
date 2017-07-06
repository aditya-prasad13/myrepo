#!/usr/bin/python
#http://192.168.33.151:8082/cgi-bin/telegraf_api_cgi.py?hostip=X.X.X.X

import sys
import MySQLdb
import cgi, cgitb
from paramiko import client

print 'Content-Type: text/plain\r\n\r\n'

conn=MySQLdb.connect('192.168.27.100','dbchefrdonly','dbchefrdonly100','db_sysadmin')
cursor=conn.cursor()

conn1=MySQLdb.connect('192.168.37.253','grafins','grafins@253','grafana')
cursor1=conn1.cursor()

class ssh:
    client = None
    
    def __init__(self, address, username, password):
	    # Let the user know we're connecting to the server
	    print("Connecting to server.")
	    # Create a new SSH client
	    self.client = client.SSHClient()
	    # The following line is required if you want the script to be able to access a server that's not yet in the known_hosts file
	    self.client.set_missing_host_key_policy(client.AutoAddPolicy())
	    # Make the connection
	    self.client.connect(address, username=username, password=password, look_for_keys=False)
	
    def sendCommand(self, command):
	    # Check if connection is made previously
	    if(self.client):
		stdin, stdout, stderr = self.client.exec_command(command)
		while not stdout.channel.exit_status_ready():
		    # Print stdout data when available
		    if stdout.channel.recv_ready():
			# Retrieve the first 1024 bytes
			alldata = stdout.channel.recv(1024)
			while stdout.channel.recv_ready():
			    # Retrieve the next 1024 bytes
			    alldata += stdout.channel.recv(1024)
    
			# Print as string with utf8 encoding
			print(str(alldata).encode('utf8'))
	    else:
		print("Connection not opened.")    

# Create instance of FieldStorage 
form = cgi.FieldStorage()

#Get data from Fields 
hst = form.getvalue('hostip')
#usr= form.getvalue('user')
#pwd= form.getvalue('passwd')

usr= 'root'
pwd= 'tooroot'

#check if IP is already in monitoring
sql="select concat(replace(private_ip,'.','_'),'_',project) from tbl_infra where private_ip='% s'" % hst
cursor.execute(sql)
uipprj=cursor.fetchone()[0]

sql1="select slug from dashboard where org_id=1 and slug='% s'" % uipprj
cursor1.execute(sql1)
gipprj=cursor1.fetchone()[0]

if uipprj.lower() == gipprj:
    print "The IP % s is already added in monitoring." % hst
    exit()

#add chef hostname in the hosts file
connection = ssh(hst,usr,pwd)
command='if [[ ! `cat /etc/hosts|grep "192.168.33.151"` ]];then echo "192.168.33.151 sysaddb33151.timesgroup.com" >> /etc/hosts;fi'
connection.sendCommand(command)
            
connection = ssh("192.168.33.151", "root", "151##McitY6")
command='knife cookbook upload -a;knife bootstrap %s --ssh-user %s --ssh-password \'%s\' --node-name %sPROD -r "recipe[telegraf_api]" -y' %(hst,usr,pwd,hst)
connection.sendCommand(command)

