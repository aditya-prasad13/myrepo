#!/usr/bin/python
import MySQLdb


class DB_Connector(object):

  """ Humble Database Connection Class """
  def __init__(self,host,user,passwd,db):
    self.host = host
    self.user = user
    self.passwd = passwd
    self.db = db
    self.CreateConnection()

  def CreateConnection(self):
    self.connection = MySQLdb.connect(self.host,self.user,self.passwd,self.db)

  def DestroyConnection(self):
    self.connection.close()

  def Execute(self, sql_statement):
    cursor = self.connection.cursor()
    cursor.execute(sql_statement)
    if  cursor.rowcount > 0:
      result = cursor.fetchone()[0]
      cursor.close()
      return result
    else:
      return ""
