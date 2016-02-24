# -*- coding: utf-8 -*-
"""
Created on Sun Jun 14 17:20:40 2015

@author: thor
"""

import os
import sqlite3
import traceback
import logging

from rsa import PrivateKey, PublicKey
from time import time
from json import loads

from const import DB_FILE, DelFromNodeHours
from exception import *

def ChangePath( newPath ):
    "for testing"
    global DB_FILE
    DB_FILE = newPath


class SqliteDB( object ):
    ""
    def __init__( self, path = '' ):
        ""
        self.path = path or DB_FILE
        
    def __enter__( self ):
        ""
        self.conn = sqlite3.connect( self.path )
        return self.conn.cursor()
    
    def __exit__( self, eType, eObj, tb ):
        ""
        if eType is not None:
            logging.error( '======= SqliteDB catches ======\n%s  %s\n%s\n============================'
                            % ( repr( eType ), repr( eObj ), ''.join( traceback.format_tb( tb ))))
        self.conn.commit()
        self.conn.close()
    
    @staticmethod
    def SetMod():
        "重设数据库文件的访问权限"
        os.chmod( DB_FILE, 0600 )

def _UpdateStr( d ):
    "make str for update sql"
    def statement( v ):
        if isinstance( v, ( PrivateKey, PublicKey )):
            return v.save_pkcs1()
        return v
    cols, vals = tuple( zip( *d.items()))
    return ','.join( [( c + '=?' ) for c in cols] ), tuple( map( statement, vals ))

def _InsertStr( d ):
    "make str for insert sql"
    def statement( v ):
        if isinstance( v, ( PrivateKey, PublicKey )):
            return v.save_pkcs1()
        return v
    ks, vs = zip( *d.items())
    vStrs = [statement( v ) for v in vs]
    return ','.join( ks ), tuple( vStrs )

def _WhereStr( d ):
    "make where str"
    def statement( v ):
        if isinstance( v, ( PrivateKey, PublicKey )):
            return v.save_pkcs1()
        return v
    cols, vals = tuple( zip( *d.items()))
    return ' and '.join( [( c + '=?' ) for c in cols] ), tuple( map( statement, vals ))
    #return u' and '.join( [statement( *it ) for it in d.items()] )
    

def UpdateNodeOrNew( param, where ):
    "if neighbor node exist then update else create."
    logging.debug( 'UpdateNodeOrNew param = %s' % repr( param ))
    param['LastTime'] = int( time() * 1000 )
    PubKeyStr = param['PubKey'].save_pkcs1()
    if 'address' in param:
        Addrs = param.pop( 'address' )
    elif 'addr' in param:
        Addrs = param.pop( 'addr' )
    else:
        Addrs = ()
    with SqliteDB() as cursor:
        if where:       #update
            ucols, uvals = _UpdateStr( param )
            wcols, wvals = _WhereStr( where )
            vals = uvals + wvals
            sql = u'''update node set %s where %s;''' % ( ucols, wcols )
        else:           #insert
            exist = cursor.execute( 'select id from node where PubKey = ?;', ( PubKeyStr, )).fetchone()
            if exist is None:
                cols, vals = _InsertStr( param )
                sql = u'insert into node (%s) values(%s)' % ( cols, ','.join( ['?'] * len( vals )))
            else:
                cols, vals = _UpdateStr( param )
                sql = u'''update node set %s where id = %s;''' % ( cols, exist[0] )
        cursor.execute( sql, vals )
        
        for Addr in Addrs:
            sql = 'insert into address (addr, NodePubKey) values(?, ?)'
            cursor.execute( sql, ( Addr, PubKeyStr ))
    
