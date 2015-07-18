# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 22:04:20 2015

@author: thor
"""

import logging

from threading import Thread
#from Queue import Queue
from random import choice, randint
import rsa1 as rsa
from md5 import md5
from base64 import encodestring, decodestring
import urllib2
from urllib import urlencode

from sqlitedb import SqliteDB, CreateNodeORUpdate, CreateSelfNode, GetAllNode, GetNodeById
from exception import *
from const import TechInfo, PFPVersion, SignHashFunc
from crypto import CBCEncrypt, CBCDecrypt


class NeighborNode( object ):
    ""
    LiveD = {}
    AllNodes = []
    
    
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
        return cls.LiveD.setdefault( md5( pubK ).digest(), cls.New( msgBody ))
        
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
        condi = { transD.get( k, k ): v for k, v in msgBody.items() if k not in ( 'Time', ) }
        CreateNodeORUpdate( condi )
        return cls( **condi )
    
    def __init__( self, **kwds ):
        ""
        #self.MsgQ = Queue()
        self.tasks = set( [] )
        for k, v in kwds.items():
            setattr( self, k, v )
        if hasattr( self, 'PubKey' ):
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
    
#    def Send( self, msgObj ):
#        "send to remote node"
#        data = urlencode( { 'pfp': msgObj.Issue() } )
#        req = urllib2.Request( url, data )
#        response = urllib2.urlopen( req )
#        
#        reply = response.read()
    
    def SetTask( self, task ):
        ""
        self.tasks.add( task )
    
    def ChkTask( self ):
        ""
        self.tasks.discard( { task for task in self.tasks if task.TimeOver() })
        
    def Reply( self, msgObj ):
        "reply the message directlly"
        #print 'NeighborNode.Reply'
        return msgObj.Reply( self )
    
    def Append( self ):
        "get the additional messages to the neighbor"
        return ()


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


