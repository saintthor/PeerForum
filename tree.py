# -*- coding: utf-8 -*-
"""
Created on Sun Aug  9 23:49:38 2015

@author: thor
"""

from json import loads, dumps
from time import time
from hashlib import md5, sha1

from user import SelfUser, OtherUser
from sqlitedb import GetOneArticle, SaveArticle, SaveTopicLabels, SaveTopic, UpdateTopic

class Article( object ):
    ""
    NORMAL = 0
    LIKE = 1
    CHAT = 2
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
                'root': self.ItemD.get( 'RootID', self.id ),    #for root, the itemD is filled before creating rootId. so, itemD.RootID is null
                'items': self.ItemStr,
                'content': self.content,
                'Type': self.ItemD['Type'],
                'CreateTime': self.ItemD['CreateTime'],
                'AuthPubKey': self.ItemD['AuthPubKey'],
                    } )
        SaveArticle( **kwds )
        
        if not self.IsRoot():
            UpdateTopic( self.ItemD['RootID'], **{
                                    'LastAuthName': self.ItemD.get( 'NickName' ),
                                    'LastTime': self.ItemD.get( 'CreateTime' ),
                                                } )
    
    def Check( self ):
        "do not check destroy time here"
        assert self.ItemD.get( 'IDHashType', 'sha1' ).lower() == 'sha1'
        assert self.id == sha1( self.ItemStr ).hexdigest()
        assert self.ItemD.get( 'SignHashType', 'md5' ).lower() == 'md5'
        
        content = self.content.encode( 'utf8' ) if self.ItemD['Type'] == Article.NORMAL else self.ItemD['ParentID']
        AuthPubKey = self.ItemD.get( 'AuthPubKey' )
        author = OtherUser( AuthPubKey )
        assert author.Verify( content, self.ItemD['Sign'] )
    
    def IsRoot( self ):
        ""
        return not self.ItemD.get( 'RootID' )
    
    def GetLabels( self ):
        ""
        return self.ItemD.get( 'Labels' ).split( ',' )
        
                
    @classmethod
    def New( cls, user, Type = 0, content = '', life = 0, **kwds ):
        "create from local"
        #SignFunc = ( lambda s: md5( s ).hexdigest() ) if user is None else user.Sign
        itemD = {} if user is None else user.InitItem()         #get AuthPubKeyType, AuthPubKey, NickName
        itemD['Type'] = Type
        if Type == Article.NORMAL:
            assert content
            itemD['Sign'] = user.Sign( content.encode( 'utf8' ))
        elif Type == Article.LIKE:
            content = ''        #LIKE has no content, life, ProtoID, Labels
            life = 0
            for k in kwds.viewkeys() & { 'ProtoID', 'Labels' }:
                del kwds[k]
            itemD['Sign'] = user.Sign( kwds['ParentID'] )
        else:
            raise       #for chat here
        
        itemD['CreateTime'] = int( time() * 1000 )
        if life > 0:
            itemD['DestroyTime'] = itemD['CreateTime'] + life
        itemD['SignHashType'] = 'md5'
        itemD['IDHashType'] = 'sha1'
        for k in kwds.viewkeys() & { 'RootID', 'ParentID', 'ProtoID', 'Labels' }:
            itemD[k] = kwds[k]      #all texts should be encoded to utf-8
            if k == 'ParentID':
                Parent = cls.Get( kwds[k] )
                if 'DestroyTime' in Parent.ItemD:
                    itemD['DestroyTime'] = min( itemD.get( 'DestroyTime', 9999999999999 ), Parent.ItemD['DestroyTime'] )
        
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
    a = Article.New( SelfUser(), 0, u'儿童怪问客从来，迂阔颟顸语近呆。醉指他乡风物好，淡真不必甚多才。',
                    0, Labels = u'诗', RootID = '9786b0cb0761e87e720733e45bc6c831785f0bac', ParentID = '9786b0cb0761e87e720733e45bc6c831785f0bac', )
    a.Save()
    j = a.Issue()
    print j
    print Article.Receive( j )