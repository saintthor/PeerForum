# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 22:02:40 2015

@author: thor
"""
from sqlitedb import CreateSelfUser, GetDefaultUser, GetSelfPubKeyStrs, SetSelfUserName
import rsa
from base64 import encodestring, decodestring
from const import SignHashFunc


class OtherUser( object ):
    ""
    def __init__( self, pubK, kType = 'rsa', name = '' ):
        ""
        assert kType.lower() == 'rsa'
        self.Name = name
        self.PubKey = rsa.PublicKey.load_pkcs1( pubK )

    def Verify( self, message, sign ):
        ""
        return rsa.verify( message, decodestring( sign ), self.PubKey )


class SelfUser( object ):
    ""
    AllPubKeyStrs = set()
    
    @classmethod
    def New( cls, name = 'DefaultUser' ):
        "create a new self user."
        PubKey, PriKey = rsa.newkeys( 2048 )
        CreateSelfUser( NickName = name, PubKey = PubKey.save_pkcs1(), PriKey = PriKey.save_pkcs1() )

    def __init__( self, condi = '' ):
        ""
        UserData = GetDefaultUser()
        if UserData is None:
            self.New()
            UserData = GetDefaultUser()
            
        self.NickName, self.PubKeyStr, PriKeyStr = UserData
        self.PubKey = rsa.PublicKey.load_pkcs1( self.PubKeyStr )
        self.PriKey = rsa.PrivateKey.load_pkcs1( PriKeyStr )
#        try:
#            self.NickName = NickName.encode( 'ascii' )
#        except:
#            self.NickName = NickName.encode( 'utf8' )
        
    def Issue( self ):
        ""
        return self.PubKeyStr, self.NickName
        
    def Sign( self, msg ):
        ""
        return encodestring( rsa.sign( msg, self.PriKey, SignHashFunc ))
    
    def InitItem( self ):
        "for article items"
        return {
            'AuthPubKey': self.PubKeyStr,
            'NickName': self.NickName,
                }
    
    def SetName( self, name ):
        ""
        self.NickName = name
        SetSelfUserName( self.PubKeyStr, name )
                
    @classmethod
    def Init( cls ):
        ""
        cls.AllPubKeyStrs = set( GetSelfPubKeyStrs())
        
    @classmethod
    def IsSelf( cls, pubK ):
        ""
        return pubK in cls.AllPubKeyStrs