# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 15:33:58 2015

@author: thor
"""
import logging
import traceback
import threading
from json import loads, dumps
from base64 import decodestring
from Queue import Empty
import rsa1 as rsa

from time import time, sleep
from bottle import route, run, post, debug, request, static_file
import urllib2
from urllib import urlencode

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
    def SendToAddr( cls, msgType, addr, bp = 'HTTP', **kwds ):
        "no neighbor data for addr. for QryPubKeyMsg"
        Remote = NeighborNode( address = addr, ServerProtocol = bp )
        cls.SendMessage( Remote, msgType, **kwds )
        
    @classmethod
    def SendMessage( cls, Remote, *msgTypes, **kwds ):
        "send to certain remote node."
        Msgs = [PFPMessage( msgType ) for msgType in msgTypes]
        [Msg.SetRemoteNode( Remote ) for Msg in Msgs]
        [Msg.InitBody() for Msg in Msgs]
        Remote.Buffer( [Msg.Issue() for Msg in Msgs] )
        while Remote is not None:
            #ReplyStr = Remote.Send()
            ReplyStr = cls.Send( *Remote.AllToSend())
            print '\nReplyStr =', ReplyStr
            if not ReplyStr:
                break
            Remote = cls.Reply( ReplyStr.split( '\n' ))
    
    @classmethod
    def Send( cls, addr, msgs ):
        "send to remote node"
        data = urlencode( { 'pfp': '\n'.join( msgs ) } )
        req = urllib2.Request( addr, data )
        print 'PeerForum.Send', addr, len( data )
        response = urllib2.urlopen( req )
        
        return response.read()
    
    @classmethod
    def SendBuffer( cls, remote ):
        ""
        print 'SendBuffer'
        threading.Thread( target = cls.Send, args = remote.AllToSend() ).start()
        
    @classmethod
    def SendToAll( cls, *msgTypes, **kwds ):
        ""
        print 'SendToAll'
        for Remote in NeighborNode.AllTargets():       #may in thread
            try:
                cls.SendMessage( Remote, *msgTypes, **kwds )
            except:
                pass
    
    @classmethod
    def Dida( cls, counter = [0] ):
        ""
        print 'PeerForum.Dida', NeighborNode.taskQ.qsize()
        while True:
            try:
                task, param = NeighborNode.taskQ.get_nowait()
                print '\nNeighborNode.task', task, param
                getattr( cls, task )( param )
            except Empty:
                break
            
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
        print '===== Reply ====='
        sleep( 1 )
        for MsgStr in filter( None, msgLines ):
            print len( MsgStr ), MsgStr[0]
            ComingMsg = PFPMessage( ord( MsgStr[0] ))
            Neighbor = ComingMsg.Receive( loads( MsgStr[1:] ))      #create neighbor obj from MsgStr
            
        return Neighbor

    #===================== http apis with bottle ===================================
    @staticmethod
    @post( '/node' )
    def pfp():
        'pfp api'
        if request.method == 'GET':
            return 'not permitted.'
        
        #AllMsgs = reduce( list.__add__, [PeerForum.Reply( msg ) for msg in request.POST['pfp'].split( '\n' ) if msg] )
        Remote = PeerForum.Reply( request.POST['pfp'].split( '\n' ))
        # for testing ---------
        PeerForum.Dida()
        #----------------------
        if Remote is None:
            return ''
        addr, AllMsgs = Remote.AllToSend()
        print 'pfp end', time()
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

def test():
    ""
    threading.Thread( target = PeerForum.SendToAll, args = ( 0x20, )).start()
    #raise
    return
    
    
if __name__ == '__main__':
    InitDB()
    SqliteDB.SetMod()
    logging.basicConfig( filename = LOG_FILE, level = logging.DEBUG )
    PFPMessage.Init()
    NeighborNode.Init()
    PeerForum.ChkEnv()
    #test()
    debug( True )
    run( host = '0.0.0.0', port = 8000, reloader = True )   #set reloader to False to avoid initializing twice.
