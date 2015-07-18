# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 15:33:58 2015

@author: thor
"""
import logging
import traceback
from json import loads, dumps
from base64 import decodestring
#import re
import rsa1 as rsa

from time import time, sleep
from bottle import route, run, post, debug, request, static_file

import user

from node import NeighborNode, SelfNode
from protocol import PFPMessage
from const import LOG_FILE, CommunicateCycle
from sqlitedb import SqliteDB, InitDB
from exception import *


class PeerForum( object ):
    "physical node"
    LocalNode = None
    
    @classmethod
    def ChkEnv( cls ):
        ""
        for i in range( 2 ):
            try:
                cls.LocalNode = PFPMessage.LocalNode = SelfNode()
                break
            except NoAvailableNodeErr:
                SelfNode.New()
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
    
    @classmethod
    def Dida( cls, counter = [0] ):
        ""
        counter[0] = n = counter[0] + 1
        if n % CommunicateCycle == 0:
            cls.Communicate()
        return {}
    
    @classmethod
    def Communicate( cls ):
        ""
        Remote = NeighborNode.Pick()
        task = QryPubKeyTask( Remote )
        Steps = task.StepGen()
        ComingMsg = None
        
        while True:
            try:
                MsgCls = Steps.send( ComingMsg )
                if MsgCls is None:
                    sleep( 1 )
                    continue
            except StopIteration:
                print 'test over.'
                break
            
            print 'MsgCls is ', MsgCls
            Message = MsgCls()
            Message.SetRemoteNode( Remote )
            data = urlencode( { 'pfp': Message.Issue() } )
            print '============ send data ============\n', data
            req = urllib2.Request( Remote.Addr, data )
            response = urllib2.urlopen( req )
            reply = response.read()
            print '============ get reply ============\n', reply
            ComingMsg = None
            Msgs = []
            for msgStr in reply.split( '\n' ):
                if not msgStr:
                    continue
                ComingMsg = PFPMessage( ord( msgStr[0] ))
                MsgBody = loads( msgStr[1:] )
                
                VerifyStr = ComingMsg.GetBody( MsgBody )
                if VerifyStr:
                    body = loads( VerifyStr )
                    Remote.PubKey = rsa.PublicKey.load_pkcs1( body['PubKey'] )
                    Remote.Verify( VerifyStr, decodestring( MsgBody['sign'] ))
                
                Msgs.extend( Remote.Reply( ComingMsg ) + Remote.Append())
    
    @classmethod
    def Reply( cls, msgStr ):
        "reply other nodes."
        #print 'PeerForum.Reply', ord( msgStr[0] ), msgStr
        ComingMsg = PFPMessage( ord( msgStr[0] ))
        MsgBody = loads( msgStr[1:] )
        
        VerifyStr = ComingMsg.GetBody( MsgBody )
        if VerifyStr:
            #Neighbor = cls.LiveNeighborD.setdefault( ComingMsg.PubKey, NeighborNode.New( loads( VerifyStr )))
            Neighbor = NeighborNode.Get( ComingMsg.PubKey, loads( VerifyStr ))
            Neighbor.Verify( VerifyStr, decodestring( MsgBody['sign'] ))
        else:
            #Neighbor = cls.LiveNeighborD.setdefault( ComingMsg.PubKey, NeighborNode.New( MsgBody ))
            Neighbor = NeighborNode.Get( ComingMsg.PubKey, MsgBody )
            
        Messages = Neighbor.Reply( ComingMsg ) + Neighbor.Append()
        print 'Messages = ', Messages
        
        return Messages

    #===================== http apis with bottle ===================================
    @staticmethod
    @post( '/node' )
    def pfp():
        'pfp api'
        if request.method == 'GET':
            return 'not permitted.'
        
        AllMsgs = reduce( list.__add__, [PeerForum.Reply( msg ) for msg in request.POST['pfp'].split( '\n' ) if msg] )
        return '\n'.join( AllMsgs )
        
    @staticmethod
    @route( '/' )
    def local():
        'for local ui'
        #if re.match( r'^localhost(\:\d+)?$', request.environ.get( 'HTTP_HOST' )) is None:
        if request['REMOTE_ADDR'] != '127.0.0.1':
            return 'not permitted.'
        if request.method == 'GET':
            return static_file( 'index.html', root='.' )
        try:
            return getattr( PeerForum, request.POST['cmd'] )( request.POST )
        except Exception, e:
            logging.error( traceback.format_exc())
            return { 'error': str( e ) }
        
    @staticmethod
    @route( '/inc:fname#.+#' )
    def static( fname ):
        'static files'
        if request['REMOTE_ADDR'] != '127.0.0.1':
            return 'not permitted.'
        return static_file( '/inc/%s' % fname, root='.' )
    

if __name__ == '__main__':
    InitDB()
    SqliteDB.SetMod()
    logging.basicConfig( filename = LOG_FILE, level = logging.DEBUG )
    PFPMessage.Init()
    NeighborNode.Init()
    PeerForum.ChkEnv()
    debug( True )
    run( host = '0.0.0.0', port = 8000, reloader = True )   #set reloader to False to avoid initializing twice.
