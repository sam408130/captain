#-*- coding: utf-8 -*-

import logging
import traceback
import datetime
import platform
import os
from sqlhelper import SqlHelper
from sqlhelperOnline import SqlHelperOnline
from bs4 import CData
from bs4 import NavigableString
import re
import config

def make_dir(dir):
    log('make dir:%s' % dir)
    if not os.path.exists(dir):
        os.makedirs(dir)


def log(msg, level = logging.DEBUG):
    #logging.log(level, msg)
    print('%s [level:%s] msg:%s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), level, msg))

    if level == logging.WARNING or level == logging.ERROR:
        for line in traceback.format_stack():
            print(line.strip())

        for line in traceback.format_stack():
            logging.log(level, line.strip())


def get_first_text(soup, strip = False, types = (NavigableString, CData)):
    data = None
    for s in soup._all_strings(strip, types = types):
        data = s
        break
    return data


def get_texts(soup, strip = False, types = (NavigableString, CData)):
    texts = []
    for s in soup._all_strings(strip, types = types):
        texts.append(s)

    return texts


def get_platform():
    plat = platform.platform()
    if plat.find('Darwin') != -1:
        return 'mac'
    elif plat.find('Linux') != -1:
        return 'linux'
    else:
        return 'mac'


def get_date():
    return datetime.datetime.today().strftime('%Y-%m-%d')

def fix_item():
    command = "SELECT * from {0}".format(config.yishou_item_table,get_date())
    sql = SqlHelper()
    data = sql.query(command)
    for each in data:
        command = "SELECT * from {0} WHERE goods_id = \'{1}\'".format(config.yishou_activity_detail_table,each[1])
        item = sql.query_one(command)
        if item:
            command = "UPDATE {0} SET activity_id = \'{1}\' WHERE item_id=\'{2}\'".format(config.yishou_item_table,item[1],each[1])
            sql.execute(command)



def upload_data():

    log('start upload yishou activity')
    sql = SqlHelper()
    sql_online = SqlHelperOnline()
    command = "SELECT * from {0} WHERE special_start_time > \'{1}\'".format(config.yishou_activity_table,get_date())
    activities = sql.query(command)
    for each in activities:
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = (None,dt,'yishou',each[1],each[2],each[10],each[4],each[5])
        log('upload activity:%s' % (each[2]))
        command = ("INSERT IGNORE INTO ic_compete_product_activity"
                "(id,create_date,channel,activity_id,activity_name,activity_desc,activity_start_time,activity_end_time)"
                "VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
        )
        sql_online.insert_data(command, msg)


    log('start upload yishou item')
    command = "SELECT * from {0} WHERE create_time > \'{1}\' AND status = 0".format(config.yishou_item_table,get_date())
    sql = SqlHelper()
    data = sql.query(command)
    sql_online = SqlHelperOnline()
    for each in data:
        msg = (None,each[1],each[2],each[3],0,each[5],each[6])
        log('upload item:%s' % (each[1]))
        command = ("INSERT IGNORE INTO ic_compete_product_item"
                "(id,item_id,create_time,channel,status,content,activity_id)"
                "VALUES(%s,%s,%s,%s,%s,%s,%s)"
        )
        sql_online.insert_data(command, msg)




def import_compare_date():
    data = open('query_result.csv','r').readlines()
    command = (
        "CREATE TABLE IF NOT EXISTS {} ("
        "`id` INT(8) NOT NULL AUTO_INCREMENT,"
        "`user_id` BIGINT(20) NOT NULL COMMENT '上新用户id',"
        "`phone` CHAR(15) NOT NULL,"
        "`user_password` TEXT NOT NULL,"
        "`amount` CHAR(20) NOT NULL,"
        "`token` TEXT DEFAULT NULL,"
        "`uid` INT(10) DEFAULT NULL,"
        "`checked` CHAR(5) NOT NULL,"
        "`page` INT(5) NOT NULL,"
        "`finished` INT(2) NOT NULL,"
        "PRIMARY KEY(id),"
        "UNIQUE KEY `user_id` (`user_id`)"
        ") ENGINE=InnoDB".format('temp_users')
    )
    sql = SqlHelper()
    sql.create_table(command)

    for i,each in enumerate(data):
        if i==0:continue
        mat = re.compile(',').split(each.replace('\n',''))
        checked = 'no'


        command = "SELECT * from {0} WHERE user_id = \'{1}\' ".format(config.yishou_login_table,mat[0])
        user = sql.query_one(command)

        if user[6] == 'yes':
            command = "SELECT * from {0} WHERE shangxin_id = \'{1}\' ".format(config.yishou_user_table,mat[0])
            yishou_user = sql.query_one(command)
            if yishou_user:
                msg = (None,mat[0],mat[1],mat[2].replace(r'\"',''),mat[3],yishou_user[1],yishou_user[9],'yes',1,0)
                command = ("INSERT IGNORE INTO {} "
                    "(id, user_id,phone,user_password,amount,uid,token,checked,page,finished)"
                    "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)".format('temp_users')
                )
                sql.insert_data(command, msg)
            else:
                msg = (None,mat[0],mat[1],mat[2].replace(r'\"',''),mat[3],'yes',1,0)
                command = ("INSERT IGNORE INTO {} "
                    "(id, user_id,phone,user_password,amount,checked,page,finished)"
                    "VALUES(%s, %s, %s, %s, %s, %s, %s,%s)".format('temp_users')
                )
                sql.insert_data(command, msg)

        else:
            msg = (None,mat[0],mat[1],mat[2].replace(r'\"',''),mat[3],'no',1,0)
            command = ("INSERT IGNORE INTO {} "
                "(id, user_id,phone,user_password,amount,checked,page,finished)"
                "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)".format('temp_users')
            )
            sql.insert_data(command, msg)






def key_print(msg):
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    print ""
    print msg
    print ""
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
