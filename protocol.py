#! /usr/bin/env python
#coding=utf-8

import rsa1 as rsa

#import threading
#import traceback
from time import time
from json import loads, dumps
from base64 import encodestring, decodestring

from exception import *
from const import MaxTimeDiff, MaxSearchAddrStep
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
        ""   
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
        
        if not self.FlowControl():
            return Neighbor
            
        self.RcvData( Neighbor )
        Neighbor.Buffer( self.Reply( Neighbor ))
        
        return Neighbor
    
    def FlowControl( self ):
        "record each message for flow control."
        return True
        
        
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
        "encrypt and sign"
        print self.__class__.__name__, '.EncryptBody', self.body
        BodyStr = dumps( self.body )
        CryptMsgD = self.RemoteNode.Encrypt( BodyStr )
        CryptMsgD['sign'] = self.LocalNode.Sign( BodyStr )
        #print CryptMsgD
        return dumps( CryptMsgD )
    
    def SetRemoteNode( self, rmtNode ):
        "send target"
        self.RemoteNode = rmtNode
    
    def PostTo( self, *nodes ):
        "send to remote node without expecting response"
        for rmtNode in nodes:
            self.SetRemoteNode( rmtNode )
            MsgStr = chr( self.code ) + self.EncryptBody()
            rmtNode.Buffer(( MsgStr, ))
            NeighborNode.taskQ.put(( 'SendBuffer', rmtNode ))
        
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
    normal steps:
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
            #print 'NodeInfoMsg.InitBody', self.body
            
        elif isinstance( forMsg, NodeInfoMsg ):
            if forMsg.body.get( 'Step', 0 ) == 0:       #--QryPubKeyMsg->, <-NodeInfoMsg--, --NodeInfoMsg->, Over.
                print '\nquery task finished.\n'
                return False
            self.body = self.LocalNode.GetInfo()        #--QryPubKeyMsg->, <-NodeInfoMsg--, go on.
            #self.body['Step'] = 0
            #print '\nquery task goes on.\n'
            
        elif isinstance( forMsg, SearchAddrMsg ):       #--SearchAddrMsg->
            #assert forMsg.body["ObjPubKey"] == self.LocalNode.PubKeyStr
            self.body = self.LocalNode.GetInfo()
            
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
        self.body = {}
        

class NodeAnswerMsg( PFPMessage ):
    ""
    code = 0x13
    
    def InitBody( self, forMsg = None ):
        ""
        self.body = { 'Nodes': self.RemoteNode.GetSomeInfo() }
            
    def RcvData( self, remote ):
        ""
        #print 'NodeAnswerMsg.RcvData: save neighbors here\n'
        for nbData in self.body['Nodes']:
            NeighborNode.NewNeighbor( nbData )


class AckMsg( PFPMessage ):
    "?"
    code = 0x14

class SearchAddrMsg( PFPMessage ):
    """
    ask addr for a node with pubkey known.
    nomal steps:
    A -----SearchAddrMsg---> B
    if B is the Obj or B has the Obj in neighbors:
        A <----NodeInfoMsg------ B      A gets Obj's info
    elif Step > 0:
        Step--
        B -----SearchAddrMsg---> C      ask more nodes
        if C is the Obj or C has the Obj in neighbors:
            A <----NodeInfoMsg------ C      A gets Obj's info
        elif Step > 0:
            ......
    """
    code = 0x15
    ReplyCode = 0x11

    def InitBody( self ):
        ""
        print 'SearchAddrMsg.InitBody'
        self.body = {
                "ObjPubKey": self.RemoteNode.PubKeyStr,
                #"ObjPubKey": self.LocalNode.PubKeyStr,
                "Step": 3,
                    }
                    
    def Receive( self, msgBody ):
        "PubKey and Address belongs to the source. ForwardPubKey belongs to the forwarder."   
        VerifyStr = self.GetBody( msgBody )
        print 'SearchAddrMsg.Receive: ', VerifyStr
        
        body = loads( VerifyStr )
        if 'ForwardPubKey' in self.body:
            SourceNode = NeighborNode( PubKey = self.body['PubKeyStr'], address = self.body['Address'] )    #temp node. do not save.
            ForwardNode = NeighborNode( PubKey = body['ForwardPubKey'] )    #temp node only for verifying
        else:
            ForwardNode = SourceNode = NeighborNode( PubKey = self.body['PubKeyStr'], address = self.body['Address'] )

        ForwardNode.Verify( VerifyStr, decodestring( msgBody['sign'] ))
        
        if not self.FlowControl():
            return
                
        if self.LocalNode.PubKeyStr == self.body["ObjPubKey"]:          #self is objnode
            print 'self is obj.'
            MsgStrs = PFPMessage.Reply( self, SourceNode )
            #print 'MsgStrs =', MsgStrs
            SourceNode.Buffer( MsgStrs )
            return SourceNode
        else:                                           #not found
            Step = self.body.get( 'Step', 0 )
            FwdMsg = PFPMessage( self.code )
            FwdMsg.body = {}
            FwdMsg.body.update( self.body )
            FwdMsg.body['Time'] = int( time() * 1000 )
            FwdMsg.body['Step'] = min( Step, MaxSearchAddrStep ) - 1
            FwdMsg.body['PubKey'] = FwdMsg.body.pop( 'PubKeyStr' )      #source node's pubK
            FwdMsg.body['ForwardPubKey'] = self.LocalNode.PubKeyStr     #forward node's pubK
            
            ObjNode = NeighborNode.SearchNode( self.body["ObjPubKey"] )
            if ObjNode is not None:
                print 'find obj in neighbors.'
                FwdMsg.PostTo( ObjNode )
            elif Step > 0:
                print 'forward to neighbors here.'
                objPKStr = FwdMsg.body["PubKey"]
                FwdMsg.PostTo( *[rmt for rmt in NeighborNode.AllTargets() if rmt.PubKeyStr != objPKStr] )
    
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

            
            
    