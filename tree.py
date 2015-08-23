# -*- coding: utf-8 -*-
"""
Created on Sun Aug  9 23:49:38 2015

@author: thor
"""

from json import loads, dumps
from time import time
from hashlib import md5, sha1
from random import randint

from user import SelfUser, OtherUser
from sqlitedb import GetOneArticle, SaveArticle, SaveTopicLabels, SaveTopic, UpdateTopic, GetRootIds, GetTreeAtcls
from const import MaxOfferRootNum, TitleLength

class Article( object ):
    ""
    #------------------ for status
    BLOCK = -1
    RECEIVE = 0
    PASS = 1
    GOOD = 2
    #------------------ for Type
    NORMAL = 0
    LIKE = 1
    CHAT = 2
    #------------------
    MinTime = 1439596800000     #2015-8-15 00:00:00
    LiveD = {}
    
    def __init__( self, Id = None, itemD = None, itemStr = '', content = '' ):
        ""
        if Id is None:                  #create
            self.ItemD = itemD
            self.status = 1
            self.ItemStr = dumps( itemD )
            self.id = sha1( self.ItemStr ).hexdigest()
        else:                           #receive or load from local
            self.id = Id
            self.ItemStr = itemStr
            self.ItemD = loads( itemStr )
            
        self.content = content
        #self.Children = set()
    
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
        
        if 'ProtoID' in self.ItemD:            #assert proto.user is self.user
            Proto = self.Get( self.ItemD['ProtoID'] )
            assert Proto.ItemD['AuthPubKey'] == self.ItemD['AuthPubKey']
        
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
        if atclId in cls.LiveD:
            return cls.LiveD[atclId]
        ItemStr, Content = GetOneArticle( 'items', 'content', id = atclId )
        return cls( Id = atclId, itemStr = ItemStr, content = Content )
    
    @classmethod
    def Cache( cls, d ):    #d = { atclId: ( itemStr, content ) }
        ""
        for atclId, ( itemStr, content ) in d.iteritems():
            if atclId not in cls.LiveD:
                cls.LiveD[atclId] = cls( atclId, itemStr = itemStr, content = content )
                
class TreeStruct( object ):
    ""
    def __init__( self, nodeId, parent = None, children = ()):
        ""
        self.NodeId = nodeId
        self.Parent = parent
        self.Children = set( children )
    
    def Add( self, child ):
        ""
        self.Children.add( child )
    
    def IsLeaf( self ):
        ""
        return not self.Children
    
    def IsRoot( self ):
        ""
        return not self.Parent
    
        
class Topic( object ):
    ""
    LiveD = {}
    
    def __init__( self, root ):
        ""
        #print root.ItemD
        assert root.ItemD.get( 'Type' ) == 0
        assert root.ItemD.get( 'Labels' ) > ''          #every tree must has labels
        self.Root = root
        self.AtclD = { root.id: root }
        self.StructD = None
    
    def Save( self, **kwds ):
        ""
        print 'Topic.Save'
        SaveTopic( **kwds )
        SaveTopicLabels( self.Root.id, self.Root.GetLabels())
    
    def GetInfo( self ):
        ""
        return {
            "TreeId": self.Root.id,
            "Length": len( self ),
            "SnapShot": self.SnapShot,
                }

    def SetSnapShot( self ):
        ""
        IdStr = ''.join( sorted( self.AtclD.keys()))
        self.SnapShot = sha1( IdStr ).hexdigest()
    
    def GetLeaves( self ):
        "get the leaf nodes in the tree."
        return self.AtclD.viewkeys() - { atcl.ItemD.get( 'ParentID', '' ) for atcl in self.AtclD.itervalues() }
    
    def Instruct( self ):
        "build tree structure"
        if self.StructD is not None:
            return
        NodeD = self.AtclD
        StructD = {}
        for atclId, atcl in NodeD.iteritems():
            ParentId = atcl.ItemD.get( 'ParentID', '' )
#            Parent = NodeD.get( ParentId ) if ParentId else True
#            if Parent is not None:
            StructD.setdefault( atclId, TreeStruct( atclId, ParentId ))
            StructD.setdefault( ParentId, TreeStruct( ParentId )).Add( atclId )

        self.StructD = StructD   #there may be multi articles in struct.root when editing the root. put roots in struct.children.
        
    def ChkByLeaves( self, leaves ):
        "check remote leaves and return the more articles"
        print 'Topic.ChkByLeaves'
        self.Instruct()
        LocalLeaves = self.GetLeaves()
        RemoteAtcls = set()
        
        AskBack = leaves - self.StructD.viewkeys()      #remote is more than local
        