def GetNodeByPubKeyOrNew( d ):
    "or new"
    logging.debug( 'GetNodeByPubKeyOrNew' )
    with SqliteDB() as cursor:
        cols = 'name', 'PubKey', 'discription', 'TechInfo', 'PFPVer', 'ServerProtocol', 'level'
        if not isinstance( d['PubKey'], basestring ):
            d['PubKey'] = d['PubKey'].save_pkcs1()
        exist = cursor.execute( 'select %s from node where PubKey = ?;' % ','.join( cols ), ( d['PubKey'], )).fetchone()
        
        if exist is not None:
            for i, col in enumerate( cols ):
                d.setdefault( col, exist[i] )
            d['Addrs'] = map( tuple, cursor.execute( "select type, addr from address where NodePubKey = ?",
                                                    ( d['PubKey'], )).fetchall())
        else:
            if 'addr' in d:
                addr = d.pop( 'addr' )
                print 'addr', addr
            cols, vals = _InsertStr( d )
            sql = u'insert into node (%s) values(%s)' % ( cols, ','.join( ['?'] * len( vals )))
            cursor.execute( sql, vals )
    
def GetNodeInfoByPubKey( pubK, kItems ):
    "for search"
    with SqliteDB() as cursor:
        ProtocolKs, dataCols = zip( *kItems )
        exist = cursor.execute( 'select %s from node where PubKey = ?;' % ','.join( dataCols ), ( pubK, )).fetchone()
        return dict( zip( dataCols, exist ))


def CreateSelfNode( **kwds ):
    ""
    if 'address' in kwds:
        kwds.pop( 'address' )
    with SqliteDB() as cursor:
        cols, vals = _InsertStr( kwds )
        sql = u'insert into selfnode (%s) values(%s)' % ( cols, ','.join( ['?'] * len( vals )))
        cursor.execute( sql, vals )

def CreateSelfUser( **kwds ):
    ""
    with SqliteDB() as cursor:
        cols, vals = _InsertStr( kwds )
        sql = u'insert into self (%s) values(%s)' % ( cols, ','.join( ['?'] * len( vals )))
        cursor.execute( sql, vals )

def GetSelfPubKeyStrs():
    ""
    with SqliteDB() as cursor:
        return [r[0] for r in cursor.execute( 'select PubKey from self' ).fetchall()]

def GetDefaultUser():
    ""
    with SqliteDB() as cursor:
        sql = """select NickName, PubKey, PriKey from self where status >= 0 order by status desc limit 1;"""
        return cursor.execute( sql ).fetchone()

def GetSelfNode( single = True ):
    "get one or all"
    logging.debug( 'GetSelfNode' )
    with SqliteDB() as cursor:
        if single:
            data = cursor.execute( """select name, PubKey, PriKey, ServerProtocol, discription, level
                            from selfnode where level >= 0 order by level desc limit 1;""" ).fetchone()
            if data is None:
                raise NoAvailableNodeErr
                
            addrs = cursor.execute( "select addr from address where NodePubKey = ?", ( data[1], )).fetchall()
            
            return data + ( [a[0] for a in addrs], )
        else:
            d = {}
            for data in cursor.execute( """select PubKey, name, ServerProtocol, discription, level, addr
                                            from selfnode join address on selfnode.PubKey = address.NodePubKey 
                                            where level >= 0;""" ).fetchall():
                PubKey, EachAddr = data[0], data[5]
                data = data[1:5] + ( [], )
                d.setdefault( PubKey, data )[-1].append( EachAddr )
        
            return d

def EditSelfNode( pubKey, name, desc, addrs ):
    ""
    logging.debug( 'EditSelfNode' )
    with SqliteDB() as cursor:
        cursor.execute( 'update selfnode set name = ?, discription = ? where PubKey = ?', ( name, desc, pubKey ));
        cursor.execute( 'delete from address where NodePubKey = ?', ( pubKey, ));
        for addr in addrs:
            cursor.execute( 'insert into address (NodePubKey, addr) values(?, ?)', ( pubKey, addr ));
        

def SetSelfUserName( pubKey, name ):
    ""
    with SqliteDB() as cursor:
        cursor.execute( 'update self set NickName = ? where PubKey = ?', ( name, pubKey ));
        
def GetAllNode( *cols, **filterd ):
    ""
    with SqliteDB() as cursor:
        wcols, vals = _WhereStr( filterd )
        sql = u'''select %s from node where level > 0 and %s''' % ( ','.join( cols ), wcols )
        return cursor.execute( sql, vals ).fetchall()

