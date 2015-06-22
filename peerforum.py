# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 15:33:58 2015

@author: thor
"""
import logging

import protocol
import user
import node

from const import LOG_FILE
from sqlitedb import SqliteDB

class PeerForum( object ):
    ""
    def __init__( self ):
        ""
        self.Node = node.Node()
        self.User = user.User()
    
    def ChangeNode( self, condi ):
        "改变当前节点"
        self.Node = node.Node( condi )

    def ChangeUser( self, condi ):
        "改变当前节点"
        self.User = user.User( condi )

if __name__ == '__main__':
    SqliteDB.SetMod()
    logging.basicConfig( filename=LOG_FILE, level=logging.DEBUG )
    PeerForum()