# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 22:02:40 2015

@author: thor
"""
from sqlitedb import SqliteDB

class User( object ):
    "peerforum user"
    def __init__( self, condi = '' ):
        ""
        with SqliteDB() as cursor:
            if condi:
                sql = """select NickName, PubKey, PriKey from self where %s and level >= 0;""" % condi
            else:
                sql = """select name, PubKey, PriKey from self where level >= 0 order by level desc limit 1;"""
                            
            UserData = cursor.execute( sql ).fetchone()
        
        if UserData is None:
            raise NoAvailableUserErr
            
        self.NickName, self.PubKey, self.PriKey = UserData
        
