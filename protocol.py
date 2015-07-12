#! /usr/bin/env python
#coding=utf-8

import rsa1 as rsa

from time import time
from json import loads, dumps
from base64 import encodestring, decodestring

from exception import *
from const import MaxTimeDiff


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
    
    def __new__( cls, code ):
        ""
        SubClass = cls.MsgMap[code]
        return object.__new__( SubClass )
    
    def __init__( self, code ):
        ""
        self.code = code
    
    def GetBody( self, msgD ):
        "this is a received message from remote. decrypt and verify."
        BodyStr = self.LocalNode.Decrypt( decodestring( msgD['msg'] ), decodestring( msgD['key'] ))
        self.ChkMsgBody( loads( BodyStr ))
        return BodyStr
    
    def VerifyBody( self, verifyFunc, bodyStr, msgD ):
        ""
        if not verifyFunc( bodyStr, decodestring( msgD['sign'] )):
            raise VerifyFailedErr
    
    def ChkMsgBody( self, bodyD ):
        ""
        if not bodyD.viewkeys() > self.MustHas:
            raise MsgKeyLackErr
            
        for k, v in bodyD.items():
            try:
                val = getattr( self, '_Check_%s' % k )( v )
                if val is not None:
                    bodyD[k] = val
            except AttributeError:
                pass
        
        for k, v in bodyD.items():
            setattr( self, k, v )
        
        
    def Reply( self, rmtNode ):
        ""
        #print 'PFPMessage.Reply'
        if self.ReplyCode == 0:
            return ()
        RplMsg = PFPMessage( self.ReplyCode )
        RplMsg.SetRemoteNode( rmtNode )
        return RplMsg.Issue(),
    
    def Issue( self ):
        ""
        self.body['Time'] = int( time() * 1000 )
        self.body['PubKey'] = self.LocalNode.PubKeyStr
        self.body['Addr'] = self.LocalNode.Addr
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
    ""
    code = 0x10
    MustHas = { 'Time', 'PubKey' }
    ReplyCode = 0x11
    
    def EncryptBody( self ):
        "do not encrypt for this message."
        return dumps( self.body )    

    def GetBody( self, msgD ):
        "do not verify or decrypt."
        self.ChkMsgBody( msgD )
        return ''
    
    def VerifyBody( self, *args ):
        ""
        pass
    
class NodeAnswerMsg( PFPMessage ):
    ""
    code = 0x11
    Keys = { 'Address', 'NodeName', 'NodeTypeVer', 'PFPVer', 'BaseProtocol', 'Description' }
    def __init__( self, code ):
        ""
        self.code = code
        self.body = self.LocalNode.GetInfo()

class GetNodeMsg( PFPMessage ):
    ""
    code = 0x12

class ChangeAddrMsg( PFPMessage ):
    ""
    code = 0x13

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



class Task( object ):
    ""
    MsgSteps = []
    
    def __init__( self, rmtNode ):
        ""
        self.RemoteNode = rmtNode
    
    def run( self ):
        ""
        for go, come in self.MsgSteps:
            if come is None:
                yield go
                break
            reply = yield go
            while reply != come:
                reply = yield None
        
class QryPubKeyTask( Task ):
    ""
    MsgSteps = (
        ( QryPubKeyMsg, NodeAnswerMsg ),
        ( NodeAnswerMsg, None ),
            )
                
class GetNodeTask( Task ):
    ""
    MsgSteps = (
        ( GetNodeMsg, NodeAnswerMsg ),
            )
            
class ChangeAddrTask( Task ):
    ""
    MsgSteps = (
        ( ChangeAddrMsg, None ),
            )
            
class SearchAddrTask( Task ):
    ""
    MsgSteps = (
        ( SearchAddrMsg, ChangeAddrMsg ),
            )
            
class SyncAtclTask( Task ):
    ""
    MsgSteps = (
        ( ChkTreeMsg, GetTreeMsg ),
        ( AtclDataMsg, None ),
            )
            
class TimeLineAtclTask( Task ):
    ""
    MsgSteps = (
        ( GetTimeLineMsg, AtclDataMsg ),
            )
            
            
            
    