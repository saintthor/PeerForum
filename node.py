# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 22:04:20 2015

@author: thor
"""

import logging

from threading import Thread
from Queue import Queue

from sqlitedb import SqliteDB
from exception import *
from const import TechInfo, PFPVersion

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
    def New( cls, pubK ):
        ""
        return cls()
    
    def __init__( self ):
        ""
        self.MsgQ = Queue()
    
    def Reply( self, msgObj ):
        "reply the message directlly"
        #print 'NeighborNode.Reply'
        return msgObj.Reply()
    
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
            
        self.Name, self.PubKey, self.PriKey, self.SvPrtcl, self.Desc, self.Addr, self.Level = NodeData
    
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


