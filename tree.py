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
import re
import logging

from user import SelfUser, OtherUser
from sqlitedb import GetOneArticle, SaveArticle, SaveTopicLabels, SaveTopic, UpdateTopic, GetRootIds, \
                     GetTreeAtcls, SetAtclsWithoutTopic, GetAtclByUser, GetTopicRowById, \
                     GetTopicRows, SetAtclStatus, SetLabel, GetAtclByUserToShow, SearchAtcl
from const import MaxOfferRootNum, TitleLength, AutoNode, SeekSelfUser, TopicNumPerPage

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
    
    def __init__( self, Id = None, itemD = None, itemStr = '', content = '', status = None, labelStr = '' ):
        ""
        if Id is None:                  #create
            self.ItemD = itemD
            self.status = 0
            self.ItemStr = dumps( itemD )
            self.id = sha1( self.ItemStr ).hexdigest()
        else:                           #receive or load from local
            self.id = Id
            self.status = int( AutoNode ) if status is None else status
            self.ItemStr = itemStr
            self.ItemD = loads( itemStr )
            
        self.content = content
        self.LabelStr = labelStr
        self.NodeLabels = ( labelStr + '|' ).split( '|' )[1].split( ',' )
    
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
                'DestroyTime': self.ItemD.get( 'DestroyTime', 9999999999999 ),
                'GetTime': int( time() * 1000 ),
                'AuthPubKey': self.ItemD['AuthPubKey'],
                'status': self.status,
                    } )
        
        if hasattr( self, 'RemoteLabels' ):
            kwds['RemoteLabels'] = self.RemoteLabels
        if hasattr( self, 'RemoteEval' ):
            kwds['RemoteEval'] = self.RemoteEval
        else:
            kwds['GetTime'] += randint( 100000, 300000 )   #the GetTime for local created shouldn't be exact.
            
        if SaveArticle( **kwds ):
            if self.IsRoot():
                Topic.New( self )
            else:
                Topic.AddAtcl( self )
                UpdateTopic( self.ItemD['RootID'], **{
                                        'LastAuthName': self.ItemD.get( 'NickName' ),
                                        'LastTime': kwds['GetTime'],
                                                    } )


    def Check( self ):
        "do not check destroy time here"
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
            logging.error( traceback.format_exc())
    
    def Show( self, **addi ):
        "show to ui"
        ShowData = {
                'atclId': self.id,
                'content': self.content,
                'status': self.status,
                'LabelStr': self.LabelStr,
                    }
        ShowData.update( addi )
        ShowData.update( self.ItemD )
        return ShowData
        
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
        return self.ItemD.get( 'Labels' ).replace( u'，', ',' ).split( ',' )
        
    def SetStatus( self, status ):
        ""
        self.status = status
        SetAtclStatus( self.id, status )
        self.Uncache()
    
    def Uncache( self ):
        "del from cache."
        if self.id in self.LiveD:
            self.LiveD.pop( self.id )
        RootId = self.ItemD.get( 'RootID', self.id )
        Topic.Uncache( RootId )
        
    @classmethod
    def New( cls, user, Type = 0, content = '', life = 0, **kwds ):
        "create from local"
        assert Type == 0        #remove like to reduce leaf number.
        #SignFunc = ( lambda s: md5( s ).hexdigest() ) if user is None else user.Sign
        itemD = {} if user is None else user.InitItem()         #get AuthPubKeyType, AuthPubKey, NickName
        itemD['Type'] = Type
#        if Type == Article.NORMAL:
        assert content
        itemD['Sign'] = user.Sign( content.encode( 'utf-8' ) )
