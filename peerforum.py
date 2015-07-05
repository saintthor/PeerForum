# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 15:33:58 2015

@author: thor
"""
import logging
import traceback
import json
import re
import rsa1 as rsa

from time import time, sleep
from bottle import route, run, debug, request, static_file

import protocol
import user
import node

from const import LOG_FILE
from sqlitedb import SqliteDB, InitDB
from exception import *

class PeerForum0( object ):#整体架构有变，主逻辑放在前端，废弃。
    ""
    def __init__( self ):
        ""
        self.Node = self.User = None
        with SqliteDB() as cursor:
            cursor.execute( "insert into task (time, message, target, status) values(%d, 'RunNode', 0, 0);" % int( time()))
            
        self._Run()
    
    def _Run( self ):
        "主消息循环"
        def GetParamD( prmStr ):
            ""
            if not prmStr:
                return {}
            try:
                return json.loads( prmStr )
            except:
                logging.error( traceback.format_exc())
                return {}
                
        TaskId = -1

        while True:
            try:
                with SqliteDB() as cursor:
                    cursor.execute( 'update task set status = 10 where id = %d and status = 0 and target = 0' % TaskId )
                    CmdData = cursor.execute( '''select id, message from task where target = 0 and status = 0
                                                order by id limit 1''' ).fetchone()
                #print '======', CmdData
                if CmdData is None:
                    sleep( 0.5 )
                    TaskId = -1
                    continue
                
                TaskId, CmdLine = CmdData
                Segs = CmdLine.split( ':', 1 )
                
                {
                    'NewNode': self._NewNode,
                    'NewUser': self._NewUser,
                    'RunNode': self._RunNode,
                }[Segs[0]]( GetParamD( Segs[1:] ))
                
            except:
                sleep( 1 )
                logging.error( traceback.format_exc())

    @staticmethod    
    def _InsertParams( prmD ):
        "将参数字典转为 sql insert 语句要用的格式"
        ks, vs = zip( *prmD.items())
        kStr = ','.join( ks )
        vStr = u','.join( [( u'"%s"' % v if isinstance( v, basestring ) else str( v )) for v in vs] )
        return kStr, vStr
    
    def _RunNode( self, param ):
        "启动节点"
        if self.Node is None:
            try:
                self.Node = node.Node()
            except:
                logging.error( traceback.format_exc())
        
    def _NewNode( self, param ):
        "新建节点"
        pub, pri = rsa.newkeys( 2048 )
        param['PubKey'] = pub.save_pkcs1()
        param['PriKey'] = pri.save_pkcs1()
        param.setdefault( 'ServerProtocol', 'None' )
        sql = u'insert into selfnode ( %s ) values( %s )' % self._InsertParams( param )
        print '_NewNode', sql
        with SqliteDB() as cursor:
            cursor.execute( sql )
    
    def _NewUser( self, param ):
        ""
        pass
        
    def ChangeNode( self, condi ):
        "改变当前节点"
        self.Node = node.Node( condi )

    def ChangeUser( self, condi ):
        "改变当前用户"
        self.User = user.User( condi )
        

class PeerForum( object ):
    ""
    LocalNode = None
    LiveNeighborD = {}
    
    @classmethod
    def ChkEnv( cls ):
        ""
        InitDB()
        for i in range( 2 ):
            try:
                cls.LocalNode = node.SelfNode()
                break
            except NoAvailableNodeErr:
                cls.NewSelfNode()
        else:
            return { 'error': 'no availabel self node.' }
        return { 'CurNode': cls.LocalNode.Show() }
    
    @staticmethod
    def GetNode():
        ""
        return {}
    
    @staticmethod
    def GetAllUser():
        ""
        return {}
    
    @staticmethod
    def Reply_0x10( msg ):
        "query pubkey"
        return ''
    
@route( '/' )
def local():
    'for local ui'
    if re.match( r'^localhost(\:\d+)?$', request.environ.get( 'HTTP_HOST' )) is None:
        return 'not permitted.'
    if request.method == 'GET':
        return static_file( 'index.html', root='.' )
    try:
        return PeerForum.getattr( request.POST['cmd'] )( request.POST )
    except Exception, e:
        logging.error( traceback.format_exc())
        return { 'error': str( e ) }
    
@route( '/node' )
def pfp():
    'pfp api'
    if request.method == 'GET':
        return 'not permitted.'
    
    return '\n'.join( [PeerForum.getattr( 'Reply_%s' % hex( ord( msg[0] )))( msg )
                        for msg in request.POST['pfp'].split( '\n' ) if msg] )
    
@route( '/inc:fname#.+#' )
def static( fname ):
    'static files'
    if re.match( r'^localhost(\:\d+)?$', request.environ.get( 'HTTP_HOST' )) is None:
        return 'not permitted.'
    return static_file( '/inc/%s' % fname, root='.' )
    



if __name__ == '__main__':
    SqliteDB.SetMod()
    logging.basicConfig( filename = LOG_FILE, level = logging.DEBUG )
    #PeerForum()
    debug( True )
    run( host = '0.0.0.0', port = 8000, reloader = True )
