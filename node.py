# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 22:04:20 2015

@author: thor
"""

import logging

#from threading import Thread
from Queue import Queue, Empty
from random import choice, randint
import rsa1 as rsa
from base64 import encodestring, decodestring

from sqlitedb import CreateSelfNode, GetAllNode, GetNodeById, GetNodeByPubKeyOrNew, UpdateNodeOrNew, \
                    GetNodesExcept, GetNodeInfoByPubKey, GetSelfNode, GetTargetNodes
from exception import *
from const import TechInfo, PFPVersion, SignHashFunc, GetNodeNum
from crypto import CBCEncrypt, CBCDecrypt


class NeighborNode( object ):
    ""
    LiveD = {}
    AllNodes = []
    taskQ = Queue()
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
        cls.AllNodes = GetAllNode( 'id', 'level', ServerProtocol = 'HTTP' )
    
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
    
#    @classmethod
#    def GetSomeInfo( cls, excpStr = '' ):
#        ""
#        result = []
#        its = [it for it in cls.transD.items() if it[0] != 'id']
#        ProtocolKs = [it[0] for it in its]
#        for NodeData in GetNodeByIds( *[it[1] for it in its] )
#        return []
    
    @classmethod
    def Get( cls, pubK, msgBody = None ):
        ""
        #print 'Neighbor.Get', pubK, msgBody, pubK in cls.LiveD
#        if msgBody is None:
#            return cls.LiveD.get( pubK, cls.SearchNode( pubK ))
        return cls.LiveD.setdefault( pubK, cls._New( msgBody ))
        
    @classmethod
    def AllTargets( cls ):
        ""
        for pubK, addrs in GetTargetNodes():
            print pubK, addrs
            yield cls( PubKey = pubK, Addrs = addrs )
        
    @classmethod
    def _New( cls, msgBody ):
        ""
        #print 'Neighbor._New'
        condi = { cls.transD.get( k, k ): v for k, v in msgBody.items()
                    if k not in ( 'Time', 'PubKeyStr', 'ForwardPubKey', 'ObjPubKey', 'Step', 'Address' ) }
        GetNodeByPubKeyOrNew( condi )
        return cls( **condi )
    
    @classmethod
    def NewNeighbor( cls, neighbor ):
        "save new neighbor from other node"
        print 'Neighbor.NewNeighbor'
        condi = { cls.transD.get( k, k ): v for k, v in neighbor.items() if k not in ( 'Time', 'PubKeyStr' ) }
        GetNodeByPubKeyOrNew( condi )
    
    @classmethod
    def SearchNode( cls, pubK ):
        ""
        its = [it for it in cls.transD.items() if it[0] != 'id']
        try:
            return cls( **GetNodeInfoByPubKey( pubK, its ))
        except TypeError:
            return
        
    
    def __init__( self, **kwds ):
        ""
        print kwds
        self.SendBuffer = []
        #self.tasks = set( [] )
        self.id = self.PubKey = None
        for k, v in kwds.items():
            setattr( self, k, v )
        if kwds.get( 'PubKey' ):
            self.PubKeyStr = self.PubKey
            self.PubKey = rsa.PublicKey.load_pkcs1( self.PubKey )
    
    def Update( self, param ):
        ""
        print 'Neighbor.Update', param
        for k, v in param.items():
            if k in ( 'PFPVer', 'NodeName', 'Description', 'Address', 'NodeTypeVer', 'BaseProtocol' ):
                setattr( self, self.transD.get( k, k ), v )
        self.Save()
    
    def GetSomeInfo( self ):
        ""
        its = [it for it in self.transD.items() if it[0] != 'id']
        #ProtocolKs = [it[0] for it in its]
        nids = [an[0] for an in self.AllNodes]
        l = len( nids )
        for i in range( len( nids ) - GetNodeNum - 1 ):
            nids.pop( randint( 0, l - i ))
        
        return GetNodesExcept( its, nids, self.PubKey )
        
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
        #print '\nNeighborNode.Encrypt', k, self.PubKey
        return {
            "msg": encodestring( CBCEncrypt( s, k )),
            "key": encodestring( rsa.encrypt( k, self.PubKey )),
                }
    
    def Verify( self, message, sign ):
        ""
        #print '\nVerify', self.PubKeyStr
        return rsa.verify( message, sign, self.PubKey )
                
#    def Send( self ):
#        "send to remote node"
#        if not self.SendBuffer:
#            print 'NeighborNode.Send empty SendBuffer. id is', id( self )
#            return ''
#        data = urlencode( { 'pfp': '\n'.join( self.SendBuffer ) } )
#        self.SendBuffer = []
#        print 'NeighborNode.Send', self.address, len( data )
#        req = urllib2.Request( self.address, data )
#        response = urllib2.urlopen( req )
#        
#        return response.read()
    
#    def SetTask( self, task ):
#        ""
#        self.tasks.add( task )
    
#    def ChkTask( self ):
#        ""
#        self.tasks.discard( { task for task in self.tasks if task.TimeOver() })
        
    def Buffer( self, msgStrs ):
        "buffer the message. wait to send."
        #print '\nNeighborNode.Buffer. id is', id( self ),
        self.SendBuffer.extend( msgStrs )
        #print len( self.SendBuffer )
    
    def AllToSend( self ):
        "get the additional messages to the neighbor"
        Msgs = self.SendBuffer
        self.SendBuffer = []
        return self.Addrs, Msgs

class SelfNode( object ):
    "peerforum self node"
    @classmethod
    def New( cls ):
        "create a new self node."
        print 'creating local node...'
        PubKey, PriKey = rsa.newkeys( 1024 )
        CreateSelfNode( PubKey = PubKey.save_pkcs1(), PriKey = PriKey.save_pkcs1() )
        
    def __init__( self, condi = '' ):
        ""                            
        NodeData = GetSelfNode()
            
        self.Name, self.PubKeyStr, PriKeyStr, self.SvPrtcl, self.Desc, self.Level, self.Addrs = NodeData
        self.PubKey = rsa.PublicKey.load_pkcs1( self.PubKeyStr )
        self.PriKey = rsa.PrivateKey.load_pkcs1( PriKeyStr )
    
    def Decrypt( self, secMsg, secK ):
        ""
        #print '\nSelfNode.Decrypt', self.PubKey
        key = rsa.decrypt( secK, self.PriKey )
        return CBCDecrypt( secMsg, key )
    
    def Sign( self, msg ):
        ""
        #print '\nSign', self.PubKeyStr
        return encodestring( rsa.sign( msg, self.PriKey, SignHashFunc ))
        
    def GetInfo( self ):
        ""
        return {
            "Address": self.Addrs,
            "NodeName": self.Name,
            "NodeTypeVer": TechInfo,
            "PFPVer": PFPVersion,
            "BaseProtocol": self.SvPrtcl,
            "Description": self.Desc,
                }
                
    def Show( self ):
        "show in local client"
        return [self.Name, self.PubKey, self.Level]


