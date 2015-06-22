# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 23:05:57 2015

@author: thor
"""
from const import DB_FILE
from sqlitedb import SqliteDB


def FileExist( fpath ):
    ""
    if fpath[:2] == './':
        import os
        segs = os.path.abspath( __file__ ).split( '/' )[:-1]
        fpath = '/'.join( segs ) + fpath[1:]
        
    return os.path.isfile( fpath )


def NewRSA():
    ""
    import rsa1 as rsa
    return rsa.newkeys( 2048 )
    
        
def InitDB():
    ""
    if FileExist( DB_FILE ):
        print '================\nThe db file %s already exists. \nIf you want to use another db file path, set the DB_FILE in const.py.\n============' % DB_FILE
        return
        
    with SqliteDB() as c:
        #飘论坛的用户
        c.execute( "create table user (NickName varchar(32), PubKey varchar(1024) unique, status int(2));" )
        #自己的马甲
        c.execute( """create table self (NickName varchar(32), PubKey varchar(1024) unique,
                    PriKey varchar(4096), status int(2) default 0);""" )
        #邻节点
        c.execute( """create table node (name varchar(32), PubKey varchar(1024) unique,
                    discription varchar(2048), address varchar(64), TechInfo varchar(64),
                    PFPVer varchar(16), ServerProtocol varchar(16), status int(2) default 0);""" )
        #自身节点
        c.execute( """create table selfnode (name varchar(32), PubKey varchar(1024) unique,
                    discription varchar(2048), PriKey varchar(4096), address varchar(64),
                    ServerProtocol varchar(16), level int(2) default 0);""" )
        #帖子
        c.execute( """create table article (content varchar(20480), id varchar(256) unique,
                    items varchar(8192), root varchar(256), status int(2) default 0,
                    AuthPubKey varchar(1024), Type int(2) default 0, CreateTime int(13));""" )
        #标签
        c.execute( """create table label (name varchar(32), type int(2), TopicID varchar(256));""" )
        #运行时
        c.execute( """create table run (time int(13), message varchar(8192), direction int(2), status int(2));""" )
        c.execute( """insert into run (time, message, direction, status) values(%d, 'NewUser', 0, 0);""" )
        c.execute( """insert into run (time, message, direction, status) values(%d, 'NewNode', 0, 0);""" )
        
    print 'db initialized.'

if __name__ == "__main__":
    InitDB()