# -*- coding: utf-8 -*-
"""
Created on Sun Aug  9 23:49:38 2015

@author: thor
"""

from json import loads, dumps
from time import time
from hashlib import md5, sha1

from user import SelfUser, OtherUser

class Article( object ):
    ""
    NORMAL = 0
    LIKE = 1
    
    def __init__( self, Id = None, itemD = None, itemStr = '', content = '' ):
        ""
        if Id is None:                  #create
            self.ItemD = itemD
            self.ItemStr = dumps( itemD )
            self.id = sha1( self.ItemStr ).hexdigest()
        else:                           #receive
            self.id = Id
            self.ItemStr = itemStr
            self.ItemD = loads( itemStr )
        self.content = content
    
    def Issue( self ):
        ""
        return {
            'Id': self.id,
            'Items': self.ItemStr,
            'Content': self.content,
                }
    
    def Check( self ):
        "do not check destroy time here"
        assert self.ItemD.get( 'IDHashType', 'sha1' ).lower() == 'sha1'
        assert self.id == sha1( self.ItemStr ).hexdigest()
        assert self.ItemD.get( 'SignHashType', 'md5' ).lower() == 'md5'
        
        content = self.content if self.ItemD['Type'] == Article.NORMAL else self.ItemD['ParentID']
        AuthPubKey = self.ItemD.get( 'AuthPubKey' )
        author = None if AuthPubKey is None else OtherUser( AuthPubKey )
        if author is None:
            assert self.ItemD['Sign'] == md5( content ).hexdigest()
        else:
            assert author.Verify( content, self.ItemD['Sign'] )
        
                
    @classmethod
    def New( cls, user = None, Type = 0, content = '', life = 0, **kwds ):
        "create from localhost"
        SignFunc = ( lambda s: md5( s ).hexdigest() ) if user is None else user.Sign
        itemD = {} if user is None else user.InitItem()         #get AuthPubKeyType, AuthPubKey, NickName
        itemD['Type'] = Type
        if Type == Article.NORMAL:
            itemD['Sign'] = SignFunc( content )
        else:
            content = ''
            itemD['Sign'] = SignFunc( kwds['ParentID'] )
        
        itemD['CreateTime'] = int( time() * 1000 )
        if life > 0:
            itemD['DestroyTime'] = itemD['CreateTime'] + life
        itemD['SignHashType'] = 'md5'
        itemD['IDHashType'] = 'sha1'
        for k in kwds.viewkeys() & ( 'RootID', 'ParentID', 'ProtoID', 'Labels' ):
            itemD[k] = kwds[k]      #all texts should be encoded to utf-8
        
        return cls( None, itemD = itemD, content = content )

    @classmethod
    def Receive( cls, atclData ):
        "get from other nodes"
        #atclData['Content'] += 'e'
        Atcl = cls( atclData['Id'], itemStr = atclData['Items'], content = atclData['Content'] )
        Atcl.Check()
        return Atcl
    

class PFTree( object ):
    ""
    def __init__( self, root ):
        ""
        self.Root = root


if __name__ == '__main__':
    a = Article.New( SelfUser(), 0, '从假牙假肢，到人工肾人工心，借助於现代医学之力，人可以把自己身上的一切部件——只除开大脑——都更新替换而仍不失为自己。科学终於证明，所谓自我，无非是我的大脑而已。我就是我的大脑。如果一个人的大脑受到某种损害但依然能保持自我，那么，这个叫做自我的东西到底存身于我的大脑的哪个地方呢？',
                    0, RootID = 'zzzzzzzzzz', ParentID = 'sssssssssss', ProtoID = 'wwwwwwwwwwwww', Labels = '医学,替换' )
    j = a.Issue()
    print j
    print Article.Receive( j )