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
from protocol import PFPMessage, QryPubKeyMsg, NodeInfoMsg, GetNodeMsg, NodeAnswerMsg, SearchAddrMsg, \
                    NoticeMsg, ChkTreeMsg, GetTreeMsg, AtclDataMsg, GetTimeLineMsg
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
    def SendToAddr( cls, msgType, addr, bp = 'HTTP', **kwds ):
        "no neighbor data for addr. for QryPubKeyMsg"
        Remote = NeighborNode( address = addr, ServerProtocol = bp )
        cls.SendMessage( Remote, msgType, msgType, **kwds )
        
    @classmethod
    def SendMessage( cls, Remote, *msgTypes, **kwds ):
        "send to certain remote node."
        Msgs = [PFPMessage( msgType ) for msgType in msgTypes]
        [Msg.SetRemoteNode( Remote ) for Msg in Msgs]
        ReplyStr = Remote.Send( u'\n'.join( [Msg.Issue() for Msg in Msgs] ))
        print '\nReplyStr =', ReplyStr
        cls.Reply( ReplyStr.split( '\n' ))
        
#        task = QryPubKeyTask( Remote )
#        task.Start()
    
    @classmethod
    def SendToAll( cls, *msgTypes, **kwds ):
        ""
        print 'SendToAll'
        for Remote in NeighborNode.AllTargets():       #may in thread
            cls.SendMessage( Remote, *msgTypes, **kwds )
    
    @classmethod
    def Dida( cls, counter = [0] ):
        ""
        print 'PeerForum.Dida'
        counter[0] = n = counter[0] + 1
        if n % CommunicateCycle == 0:
            cls.Communicate()
        return {}
    
    @classmethod
    def Communicate( cls ):
        ""
        print 'PeerForum.Communicate'
#        Remote = NeighborNode.Pick()
#        print 'Pick NeighborNode', Remote
#        if Remote is None:
#            return
#        task = QryPubKeyTask( Remote )
#        task.Start()
    
    @classmethod
    def Reply( cls, msgLines ):
        "reply other nodes."
        print 'Reply'
        for MsgStr in filter( None, msgLines ):
            print MsgStr
            ComingMsg = PFPMessage( ord( MsgStr[0] ))
            Neighbor = ComingMsg.Receive( loads( MsgStr[1:] ))      #create neighbor obj from MsgStr
            
        return Neighbor.AllToSend()

#    @classmethod
#    def Reply0( cls, msgStr ):
#        "reply other nodes."
#        #print 'PeerForum.Reply', ord( msgStr[0] ), msgStr
#        ComingMsg = PFPMessage( ord( msgStr[0] ))
#        MsgBody = loads( msgStr[1:] )
#        
#        VerifyStr = ComingMsg.GetBody( MsgBody )
#        if VerifyStr:
#            Neighbor = NeighborNode.Get( ComingMsg.PubKey, loads( VerifyStr ))
#            Neighbor.Verify( VerifyStr, decodestring( MsgBody['sign'] ))
#        else:
#            Neighbor = NeighborNode.Get( ComingMsg.PubKey, MsgBody )
#            
#        Messages = Neighbor.Reply( ComingMsg ) + Neighbor.Append()
#        print 'Messages = ', Messages
#        
#        return Messages

    #===================== http apis with bottle ===================================
    @staticmethod
    @post( '/node' )
    def pfp():
        'pfp api'
        if request.method == 'GET':
            return 'not permitted.'
        
        #AllMsgs = reduce( list.__add__, [PeerForum.Reply( msg ) for msg in request.POST['pfp'].split( '\n' ) if msg] )
        AllMsgs = PeerForum.Reply( request.POST['pfp'].split( '\n' ))
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
    PeerForum.SendToAddr( 0x10, 'http://127.0.0.1:8001/node' ) #test
    debug( True )
    run( host = '0.0.0.0', port = 8000, reloader = False )   #set reloader to False to avoid initializing twice.
