# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 15:33:58 2015

@author: thor
"""
import logging
import traceback
from json import loads, dumps
#import re
import rsa1 as rsa

from time import time, sleep
from bottle import route, run, post, debug, request, static_file

import user

from node import NeighborNode, SelfNode
from protocol import PFPMessage
from const import LOG_FILE
from sqlitedb import SqliteDB, InitDB
from exception import *


class PeerForum( object ):
    "physical node"
    LocalNode = None
    LiveNeighborD = {}
    
    @classmethod
    def ChkEnv( cls ):
        ""
        for i in range( 2 ):
            try:
                cls.LocalNode = PFPMessage.LocalNode = SelfNode()
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
    
    @classmethod
    def Reply( cls, msgStr ):
        ""
        print 'PeerForum.Reply', msgStr
        Message = PFPMessage( ord( msgStr[0] ))
        MsgBody = loads( msgStr[1:] )
        Message.Receive( MsgBody )
        Neighber = cls.LiveNeighborD.setdefault( Message.PubKey, NeighborNode.New( MsgBody ))
        Messages = Neighber.Reply( Message ) + Neighber.Append()
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
    PeerForum.ChkEnv()
    debug( True )
    run( host = '0.0.0.0', port = 8000, reloader = True )
