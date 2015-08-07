#! /usr/bin/env python
#coding=utf-8

import rsa1 as rsa

from time import time
from json import loads, dumps
from base64 import encodestring, decodestring

from exception import *
from const import MaxTimeDiff, TaskLiveSec, GetNodeStep, GetNodeMaxStep
from node import NeighborNode

class PFPMessage( object ):
    ""
    ReplyCode = 0
    MsgMap = {}
    MustHas = { 'Time', 'PubKey' }
    LocalNode = None
    
    @classmethod
    def Init( cls ):
        ""
        cls.MsgMap.update( { c.code: c for c in cls.__subclasses__() } )
    
    
    def __new__( cls, code = 0 ):
        ""
        if cls != PFPMessage:
            return object.__new__( cls )
        SubClass = cls.MsgMap[code]
        return object.__new__( SubClass )
    
    def __init__( self, code = 0 ):
        ""
        self.code = code or self.code
        
    def GetBody( self, msgD ):
        "this is a received message from remote. decrypt."
        BodyStr = self.LocalNode.Decrypt( decodestring( msgD['msg'] ), decodestring( msgD['key'] ))
        self.ChkMsgBody( loads( BodyStr ))
        return BodyStr
    
    def __getitems__( self, k ):
        ""
        pass
    
    def ChkMsgBody( self, bodyD ):
        "for received messages"
        if not bodyD.viewkeys() > self.MustHas:
            raise MsgKeyLackErr
            
        for k, v in bodyD.items():
            try:
                val = getattr( self, '_Check_%s' % k )( v )
                if val is not None:
                    bodyD[k] = val
                if k == 'PubKey':
                    bodyD['PubKeyStr'] = v
            except AttributeError:
                pass
        
        self.body = bodyD
#        for k, v in bodyD.items():
#            setattr( self, k, v )
        
    def Receive( self, msgBody ):
        "if Neighbor is None, the communication is founded by remote."   
        print
        VerifyStr = self.GetBody( msgBody )
        if VerifyStr:                                   #not QryPubKeyMsg
            print self.__class__.__name__, '.Receive 1: ', VerifyStr
            Neighbor = NeighborNode.Get( self.body['PubKeyStr'], loads( VerifyStr ))
            Neighbor.Verify( VerifyStr, decodestring( msgBody['sign'] ))
            #self.RcvData( Neighbor, loads( VerifyStr ) )
        else:
            print self.__class__.__name__, '.Receive 2: ', msgBody
            Neighbor = NeighborNode.Get( self.body['PubKeyStr'], msgBody )
            
        self.RcvData( Neighbor )
        Neighbor.Buffer( self.Reply( Neighbor ))
        
        return Neighbor
    
#    def Send( self ):
#        ""
#        self.RemoteNode.Send( self.Issue())
        
        
    def RcvData( self, remote ):
        ""
        pass

    def Reply( self, rmtNode ):
        ""
        print self.__class__.__name__, '.Reply', self.ReplyCode
        if self.ReplyCode == 0:
            return ()
        RplMsg = PFPMessage( self.ReplyCode )
        RplMsg.SetRemoteNode( rmtNode )
        
        if RplMsg.InitBody( self ) != False:
            return RplMsg.Issue(),
        return ()
    
    def Issue( self ):
        ""
        self.body['Time'] = int( time() * 1000 )
        self.body['PubKey'] = self.LocalNode.PubKeyStr
        self.body['Address'] = self.LocalNode.Addr
        for k, v in self.body.items():
            if v is None:
                self.body[k] = ''
        return chr( self.code ) + self.EncryptBody()
    
    def EncryptBody( self ):
        ""
        print 'EncryptBody', self.body
        BodyStr = dumps( self.body )
        CryptMsgD = self.RemoteNode.Encrypt( BodyStr )
        CryptMsgD['sign'] = self.LocalNode.Sign( BodyStr )
        #print type( CryptMsgD['msg'] ), CryptMsgD['msg']
        return dumps( CryptMsgD )
    
    def SetRemoteNode( self, rmtNode ):
        "send target"
        self.RemoteNode = rmtNode
        
    @staticmethod
    def _Check_Time( v ):
        ""
        diff = abs( time() * 1000 - v )
        if diff > MaxTimeDiff:
            raise RemoteTimeErr
    
    @staticmethod
    def _Check_PubKeyType( v ):
        ""
        if v.upper() != 'RSA':
            raise PubKeyTypeNotSupportedErr
        
    @staticmethod
    def _Check_PubKey( v ):
        ""
        return rsa.PublicKey.load_pkcs1( v )


class QryPubKeyMsg( PFPMessage ):
    """
    query the pubkey of the node only addr known.
    normal task steps:
    A -----QryPubKeyMsg----> B      don't send more info because this message is not encrypted.
    A <----NodeInfoMsg------ B      A gets B's info
    A -----NodeInfoMsg-----> B      B gets A's info. they become neighbors.
    """
    code = 0x10
    ReplyCode = 0x11
    
    def InitBody( self ):
        "for send messages"
        self.body = {}        
        
#    def Reply( self, rmtNode ):
#        ""
#        RplMsg = PFPMessage( self.ReplyCode )
#        RplMsg.InitBody( self )
#        RplMsg.SetRemoteNode( rmtNode )
#        return RplMsg.Issue(),
    
    def EncryptBody( self ):
        "do not encrypt for this message."
        return dumps( self.body )    

    def GetBody( self, msgD ):
        "do not verify or decrypt."
        self.ChkMsgBody( msgD )
    
    
