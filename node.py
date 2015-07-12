# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 22:04:20 2015

@author: thor
"""

import logging

from threading import Thread
from Queue import Queue
from random import choice
import rsa1 as rsa
from base64 import encodestring, decodestring

from sqlitedb import SqliteDB, CreateNodeORUpdate
from exception import *
from const import TechInfo, PFPVersion, SignHashFunc
from crypto import CBCEncrypt, CBCDecrypt

class Communication( Thread ):
    "communicate with remote node"
    
    def __init__( self, RmtAddr, RmtPubK, SelfAddr, SelfPriK ):
        Thread.__init__( self )
        self.RemoteAddr = RmtAddr
        self.RemotePubK = RmtPubK
        self.LocalAddr = SelfAddr
        self.LocalPriK = SelfPriK
    
    def run( self ):
        pass
    
    def CallRemote( self, msg ):
        ""
        pass
    
    def Sign( self ):
        ""
        pass


class NeighborNode( object ):
    ""
    @classmethod
    def New( cls, msgBody ):
        ""
        transD = {
            'NodeName': 'name',
            'Description': 'discription',
            'Address': 'address',
            'NodeTypeVer': 'TechInfo',
            'BaseProtocol': 'ServerProtocol',            
                }
        return cls( **{ transD.get( k, k ): v for k, v in msgBody.items() if k not in ( 'Time', ) } )
    
    def __init__( self, **kwds ):
        ""
        self.MsgQ = Queue()
        self.tasks = []
        CreateNodeORUpdate( kwds )
        for k, v in kwds.items():
            setattr( self, k, v )
        self.PubKey = rsa.PublicKey.load_pkcs1( self.PubKey )
    
    def Encrypt( self, s ):
        ""
        if not hasattr( self, 'PubKey' ):
            raise NodePubKeyInvalidErr
        k = ''.join( [choice( "1234567890)(*&^%$#@!`~qazxswedcvfrtgbnhyujm,kiolp;.[]{}:?><\"\\'/PLOKMIJNUHBYGVTFCRDXESZWAQ" )
                        for i in range( 32 )] )
        #print k, self.PubKey
        return {
            "msg": encodestring( CBCEncrypt( s, k )),
            "key": encodestring( rsa.encrypt( k, self.PubKey )),
                }
    
    def Verify( self, message, sign ):
        ""
        return rsa.verify( message, sign, self.PubKey )
        
    def Reply( self, msgObj ):
        "reply the message directlly"
        #print 'NeighborNode.Reply'
        return msgObj.Reply( self )
    
    def Append( self ):
        "get the additional messages to the neighbor"
        return ()


class SelfNode( object ):
    "peerforum self node"
    def __init__( self, condi = '' ):
        ""
        with SqliteDB() as cursor:
            if condi:
                sql = """select name, PubKey, PriKey, ServerProtocol, discription, address, level
                            from selfnode where %s and level >= 0;""" % condi
            else:
                sql = """select name, PubKey, PriKey, ServerProtocol, discription, address, level
                            from selfnode where level >= 0 order by level desc limit 1;"""
                            
            NodeData = cursor.execute( sql ).fetchone()
        
        if NodeData is None:
            raise NoAvailableNodeErr
            
        self.Name, self.PubKeyStr, PriKeyStr, self.SvPrtcl, self.Desc, self.Addr, self.Level = NodeData
        self.PubKey = rsa.PublicKey.load_pkcs1( self.PubKeyStr )
        self.PriKey = rsa.PrivateKey.load_pkcs1( PriKeyStr )
    
    def Decrypt( self, secMsg, secK ):
        ""
        key = rsa.decrypt( secK, self.PriKey )
        return CBCDecrypt( secMsg, key )
    
    def Sign( self, msg ):
        ""
        return encodestring( rsa.sign( msg, self.PriKey, SignHashFunc ))
        
    def GetInfo( self ):
        ""
        return {
            "Address": self.Addr,
            "NodeName": self.Name,
            "NodeTypeVer": TechInfo,
            "PFPVer": PFPVersion,
            "BaseProtocol": self.SvPrtcl,
            "Description": self.Desc,
                }
                
    def Show( self ):
        "show in local client"
        return [self.Name, self.PubKey, self.Level]


