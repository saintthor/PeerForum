# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 22:04:20 2015

@author: thor
"""

import logging

from threading import Thread
from Queue import Queue, Empty
from random import choice, randint
import rsa1 as rsa
from md5 import md5
from base64 import encodestring, decodestring
import urllib2
from urllib import urlencode

from sqlitedb import SqliteDB, CreateSelfNode, GetAllNode, GetNodeById, GetNodeByPubKeyOrNew, UpdateNodeOrNew
from exception import *
from const import TechInfo, PFPVersion, SignHashFunc
from crypto import CBCEncrypt, CBCDecrypt


class NeighborNode( object ):
    ""
    LiveD = {}
    AllNodes = []
    transD = {
        'id': 'id',
        'PubKey': 'PubKey',
        'PFPVer': 'PFPVer',
        'NodeName': 'name',
        'Description': 'discription',
        'Address': 'address',
        'NodeTypeVer': 'TechInfo',
        'BaseProtocol': 'ServerProtocol',            
            }
    
    
    @classmethod
    def Init( cls ):
        ""
        cls.AllNodes = GetAllNode( 'id', 'level' )
    
    @classmethod
    def Pick( cls ):
        "pick one neighbor by chance of level to start communication"
        Nodes = cls.AllNodes
        if Nodes:
            SumLevel = sum( [n[1] for n in Nodes] )
            point = randint( 0, SumLevel - 1 )
            for node in Nodes:
                point -= node[1]
                if point < 0:
                    return cls( **GetNodeById( node[0] ))
    
    @classmethod
    def Get( cls, pubK, msgBody ):
        ""
        return cls.LiveD.setdefault( pubK, cls._New( msgBody ))
        
    @classmethod
    def _New( cls, msgBody ):
        ""
        condi = { cls.transD.get( k, k ): v for k, v in msgBody.items() if k not in ( 'Time', ) }
        #CreateNodeORUpdate( condi )
        GetNodeByPubKeyOrNew( condi )
        return cls( **condi )
    
    def __init__( self, **kwds ):
        ""
        self.SendBuffer = []
        self.tasks = set( [] )
        self.id = self.PubKey = None
        for k, v in kwds.items():
            setattr( self, k, v )
        #if hasattr( self, 'PubKey' ):
        if kwds.get( 'PubKey' ):
            self.PubKey = rsa.PublicKey.load_pkcs1( self.PubKey )
    
    def Update( self, param ):
        ""
        for k, v in param.items():
            setattr( self, k, v )
        self.Save()
        
    def InitPubKey( self, pubK ):
        "init pubkey if it is avoid."
        if not isinstance( self.PubKey, rsa.PublicKey ):
            self.PubKey = pubK
            self.Save()
            return True
    
    def Save( self ):
        ""
        if self.id is not None:
            where = { 'id': self.id }
        else:
            where = {}
        #print where, self.id
        param = { k: getattr( self, k ) for k in self.transD.values() if hasattr( self, k ) and k != 'id' }
        UpdateNodeOrNew( param, where )
    
    def Encrypt( self, s ):
        ""
        if not hasattr( self, 'PubKey' ):
            raise NodePubKeyInvalidErr
        k = ''.join( [choice( "1234567890)(*&^%$#@!`~qazxswedcvfrtgbnhyujm,kiolp;.[]{}:?><\"\\'/PLOKMIJNUHBYGVTFCRDXESZWAQ" )
                        for i in range( 32 )] )
        print 'NeighborNode.Encrypt', k, self.PubKey
        return {
            "msg": encodestring( CBCEncrypt( s, k )),
            "key": encodestring( rsa.encrypt( k, self.PubKey )),
                }
    
    def Verify( self, message, sign ):
        ""
        return rsa.verify( message, sign, self.PubKey )                
                
    def Send( self, msgLines ):
        "send to remote node"
        addiLines = self.SendBuffer
        self.SendBuffer = []
        data = urlencode( { 'pfp': msgLines + '\n' + '\n'.join( addiLines ) } )
        print self.address
        req = urllib2.Request( self.address, data )
        response = urllib2.urlopen( req )
        
        return response.read()
    
#    def SetTask( self, task ):
#        ""
#        self.tasks.add( task )
    
    def ChkTask( self ):
        ""
        self.tasks.discard( { task for task in self.tasks if task.TimeOver() })
        
    def Buffer( self, msgStrs ):
        "buffer the message. wait to send."
        self.SendBuffer.extend( msgStrs )
    
    def AllToSend( self ):
        "get the additional messages to the neighbor"
        Msgs = self.SendBuffer
        self.SendBuffer = []
        return Msgs

class SelfNode( object ):
    "peerforum self node"
    @classmethod
    def New( cls ):
        "create a new self node."
        PubKey, PriKey = rsa.newkeys( 2048 )
        CreateSelfNode( PubKey = PubKey.save_pkcs1(), PriKey = PriKey.save_pkcs1() )
        
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
        print 'SelfNode.Decrypt', self.PubKey, self.PriKey
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


