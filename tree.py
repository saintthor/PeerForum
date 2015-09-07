# -*- coding: utf-8 -*-
"""
Created on Sun Aug  9 23:49:38 2015

@author: thor
"""

from json import loads, dumps
from time import time
from hashlib import md5, sha1
from random import randint
import traceback

from user import SelfUser, OtherUser
from sqlitedb import GetOneArticle, SaveArticle, SaveTopicLabels, SaveTopic, UpdateTopic, GetRootIds, \
                     GetTreeAtcls, SetAtclsWithoutTopic, GetAtclByUser, DelTopicLabels
from const import MaxOfferRootNum, TitleLength, AutoNode, SeekSelfUser

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
    
    def __init__( self, Id = None, itemD = None, itemStr = '', content = '', status = None, nodeLabels = '' ):
        ""
        if Id is None:                  #create
            self.ItemD = itemD
            self.status = 1
            self.ItemStr = dumps( itemD )
            self.id = sha1( self.ItemStr ).hexdigest()
        else:                           #receive or load from local
            self.id = Id
            self.status = int( AutoNode ) if status is None else status
            self.ItemStr = itemStr
            self.ItemD = loads( itemStr )
            
        self.content = content
        self.NodeLabels = set( nodeLabels )
        #self.Children = set()
    
    def Issue( self ):
        ""
        return {
            'Id': self.id,
            'Items': self.ItemStr,
            'Content': self.content,
            'NodeLabels': u','.join( self.NodeLabels ),
            'NodeEval': self.status
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
                'RemoteLabels': self.RemoteLabels,
                'RemoteEval': self.RemoteEval,
                    } )
                    
        SaveArticle( **kwds )
        
        if self.IsRoot():
            Topic.New( self )
        else:
            UpdateTopic( self.ItemD['RootID'], **{
                                    'LastAuthName': self.ItemD.get( 'NickName' ),
                                    'LastTime': self.ItemD.get( 'CreateTime' ),
                                                } )

    def SetNodeLabels( self, *labels ):
        ""
        labels = set( labels ) - self.NodeLabels
        self.NodeLabels += labels
        SaveTopicLabels( self.id, labels )
    
    def DelNodeLabels( self, *labels ):
        ""
        self.NodeLabels -= set( labels )
        DelTopicLabels( self.id, labels )

    def Check( self ):
        "do not check destroy time here"
        print 'Article.Check', self.id
        try:
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
            return True
        except:
            print traceback.format_exc()
    
    def IsRoot( self ):
        ""
        return not self.ItemD.get( 'RootID' )
    
    def IsPassed( self ):
        ""
        return self.status >= Article.PASS
    
    def SortType( self ):
        ""
        return bool( self.ItemD.get( 'RootID' )) + bool( self.ItemD.get( 'ProtoID' ))
    
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

    def SetLastNodeInfo( self, info ):
        ""
        self.RemoteLabels = info.get( 'NodeLabels', '' )
        self.RemoteEval = info.get( 'NodeEval', 1 )
        
    @classmethod
    def Receive( cls, atclData ):
        "get from other nodes"
        Atcl = cls( atclData['Id'], itemStr = atclData['Items'], content = atclData['Content'] )
        Atcl.SetLastNodeInfo( atclData )
        return Atcl
    
    @classmethod
    def Get( cls, atclId ):
        ""
        if atclId in cls.LiveD:
            return cls.LiveD[atclId]
        aData = GetOneArticle( 'items', 'content', id = atclId )
        if aData is not None:
            return cls( Id = atclId, itemStr = aData[0], content = aData[1] )
    
    @classmethod
    def GetByUser( cls, uPubK, From, To, exist ):
        "timeline"
        print 'Article.GetByUser'
        if SeekSelfUser or not SelfUser.IsSelf( uPubK ):
            for Id, items, content in GetAtclByUser( uPubK, From, To, exist ):
                print Id, items, content
                yield cls( Id = Id, itemStr = items, content = content )
        
    @classmethod
    def Cache( cls, d ):    #d = { atclId: ( itemStr, content ) }
        ""
        for atclId, ( itemStr, content, status, RmtLabels, RmtEval, NodeLabels ) in d.iteritems():
            if atclId not in cls.LiveD:
                cls.LiveD[atclId] = cls( atclId, itemStr = itemStr, content = content,
                                         status = status, nodeLabels = NodeLabels )
                
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
    
    def __repr__( self ):
        ""
        return '<%s: %s, %s>' % ( self.NodeId, self.Parent, repr( self.Children ))
    
    @classmethod
    def GetAll( cls, d, rootK ):
        ""
        for ck in d[rootK].Children:
            yield ck
            for k in cls.GetAll( d, ck ):
                yield k
        
    @classmethod
    def GetLeaves( cls, d, rootK ):
        ""
        children = d[rootK].Children
        if children:
            for ck in children:
                for k in cls.GetLeaves( d, ck ):
                    yield k
        else:
            yield rootK

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
        try:
            SaveTopic( **kwds )
            SaveTopicLabels( self.Root.id, self.Root.GetLabels())
        except:
            print traceback.format_exc()
        print 'Topic.Save over'
    
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
    
