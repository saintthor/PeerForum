# -*- coding: utf-8 -*-
"""
Created on Sun Aug  9 23:49:38 2015

@author: thor
"""

from json import loads, dumps
from time import time
from hashlib import md5, sha1

from user import SelfUser, OtherUser
from sqlitedb import GetOneArticle, SaveArticle, SaveTopicLabels, SaveTopic

class Article( object ):
    ""
    NORMAL = 0
    LIKE = 1
    MinTime = 1439596800000     #2015-8-15 00:00:00
    
    def __init__( self, Id = None, itemD = None, itemStr = '', content = '' ):
        ""
        if Id is None:                  #create
            self.ItemD = itemD
            self.ItemStr = dumps( itemD )
            self.id = sha1( self.ItemStr ).hexdigest()
        else:                           #receive or load from local
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
    
    def Save( self, **kwds ):
        ""
        kwds.update( {
                'id': self.id,
                'items': self.ItemStr,
                'content': self.content,
                'CreateTime': self.ItemD['CreateTime'],
                'AuthPubKey': self.ItemD['AuthPubKey'],
                    } )
        SaveArticle( **kwds )
    
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
    
    def IsRoot( self ):
        ""
        return not self.ItemD.get( 'ParentID' )
    
    def GetLabels( self ):
        ""
        return self.ItemD.get( 'Labels' ).split( ',' )
        
                
    @classmethod
    def New( cls, user = None, Type = 0, content = '', life = 0, **kwds ):
        "create from local"
        SignFunc = ( lambda s: md5( s ).hexdigest() ) if user is None else user.Sign
        itemD = {} if user is None else user.InitItem()         #get AuthPubKeyType, AuthPubKey, NickName
        itemD['Type'] = Type
        if Type == Article.NORMAL:
            assert content
            itemD['Sign'] = SignFunc( content )
        else:
            content = ''
            itemD['Sign'] = SignFunc( kwds['ParentID'] )
        
        itemD['CreateTime'] = int( time() * 1000 )
        if life > 0:
            itemD['DestroyTime'] = itemD['CreateTime'] + life
        itemD['SignHashType'] = 'md5'
        itemD['IDHashType'] = 'sha1'
        for k in kwds.viewkeys() & { 'RootID', 'ParentID', 'ProtoID', 'Labels' }:
            itemD[k] = kwds[k]      #all texts should be encoded to utf-8
            if k == 'ParentID':
                Parent = cls.Get( kwds[k] )
                if 'DestroyTime' in Parent.ItmeD:
                    itemD['DestroyTime'] = min( itemD['DestroyTime'], Parent.ItmeD['DestroyTime'] )
        
        #print 'Article.New', itemD
        Atcl = cls( None, itemD = itemD, content = content )
        
        if Atcl.IsRoot():
            Topic.New( Atcl )
            
        return Atcl

    @classmethod
    def Receive( cls, atclData, FromNode = '' ):
        "get from other nodes"
        #atclData['Content'] += 'e'
        Atcl = cls( atclData['Id'], itemStr = atclData['Items'], content = atclData['Content'] )
        Atcl.Check()
        #Atcl.Save( FromNode = FromNode )
        return Atcl
    
    @classmethod
    def Get( cls, atclId ):
        ""
        ItemStr, Content = GetOneArticle( 'items', 'content', id = atclId )
        return cls( Id = atclId, itemStr = ItemStr, content = Content )
        

class Topic( object ):
    ""
    def __init__( self, root ):
        ""
        #print root.ItemD
        assert root.ItemD.get( 'Type' ) == 0
        assert root.ItemD.get( 'Labels' ) > ''          #every tree must has labels
        self.Root = root
    
    def Save( self, **kwds ):
        ""
        print 'Topic.Save'
        SaveTopic( **kwds )
        SaveTopicLabels( self.Root.id, self.Root.GetLabels())

        
    @classmethod
    def New( cls, atcl ):
        ""
        print 'Topic.New'
        cls( atcl ).Save( root = atcl.id, title = atcl.content.split( '\n' )[0][:30], num = 1,
                        FirstAuthName = atcl.ItemD.get( 'NickName' ), LastAuthName = atcl.ItemD.get( 'NickName' ),
                        FirstTime = atcl.ItemD.get( 'CreateTime' ), LastTime = atcl.ItemD.get( 'CreateTime' ), )

if __name__ == '__main__':
    a = Article.New( SelfUser(), 0, '有凤\n有凤于飞，翙翙其翼。西番之使，九夏之裔。\n有凤于飞，喈喈其声。西番之使，九夏之风。\n有凤于飞，集于桐木。西番之使，九夏其慕。',
                    0, Labels = '诗' )
    a.Save()
    j = a.Issue()
    print j
    #print Article.Receive( j )