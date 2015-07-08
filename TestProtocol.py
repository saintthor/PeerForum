# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 23:14:24 2015

@author: thor
"""

import urllib2
from urllib import urlencode
from json import dumps
from time import time

url = 'http://127.0.0.1:8000/node'

PubKeyStr = '-----BEGIN RSA PUBLIC KEY-----\nMBACCQC0VWnxhjkBewIDAQAB\n-----END RSA PUBLIC KEY-----\n'
PriKeyStr = '-----BEGIN RSA PRIVATE KEY-----\nMD8CAQACCQC0VWnxhjkBewIDAQABAgkAhiOm2WsSYXECBQLWSpDzAgQ/kC9ZAgUB\npIMt4wIENh4WkQIFAtU8JHU=\n-----END RSA PRIVATE KEY-----\n'

Req = urllib2.Request( url )

QryPubKeyMsg = chr( 0x10 ) + dumps( {
                            'Time': int( time() * 1000 ),
                            "PubKey": PubKeyStr,
                            "Address": "202.112.58.200:8760", 
                                } )

print QryPubKeyMsg
data = urlencode( { 'pfp': QryPubKeyMsg } )

req = urllib2.Request( url, data )
response = urllib2.urlopen( req )
print response.read()