#    def GetLeaves( self ):
#        "get the leaf nodes in the tree."
#        return self.AtclD.viewkeys() - { atcl.ItemD.get( 'ParentID', '' ) for atcl in self.AtclD.itervalues() }
    
    def Instruct( self ):
        "build tree structure"
        if self.StructD is not None:
            return self.StructD
        NodeD = self.AtclD
        StructD = {}
        for atclId, atcl in NodeD.iteritems():
            ParentId = atcl.ItemD.get( 'ParentID', '' )
            #print ParentId, '--', atclId
            StructD.setdefault( atclId, TreeStruct( atclId, ParentId ))
            StructD.setdefault( ParentId, TreeStruct( ParentId )).Add( atclId )

        self.StructD = StructD   #there may be multi articles in struct.root when editing the root. put roots in struct.children.
        #print 'Topic.Instruct', StructD
        return self.StructD
    
    def GetUpperIds( self, leafId ):
        ""
        if self.StructD is None:
            self.Instruct()
        while leafId:
            #print 'Topic.GetUpperIds', leafId
            yield leafId
            leafId = self.StructD[leafId].Parent
        
        
    def ChkByLeaves( self, leaves ):
        "check remote leaves and return the more articles"
        print 'Topic.ChkByLeaves', leaves
        self.Instruct()
        LocalLinked = set( TreeStruct.GetAll( self.StructD, '' ))
        #print self.StructD
        #print 'LocalLinked:', LocalLinked
        RemoteNodes = set()
        
        AskBack = bool( leaves - LocalLinked )      #remote is more than local
        leaves &= LocalLinked
        #print AskBack, 'leaves:', leaves
        for leafId in leaves:
            for leaf in self.GetUpperIds( leafId ):
                if leaf in RemoteNodes:
                    break
                RemoteNodes.add( leaf )
                
        #print 'RemoteNodes:', RemoteNodes
        ReturnNodes = LocalLinked - RemoteNodes
        #print 'ReturnNodes:', ReturnNodes
        
        return [self.AtclD[Id] for Id in ReturnNodes], AskBack
        
    def __len__( self ):
        ""
        return len( self.AtclD )
        
    @classmethod
    def New( cls, atcl ):
        ""
        print 'Topic.New'
        cls( atcl ).Save( root = atcl.id, title = atcl.content.split( '\n' )[0][:TitleLength], num = 1, status = 0,
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
        "a generator to get multi topic objs from rootIds"
        print 'Topic.GetMulti rootIds =', rootIds
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
                return { 'TreeId': TreeId, 'Mode': 'leaf', 'Leaves': list( TreeStruct.GetLeaves( topic.Instruct(), '' )) }
        else:
            return { 'TreeId': TreeId, 'Mode': 'all' }
    
    @classmethod
    def GetReqAtcls( cls, treeReq, askBackFunc ):    #treeReq = { TreeId:..., Mode:..., Leaves:... }
        ""
        print 'Topic.GetReqAtcls treeReq =', treeReq
        for topic in cls.GetMulti( treeReq['TreeId'] ):
            if treeReq['Mode'] == 'all':
                print topic.AtclD
                return topic.AtclD.values()
            if treeReq['Mode'] == 'leaf':
                Atcls, AskBack = topic.ChkByLeaves( set( treeReq['Leaves'] ))
                print 'AskBack =', AskBack
                AskBack and askBackFunc( { 'TreeId': treeReq['TreeId'], 'Mode': 'leaf',
                                          'Leaves': list( TreeStruct.GetLeaves( topic.Instruct(), '' )) } )
                return Atcls
            if treeReq['Mode'] in ( "higher", "lower", "relative" ):
                pass
        return []
    
    @classmethod
    def Patch( cls ):
        "check the root articles without topic data."
        SetAtclsWithoutTopic() 

if __name__ == '__main__':
    for topic in Topic.GetMulti( '9786b0cb0761e87e720733e45bc6c831785f0bac', '1fb5381c3200bb03561cb9b79c40bed50eda8515' ):
        topic.Instruct()
        print topic.StructD
        LocalNodes = topic.StructD.viewkeys() - { '' }
        LocalLinked = set( TreeStruct.GetAll( topic.StructD, '' ))
        print '\nLocalNodes:', LocalNodes
        print 'LocalLinked:', LocalLinked
        print 'leaves:', list( TreeStruct.GetLeaves( topic.StructD, '' ))
    
#    a = Article.New( SelfUser(), 0, u'儿童怪问客从来，迂阔颟顸语近呆。醉指他乡风物好，淡真不必甚多才。',
#                    0, Labels = u'诗', RootID = '9786b0cb0761e87e720733e45bc6c831785f0bac', ParentID = '9786b0cb0761e87e720733e45bc6c831785f0bac', )
#    a.Save()
#    j = a.Issue()
#    print j
    #print Article.Receive( j )