#        for leafId in leaves:
#            if leafId not in self.StructD:          继续写这里
#                continue
#            leafNode = self.StructD[leafId]
#            
#            Id = leafId
#            while Id:
#                RemoteAtcls.add( Id )
#                Id = self.StructD[Id].Parent
#                
#            if not leafNode.IsLeaf():
#                return [self.AtclD[aid] for aid in leafNode.GetLower()]
                
        return []
        
    def __len__( self ):
        ""
        return len( self.AtclD )
        
    @classmethod
    def New( cls, atcl ):
        ""
        print 'Topic.New'
        cls( atcl ).Save( root = atcl.id, title = atcl.content.split( '\n' )[0][:TitleLength], num = 1, status = atcl.status,
                        FirstAuthName = atcl.ItemD.get( 'NickName' ), LastAuthName = atcl.ItemD.get( 'NickName' ),
                        FirstTime = atcl.ItemD.get( 'CreateTime' ), LastTime = atcl.ItemD.get( 'CreateTime' ), )
    
    @classmethod
    def Filter( cls, condi ):
        ""
        RootIds = GetRootIds( **condi )
        print 'Topic.Filter RootIds =', RootIds
        l = len( RootIds )
        for i in range( l - MaxOfferRootNum ):
            RootIds.pop( randint( 0, l - i - 1 ))
        
        for topic in cls.GetMulti( *RootIds ):
            yield topic
            
    
    @classmethod
    def GetMulti( cls, *rootIds ):
        ""
        print 'Topic.Get rootIds =', rootIds
        rootSet = set( rootIds )
        cacheSet = cls.LiveD.viewkeys()
        
        for k in rootSet & cacheSet:
            yield cls.LiveD[k]
            
        rootSet -= cacheSet
            
        TreeD = GetTreeAtcls( *rootSet )
        for k, atclD in TreeD.iteritems():
            if k not in atclD:
                continue
            Article.Cache( atclD )
            topic = cls( Article.Get( k ))
            for ak in atclD:
                topic.AtclD.setdefault( ak, Article.Get( ak ))
            topic.SetSnapShot()
            cls.LiveD[k] = topic
            yield topic
            
    @classmethod
    def Compare( cls, treeInfo ):   #treeInfo = { TreeId:..., Length:..., SnapShot:... }
        ""
        print 'Topic.Compare treeInfo =', treeInfo
        TreeId = treeInfo['TreeId']
        for topic in cls.GetMulti( TreeId ):
            if len( topic ) >= 0.5 * treeInfo['Length']:
                return { 'TreeId': TreeId, 'Mode': 'leaf', 'Leaves': list( topic.GetLeaves()) }
        else:
            return { 'TreeId': TreeId, 'Mode': 'all' }
#            if topic is None or len( topic ) < 0.5 * treeInfo['Length']:
#                return { 'TreeId': TreeId, 'Mode': 'all' }
#            return { 'TreeId': TreeId, 'Mode': 'leaf', 'Leaves': list( topic.GetLeaves()) }
    
    @classmethod
    def GetReqAtcls( cls, treeReq ):    #treeReq = { TreeId:..., Mode:..., Leaves:... }
        ""
        print 'Topic.GetReqAtcls treeReq =', treeReq
        for topic in cls.GetMulti( treeReq['TreeId'] ):
            if treeReq['Mode'] == 'all':
                return topic.AtclD.values()
            if treeReq['Mode'] == 'leaf':
                return topic.ChkByLeaves( set( treeReq['Leaves'] ))
        return []

if __name__ == '__main__':
    a = Article.New( SelfUser(), 0, u'儿童怪问客从来，迂阔颟顸语近呆。醉指他乡风物好，淡真不必甚多才。',
                    0, Labels = u'诗', RootID = '9786b0cb0761e87e720733e45bc6c831785f0bac', ParentID = '9786b0cb0761e87e720733e45bc6c831785f0bac', )
    a.Save()
    j = a.Issue()
    print j
    print Article.Receive( j )