def GetTargetNodes():
    ""
    logging.debug( 'GetTargetNodes' )
    d = {}
    with SqliteDB() as cursor:
        pubKs = [data[0] for data in cursor.execute( 'select PubKey from node where ServerProtocol = "HTTP"' ).fetchall()]
        for pubK, Type, addr in cursor.execute(
                'select NodePubKey, type, addr from address where NodePubKey in (%s)' % ','.join( ['?'] * len( pubKs )),
                tuple( pubKs )).fetchall():
            d.setdefault( pubK, [] ).append( [Type, addr] )
            
    return d.items()

def GetNodeById( nodeId ):
    ""
    logging.debug( 'GetNodeById: %s' % nodeId )
    with SqliteDB() as cursor:
        cols = 'name', 'PubKey', 'discription', 'TechInfo', 'PFPVer', 'ServerProtocol', 'level'
        node = cursor.execute(( 'select %s from node where id = ?;' % ','.join( cols )), ( nodeId, )).fetchone()
        d = dict( zip( cols, node ))
        for pubK, Type, addr in cursor.execute( 'select NodePubKey, type, addr from address where NodePubKey = ?',
                                               ( d['PubKey'], )).fetchall():
            d.setdefault( 'Addrs', [] ).append(( Type, addr ))
        if 'Addrs' in d:
            return d

def GetNodesExcept( kItems, ids, excpK ):
    ""
    logging.debug( 'GetNodesExcept' )
    IdsStr = ','.join( [str( Id ) for Id in ids] )
    exKStr = excpK.save_pkcs1() if excpK else excpK
    with SqliteDB() as cursor:
        #cols = 'name', 'PubKey', 'discription', 'address', 'TechInfo', 'PFPVer', 'ServerProtocol'
        ProtocolKs, dataCols = zip( *kItems )
        nodes = cursor.execute( '''select %s from address inner join node on address.NodePubKey = node.PubKey
                                where id in (%s) and PubKey != ?;'''
                                % ( ','.join( dataCols ), IdsStr ), ( exKStr, )).fetchall()
        return [dict( zip( ProtocolKs, nodeData )) for nodeData in nodes]

def GetOneArticle( *cols, **filterd ):
    ""
    with SqliteDB() as cursor:
        wcols, vals = _WhereStr( filterd )
        sql = 'select %s from article where %s' % ( ','.join( cols ), wcols )
        return cursor.execute( sql, vals ).fetchone()

def SaveArticle( **param ):
    ""
    #logging.debug( 'SaveArticle: %s' % param['id'] )
    param.setdefault( 'DestroyTime', 9999999999999 )
    with SqliteDB() as cursor:
        cols, vals = _InsertStr( param )
        sql = u'insert into article (%s) values(%s)' % ( cols, ','.join( ['?'] * len( vals )))
        try:
            cursor.execute( sql, vals )
        except sqlite3.IntegrityError:
            logging.warning( 'SaveArticle IntegrityError' )
            return False
    return True

def SetAtclStatus( atclId, status ):
    ""
    with SqliteDB() as cursor:
        cursor.execute( 'update article set status = ? where id = ?', ( status, atclId ))
        cursor.execute( 'update topic set status = ? where root = ?', ( status, atclId ))
        if status == 1:
            return
        RemoteK = cursor.execute( 'select FromNode from article where id = ?', ( atclId, )).fetchone()[0]
        if RemoteK:
            if status > 1:
                cursor.execute( 'update node set level = min( 99, level + 1 ) where PubKey = ?', ( RemoteK, ))
            elif status < 0:
                cursor.execute( 'update node set level = max( -1, level - 1 ) where PubKey = ?', ( RemoteK, ))
        
def UpdateArticles():
    "check destroy, del FromNode"
    t = int( time() * 1000 )
    with SqliteDB() as cursor:
        cursor.execute( 'update article set status = -2 where DestroyTime < ?', ( t, ))
        cursor.execute( 'update article set FromNode = '', RemoteLabels = '', RemoteEval = 1 where GetTime < ?',
                        (( t - DelFromNodeHours * 3600000 ),))
    
