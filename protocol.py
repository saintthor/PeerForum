#! /usr/bin/env python
#coding=utf-8

import rsa

from time import time
from json import loads, dumps
from base64 import decodestring
import logging

from exception import *
from const import MaxTimeDiff, MaxSearchAddrStep, GetTreeInHours
from node import NeighborNode
from tree import Topic, Article

class PFPMessage( object ):
    ""
    ReplyCode = 0
    BackCode = 0
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
        if not bodyD.viewkeys() >= self.MustHas:
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
        
    def Receive( self, msgBody ):
        ""   
        VerifyStr = self.GetBody( msgBody )
        if VerifyStr:                                   #not QryPubKeyMsg
            Neighbor = NeighborNode.Get( self.body['PubKeyStr'], loads( VerifyStr ))
            Neighbor.Verify( VerifyStr, decodestring( msgBody['sign'] ))
            #self.RcvData( Neighbor, loads( VerifyStr ) )
        else:
            Neighbor = NeighborNode.Get( self.body['PubKeyStr'], msgBody )
        
        Neighbor.Succeed( self.body['Time'] )
        if not self.FlowControl():
            return Neighbor
            
        self.RcvData( Neighbor )
        if self.ReplyCode > 0:
            Neighbor.Buffer( self.Reply( Neighbor ))
        if self.BackCode > 0:
            Neighbor.Buffer( self.Reply( Neighbor, self.BackCode ))
        
        return Neighbor
    
    def FlowControl( self ):
        "record each message for flow control."
        return True
        
        
    def RcvData( self, remote ):
        ""
        pass

    def Reply( self, rmtNode, rplCode = None ):
        ""
        RplMsg = PFPMessage( rplCode or self.ReplyCode )
        RplMsg.SetRemoteNode( rmtNode )
        
        if RplMsg.InitBody( self ) != False:
            return RplMsg.Issue(),
        return ()
    
    def Issue( self ):
        ""
        self.body['Time'] = int( time() * 1000 )
        self.body['PubKey'] = self.LocalNode.PubKeyStr
        #self.body['Address'] = self.LocalNode.Addr
        for k, v in self.body.items():
            if v is None:
                self.body[k] = ''
        return chr( self.code ) + self.EncryptBody()
    
    def EncryptBody( self ):
        "encrypt and sign"
        BodyStr = dumps( self.body )
        CryptMsgD = self.RemoteNode.Encrypt( BodyStr )
        CryptMsgD['sign'] = self.LocalNode.Sign( BodyStr )
        return dumps( CryptMsgD )
    
    def SetRemoteNode( self, rmtNode ):
        "send target"
        self.RemoteNode = rmtNode
    
    def PostTo( self, *nodes ):
        "send to remote node with no response expected"
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
            logging.error( '_Check_Time Error %s %s' % ( time() * 1000, v ))
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
    query the pubkey of the node that only known by addr.
    normal steps:
    A -----QryPubKeyMsg----> B      don't send more info because this message is not encrypted.
    A <----NodeInfoMsg------ B      A gets B's info includes PubKey
    A -----NodeInfoMsg-----> B      B gets A's info. they become neighbors.
    """
    code = 0x10
    ReplyCode = 0x11
    
    def InitBody( self ):
        "for send messages"
        self.body = {}        
        
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
        if forMsg is None:                              #to refresh self info to neighbors.
            self.body = self.LocalNode.GetInfo()
            
        elif isinstance( forMsg, QryPubKeyMsg ):        #--QryPubKeyMsg->, go on.
            self.body = self.LocalNode.GetInfo()
            self.body['Step'] = 1
            
        elif isinstance( forMsg, NodeInfoMsg ):
            if forMsg.body.get( 'Step', 0 ) == 0:       #--QryPubKeyMsg->, <-NodeInfoMsg--, --NodeInfoMsg->, Over.
                return False
            self.body = self.LocalNode.GetInfo()        #--QryPubKeyMsg->, <-NodeInfoMsg--, go on.
            #self.body['Step'] = 0
            
        elif isinstance( forMsg, SearchAddrMsg ):       #--SearchAddrMsg->
            #assert forMsg.body["ObjPubKey"] == self.LocalNode.PubKeyStr
            self.body = self.LocalNode.GetInfo()
            
    def RcvData( self, remote ):
        ""
        def ChkInnerAddr( addr ):
            return True
        
        self.body['Address'] = filter( ChkInnerAddr, self.body['Address'] )
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
        self.body = {
                "ObjPubKey": self.RemoteNode.PubKeyStr,
                #"ObjPubKey": self.LocalNode.PubKeyStr,
                "Step": 3,
                    }
                    
    def Receive( self, msgBody ):
        "PubKey and Address belongs to the source. ForwardPubKey belongs to the forwarder."   
        VerifyStr = self.GetBody( msgBody )
        
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
            MsgStrs = PFPMessage.Reply( self, SourceNode )
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
                FwdMsg.PostTo( ObjNode )
            elif Step > 0:
                objPKStr = FwdMsg.body["PubKey"]
                FwdMsg.PostTo( *[rmt for rmt in NeighborNode.AllTargets() if rmt.PubKeyStr != objPKStr] )
    
class NoticeMsg( PFPMessage ):
    ""
    code = 0x16

class QryTreeMsg( PFPMessage ):
    """
    ask remote node for trees by query conditions. and tell remote the hot trees to offer.
    A -----QryTreeMsg -----> B  ( optional )
    A <----TreesInfoMsg ---- B
    A -----GetTreeMsg -----> B
    A <----AtclDataMsg ----- B
    """
    code = 0x20
    ReplyCode = 0x21
    BackCode = 0x20
    
    def InitBody( self, forMsg = None ):
        ""
        t = int( time() * 1000 )
        #GetTreeInHours = 480
        Step = 1 if forMsg is None else ( forMsg.body.get( 'Step', 0 ) - 1 )
        if Step < 0:
            return False
        self.body = {
                "From": t - GetTreeInHours * 3600 * 1000,
                "To": t,
                "Status": 1,
                "Step": Step,
                    }

class TreesInfoMsg( PFPMessage ):
    ""
    code = 0x21
    ReplyCode = 0x22
    
    def InitBody( self, forMsg = None ):
        ""
        self.body = {
                'Offer': [tpc.GetInfo() for tpc in Topic.Filter( forMsg.body )],
                    }
        if not self.body['Offer']:
            return False

class GetTreeMsg( PFPMessage ):
    ""
    code = 0x22
    ReplyCode = 0x23
    
    def InitBody( self, forMsg = None ):
        ""
        if not forMsg.body.get( 'Offer' ):
            return False

        self.body = {
                'Trees': filter( None, [Topic.Compare( TreeInfo ) for TreeInfo in forMsg.body['Offer']] ),
                    }

class AtclDataMsg( PFPMessage ):
    ""
    code = 0x23
    
    def InitBody( self, forMsg = None ):
        ""        
        if isinstance( forMsg, GetTreeMsg ):
            if not forMsg.body.get( 'Trees' ):
                return False
            
            AskBackTrees = []       #for check leaf mode, if the remote leaves are more than local, askback
            Atcls = reduce( list.__add__, [Topic.GetReqAtcls( TreeReq, AskBackTrees.append )
                                            for TreeReq in forMsg.body['Trees']] )
            self.body = {
                    'Articles': [atcl.Issue() for atcl in Atcls if atcl.IsPassed()],
                        }
                        
            if AskBackTrees:
                self.AskBack( AskBackTrees )
                
        elif isinstance( forMsg, GetTimeLineMsg ):
            self.body = {
                    'Articles': [atcl.Issue() for atcl in Article.GetByUser(
                                    *map( forMsg.body.get, ['UserPubKey', 'From', 'To', 'Exist'] )
                                                                )],
                        }
                        
        if not self.body['Articles']:
            return False
                
                        
    def AskBack( self, trees ):
        "send back a GetTreeMsg if remote leaves are more than local"
        BackMsg = GetTreeMsg()
        BackMsg.SetRemoteNode( self.RemoteNode )
        BackMsg.body = { 'Trees': trees }
        BackMsg.RemoteNode.Buffer(( BackMsg.Issue(), ))

    def RcvData( self, remote ):
        ""
        Atcls = [Article.Receive( atclData ) for atclData in self.body['Articles']]
        Atcls.sort( key = Article.SortType )
        
        pkStr = remote.PubKeyStr
        
        for atcl in Atcls:
            if atcl.Check():
                atcl.Save( FromNode = pkStr )


class GetTimeLineMsg( PFPMessage ):
    ""
    code = 0x24
    ReplyCode = 0x23

    def InitBody( self, **body ):
        ""
        self.body = body
            
    