#        elif Type == Article.LIKE:
#            content = ''        #LIKE has no content, life, ProtoID, Labels
#            life = 0
#            for k in kwds.viewkeys() & { 'ProtoID', 'Labels' }:
#                del kwds[k]
#            itemD['Sign'] = user.Sign( kwds['ParentID'] )
#        else:
#            raise       #for chat here
        
        itemD['CreateTime'] = int( time() * 1000 )
        if life > 0:
            itemD['DestroyTime'] = itemD['CreateTime'] + life
        itemD['SignHashType'] = 'md5'
        itemD['IDHashType'] = 'sha1'

        for k in kwds.viewkeys() & { 'RootID', 'ParentID', 'ProtoID', 'Labels' }:
            itemD[k] = kwds[k]      #all texts should be encoded to utf-8
            if k == 'ParentID' and 'DestroyTime' in itemD:
                Parent = cls.Get( kwds[k] )
                itemD['DestroyTime'] = Parent.ItemD.get( 'DestroyTime', 9999999999999 )     #only root has destroytime
        
        Atcl = cls( None, itemD = itemD, content = content )
        
        if Atcl.IsRoot():
            Topic.New( Atcl )
            
        return Atcl

    def SetLastNodeInfo( self, info ):
        ""
        self.RemoteLabels = info.get( 'NodeLabels', '' )
        self.RemoteEval = info.get( 'NodeEval', 1 )
    
    @classmethod
    def Search( cls, kWord, before ):
        ""
        if re.match( r'[0-9a-f]{20}', kWord ):
            try:
                data = GetOneArticle( 'id', 'items', 'content', 'status', 'root', 'GetTime', id = kWord )
                return [cls( Id = data[0], itemStr = data[1], content = data[2], 
                    status = data[3] ).Show( rootId = data[4], GetTime = data[5] )]
            except:
                pass
            
        return [cls( Id = data[0], itemStr = data[1], content = data[2], 
                    status = data[3], labelStr = '' ).Show( rootId = data[4], GetTime = data[5] )
                    for data in SearchAtcl( kWord, before, 10 )]
    
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
    def ShowByUser( cls, uPubK, before ):
        "timeline for ui"
        return [cls( Id = data[0], itemStr = data[1], content = data[2], 
                    status = data[4], labelStr = data[3] or '' ).Show( rootId = data[5], GetTime = data[6] )
                    for data in GetAtclByUserToShow( uPubK, before, 10 )]
    
    @classmethod
    def GetByUser( cls, uPubK, From, To, exist ):
        "timeline"
        if SeekSelfUser or not SelfUser.IsSelf( uPubK ):    #set SeekSelfUser to False for high secrety
            for Id, items, content in GetAtclByUser( uPubK, From, To, exist ):
                yield cls( Id = Id, itemStr = items, content = content )
        
    @classmethod
    def Cache( cls, d ):    #d = { atclId: ( itemStr, content ) }
        ""
        for atclId, ( itemStr, content, status, RmtLabels, RmtEval, LabelStr ) in d.iteritems():
            if atclId not in cls.LiveD:
                cls.LiveD[atclId] = cls( atclId, itemStr = itemStr, content = content,
                                         status = status, labelStr = LabelStr )
                
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
        assert root.ItemD.get( 'Type' ) == 0
        assert root.ItemD.get( 'Labels' ) > ''          #every tree must has labels
        self.Root = root
        self.AtclD = { root.id: root }
        self.StructD = None
    
    def Save( self, **kwds ):
        ""
        try:
            SaveTopic( **kwds )
            SaveTopicLabels( self.Root.id, self.Root.GetLabels())
        except:
            logging.error( traceback.format_exc())
    
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
            StructD.setdefault( atclId, TreeStruct( atclId, ParentId ))
            StructD.setdefault( ParentId, TreeStruct( ParentId )).Add( atclId )

        self.StructD = StructD   #there may be multi articles in struct.root when editing the root. put roots in struct.children.
        return self.StructD
    
    def GetUpperIds( self, leafId ):
        ""
        if self.StructD is None:
            self.Instruct()
        while leafId:
            yield leafId
            leafId = self.StructD[leafId].Parent
        
        
    def ChkByLeaves( self, leaves ):
        "check remote leaves and return the more articles"
        self.Instruct()
        LocalLinked = set( TreeStruct.GetAll( self.StructD, '' ))
        RemoteNodes = set()
        
        AskBack = bool( leaves - LocalLinked )      #remote is more than local
        leaves &= LocalLinked
        for leafId in leaves:
            for leaf in self.GetUpperIds( leafId ):
                if leaf in RemoteNodes:
                    break
                RemoteNodes.add( leaf )
                
        ReturnNodes = LocalLinked - RemoteNodes
        
        return [self.AtclD[Id] for Id in ReturnNodes], AskBack
            
    def __len__( self ):
        ""
        return len( self.AtclD )
        
    @classmethod
    def New( cls, atcl ):
        ""
        if atcl.id not in cls.LiveD:
            cls.LiveD[atcl.id] = cls( atcl )
            cls.LiveD[atcl.id].Save( root = atcl.id, title = atcl.content.split( '\n' )[0][:TitleLength],
                        num = 1, status = 0, labels = atcl.ItemD.get( 'Labels', '' ),
                        FirstAuthName = atcl.ItemD.get( 'NickName', '' ), LastAuthName = atcl.ItemD.get( 'NickName', '' ),
                        FirstTime = atcl.ItemD.get( 'CreateTime' ), LastTime = atcl.ItemD.get( 'CreateTime' ), )
    
    @classmethod
    def Filter( cls, condi ):
        ""
        RootIds = GetRootIds( **condi )
        l = len( RootIds )
        for i in range( l - MaxOfferRootNum ):
            RootIds.pop( randint( 0, l - i - 1 ))
        
        for topic in cls.GetMulti( *RootIds ):
            yield topic
    
    @classmethod
    def Uncache( cls, rootId ):
        ""
        if rootId in cls.LiveD:
            cls.LiveD.pop( rootId )
    
    @classmethod
    def ListPage( cls, label, before, sortCol ):
        ""
        return GetTopicRows( label, before, sortCol, TopicNumPerPage )
    
    
    @classmethod
    def ListById( cls, rootId ):
        ""
        return GetTopicRowById( rootId )  #root, title, labels, status, num, FirstAuthName, FirstTime, LastAuthName, LastTime
    
    @classmethod
    def EditLabel( cls, rootId, label, act ):
        ""
        if rootId in cls.LiveD:
            cls.LiveD.pop( rootId )
        return SetLabel( rootId, label, act )
        
    @classmethod
    def ShowAll( cls, rootId ):
        "show all articles in this topic."
        for topic in cls.GetMulti( rootId ):
            return [rootId, { Id: atcl.Show() for Id, atcl in topic.AtclD.iteritems() }]
    
    @classmethod
    def AddAtcl( cls, atcl ):
        ""
        topic = cls.LiveD.get( atcl.ItemD['RootID'] )
        if topic is not None:
            topic.AtclD[atcl.id] = atcl
            
    @classmethod
    def GetMulti( cls, *rootIds ):
        "a generator to get multi topic objs from rootIds"
        rootSet = set( rootIds )
        cacheSet = cls.LiveD.viewkeys()
        
        for k in rootSet & cacheSet:
            yield cls.LiveD[k]
            
        rootSet -= cacheSet
        
        if rootSet:
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
        TreeId = treeInfo['TreeId']
        for topic in cls.GetMulti( TreeId ):
            if len( topic ) >= 0.5 * treeInfo['Length']:
                return { 'TreeId': TreeId, 'Mode': 'leaf', 'Leaves': list( TreeStruct.GetLeaves( topic.Instruct(), '' )) }
        else:
            return { 'TreeId': TreeId, 'Mode': 'all' }
    
    @classmethod
    def GetReqAtcls( cls, treeReq, askBackFunc ):    #treeReq = { TreeId:..., Mode:..., Leaves:... }
        ""
        for topic in cls.GetMulti( treeReq['TreeId'] ):
            if treeReq['Mode'] == 'all':
                return topic.AtclD.values()
            if treeReq['Mode'] == 'leaf':
                Atcls, AskBack = topic.ChkByLeaves( set( treeReq['Leaves'] ))
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
    pass
