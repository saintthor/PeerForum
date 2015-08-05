# -*- coding: utf-8 -*-
"""
Created on Sun Jun 14 17:20:40 2015

@author: thor
"""

import os
import sqlite3
from rsa1 import PrivateKey, PublicKey
from time import time

from const import DB_FILE

def ChangePath( newPath ):
    "for testing"
    global DB_FILE
    DB_FILE = newPath


class SqliteDB( object ):
    ""
    def __init__( self, path = '' ):
        ""
        #print 'SqliteDB.__init__', path, DB_FILE
        self.path = path or DB_FILE
        
    def __enter__( self ):
        ""
        self.conn = sqlite3.connect( self.path )
        return self.conn.cursor()
    
    def __exit__( self, *args ):
        ""
        self.conn.commit()
        self.conn.close()
    
    @staticmethod
    def SetMod():
        "重设数据库文件的访问权限"
        os.chmod( DB_FILE, 0600 )

def _UpdateStr( d ):
    "make str for update sql"
    def statement( k, v ):
        if isinstance( v, basestring ):
            return u'%s = "%s"' % ( k, v )
        if isinstance( v, ( PrivateKey, PublicKey )):
            return u'%s = "%s"' % ( k, v.save_pkcs1())
        return u'%s = %s' % ( k, v )
    return u','.join( [statement( *it ) for it in d.items()] )

def _InsertStr( d ):
    "make str for insert sql"
    def statement( v ):
        if isinstance( v, basestring ):
            return u'"%s"' % v
        if isinstance( v, ( PrivateKey, PublicKey )):
            return u'"%s"' % v.save_pkcs1()
        return u'%s' % v
    ks, vs = zip( *d.items())
    vStrs = [statement( v ) for v in vs]
    return u'( %s ) values ( %s )' % ( u','.join( ks ), u','.join( vStrs ))

def _WhereStr( d ):
    "make where str"
    def statement( k, v ):
        if isinstance( v, basestring ):
            return u'%s = "%s"' % ( k, v )
        if isinstance( v, ( PrivateKey, PublicKey )):
            return u'%s = "%s"' % ( k, v.save_pkcs1())
        return u'%s = %s' % ( k, v )
    return u' and '.join( [statement( *it ) for it in d.items()] )
    

def UpdateNodeOrNew( param, where ):
    "if neighbor node exist then update else create."
    param['LastTime'] = int( time() * 1000 )
    with SqliteDB() as cursor:
        if where:       #update
            sql = u'''update node set %s where %s;''' % ( _UpdateStr( param ), _WhereStr( where ))
        else:           #insert
            exist = cursor.execute( 'select id from node where %s;' % _WhereStr( { 'PubKey': param['PubKey'] } )).fetchone()
            if exist is None:
                sql = u'''insert into node %s''' % _InsertStr( param )
            else:
                sql = u'''update node set %s where id = %s;''' % ( _UpdateStr( param ), exist[0] )
        print 'UpdateNodeOrNew', sql
        cursor.execute( sql )
    
def GetNodeByPubKeyOrNew( d ):
    "or new"
    print 'GetOrNewNodeByPubKey', d
    with SqliteDB() as cursor:
        cols = 'name', 'PubKey', 'discription', 'address', 'TechInfo', 'PFPVer', 'ServerProtocol', 'level'
        if not isinstance( d['PubKey'], basestring ):
            d['PubKey'] = d['PubKey'].save_pkcs1()
        exist = cursor.execute( 'select %s from node where PubKey = "%s";' % ( ','.join( cols ), d['PubKey'] )).fetchone()
        
        if exist is not None:
            for i, col in enumerate( cols ):
                d.setdefault( col, exist[i] )
        else:
            sql = u'''insert into node %s''' % _InsertStr( d )
            print 'GetOrNewNodeByPubKey', sql
            cursor.execute( sql )
    
