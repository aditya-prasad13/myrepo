#!/usr/bin/python

import pymysql
import nmap
import subprocess
import time

scrpt_pth = "/root/scripts/DBmonitoring_new"
nm = nmap.PortScanner()

vsnl_mon_db = pymysql.connect(host='192.168.34.185', port=3306, user='dbchefusr', passwd='dbchefusr185',
                              db='DBmonitor_VSNL')
cursor_mon_vsnl = vsnl_mon_db.cursor()
all_mon_ip_sql = "select ip_address from dbinfra where (service_type='MariaDB' or service_type='MySQL') " \
                 "and is_alive='Yes' and is_production='Yes' and is_monitor='Yes' and service_alert ='Yes'"
cursor_mon_vsnl.execute(all_mon_ip_sql)
tmp_rslt = cursor_mon_vsnl.fetchall()
all_ip = []
for row in tmp_rslt:
    all_ip.append(row[0])

for ip in all_ip:
    # chk 3306
    nm.scan(ip, '3306')
    chk_3306 = nm[ip].tcp(3306)['state']

    # chk 3309
    nm.scan(ip, '3309')
    chk_3309 = nm[ip].tcp(3309)['state']

    myport = "None"
    if chk_3309 == 'open':
        myport = 3309
    elif chk_3306 == 'open':
        myport = 3306

    chk_var = ''
    if myport is not None:
        # chk mysql login
        chk_db_conn = pymysql.connect(host=ip, port=myport, user='DBmonitor', passwd='DBmonitor@60', db='mysql')
        cursor_chk_db = chk_db_conn.cursor()
        chk_sql = "select 1 from dual"
        cursor_chk_db.execute(chk_sql)
        chk_var = cursor_chk_db.fetchone()[0]

    if chk_var != 1:
        cur_time = time.ctime()
        cur_time = cur_time + '\r\n'

        mysql_port_status = ''
        if chk_3309 == 'open' or chk_3306 == 'open':
            mysql_port_status = "NOTE:MySQL port seems UP but login has timed-out/failed.\r\nKindly check server " \
                                "load and disk space as well\r\n"

        emailid_sql = "select email_1,email_2,email_3 from dbinfra where ip_address='%s'" % ip
        cursor_mon_vsnl.execute(emailid_sql)
        emltmp = cursor_mon_vsnl.fetchmany(3)[0]
        eml1 = emltmp[0]
        eml2 = emltmp[1]
        eml3 = emltmp[2]

        alrt_ins_sql = "insert into dbalerts(ipaddress,alert_type) values ('%s','mysql_service')" % ip
        cursor_mon_vsnl.execute(alrt_ins_sql)
        vsnl_mon_db.commit()

        alrt_cnt_sql = "select count(1) from dbalerts where ipaddress='%s' and alert_type='mysql_service'" % ip
        cursor_mon_vsnl.execute(alrt_cnt_sql)
        alrt_cnt = cursor_mon_vsnl.fetchone()[0]

        # collate all above alert info into file
        fname = "%s/DBalert/CheckMySQL_%s.txt" % (scrpt_pth, ip)
        f = open(fname, "w+")
        f.write(cur_time)
        f.write(mysql_port_status)
        f.close()

        if alrt_cnt != 2:
            mail_cmd = 'cat %s|mutt -e "set from=root@VSNL-DBMon34185.in realname=\"root\"" -s ' \
                       '"AUTO:Check MySQL Service on %s" %s' % (fname, ip, eml1)
            send_mail = subprocess.Popen(mail_cmd, shell=True)
            send_mail.communicate()
            print "send mail to dbadmin"
        if alrt_cnt == 2:
            mail_cmd = 'cat %s|mutt -e "set from=root@VSNL-DBMon34185.in realname=\"root\"" -s ' \
                       '"AUTO:Check MySQL Service on %s" %s' % (fname, ip, eml1 + ' ' + eml2)
            send_mail = subprocess.Popen(mail_cmd, shell=True)
            send_mail.communicate()
            print "send mail to tilalerts and dbadmin"
