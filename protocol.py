#! /usr/bin/env python
#coding=utf-8

import hashlib
import json
import re
import rsa1 as rsa

from time import time
from json import loads

from sqlitedb import SqliteDB
from exception import *


class PFPMessage( object ):
    ""
    MsgMap = {}
    
    @classmethod
    def Init( cls ):
        ""
        cls.MsgMap.update( { c.code: c for c in cls.__subclasses__() } )
    
    def __new__( cls, msg ):
        ""
        MsgD = loads( msg[1:] )
        SubClass = cls.MsgMap[msg[0]]
        
        if not MsgD.viewkeys() > SubClass.MustHas:
            raise MsgKeyLackErr
            
        for k, v in MsgD.items():
            Checker = cls.getattr( '_Check_%s' % k )
            if Checker is not None:
                val = Checker( v )
                if val is not None:
                    MsgD[k] = val
        
        return SubClass.__new__( SubClass, MsgD )
    
    @staticmethod
    def _Check_Time( v ):
        ""
        diff = abs( time() * 1000 - v )
        if diff > 15:
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
    AnswerCode = 0x11

class NodeAnswerMsg( PFPMessage ):
    ""
    code = 0x11

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



