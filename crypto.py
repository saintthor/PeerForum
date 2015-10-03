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
#    from random import randint
#    from base64 import encodestring
#    s = 'oejf0wjf09r092u04u088urf009ur-2[riq[[-23r][wfjf'
#    k = randint( 0, 2**256 - 1 )
#    print k
    
