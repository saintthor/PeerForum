# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 21:49:20 2015

@author: thor
"""
from tree import Article
from user import SelfUser
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
#    a = Article.New( SelfUser(), 0, u'无念方出世，蜗居好避人。西风今古意，说与小雷神。',
#                    0, Labels = u'诗', RootID = '9786b0cb0761e87e720733e45bc6c831785f0bac', ParentID = '7df3643dfab56ef3fcbe43a2511a3f52e6e19532', )
#    a.Save()
#    print a.Issue()
#    raise
    test()
    debug( True )
    run( host = '0.0.0.0', port = 8002, reloader = False )
    