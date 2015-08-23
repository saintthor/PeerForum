# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 21:49:20 2015

@author: thor
"""

from peerforum import PeerForum, test
from bottle import run, debug

from sqlitedb import ChangePath, InitDB
from protocol import PFPMessage

ChangePath( './test.db' )

class TestPeerForum( PeerForum ):
    ""
    LocalNode = None
    LiveNeighborD = {}

if __name__ == '__main__':
    InitDB()
    PFPMessage.Init()
    TestPeerForum.ChkEnv()
    #print 'TestPeerForum.LocalNode.PubKey: ', TestPeerForum.LocalNode.PubKey
    test()
    debug( True )
    run( host = '0.0.0.0', port = 8002, reloader = False )
    