def SaveTopicLabels( topicId, labels, Type = 0 ):
    ""
    with SqliteDB() as cursor:
        for label in filter( None, labels ):
            cols, vals = _InsertStr( { 'name': label, 'TopicID': topicId, 'type': Type } )
            sql = u'insert into label (%s) values(%s)' % ( cols, ','.join( ['?'] * len( vals )))
            cursor.execute( sql, vals )
            
def DelTopicLabels( topicId, labels ):
    """
    NOTE:
    use this api to delete both static labels and node labels in the current node.
    when sending to other nodes, the deleted static labels will also be sent.
    because the static labels can not be changed after creation.
    """
    with SqliteDB() as cursor:
        cursor.execute( 'delete from label where TopicID = ? and name in (%s)' % ','.join( ['?'] * len( labels )),
                       ( topicId, ) + tuple( labels ))
    
def UpdateTopic( tpcId, **param ):
    ""
    with SqliteDB() as cursor:
        cols, vals = _UpdateStr( param )
        sql = 'update topic set num = num + 1, %s where root = ?' % cols
        cursor.execute( sql, vals + ( tpcId, ))

def SaveTopic( **param ):
    ""
    with SqliteDB() as cursor:
        cols, vals = _InsertStr( param )
        sql = u'insert into topic (%s) values(%s)' % ( cols, ','.join( ['?'] * len( vals )))
        cursor.execute( sql, vals )

def GetRootIds( **condi ):
    ""
    status = max( condi.get( 'Status', 1 ), 1 )
    with SqliteDB() as cursor:
        return [tpc[0] for tpc in cursor.execute(
                        'select root from topic where LastTime >= ? and LastTime <= ? and status >= ?', 
                        ( condi['From'], condi['To'], status )
                                                ).fetchall()]

def GetTopicRowById( rootId ):
    ""
    with SqliteDB() as cursor:
        for row in cursor.execute(
            '''select root, title, labels, status, num, FirstAuthName, FirstTime, LastAuthName, LastTime
                from topic where root=?''', ( rootId, )
                                ).fetchall():
            return row
            
def GetTopicRows( label, before, sortCol, limit ):
    ""
    with SqliteDB() as cursor:
        if label:
            now = int( time() * 1000 )
            if before > now:
                cursor.execute( 'insert into labellog (name, ShowTime) values( ?, ? );', ( label, now ))
            return cursor.execute(
                '''select root, title, labels, status, num, FirstAuthName, FirstTime, LastAuthName, LastTime
                    from topic join label on topic.root = label.TopicID where label.name = ? and %s <= ?
                    order by %s desc limit ?''' % ( sortCol, sortCol ), ( label, before, limit )
                                    ).fetchall()
        else:
            return cursor.execute(
                '''select root, title, labels, status, num, FirstAuthName, FirstTime, LastAuthName, LastTime
                    from topic where %s <= ? order by %s desc limit ?''' % ( sortCol, sortCol ), ( before, limit )
                                    ).fetchall()

def GetAllLabels():
    ""
    with SqliteDB() as cursor:
        d = { LabelName: 0 for LabelName in [c[0] for c in cursor.execute( 'select distinct name from label' ).fetchall()] }
        d.update( dict( cursor.execute( 'select name, count(*) from labellog group by name' ).fetchall()))
        return d
    
def GetTreeAtcls( *rootIds ):
    ""
    d = {}
    with SqliteDB() as cursor:
        for root, Id, itemStr, content, status, RLabels, REval in cursor.execute(
                    'select root, id, items, content, status, RemoteLabels, RemoteEval from article where root in (%s)' % ','.join( ['?'] * len( rootIds )),
                    tuple( rootIds )
                        ).fetchall():
            d.setdefault( root, {} )[Id] = [itemStr, content, status, RLabels, REval, '']
    
        for root, labels in cursor.execute(
                    'select root, labels from topic where root in (%s)' % ','.join( ['?'] * len( rootIds )),
                    tuple( rootIds )
                        ).fetchall():
            d[root][root][-1] = labels
        
    return d