class NodeInfoMsg( PFPMessage ):
    "confirm node info. answer for QryPubKeyMsg or SearchAddrMsg or itself"
    code = 0x11
    ReplyCode = 0x11
    Keys = { 'Address', 'NodeName', 'NodeTypeVer', 'PFPVer', 'BaseProtocol', 'Description' }
    
    def InitBody( self, forMsg = None ):
        ""
        print 'NodeInfoMsg.InitBody', forMsg
        if forMsg is None:                              #to refresh self info to neighbors.
            self.body = self.LocalNode.GetInfo()
            
        elif isinstance( forMsg, QryPubKeyMsg ):        #--QryPubKeyMsg->, go on.
            self.body = self.LocalNode.GetInfo()
            self.body['Step'] = 1
            print 'NodeInfoMsg.InitBody', self.body
            
        elif isinstance( forMsg, NodeInfoMsg ):
            if forMsg.body.get( 'Step', 0 ) == 0:       #--QryPubKeyMsg->, <-NodeInfoMsg--, --NodeInfoMsg->, Over.
                print '\nquery task finished.\n'
                return False
            self.body = self.LocalNode.GetInfo()        #--QryPubKeyMsg->, <-NodeInfoMsg--, go on.
            self.body['Step'] = 0
            print '\nquery task goes on.\n'
            
        elif isinstance( forMsg, SearchAddrMsg ):
            pass
            
    def RcvData( self, remote ):
        ""
        print 'NodeInfoMsg.RcvData'#, rcvBody
        remote.Update( self.body )


class GetNodeMsg( PFPMessage ):
    "ask for more neighbor node."
    code = 0x12
    ReplyCode = 0x13

    def InitBody( self ):
        ""
        self.body = self.LocalNode.GetInfo()
        self.body['Step'] = 3
        
    def RcvData( self, remote ):
        ""
        print 'GetNodeMsg.RcvData'


class NodeAnswerMsg( PFPMessage ):
    ""
    code = 0x13
    
    def InitBody( self, forMsg = None ):
        ""
        self.body = { 'Nodes': self.RemoteNode.GetSomeInfo() }
            
    def RcvData( self, remote ):
        ""
        print 'NodeAnswerMsg.RcvData: save neighbors here'


class AckMsg( PFPMessage ):
    "?"
    code = 0x14

class SearchAddrMsg( PFPMessage ):
    ""
    code = 0x15

class NoticeMsg( PFPMessage ):
    ""
    code = 0x16

class ChkTreeMsg( PFPMessage ):
    ""
    code = 0x20

class GetTreeMsg( PFPMessage ):
    ""
    code = 0x21

class AtclDataMsg( PFPMessage ):
    ""
    code = 0x22

class GetTimeLineMsg( PFPMessage ):
    ""
    code = 0x23


#no tasks. PHP should be a no status protocol.
#class Task( object ):
#    ""
#    MsgSteps = []
#    
#    def __init__( self, rmtNode ):
#        ""
#        self.RemoteNode = rmtNode
#        self.StartAt = time()
#        
#    def Start( self ):
#        ""
#        print 'Task.Start'
#        Steps = self.StepGen()
#        ComingMsgBuff = [None]
#        
#        while True:
#            try:
#                MsgClses = filter( None, [Steps.send( msg ) for msg in ComingMsgBuff] )
#                ComingMsgBuff = [None]
#                if not MsgClses:
#                    sleep( 1 )
#                    continue
#            except StopIteration:
#                print 'task over.'
#                break
#            
#            Msgs = [MsgCls() for MsgCls in MsgClses]
#            [msg.SetRemoteNode( self.RemoteNode ) for msg in Msgs]
#            print 'zzzzzzzzzzzzzz'
#            [msg.InitBody() for msg in Msgs]
#            reply = self.RemoteNode.Send( '\n'.join( [msg.Issue() for msg in Msgs] ))
#            print '============ get reply ============\n', reply
#            
#            for msgStr in filter( None, reply.split( '\n' )):
#                ComingMsg = PFPMessage( ord( msgStr[0] ))
#                ComingMsg.Receive( loads( msgStr[1:] ), self.RemoteNode )
#                ComingMsgBuff.append( ComingMsg )
#
#
#    def StepGen( self ):
#        "need rewrite"
#        for go, come in self.MsgSteps:
#            if come is None:
#                yield go
#                break
#            reply = yield go
#            while not isinstance( reply, come ):
#                reply = yield None
#    
#    def TimeOver( self ):
#        ""
#        return time() - self.StartAt > TaskLiveSec
#        
#    def __hash__( self ):
#        "no same type task in one node."
#        return hash( self.__class__ )
#        
#    def __cmp__( self, other ):
#        "no same type task in one node."
#        return cmp( self.__class__, other.__class__ )
#        
#        
#class QryPubKeyTask( Task ):
#    ""
#    MsgSteps = (
#        ( QryPubKeyMsg, NodeInfoMsg ),
#        ( NodeInfoMsg, None ),
#            )
#                
#class ChangeInfoTask( Task ):
#    ""
#    MsgSteps = (
#        ( NodeInfoMsg, None ),
#            )
#            
#class GetNodeTask( Task ):
#    ""
#    MsgSteps = (
#        ( GetNodeMsg, NodeAnswerMsg ),
#            )
#            
#class SearchAddrTask( Task ):
#    ""
#    MsgSteps = (
#        ( SearchAddrMsg, NodeInfoMsg ),
#            )
#            
#class SyncAtclTask( Task ):
#    ""
#    MsgSteps = (
#        ( ChkTreeMsg, GetTreeMsg ),
#        ( AtclDataMsg, None ),
#            )
#            
#class TimeLineAtclTask( Task ):
#    ""
#    MsgSteps = (
#        ( GetTimeLineMsg, AtclDataMsg ),
#            )
            
            
            
    