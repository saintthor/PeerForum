# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 16:01:52 2015

@author: thor
"""

class PeerForumErr( Exception ): pass

class NoAvailableNodeErr( PeerForumErr ): pass
    
class NoAvailableUserErr( PeerForumErr ): pass
    
class RemoteTimeErr( PeerForumErr ): pass
    
class PubKeyTypeNotSupportedErr( PeerForumErr ): pass
    
class MsgKeyLackErr( PeerForumErr ): pass
    
class NodePubKeyInvalidErr( PeerForumErr ): pass
   
class VerifyFailedErr( PeerForumErr ): pass
    
class UserAuthorityErr( PeerForumErr ): pass
    
    
    
    
    
    
    
    
    