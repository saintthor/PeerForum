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

from user import SelfUser
from node import NeighborNode, SelfNode
from tree import Article, Topic
from protocol import PFPMessage, GetTimeLineMsg
from const import LOG_FILE, CommunicateCycle, GetTimeLineInHours
from sqlitedb import SqliteDB, InitDB, GetAtclIdByUser
from exception import *


class PeerForum( object ):
    "physical node"
    LocalNode = None
    LocalUser = None
    
    @classmethod
    def cmdChkEnv( cls, *args ):
        ""
        result = {}
        try:
            cls.LocalNode = PFPMessage.LocalNode = SelfNode()
            result['CurNode'] = cls.LocalNode.Issue()
            cls.LocalUser = SelfUser()
            result['CurUser'] = cls.LocalUser.Issue()
        except NoAvailableNodeErr:
            result.setdefault( 'error', [] ).append( 'no availabel self node.' )
            
        return result
    
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
        Remote = NeighborNode( Addrs = [[0, addr]], ServerProtocol = bp )
        cls.SendMessage( Remote, msgType, **kwds )
        
    @classmethod
    def SendMessage( cls, Remote, *msgTypes, **kwds ):
        "send to certain remote node."
        print 'PeerForum.SendMessage'
        Msgs = [PFPMessage( msgType ) for msgType in msgTypes]
        [Msg.SetRemoteNode( Remote ) for Msg in Msgs]
        [Msg.InitBody() for Msg in Msgs]
        Remote.Buffer( [Msg.Issue() for Msg in Msgs] )
        while Remote is not None:
            ReplyStr = cls.Send( *Remote.AllToSend() )
            print '\nReplyStr =', ReplyStr
            if not ReplyStr:
                break
            Remote = cls.Reply( ReplyStr.split( '\n' ))
    
    @classmethod
    def SendMsgToRemote( cls, remote, msg ):
        ""
        print 'PeerForum.SendMsgToRemote'
        msg.SetRemoteNode( remote )
        remote.Buffer(( msg.Issue(), ))
        while remote is not None:
            ReplyStr = cls.Send( *remote.AllToSend())
            print '\nReplyStr =', ReplyStr
            if not ReplyStr:
                break
            remote = cls.Reply( ReplyStr.split( '\n' ))        
        
    
    @classmethod
    def Send( cls, addrs, msgs ):
        "send to remote node"
        print 'PeerForum.Send', addrs
        data = urlencode( { 'pfp': '\n'.join( msgs ) } )
        for Type, addr in addrs:
            try:
                req = urllib2.Request( addr, data )
                print 'PeerForum.Send to', addr, len( data )
                response = urllib2.urlopen( req )
                return response.read()
                break
            except:
                print traceback.format_exc()
                pass
        print 'PeerForum.Send all addrs failed.'
        return ''
    
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
    
