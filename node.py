# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 22:04:20 2015

@author: thor
"""

import logging

from sqlitedb import SqliteDB
from exception import *


class Node( object ):
    "peerforum node"
    def __init__( self, condi = '' ):
        ""
        with SqliteDB() as cursor:
            if condi:
                sql = """select name, PubKey, PriKey, ServerProtocol, discription, address
                            from selfnode where %s and level >= 0;""" % condi
            else:
                sql = """select name, PubKey, PriKey, ServerProtocol, discription, address
                            from selfnode where level >= 0 order by level desc limit 1;"""
                            
            NodeData = cursor.execute( sql ).fetchone()
        
        if NodeData is None:
            raise NoAvailableNodeErr
            
        self.Name, self.PubKey, self.PriKey, self.SvPrtcl, self.Desc, self.Addr = NodeData
        
        self.Run()
        
    def Run( self ):
        ""
        pass