#def CreateNodeORUpdate( d ):
#    "if neighbor node exist then update else create."
#    print 'CreateNodeORUpdate', d
#    with SqliteDB() as cursor:
#        cols = 'name', 'PubKey', 'discription', 'address', 'TechInfo', 'PFPVer', 'ServerProtocol', 'level'
#        exist = None
#        
#        if 'address' in d:
#            exist = cursor.execute( 'select %s from node where PubKey = "" and address = "%s";' % ( ','.join( cols ), d['address'] )).fetchone()
#            sql = u'''update node set %s where address = "%s";''' % ( _UpdateStr( d ), d['address'] )
#            
#        if exist is None and 'PubKey' in d:
#            if not isinstance( d['PubKey'], basestring ):
#                d['PubKey'] = d['PubKey'].save_pkcs1()
#            exist = cursor.execute( 'select %s from node where PubKey = "%s";' % ( ','.join( cols ), d['PubKey'] )).fetchone()
#            PubKey = d.pop( 'PubKey' )
#            sql = u'''update node set %s where PubKey = "%s";''' % ( _UpdateStr( d ), PubKey )
#            
#        if exist is not None:
#            print 'CreateNodeORUpdate', sql
#            cursor.execute( sql )
#            for i, col in enumerate( cols ):
#                d.setdefault( col, exist[i] )
#        else:
#            sql = u'''insert into node %s''' % _InsertStr( d )
#            print 'CreateNodeORUpdate', sql
#            cursor.execute( sql )

def CreateSelfNode( **kwds ):
    ""
    with SqliteDB() as cursor:
        sql = u'''insert into selfnode %s''' % _InsertStr( kwds )
        cursor.execute( sql )

def GetAllNode( *cols ):
    ""
    with SqliteDB() as cursor:
        sql = u'''select %s from node where level > 0 and ServerProtocol = "HTTP"''' % ','.join( cols )
        return cursor.execute( sql ).fetchall()

def GetNodeById( nodeId ):
    ""
#    d = {}
    with SqliteDB() as cursor:
        cols = 'name', 'PubKey', 'discription', 'address', 'TechInfo', 'PFPVer', 'ServerProtocol', 'level'
        node = cursor.execute( 'select %s from node where id = %s;' % ( ','.join( cols ), nodeId )).fetchone()
        return dict( zip( cols, node ))
#        if node:
#            for i, col in enumerate( cols ):
#                d.setdefault( col, node[i] )
#    return d

def GetNodesExcept( ids, excpK ):
    ""
    IdsStr = ','.join( [str( Id ) for Id in ids] )
    exKStr = excpK.save_pkcs1()
    with SqliteDB() as cursor:
        cols = 'name', 'PubKey', 'discription', 'address', 'TechInfo', 'PFPVer', 'ServerProtocol'
        print 'select %s from node where id in (%s);' % ( ','.join( cols ), IdsStr )
        nodes = cursor.execute( 'select %s from node where id in (%s) and PubKey != "%s";'
                                % ( ','.join( cols ), IdsStr, exKStr )).fetchall()
        return [dict( zip( cols, nodeData )) for nodeData in nodes]
    
def test():
    print GetNodesExcept( [1], '' )
    #UpdateNodeOrNew( { 'name': 'NNNNNNNNNN', 'PFPVer': '0.1' }, { 'id': 4 } )

def FileExist( fpath ):
    "check if the db file exist."
    if fpath[:2] == './':
        import os
        segs = os.path.abspath( __file__ ).split( '/' )[:-1]
        fpath = '/'.join( segs ) + fpath[1:]
        
    return os.path.isfile( fpath )
        
def InitDB( path = '' ):
    "init db if the db file is not exist."
    if not path:
        path = DB_FILE
        
    if FileExist( path ):
        #print '================\nThe db file %s already exists. \nIf you want to use another db file path, set the DB_FILE in const.py.\n============' % DB_FILE
        return
        
    with SqliteDB( path ) as c:
        #飘论坛的用户
        c.execute( "create table user (NickName varchar(32), PubKey varchar(1024) unique, status int(2) default 0);" )
        #自己的马甲
        c.execute( """create table self (NickName varchar(32), PubKey varchar(1024) unique,
                    PriKey varchar(4096), status int(2) default 0);""" )
        #邻节点
        c.execute( """create table node (id integer primary key not null, name varchar(32) default '', 
                    PubKey varchar(1024) unique, discription varchar(2048) default '', address varchar(64) default '',
                    TechInfo varchar(64) default '', PFPVer varchar(16) default '', ServerProtocol varchar(16) default '',
                    LastTime int(14) default 0, level int(2) default 10);""" )
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
#        #运行时
#        c.execute( """create table task (id integer primary key not null, time int(13),
#                        message varchar(8192), target int(2), status int(2));""" )
#        
#        t = int( time())
#        c.execute( """insert into task (time, message, target, status) values(%d, 'NewUser', 0, 0);""" % t )
#        c.execute( """insert into task (time, message, target, status) values(%d, 'NewNode', 0, 0);""" % t )
#        
    print 'db initialized.'

if __name__ == '__main__':
    test()