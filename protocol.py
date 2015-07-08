#! /usr/bin/env python
#coding=utf-8

import hashlib
import json
import re
import rsa1 as rsa

from time import time
from json import loads, dumps

from sqlitedb import SqliteDB
from exception import *
from const import MaxTimeDiff


class PFPMessage( object ):
    ""
    ReplyCode = 0
    MsgMap = {}
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
    
    def Receive( self, msgD ):
        "this is a received message from remote."
        if not msgD.viewkeys() > self.MustHas:
            raise MsgKeyLackErr
            
        for k, v in msgD.items():
            try:
                val = getattr( self, '_Check_%s' % k )( v )
                if val is not None:
                    msgD[k] = val
            except AttributeError:
                pass
        
        for k, v in msgD.items():
            setattr( self, k, v )
        
    def Reply( self ):
        ""
        print 'PFPMessage.Reply'
        if self.ReplyCode == 0:
            return ()
        RplMsg = PFPMessage( self.ReplyCode )
        return RplMsg.Issue(),
    
    def Issue( self ):
        ""
        self.body['Time'] = int( time() * 1000 )
        self.body['PubKey'] = self.LocalNode.PubKey
        self.body['Addr'] = self.LocalNode.Addr
        return chr( self.code ) + dumps( self.body )
        
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



