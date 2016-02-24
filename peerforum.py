# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 15:33:58 2015

@author: thor
"""
import logging
import traceback
import threading
from json import loads, dumps
from Queue import Empty

from time import time
from bottle import route, run, post, debug, request, static_file
import urllib2
from urllib import urlencode

from user import SelfUser
from node import NeighborNode, SelfNode
from tree import Article, Topic
from protocol import PFPMessage, GetTimeLineMsg
from const import LOG_FILE, GetTimeLineInHours, LocalPort, AutoNode
from sqlitedb import SqliteDB, InitDB, GetAtclIdByUser, GetAllLabels, RecordUser, GetAllUsers
from exception import *


class PeerForum( object ):
    "physical node"
    LocalNode = None
    LocalUser = None
    
    @classmethod
    def Init( cls ):
        ""
        cls.LocalNode = PFPMessage.LocalNode = SelfNode()
        cls.LocalUser = SelfUser()
    
    @classmethod
    def cmdChkEnv( cls, *args ):
        ""
        result = {}
#        try:
#            cls.LocalNode = PFPMessage.LocalNode = SelfNode()
#            result['CurNode'] = cls.LocalNode.Issue()
#            cls.LocalUser = SelfUser()
#            result['CurUser'] = cls.LocalUser.Issue()
#        except NoAvailableNodeErr:
#            result.setdefault( 'error', [] ).append( 'no availabel self node.' )
            
        result['CurNode'] = cls.LocalNode.Issue()
        result['CurUser'] = cls.LocalUser.Issue()
        result['AllLabels'] = GetAllLabels()
        result['AllUsers'] = GetAllUsers()
        
        return result
        
    @classmethod
    def SendToAddr( cls, msgType, addr, bp = 'HTTP', **kwds ):
        "no neighbor data for addr. for QryPubKeyMsg"
        #logging.debug( 'SendToAddr addr = %s' % repr( addr ))
        Remote = NeighborNode( Addrs = [( 0, addr )], ServerProtocol = bp )
        cls.SendMessage( Remote, msgType, **kwds )
        
    @classmethod
    def SendMessage( cls, Remote, *msgTypes, **kwds ):
        "send to certain remote node."
        Msgs = [PFPMessage( msgType ) for msgType in msgTypes]
        [Msg.SetRemoteNode( Remote ) for Msg in Msgs]
        [Msg.InitBody() for Msg in Msgs]
        Remote.Buffer( [Msg.Issue() for Msg in Msgs] )
        while Remote is not None:
            ReplyStr = cls.Send( *Remote.AllToSend() )
            if not ReplyStr:
                break
            Remote = cls.Reply( ReplyStr.split( '\n' ))
    
    @classmethod
    def SendMsgToRemote( cls, remote, msg ):
        ""
        msg.SetRemoteNode( remote )
        remote.Buffer(( msg.Issue(), ))
        while remote is not None:
            ReplyStr = cls.Send( *remote.AllToSend())
            if not ReplyStr:
                break
            remote = cls.Reply( ReplyStr.split( '\n' ))        
    
    @classmethod
    def Send( cls, addrs, msgs ):
        "send to remote node"
        data = urlencode( { 'pfp': '\n'.join( msgs ) } )
        logging.debug( 'Send addrs: %s' % repr( addrs ))
        for Type, addr in set( addrs ):
            try:
                req = urllib2.Request( addr, data )
                response = urllib2.urlopen( req )
                return response.read()
                break
            except:
                pass
        return ''
    
    @classmethod
    def SendBuffer( cls, remote ):
        ""
        threading.Thread( target = cls.Send, args = remote.AllToSend() ).start()
        
    @classmethod
    def SendToAll( cls, *msgTypes, **kwds ):
        ""
        for Remote in NeighborNode.AllTargets():       #may in thread
            try:
                cls.SendMessage( Remote, *msgTypes, **kwds )
            except:
                pass
        
    @classmethod
    def GetTimeLine( cls, userPubK, From = None, To = None ):
        ""
        To = To or int( time() * 1000 )
        From  = From or To - GetTimeLineInHours * 3600 * 1000
        existKs = GetAtclIdByUser( userPubK, From, To )
        
        Msg = GetTimeLineMsg()
        Msg.InitBody( UserPubKey = userPubK, From = From, To = To, Exist = existKs )
        
        for Remote in NeighborNode.AllTargets():       #may in thread
            try:
                cls.SendMsgToRemote( Remote, Msg )
            except:
                logging.error( traceback.format_exc())
    
#    @classmethod
#    def cmdLike( cls, param ):
#        ""
#        Like = Article.New( cls.LocalUser, Type = 1, ParentID = param['atclId'], RootID = param['root'] )
#        Like.Save()
#        return { 'Like': Like.Show() }
    
    @classmethod
    def cmdEditSelfNode( cls, param ):
        ""
        PortStr = ':%d' % LocalPort
        addrs = [(( addr + PortStr ) if PortStr not in addr else addr ) for addr in loads( param['Addresses'] )]
        cls.LocalNode.Edit( param['Name'].decode( 'utf-8' )[:10],
                           param['Desc'].decode( 'utf-8' )[:500], addrs )
        return { 'SetStatus': 'ok' }
    
    @classmethod
    def cmdAddNeighbor( cls, param ):
        ""
        cls.SendToAddr( 0x10, param['Address'] )
        return { 'AddNeighbor': 'ok' }

    @classmethod
    def cmdSetSelfUserName( cls, param ):
        ""
        cls.LocalUser.SetName( param['Name'].decode( 'utf-8' )[:10] )
        return { 'SetStatus': 'ok' }
    
    @classmethod
    def cmdSetUserStatus( cls, param ):
        ""
        PubKey, Name, Status = param['PubKey'], param['Name'].decode( 'utf-8' ), int( param['Status'] )
        RecordUser( PubKey, Name, Status )
        return { 'UserStatus': [PubKey, Name, Status] }
    
    @classmethod
    def cmdGetTimeLine( cls, param ):
        ""
        UserPubKey = param['user']
        if UserPubKey == 'me':
            UserPubKey = cls.LocalUser.PubKeyStr
        return { 'TimeLine': Article.ShowByUser( UserPubKey, int( param['before'] )) }
    
    @classmethod
    def cmdSetStatus( cls, param ):
        ""
        Atcl = Article.Get( param['atclId'] )
        Atcl.SetStatus( int( param['status'] ))
        return { 'SetStatus': 'ok' }
    
    @classmethod
    def cmdSearch( cls, param ):
        ""
        return { 'TimeLine': Article.Search( param['kword'].decode( 'utf-8' ), int( param['before'] )) }
        
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
        life = int( topic['life'] )
        Labels = topic['Labels'].decode( 'utf-8' )
        content = topic['content'].decode( 'utf-8' )
        
        Root = Article.New( cls.LocalUser, content = content, life = life, Labels = Labels )
        Root.Save()
        return { 'NewTopic': Topic.ListById( Root.id ) }
    
    @classmethod
    def cmdGetTpcList( cls, condi ):
        ""
        SortCol = condi['sortby']
        Before = int( condi['before'] )
        Label = condi['label'].decode( 'utf-8' )
        
        return { 'PageTopics': Topic.ListPage( Label, Before, SortCol ) }
        
    @classmethod
    def cmdDida( cls, param, counter = [0] ):
        ""
        while True:
            try:
                task, param = NeighborNode.taskQ.get_nowait()
                getattr( cls, task )( param )
            except Empty:
                break
            
        counter[0] = n = counter[0] + 1

        try:
            for _ in range( int( len( NeighborNode.AllNodes ) ** 0.5 )):
                Remote = NeighborNode.Pick()
                for cyc, mod, code in (
                            ( 1, 0, 0x20 ),         #QryTreeMsg
                            ( 6, 0, 0x11 ),        #NodeInfoMsg
                            ( 6, 5, 0x12 ),        #GetNodeMsg
                                    ):
                    if n % cyc == mod:
                        threading.Thread( target = cls.SendMessage, args = ( Remote, code )).start()
        except:
            pass
        
        return {}
        
    @classmethod
    def Reply( cls, msgLines ):
        "reply other nodes."
        Neighbor = None
        for MsgStr in filter( None, msgLines ):
            ComingMsg = PFPMessage( ord( MsgStr[0] ))
            logging.info( '---------coming msg---%s---%s' % ( ComingMsg.__class__.__name__, MsgStr[:20] ))
            Neighbor = ComingMsg.Receive( loads( MsgStr[1:] ))      #create neighbor obj from MsgStr
            
        return Neighbor

    #===================== http apis with bottle ===================================
    @staticmethod
    @post( '/' )
    def pfp():
        'pfp api'
        if request.method == 'GET':
            return 'not permitted.'
        
        Remote = PeerForum.Reply( filter( None, request.POST['pfp'].split( '\n' )))
        #Remote = PeerForum.Reply( filter( lambda ln: ln and ord( ln[0] ) not in ( 0x21, 0x23 ), request.POST['pfp'].split( '\n' )))
        # for testing ---------
        #PeerForum.cmdDida()
        #----------------------
        if Remote is None:
            return ''
        addrs, AllMsgs = Remote.AllToSend()
        logging.info( 'pfp return.' )
        return '\n'.join( AllMsgs )
        
    @staticmethod
    @route( '/web' )
    @post( '/web' )
    def local():
        'for local ui'
        #if re.match( r'^localhost(\:\d+)?$', request.environ.get( 'HTTP_HOST' )) is None:
        if request['REMOTE_ADDR'] != '127.0.0.1':
            return 'not permitted.'
        if request.method == 'GET':
            return static_file( 'index.html', root='.' )
        try:
            logging.info( 'cmd: %s' % request.POST['cmd'] )
            if AutoNode and request.POST['cmd'] in ( 'NewTopic', 'Reply', 'AddLabel', 'DelLabel', 'SetUserStatus',
                                                 'SetStatus', 'SetSelfUserName', 'AddNeighbor', 'EditSelfNode' ):
                return { 'error': 'autonode does not allow this action.' }
            result = getattr( PeerForum, 'cmd' + request.POST['cmd'] )( request.POST )
            return dumps( result )
        except Exception, e:
            logging.error( traceback.format_exc())
            return { 'error': str( e ) }
        
    @staticmethod
    @route( '/inc:fname#.+#' )
    def static( fname ):
        'static files'
        if not AutoNode and request['REMOTE_ADDR'] != '127.0.0.1':
            return 'not permitted.'
        return static_file( '/inc/%s' % fname, root='.' )

def test():
    ""
    #PeerForum.GetTimeLine( '-----BEGIN RSA PUBLIC KEY-----\nMIIBCgKCAQEAzXrwCvJM60raP3dcbreAdJCVzKCwXD9M8QFrAMPfQMJ2eSj18fib\nbCTvCqP+saX9WzAtAeuD4042GEQiV/28z3iX3cL2njHaH9G5H7b9Eip5wbQyH0Ji\nU6wHOvQuBuB69gjVbcRwoMnGXYwEC6hxXLPNcBas1f3xunm8HIRM1Iypkk+BmFJW\n47vrekwmYGfiNeO8mnlqrwkzvW91CuTzoZEfg8PE70QuwDXaLwicoHtJYG34OEbl\ncUbCkmibKMO3M7yki5MyfQicxpOM6be2nmXDuLFA47CoH7xPUfSP9Wd6bctJfRwX\nCf1wyAHhZjYTCWdvQ+Vy567y+uzSosb1XwIDAQAB\n-----END RSA PUBLIC KEY-----\n', From = 1400801099622 )
    #from tree import Topic
    #Topic.Patch()
    #PeerForum.SendToAddr( 0x10, 'http://127.0.0.1:8000/node' )
    #threading.Thread( target = PeerForum.SendToAll, args = ( 0x20, )).start()
    #raise
    return
    
    
if __name__ == '__main__':
    InitDB()
    SqliteDB.SetMod()
    logging.basicConfig( filename = LOG_FILE, level = logging.DEBUG )
    PFPMessage.Init()
    SelfUser.Init()
    NeighborNode.Init()
    PeerForum.Init()
    #test()
    debug( True )
    run( host = '0.0.0.0', port = LocalPort, reloader = True )   #set reloader to False to avoid initializing twice.
