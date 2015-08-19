# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 22:02:40 2015

@author: thor
"""
from sqlitedb import CreateSelfUser, GetDefaultUser
import rsa1 as rsa
from base64 import encodestring, decodestring
from const import SignHashFunc


class OtherUser( object ):
    ""
    def __init__( self, pubK, kType = 'rsa', name = '' ):
        ""
        assert kType.lower() == 'rsa'
        self.Name = name
        #print '\nOtherUser.__init__', pubK
        self.PubKey = rsa.PublicKey.load_pkcs1( pubK )

    def Verify( self, message, sign ):
        ""
        #print '\nVerify', message, sign
        return rsa.verify( message, decodestring( sign ), self.PubKey )


class SelfUser( object ):
    ""
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
            
        
    def Sign( self, msg ):
        ""
        #print '\nSign', self.PubKeyStr
        return encodestring( rsa.sign( msg, self.PriKey, SignHashFunc ))
    
    def InitItem( self ):
        "for article items"
        return {
            'AuthPubKey': self.PubKeyStr,
            'NickName': self.NickName,
                }