def SetAtclsWithoutTopic():
    ""
    d = {}
    with SqliteDB() as cursor:
        for root, Id, itemStr, content in cursor.execute(
                    '''select root, id, items, content from article where root in 
                        ( select article.id from article left outer join topic on article.id = topic.root
                        where article.id = article.root and topic.root is null )'''
                                                ).fetchall():
            itemD = loads( itemStr )
            labels = itemD.get( 'Labels', '' ) if root == Id else ''
            firstLine = content.split( '\n' )[0] if root == Id and content else ''
            d.setdefault( root, {} )[Id] = itemD['CreateTime'], itemD['NickName'], firstLine, labels
            
        for root, atclD in d.items():
            atclItems = atclD.values()
            first = min( atclItems, key = lambda x: x[0] )[:2]
            last = max( atclItems, key = lambda x: x[0] )[:2]
            titleLine = atclD[root][2]
            labels = atclD[root][3]
            
            SaveTopic( root = root, title = titleLine[:30], num = len( atclD ), status = 0,
                        FirstAuthName = first[1], LastAuthName = last[1],
                        FirstTime = first[0], LastTime = last[0] )      #LastTime should be the last GetTime
            SaveTopicLabels( root, labels )
            
    return len( d )

def SetLabel( rootId, labelName, act ):
    "add or remove one label at one time"
    with SqliteDB() as cursor:
        LabelStr = cursor.execute( 'select labels from topic where root = ?', ( rootId, )).fetchone()[0]
        StaticLStr, ThisLStr = ( LabelStr + '|' ).split( '|' )[:2]
        StaticLabels = StaticLStr.split( ',' )
        ThisLabels = ThisLStr.split( ',' )

        if act == '+' and labelName not in ( StaticLabels + ThisLabels ):
            cursor.execute( 'insert into label (name, type, TopicID) values(?,?,?)', ( labelName, 1, rootId ))
            LabelStr += ( ',' if '|' in LabelStr else '|' ) + labelName
            cursor.execute( 'update topic set labels = ? where root = ?', ( LabelStr, rootId ))
        elif labelName in ( StaticLabels + ThisLabels ):
            if len( StaticLabels ) + len( ThisLabels ) < 2:
                return LabelStr
            cursor.execute( 'delete from label where name = ? and TopicID = ?', ( labelName, rootId ))
            if labelName in StaticLabels:
                StaticLabels.remove( labelName )
                StaticLStr = u','.join( StaticLabels )
            elif labelName in ThisLabels:
                ThisLabels.remove( labelName )
                ThisLStr = u','.join( ThisLabels )
            LabelStr = u'|'.join( [StaticLStr, ThisLStr] )
            if LabelStr == '|':
                LabelStr = ''
            cursor.execute( 'update topic set labels = ? where root = ?', ( LabelStr, rootId ))
        return LabelStr
    
def GetAtclIdByUser( uPubK, From, To ):
    ""
    with SqliteDB() as cursor:
        atcls = cursor.execute( 'select id from article where AuthPubKey = ? and CreateTime >= ? and CreateTime <= ?',
                               ( uPubK, From, To )).fetchall()
        return [a[0] for a in atcls]
    
def GetAtclByUser( uPubK, From, To, exist = () ):
    "to trans"
    exist = tuple( exist ) + ( 'zzz', )
    with SqliteDB() as cursor:                                            #for testing check status condition availible
        sql = '''select id, items, content from article where AuthPubKey = ? and status > 0 
                and CreateTime >= ? and CreateTime <= ? and id not in (%s)''' % ','.join( ['?'] * len( exist ))
        return cursor.execute( sql, ( uPubK, From, To ) + exist ).fetchall()

def SearchAtcl( kWord, before, num ):
    "to show"
    with SqliteDB() as cursor:
        return cursor.execute( '''select id, items, content, status, root, GetTime from article 
                                where content like ? and GetTime <= ? order by GetTime desc limit ?''',
                                ( '%' + kWord + '%', before, num )).fetchall()
    

