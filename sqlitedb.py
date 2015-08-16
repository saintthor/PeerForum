# -*- coding: utf-8 -*-
"""
Created on Sun Jun 14 17:20:40 2015

@author: thor
"""

import os
import sqlite3
from rsa1 import PrivateKey, PublicKey
from time import time

from const import DB_FILE, DelFromNodeHours

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
            return "'%s'" % v
        if isinstance( v, ( PrivateKey, PublicKey )):
            return '"%s"' % v.save_pkcs1()
        return '%s' % v
    ks, vs = zip( *d.items())
    vStrs = [statement( v ) for v in vs]
    return '( %s ) values ( %s )' % ( ','.join( ks ), ','.join( vStrs ))

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
    #print 'GetNodeByPubKeyOrNew', d
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
    
def GetNodeInfoByPubKey( pubK, kItems ):
    "for search"
    print 'GetNodeInfoByPubKey'
    with SqliteDB() as cursor:
        ProtocolKs, dataCols = zip( *kItems )
        exist = cursor.execute( 'select %s from node where PubKey = "%s";' % ( ','.join( dataCols ), pubK )).fetchone()
        #exist = None
        print '\nexist =', exist
        return dict( zip( dataCols, exist ))


def CreateSelfNode( **kwds ):
    ""
    with SqliteDB() as cursor:
        sql = u'''insert into selfnode %s''' % _InsertStr( kwds )
        cursor.execute( sql )

def CreateSelfUser( **kwds ):
    ""
    with SqliteDB() as cursor:
        sql = u'''insert into self %s''' % _InsertStr( kwds )
        cursor.execute( sql )

def GetDefaultUser():
    ""
    with SqliteDB() as cursor:
        sql = """select NickName, PubKey, PriKey from self where status >= 0 order by status desc limit 1;"""
        return cursor.execute( sql ).fetchone()

def GetAllNode( *cols, **filterd ):
    ""
    with SqliteDB() as cursor:
        sql = u'''select %s from node where level > 0 and %s''' % ( ','.join( cols ), _WhereStr( filterd ))
        return cursor.execute( sql ).fetchall()

def GetNodeById( nodeId ):
    ""
    with SqliteDB() as cursor:
        cols = 'name', 'PubKey', 'discription', 'address', 'TechInfo', 'PFPVer', 'ServerProtocol', 'level'
        node = cursor.execute( 'select %s from node where id = %s;' % ( ','.join( cols ), nodeId )).fetchone()
        return dict( zip( cols, node ))

def GetNodesExcept( kItems, ids, excpK ):
    ""
    IdsStr = ','.join( [str( Id ) for Id in ids] )
    exKStr = excpK.save_pkcs1() if excpK else excpK
    with SqliteDB() as cursor:
        #cols = 'name', 'PubKey', 'discription', 'address', 'TechInfo', 'PFPVer', 'ServerProtocol'
        ProtocolKs, dataCols = zip( *kItems )
        #print 'select %s from node where id in (%s);' % ( ','.join( cols ), IdsStr )
        nodes = cursor.execute( 'select %s from node where id in (%s) and PubKey != "%s";'
                                % ( ','.join( dataCols ), IdsStr, exKStr )).fetchall()
        return [dict( zip( ProtocolKs, nodeData )) for nodeData in nodes]

def GetOneArticle( *cols, **filterd ):
    ""
    with SqliteDB() as cursor:
        sql = 'select %s from node where %s' % ( ','.join( cols ), _WhereStr( filterd ))
        return cursor.execute( sql ).fetchone()

def SaveArticle( **param ):
    ""
    param['GetTime'] = int( time()) * 1000
    #print 'SaveArticle', param
    with SqliteDB() as cursor:
        sql = 'insert into article %s' % _InsertStr( param )
        #print sql
        cursor.execute( sql )

def UpdateArticles():
    "check destroy, del FromNode"
    t = int( time()) * 1000
    with SqliteDB() as cursor:
        cursor.execute( 'update article set status = -2 where DestroyTime < %d' % t )
        cursor.execute( 'update article set FromNode = '', GetTime = 9999999999999 where GetTime < %d'
                        % ( t - DelFromNodeHours * 3600000 ))
    
def SaveTopicLabels( topicId, labels, Type = 0 ):
    ""
    print 'SaveTopicLabels'
    with SqliteDB() as cursor:
        for label in filter( None, labels ):
            sql = 'insert into label %s' % _InsertStr( { 'name': label, 'TopicID': topicId, 'type': Type } )
            print sql
            cursor.execute( sql )
    

def SaveTopic( **param ):
    ""
    print 'SaveTopic', param
    with SqliteDB() as cursor:
        sql = 'insert into topic %s' % _InsertStr( param )
        print sql
        cursor.execute( sql )
    

def test():
    with SqliteDB() as c:
        c.execute( """create table topic (root varchar(256) unique,
                    title varchar(128) not null, num int(4), status int(2) default 0,
                    FirstAuthName  varchar(32), FirstTime int(13),
                    LastAuthName  varchar(32), LastTime int(13));""" )
    return
    transD = {
        'id': 'id',
        'PubKey': 'PubKey',
        'PFPVer': 'PFPVer',
        'NodeName': 'name',
        'Description': 'discription',
        'Address': 'address',
        'NodeTypeVer': 'TechInfo',
        'BaseProtocol': 'ServerProtocol',            
            }
    its = [it for it in transD.items() if it[0] != 'id']
    print GetNodesExcept( its, [1, 2], '' )
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
        #用户圈子       many to many
        c.execute( "create table circle (UserPubKey varchar(1024), CircleName varchar(64));" )
        #自己的马甲
        c.execute( """create table self (NickName varchar(32), PubKey varchar(1024) unique,
                    PriKey varchar(4096), status int(2) default 0);""" )
        #邻节点                            id is the alias for rowid by declared with integer.
                    #multi addrs for each node.
        c.execute( """create table node (id integer primary key asc, name varchar(32) default '', 
                    PubKey varchar(1024) unique, discription varchar(2048) default '', address varchar(64) default '',
                    TechInfo varchar(64) default '', PFPVer varchar(16) default '', ServerProtocol varchar(16) default '',
                    LastTime int(14) default 0, level int(2) default 10);""" )
        #自身节点
        c.execute( """create table selfnode (name varchar(32), PubKey varchar(1024) unique,
                    discription varchar(2048), PriKey varchar(4096), address varchar(64),
                    ServerProtocol varchar(16), level int(2) default 0);""" )
        #帖子         Type = 0 for normal, 1 for like
                                                                    #id is not rowid
        c.execute( """create table article (content varchar(60080), id varchar(256) unique,
                    items varchar(8192), root varchar(256), status int(2) default 0,
                    AuthPubKey varchar(1024), Type int(2) default 0, CreateTime int(13),
                    DestroyTime int(13) default 9999999999999,
                    GetTime int(13), FromNode varchar(1024));""" )      #GetTime and FromNode should be deleted in hours.
        #话题
        c.execute( """create table topic (root varchar(256) unique,
                    title varchar(128) not null, num int(4), status int(2) default 0,
                    FirstAuthName  varchar(32), FirstTime int(13),
                    LastAuthName  varchar(32), LastTime int(13));""" )
        #标签                                             type = 0 for static label; 1 for node label
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