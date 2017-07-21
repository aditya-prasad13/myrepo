#!/usr/bin/python

import pymysql


class Addnode(object):
    def __init__(self, ip=None):
        self.ip = ip
        self.node_add()

    def node_add(self):
        if self.ip is None:
            return "IP not entered."

        rslt_node = ''
        db_112 = pymysql.connect(host='192.168.42.112', user='grafins', passwd='grafins@253', db='inventory')
        cursor_112 = db_112.cursor()
        chk_ip_sql = "select influx_node from ip_node where ip='%s'" % self.ip
        cursor_112.execute(chk_ip_sql)
        if cursor_112.rowcount > 0:
            rslt_node = cursor_112.fetchone()[0]

        # get location and server template from infra table
        db_100 = pymysql.connect(host='192.168.27.100', user='dbchefrdonly', passwd='dbchefrdonly100', db='db_sysadmin')
        cursor_100 = db_100.cursor()

        get_info_sql = "select location,template from tbl_infra where private_ip='%s'" % self.ip
        cursor_100.execute(get_info_sql)
        get_info_reslt = cursor_100.fetchone()
        loc = get_info_reslt[0]
        tmpl = get_info_reslt[1]

        mod_ip = self.ip.replace(".", "_")
        nodelst = ["192.168.37.253", "192.169.35.253", "192.168.37.137", "172.26.102.12"]

        on_node = ''
        insrt_chk = 0
        for i in nodelst:
            db_temp = pymysql.connect(host=i, user='grafins', passwd='grafins@253', db='grafana')
            tmp_cursor = db_temp.cursor()
            chk_ip_sql = "select 1 from dashboard where title like '%s%%'" % mod_ip
            tmp_cursor.execute(chk_ip_sql)
            if tmp_cursor.rowcount > 0:
                chk_ip_rslt = tmp_cursor.fetchone()[0]
                if chk_ip_rslt == 1:
                    on_node = i
                    insrt_chk = 1
                    break

        node = ''
        influx_node = ''

        if loc == 'VSNL' and tmpl == 'Database':
            node = 1
            influx_node = '192.168.37.253'
        elif loc == 'VSNL' and tmpl != 'Database':
            node = 3
            influx_node = '192.168.37.137'
        elif loc == 'NetMagic' and tmpl == 'Database':
            node = 2
            influx_node = '192.169.35.253'
        elif loc == 'NetMagic' and tmpl != 'Database':
            node = 4
            influx_node = '172.26.102.12'

        if rslt_node == on_node and on_node == influx_node:
            return "%s entry already exists" % self.ip

        if insrt_chk == 1 and node != '' and influx_node == on_node:
            insrt_sql = "insert into ip_node(ip,node,influx_node) values ('%s',%s,'%s')" % (self.ip, node, influx_node)
            cursor_112.execute(insrt_sql)
            db_112.commit()
        elif insrt_chk == 1 and node != '' and influx_node != on_node:
            return "%s is on node %s,when it should be on %s" % (self.ip, on_node, influx_node)

        if insrt_chk == 0:
            return "%s does not exist on any of the telegraf nodes.Check if telegraf is installed/configured " \
                   "correctly." % self.ip