def GetAtclByUserToShow( uPubK, before, num ):
    "to show"
    with SqliteDB() as cursor:
        if uPubK == 'all':
            return cursor.execute( '''select id, items, content, labels, article.status, article.root, GetTime 
                                from article join user on article.AuthPubKey = user.PubKey left outer join topic 
                                on article.id = topic.root where user.status > 0 and GetTime <= ? 
                                order by GetTime desc limit ?''',
                                ( before, num )).fetchall()
        return cursor.execute( '''select id, items, content, labels, article.status, article.root, GetTime from 
                                article left outer join topic on article.id = topic.root where AuthPubKey = ? 
                                and GetTime <= ? order by GetTime desc limit ?''',
                                ( uPubK, before, num )).fetchall()
    
def GetAllUsers():
    ""
    with SqliteDB() as cursor:
        return cursor.execute( 'select PubKey, NickName, status from user' ).fetchall()

#def GetPreferLabels():
#    ""
#    with SqliteDB() as cursor:
#        return cursor.execute( 'select name, level from preferlabel order by level desc' ).fetchall()

def RecordUser( pubK, nickName, status = 1 ):
    "follow or block"
    with SqliteDB() as cursor:
        cursor.execute( 'delete from user where PubKey = ?', ( pubK, ))
        if status != 0:
            cursor.execute( 'insert into user (PubKey, NickName, status) values(?, ?, ?)', ( pubK, nickName, status ))

def test():
    return

def FileExist( fpath ):
    "check if the db file exist."
    if fpath[:2] == './':
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
        #关注或屏蔽的用户
        c.execute( "create table user (NickName varchar(32), PubKey varchar(1024) unique, status int(2) default 0);" )
        #用户圈子       many to many
        #c.execute( "create table circle (UserPubKey varchar(1024), CircleName varchar(64));" )
        #自己的马甲
        c.execute( """create table self (NickName varchar(32), PubKey varchar(1024) unique,
                    PriKey varchar(4096), status int(2) default 0);""" )
        #邻节点                            id is the alias for rowid by declared with integer.
                    #multi addrs for each node.
        c.execute( """create table node (id integer primary key asc, name varchar(32) default '', 
                    PubKey varchar(1024) unique, discription varchar(2048) default '',
                    TechInfo varchar(64) default '', PFPVer varchar(16) default '', ServerProtocol varchar(16) default '',
                    LastTime int(14) default 0, level int(2) default 10);""" )
        #自身节点
        c.execute( """create table selfnode (name varchar(32), PubKey varchar(1024) unique,
                    discription varchar(2048), PriKey varchar(4096),
                    ServerProtocol varchar(16), level int(2) default 0);""" )
                    
        #物理地址 for selfnode and neighbor. type = 0-public, 1-inner
        c.execute( """create table address (type int(2), addr varchar(256), NodePubKey varchar(1024),
                    FailNum int(5) default 0, LastCommuTime int(13) default 0, unique(addr, NodePubKey))""" )
        
        #帖子         Type = 0 for normal
                                                                    #id is article id, not rowid
        c.execute( """create table article (content varchar(60080), id varchar(256) unique,
                    items varchar(8192), root varchar(256), status int(2) default 0,
                    AuthPubKey varchar(1024), Type int(2) default 0, CreateTime int(13),
                    DestroyTime int(13) default 9999999999999, GetTime int(13), FromNode varchar(1024),
                    RemoteLabels varchar(256), RemoteEval int(2) default 1);""" )      #FromNode, RemoteLabels, RemoteEval should be deleted in hours for secrety.

        #话题         labels = staticLabel,staticLabel|nodeLabel,nodeLabel
        c.execute( """create table topic (root varchar(256) unique,
                    title varchar(128) not null, num int(4), status int(2) default 0,
                    labels varchar(256), FirstAuthName  varchar(32), FirstTime int(13),
                    LastAuthName  varchar(32), LastTime int(13));""" )  #LastTime is the last GetTime of the articles
        #标签                                             type = 0 for static label; 1 for node label
        c.execute( """create table label (name varchar(32), type int(2), TopicID varchar(256));""" )
        
        #优先标签
        #c.execute( """create table preferlabel (name varchar(32) unique, level int(2));""" )
        
        #标签显示记录
        c.execute( """create table labellog (name varchar(32), ShowTime int(13));""" )
        
    print 'db initialized.'

if __name__ == '__main__':
    test()