#    @classmethod
#    def SendMsgToAll( cls, msg ):
#        ""
#        print 'SendToAll'
#        for Remote in NeighborNode.AllTargets():       #may in thread
#            try:
#                cls.SendMsgToRemote( Remote, msg )
#            except:
#                pass
    
    @classmethod
    def GetTimeLine( cls, userPubK, From = None, To = None ):
        ""
        To = To or int( time() * 1000 )
        From  = From or To - GetTimeLineInHours * 3600 * 1000
        existKs = GetAtclIdByUser( userPubK, From, To )
        
        Msg = GetTimeLineMsg()
        Msg.InitBody( UserPubKey = userPubK, From = From, To = To, Exist = existKs )
        
        print 'PeerForum.GetTimeLine'
        for Remote in NeighborNode.AllTargets():       #may in thread
            try:
                cls.SendMsgToRemote( Remote, Msg )
            except:
                print traceback.format_exc()
    
    @classmethod
    def cmdLike( cls, param ):
        ""
        Like = Article.New( cls.LocalUser, Type = 1, ParentID = param['atclId'], RootID = param['root'] )
        Like.Save()
        return { 'Like': Like.Show() }
    
    @classmethod
    def cmdSetStatus( cls, param ):
        ""
        Atcl = Article.Get( param['atclId'] )
        Atcl.SetStatus( param['status'] )
        return { 'SetStatus': 'ok' }
    
    @classmethod
    def cmdReply( cls, param ):
        ""
        Reply = Article.New( cls.LocalUser, ParentID = param['parent'], RootID = param['root'],
                            content = param['content'].decode( 'utf-8' ))
        Reply.Save()
        return { 'Reply': [Reply.id, Reply.Show()] }
        
    @classmethod
    def cmdAddLabel( cls, param ):
        ""
        NewLabelStr = Topic.EditLabel( param['rootId'], param['label'].decode( 'utf-8' ), '+' )
        return { 'UpdateLabel': { param['rootId']: NewLabelStr }}
        
    @classmethod
    def cmdDelLabel( cls, param ):
        ""
        NewLabelStr = Topic.EditLabel( param['rootId'], param['label'].decode( 'utf-8' ), '-' )
        return { 'UpdateLabel': { param['rootId']: NewLabelStr }}
        
    @classmethod
    def cmdGetAtclTree( cls, param ):
        ""
        RplCmd = {
            'flow': 'AtclTree',
            'last': 'AtclTree',
            'tree': 'ShowTree',
                }[param['mode']]
        return { RplCmd: Topic.ShowAll( param['root'] ) }
    
    @classmethod
    def cmdNewTopic( cls, topic ):
        ""
        print topic['Labels'], topic['life']
        life = int( topic['life'] )
        Labels = topic['Labels'].decode( 'utf-8' )
        content = topic['content'].decode( 'utf-8' )
        
        Root = Article.New( cls.LocalUser, content = content, life = life, Labels = Labels )
        Root.Save()
        return { 'NewTopic': Topic.ListById( Root.id ) }
    
    @classmethod
    def cmdGetTpcList( cls, condi ):
        ""
        #print 'cmdGetTpcList', condi['label']
        SortCol = condi['sortby']
        Offset = condi['start']
        Label = condi['label'].decode( 'utf-8' )
        
        return { 'PageTopics': Topic.ListPage( Label, Offset, SortCol ) }
        
    @classmethod
    def cmdDida( cls, counter = [0] ):
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
#        if n % CommunicateCycle == 0:
#            cls.Communicate()
        return {}
        
    @classmethod
    def Reply( cls, msgLines ):
        "reply other nodes."
        print '===== Reply ====='
        #sleep( 1 )
        Neighbor = None
        for MsgStr in filter( None, msgLines ):
            ComingMsg = PFPMessage( ord( MsgStr[0] ))
            print len( MsgStr ), ComingMsg.__class__.__name__
            Neighbor = ComingMsg.Receive( loads( MsgStr[1:] ))      #create neighbor obj from MsgStr
            
        return Neighbor

    #===================== http apis with bottle ===================================
    @staticmethod
    @post( '/node' )
    def pfp():
        'pfp api'
        if request.method == 'GET':
            return 'not permitted.'
        
        #some message must be responses
        Remote = PeerForum.Reply( filter( lambda ln: ln and ord( ln[0] ) not in ( 0x21, 0x23 ), request.POST['pfp'].split( '\n' )))
        # for testing ---------
        #PeerForum.cmdDida()
        #----------------------
        if Remote is None:
            return ''
        addrs, AllMsgs = Remote.AllToSend()
        print 'pfp end', time()
        return '\n'.join( AllMsgs )
        
    @staticmethod
    @route( '/' )
    @post( '/' )
    def local():
        'for local ui'
        #if re.match( r'^localhost(\:\d+)?$', request.environ.get( 'HTTP_HOST' )) is None:
        if request['REMOTE_ADDR'] != '127.0.0.1':
            return 'not permitted.'
        if request.method == 'GET':
            return static_file( 'index.html', root='.' )
        try:
            print 'cmd:', request.POST['cmd']
            result = getattr( PeerForum, 'cmd' + request.POST['cmd'] )( request.POST )
            #print result
            return dumps( result )
        except Exception, e:
            print traceback.format_exc()
            #logging.error( traceback.format_exc())
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
    #PeerForum.GetTimeLine( '-----BEGIN RSA PUBLIC KEY-----\nMIIBCgKCAQEAzXrwCvJM60raP3dcbreAdJCVzKCwXD9M8QFrAMPfQMJ2eSj18fib\nbCTvCqP+saX9WzAtAeuD4042GEQiV/28z3iX3cL2njHaH9G5H7b9Eip5wbQyH0Ji\nU6wHOvQuBuB69gjVbcRwoMnGXYwEC6hxXLPNcBas1f3xunm8HIRM1Iypkk+BmFJW\n47vrekwmYGfiNeO8mnlqrwkzvW91CuTzoZEfg8PE70QuwDXaLwicoHtJYG34OEbl\ncUbCkmibKMO3M7yki5MyfQicxpOM6be2nmXDuLFA47CoH7xPUfSP9Wd6bctJfRwX\nCf1wyAHhZjYTCWdvQ+Vy567y+uzSosb1XwIDAQAB\n-----END RSA PUBLIC KEY-----\n', From = 1400801099622 )
    #from tree import Topic
    #Topic.Patch()
    #PeerForum.SendToAddr( 0x10, 'http://127.0.0.1:8000/node' )
    threading.Thread( target = PeerForum.SendToAll, args = ( 0x20, )).start()
    #raise
    return
    
    
if __name__ == '__main__':
    InitDB()
    SqliteDB.SetMod()
    logging.basicConfig( filename = LOG_FILE, level = logging.DEBUG )
    PFPMessage.Init()
    SelfUser.Init()
    NeighborNode.Init()
    #PeerForum.cmdChkEnv()
    #test()
    debug( True )
    run( host = '0.0.0.0', port = 8000, reloader = True )   #set reloader to False to avoid initializing twice.
