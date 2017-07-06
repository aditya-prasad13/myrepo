#!/usr/bin/python
from db_conn import DB_Connector


class getnode(object):

  def __init__(self,host):
    self.hst = host
    self.loc()

  def loc(self):
    dbconn=DB_Connector('192.168.42.112','invent','invent#123','inventory')
    sql="select node from ip_node where ip='% s'" % self.hst
    result=dbconn.Execute(sql)
    return result
