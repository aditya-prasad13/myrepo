#!/usr/bin/python
from db_conn import DB_Connector


class getloc(object):

  def __init__(self,host):
    self.hst = host
    self.loc()

  def loc(self):
    dbconn=DB_Connector('192.168.27.100','dbchefrdonly','dbchefrdonly100','db_sysadmin')
    sql="select location from tbl_infra where private_ip='% s'" % self.hst
    result=dbconn.Execute(sql)
    return result
