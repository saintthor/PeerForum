# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 23:14:24 2015

@author: thor
"""

import urllib2
from urllib import urlencode
from json import dumps, loads
from time import time
import rsa1 as rsa
from base64 import encodestring, decodestring
from crypto import CBCEncrypt, CBCDecrypt

url = 'http://127.0.0.1:8000/node'

PubKeyStr = '-----BEGIN RSA PUBLIC KEY-----\nMIGJAoGBAJ5nfLMI1HUIr+91+FjtxetWF0TTsp9Clv97rNtR6whQL6wUdxzmqY3l\n3vQUtI2cIRwlNBXKZcR/5Ho3XrH39UiEsOZUs+pPMDXyWi4iifE56vKMGlw9vxat\nSA5iZldpDj2OeGXDY6WSOSO/VuOF//vO96Ha49YmX9Tw56a2l40LAgMBAAE=\n-----END RSA PUBLIC KEY-----\n'
PriKeyStr = '-----BEGIN RSA PRIVATE KEY-----\nMIICYgIBAAKBgQCeZ3yzCNR1CK/vdfhY7cXrVhdE07KfQpb/e6zbUesIUC+sFHcc\n5qmN5d70FLSNnCEcJTQVymXEf+R6N16x9/VIhLDmVLPqTzA18louIonxOeryjBpc\nPb8WrUgOYmZXaQ49jnhlw2Olkjkjv1bjhf/7zveh2uPWJl/U8OemtpeNCwIDAQAB\nAoGAUp287w+q54NpZ2ZK6e7RbEWRi0cygVfUs1lItXbLM6HGy2Q9H6i6RBThLMJj\nzPviVPCecsMGQu9FNe0MhnGzioeic1aOUzabCyYCYTdrc/qURsdS3VUUQpAqe1ul\nhxj2dnOvDFC6fxHmwAMh1BeuXaAWRM4L+OnQeOECwhLWVakCRQD7e/Ye0LPX43Zz\nluh8vTj6gyTJzFCvtma0IsLfJtPt2AHIGHK30vvJvP49vgAQfQf5BgnoQttEDg4O\nhLIhiP+XWY7hDQI9AKE/plc+XwWw3T8JaOmHFwc6P86OS7w7hFeVFew6ASiAfr84\nvyvTrmIvVwMyG9X87ZS9rfdJr/k7n0SwdwJFALC1+0zN9AF4eQxh9v1n7TjCnEAc\njHnb3rEnV+18GCEhzqau3zViUMECR1hVQTBU2xxV7PJCwFZC1gfHoG/GF2tfZ/Gl\nAj0AiBae/by/F594aq43Y/hGYCwyE9MWaivU+tHxaahet98SmbJ77bI+19DaX/EX\nexd3L/SR8UW4heFi/ubrAkUAkAdWeA6snOCPMZ7SmwB5cPyxjpsw55p2EeRL5OAO\nmqS1lb8AB4kjnhMjQRsytNcl9toWL7IxxPHlLM1qtMoy8wOB8A8=\n-----END RSA PRIVATE KEY-----\n'
PriKey = rsa.PrivateKey.load_pkcs1( PriKeyStr )

Req = urllib2.Request( url )

QryPubKeyMsg = chr( 0x10 ) + dumps( {
                            'Time': int( time() * 1000 ),
                            "PubKey": PubKeyStr,
                            "Address": "202.112.58.200:8760", 
                                } )

#print QryPubKeyMsg
data = urlencode( { 'pfp': QryPubKeyMsg } )

req = urllib2.Request( url, data )
response = urllib2.urlopen( req )

reply = response.read()
print '============ get reply ============\n', reply
print 'code: ', reply[0]
body = loads( reply[1:] )
for k, v in body.items():
    body[k] = v = decodestring( v )
    print k, ':', v

key = rsa.decrypt( body['key'], PriKey )
print 'get key: ', key
message = CBCDecrypt( body['msg'], key )
print 'get msg: ', message
RemotePubKey = rsa.PublicKey.load_pkcs1( loads( message )['PubKey'] )
print 'verify sign: ', rsa.verify( message, body['sign'], RemotePubKey )
