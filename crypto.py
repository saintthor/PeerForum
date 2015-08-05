# -*- coding: utf-8 -*-
"""
Created on Wed Dec 10 17:02:11 2014

@author: thor
"""

from Crypto.Cipher import AES

def Pad( text, size=16 ):
    ""
    pad = size - len( text ) % size
    return text + chr( pad ) * pad
    
def CBCEncrypt( s, k ):
    ""
    aes = AES.new( k, mode=AES.MODE_CBC, IV=k[8:24] )             #must create aes everytime.
    return aes.encrypt( Pad( s ))    
                    
def CBCDecrypt( s, k ):
    ""
    aes = AES.new( k, mode=AES.MODE_CBC, IV=k[8:24] )            #must create aes everytime.
    s0 = aes.decrypt( s )
    return s0[:-ord(s0[-1])]#.encode('utf8')
    
    
#if __name__ == '__main__':
#    import binascii
#    from base64 import encodestring
#    s = 'oejf0wjf09r092u04u088urf009ur-2[riq[[-23r][wfjf'
#    key = "(8FGII!9N'xE4MIGF1gTcQT$*7ME*3bk"
#    print s
#    from time import time
#    t0 = time()
#    s2 = CBCEncrypt( s, key )
#    print s2
#    print 'b2a_hex', binascii.b2a_hex( s2 )
#    print 'b2a_hqx', binascii.b2a_hqx( s2 )
#    print 'b2a_qp', binascii.b2a_qp( s2 )
#    print 'b2a_base64', binascii.b2a_base64( s2 ), encodestring( s2 )
#    print time() - t0
