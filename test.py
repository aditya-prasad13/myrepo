#!/usr/bin/python
#http://192.168.38.66/cgi-bin/test.py?ip=xx.xx.xx.xx

import cgi, cgitb
import paramiko
import sys
import mysql.connector
import json
import urllib2
import urllib
import os
import subprocess
import commands
import MySQLdb
from os import system

print 'Content-Type: text/plain\r\n\r\n'

# Create instance of FieldStorage
form = cgi.FieldStorage()

#Get ip from url
ip = form.getvalue('ip')

#cmd='''mysql -h192.168.27.100 -P 3306 -uroot -pl0bstEr db_sysadmin -Bse """"select concat(concat(private_ip,'_'),PROJECT) from tbl_infra where PRIVATE_IP=%s """, [ip]  
#output = commands.getoutput(cmd)
#output1=output.replace(".", "_")
#print output1



# Create a connection object and create a cursor
Con = MySQLdb.Connect(host="192.168.27.100", port=3306, user="root", passwd="l0bstEr", db="db_sysadmin")
Cursor = Con.cursor()

# Make SQL string and execute it
Cursor.execute ("select concat(concat(private_ip,'_'),PROJECT) from tbl_infra where PRIVATE_IP=%s ", [ip])


# Fetch all results from the cursor into a sequence and close the connection
Results = Cursor.fetchone()[0]
Results=Results.replace(".", "_")
Results=Results.replace(" ", "")
Results=Results.replace("""/""", "_")
print Results
Con.close()
