# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 22:04:20 2015

@author: thor
"""

#import logging

#from threading import Thread
from Queue import Queue, Empty
from random import choice, randint
import md5
import rsa
import logging
from base64 import encodestring#, decodestring
#import inspect

from sqlitedb import CreateSelfNode, GetAllNode, GetNodeById, GetNodeByPubKeyOrNew, UpdateNodeOrNew, SetNodeAddrs,\
                    GetNodesExcept, GetNodeInfoByPubKey, GetSelfNode, GetTargetNodes, EditSelfNode, CountNodeFail
from exception import *
from const import TechInfo, PFPVersion, SignHashFunc, GetNodeNum


def GetRealK( k, l, kStr = '' ):
    ""
    lk = len( k )
    if not kStr:
        kStr = ''.join( map( chr, k ))
    m = map( ord, md5.md5( kStr ).digest())
    lm = len( m )
    for i in range( l - lk ):
        k.append( k[2 - lk] ^ k[9 - lk] ^ k[20 - lk] ^ m[i % lm] )
    return k
    

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
        #'Address': 'address',
        'Address': 'addr',
        'NodeTypeVer': 'TechInfo',
        'BaseProtocol': 'ServerProtocol',
        'LastTime': 'LastTime',
        'FailNum': 'FailNum',
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
    
    @classmethod
    def Get( cls, pubK, msgBody = None ):
        ""
#        if msgBody is None:
#            return cls.LiveD.get( pubK, cls.SearchNode( pubK ))
        if pubK not in cls.LiveD:
            cls.LiveD[pubK] = cls._New( msgBody )
        return cls.LiveD[pubK]
        
    @classmethod
    def AllTargets( cls ):
        ""
        for pubK, addrs in GetTargetNodes():
            yield cls( PubKey = pubK, Addrs = addrs )
        
    @classmethod
    def _New( cls, msgBody ):
        ""
        condi = { cls.transD.get( k, k ): v for k, v in msgBody.items()
                    if k not in ( 'Time', 'PubKeyStr', 'ForwardPubKey', 'ObjPubKey', 'Step', 'Address' ) }
        GetNodeByPubKeyOrNew( condi )
        cls.Init()              #reset cls.AllNodes
        return cls( **condi )
    
    @classmethod
    def NewNeighbor( cls, neighbor ):
        "save new neighbor from other node"
        condi = { cls.transD.get( k, k ): v for k, v in neighbor.items()
                    if k not in ( 'Time', 'PubKeyStr', 'ForwardPubKey', 'ObjPubKey', 'Step', 'Address', 'Addresses' ) }
        GetNodeByPubKeyOrNew( condi )
        SetNodeAddrs( neighbor['PubKey'], neighbor['Addresses'] )
        cls.Init()
    
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
        self.Addrs = ()
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
        for k, v in param.items():
            if k in ( 'PFPVer', 'NodeName', 'Description', 'Address', 'NodeTypeVer', 'BaseProtocol' ):
                setattr( self, self.transD.get( k, k ), v )
        self.Save()
        self.Init()
    
    def RecordFail( self ):
        "count fail num when communicate fails"
        if hasattr( self, 'PubKeyStr' ):
            CountNodeFail( self.PubKeyStr )
    
    def Succeed( self, lastTime ):
        "receive something from neighbor"
        self.LastTime = lastTime
        self.FailNum = 0
        self.Save()
    
    def RecSeccAddr( self, addr ):
        ""
        pass
    
    def GetSomeInfo( self ):
        ""
        its = [it for it in self.transD.items() if it[0] not in ( 'id', 'LastTime', 'FailNum', 'Address' )]
        nids = [an[0] for an in self.AllNodes]
        l = len( nids )
        for i in range( len( nids ) - GetNodeNum - 1 ):
            nids.pop( randint( 0, l - i ))
        
        return GetNodesExcept( its, nids, self.PubKey )
        
    def InitPubKey( self, pubK ):
        "init pubkey if it is void."
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
        param = { k: getattr( self, k ) for k in self.transD.values() if hasattr( self, k ) and k != 'id' }
        UpdateNodeOrNew( param, where )
            
    def Encrypt( self, s ):
        ""
        if not hasattr( self, 'PubKey' ):
            raise NodePubKeyInvalidErr
        k = [randint( 0, 255 ) for _ in range( randint( 25, 32 ))]
        kStr = ''.join( map( chr, k ))
        RealK = GetRealK( k, len( s ), kStr )
        encrypted = ''.join( map( chr, map( int.__xor__, RealK, map( ord, s ))))
        return {
            "msg": encodestring( encrypted ),
            "key": encodestring( rsa.encrypt( kStr, self.PubKey )),
                }
    
#    def Encrypt0( self, s ):
#        ""
#        if not hasattr( self, 'PubKey' ):
#            raise NodePubKeyInvalidErr
#        k = ''.join( [choice( "1234567890)(*&^%$#@!`~qazxswedcvfrtgbnhyujm,kiolp;.[]{}:?><\"\\'/PLOKMIJNUHBYGVTFCRDXESZWAQ" )
#                        for i in range( 32 )] )
#        return {
#            "msg": encodestring( CBCEncrypt( s, k )),
#            "key": encodestring( rsa.encrypt( k, self.PubKey )),
#                }
    
    def Verify( self, message, sign ):
        ""
        return rsa.verify( message, sign, self.PubKey )
                        
    def Buffer( self, msgStrs ):
        "buffer the message. wait to send."
        self.SendBuffer.extend( msgStrs )
    
    def AllToSend( self ):
        "get the additional messages to the neighbor"
        Msgs = self.SendBuffer
        logging.info( 'AllToSend: %s' % ' - '.join( [m[:20] for m in Msgs] ))
        self.SendBuffer = []
        return self.Addrs, Msgs

class SelfNode( object ):
    "peerforum self node"
    @classmethod
    def New( cls ):
        "create a new self node."
        PubKey, PriKey = rsa.newkeys( 1024 )
        CreateSelfNode( PubKey = PubKey.save_pkcs1(), PriKey = PriKey.save_pkcs1(), ServerProtocol = 'HTTP' )
        
    def __init__( self, condi = '' ):
        ""
        try:
            NodeData = GetSelfNode()
        except NoAvailableNodeErr:
            self.New()
            NodeData = GetSelfNode()
            
        self.Name, self.PubKeyStr, PriKeyStr, self.SvPrtcl, self.Desc, self.Level, self.Addrs = NodeData
        self.PubKey = rsa.PublicKey.load_pkcs1( self.PubKeyStr )
        self.PriKey = rsa.PrivateKey.load_pkcs1( PriKeyStr )
        
    def Decrypt( self, secMsg, secK ):
        ""
        kStr = rsa.decrypt( secK, self.PriKey )
        k = map( ord, kStr )
        RealK = GetRealK( k, len( secMsg ), kStr )
        return ''.join( map( chr, map( int.__xor__, RealK, map( ord, secMsg ))))
        
#    def Decrypt0( self, secMsg, secK ):
#        ""
#        key = rsa.decrypt( secK, self.PriKey )
#        return CBCDecrypt( secMsg, key )
    
    def Edit( self, name, desc, addrs ):
        ""
        self.Name = name
        self.Desc = desc
        self.Addrs = filter( None, addrs )
        EditSelfNode( self.PubKeyStr, name, desc, self.Addrs )
        
    def Sign( self, msg ):
        ""
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
    
    def GetPort( self ):
        ""
        return int( self.Addrs[0].split( ':' )[-1].split( '/' )[0] )
                
    def Issue( self ):
        "show in local client"
        return self.PubKeyStr, self.Name, self.Desc, self.Addrs, self.Level
