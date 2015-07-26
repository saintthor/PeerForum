# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 23:14:24 2015

@author: thor
"""

import urllib2
from urllib import urlencode
from json import loads
from time import sleep
import rsa1 as rsa
from base64 import decodestring

from sqlitedb import SqliteDB
from node import SelfNode, NeighborNode
from protocol import PFPMessage, QryPubKeyTask

class TestSelfNode( SelfNode ):
    ""
    def __init__( self ):
        ""
        self.Name = 'TestNode'
        with SqliteDB( './test.db' ) as cursor:
            self.PubKeyStr, PriKeyStr = cursor.execute( "select PubKey, PriKey from selfnode" ).fetchone()
#        self.PubKeyStr = '-----BEGIN RSA PUBLIC KEY-----\nMIGJAoGBAJ5nfLMI1HUIr+91+FjtxetWF0TTsp9Clv97rNtR6whQL6wUdxzmqY3l\n3vQUtI2cIRwlNBXKZcR/5Ho3XrH39UiEsOZUs+pPMDXyWi4iifE56vKMGlw9vxat\nSA5iZldpDj2OeGXDY6WSOSO/VuOF//vO96Ha49YmX9Tw56a2l40LAgMBAAE=\n-----END RSA PUBLIC KEY-----\n'
#        PriKeyStr = '-----BEGIN RSA PRIVATE KEY-----\nMIICYgIBAAKBgQCeZ3yzCNR1CK/vdfhY7cXrVhdE07KfQpb/e6zbUesIUC+sFHcc\n5qmN5d70FLSNnCEcJTQVymXEf+R6N16x9/VIhLDmVLPqTzA18louIonxOeryjBpc\nPb8WrUgOYmZXaQ49jnhlw2Olkjkjv1bjhf/7zveh2uPWJl/U8OemtpeNCwIDAQAB\nAoGAUp287w+q54NpZ2ZK6e7RbEWRi0cygVfUs1lItXbLM6HGy2Q9H6i6RBThLMJj\nzPviVPCecsMGQu9FNe0MhnGzioeic1aOUzabCyYCYTdrc/qURsdS3VUUQpAqe1ul\nhxj2dnOvDFC6fxHmwAMh1BeuXaAWRM4L+OnQeOECwhLWVakCRQD7e/Ye0LPX43Zz\nluh8vTj6gyTJzFCvtma0IsLfJtPt2AHIGHK30vvJvP49vgAQfQf5BgnoQttEDg4O\nhLIhiP+XWY7hDQI9AKE/plc+XwWw3T8JaOmHFwc6P86OS7w7hFeVFew6ASiAfr84\nvyvTrmIvVwMyG9X87ZS9rfdJr/k7n0SwdwJFALC1+0zN9AF4eQxh9v1n7TjCnEAc\njHnb3rEnV+18GCEhzqau3zViUMECR1hVQTBU2xxV7PJCwFZC1gfHoG/GF2tfZ/Gl\nAj0AiBae/by/F594aq43Y/hGYCwyE9MWaivU+tHxaahet98SmbJ77bI+19DaX/EX\nexd3L/SR8UW4heFi/ubrAkUAkAdWeA6snOCPMZ7SmwB5cPyxjpsw55p2EeRL5OAO\nmqS1lb8AB4kjnhMjQRsytNcl9toWL7IxxPHlLM1qtMoy8wOB8A8=\n-----END RSA PRIVATE KEY-----\n'
        self.SvPrtcl = 'HTTP'
        self.Desc = '如果你看到我，那是出大事了。'
        self.PubKey = rsa.PublicKey.load_pkcs1( self.PubKeyStr )
        self.PriKey = rsa.PrivateKey.load_pkcs1( PriKeyStr )
        self.Addr = "http://127.0.0.1:8001/node"

class TestNeighborNode( NeighborNode ):
    ""
    def __init__( self, **kw ):
        ""
        self.tasks = set( [] )
        for k, v in kw.items():
            setattr( self, k, v )
        if hasattr( self, 'PubKey' ):
            self.PubKey = rsa.PublicKey.load_pkcs1( self.PubKey )
        self.Addr = 'http://127.0.0.1:8000/node'
        
def test():
    ""
    PFPMessage.Init()
    Remote = TestNeighborNode()
    #LiveNeighborD = { Remote.PubKey: Remote }
    PFPMessage.LocalNode = TestSelfNode()
    
    task = QryPubKeyTask( Remote )
    TaskMsg = task.StepGen()
    ComingMsg = None
    
    while True:
        try:
            MsgCls = TaskMsg.send( ComingMsg )
            if MsgCls is None:
                sleep( 1 )
                continue
        except StopIteration:
            print 'test over.'
            break
        
        print 'MsgCls is ', MsgCls
        Message = MsgCls()
        Message.SetRemoteNode( Remote )
        data = urlencode( { 'pfp': Message.Issue() } )
        print '============ send data ============\n', data
        req = urllib2.Request( Remote.Addr, data )
        response = urllib2.urlopen( req )
        reply = response.read()
        print '============ get reply ============\n', reply
        ComingMsg = None
        Msgs = []
        for msgStr in reply.split( '\n' ):
            if not msgStr:
                break
            ComingMsg = PFPMessage( ord( msgStr[0] ))
            MsgBody = loads( msgStr[1:] )
            
            VerifyStr = ComingMsg.GetBody( MsgBody )
            if VerifyStr:
                body = loads( VerifyStr )
                Remote.PubKey = rsa.PublicKey.load_pkcs1( body['PubKey'] )
                Remote.Verify( VerifyStr, decodestring( MsgBody['sign'] ))
            
            #Msgs.extend( Remote.Reply( ComingMsg ) + Remote.Append())
        

if __name__ == '__main__':
    test()







#url = 'http://127.0.0.1:8000/node'
#
#QryPubKeyMsg = chr( 0x10 ) + dumps( {
#                            'Time': int( time() * 1000 ),
#                            "PubKey": PubKeyStr,
#                            "Address": "202.112.58.200:8760", 
#                                } )
#
##print QryPubKeyMsg
#data = urlencode( { 'pfp': QryPubKeyMsg } )
#
#req = urllib2.Request( url, data )
#response = urllib2.urlopen( req )
#
#reply = response.read()
#print '============ get reply ============\n', reply
#print 'code: ', reply[0]
#body = loads( reply[1:] )
#for k, v in body.items():
#    body[k] = v = decodestring( v )
#    print k, ':', v
#
#key = rsa.decrypt( body['key'], PriKey )
#print 'get key: ', key
#message = CBCDecrypt( body['msg'], key )
#print 'get msg: ', message
#RemotePubKey = rsa.PublicKey.load_pkcs1( loads( message )['PubKey'] )
#print 'verify sign: ', rsa.verify( message, body['sign'], RemotePubKey )
#
#print '====================  send 0x11  ========================'
#body = {
#    "Address": '',
#    "NodeName": u'未提交',
#    "NodeTypeVer": 'TechInfo',
#    "PFPVer": 'PFPVersion',
#    "BaseProtocol": 'HTTP',
#    "Description": '老眼平生空四海。',
#        }
#                
#body['Time'] = int( time() * 1000 )
#body['PubKey'] = PubKeyStr
#
#BodyStr = dumps( body )
#CryptMsgD = {}
#k = ''.join( [choice( "1234567890)(*&^%$#@!`~qazxswedcvfrtgbnhyujm,kiolp;.[]{}:?><\"\\'/PLOKMIJNUHBYGVTFCRDXESZWAQ" )
#                        for i in range( 32 )] )
#CryptMsgD['msg'] = encodestring( CBCEncrypt( BodyStr, k ))
#CryptMsgD['key'] = encodestring( rsa.encrypt( k, RemotePubKey ))
#CryptMsgD['sign'] = encodestring( rsa.sign( BodyStr, PriKey, 'MD5' ))
##print type( CryptMsgD['msg'] ), CryptMsgD['msg']
#MsgStr = chr( 0x11 ) + dumps( CryptMsgD )
#
#data = urlencode( { 'pfp': MsgStr } )
#
#req = urllib2.Request( url, data )
#response = urllib2.urlopen( req )
#print response.read()