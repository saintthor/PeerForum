# -*- coding: utf-8 -*-
"""
Created on Wed Mar 16 23:11:47 2016

@author: thor
"""
import md5
from base64 import encodestring, decodestring

def GetRealK( k, l, kStr = '' ):
    ""
    lk = len( k )
    if not kStr:
        kStr = ''.join( map( chr, k ))
    m = map( ord, md5.md5( kStr ).digest())
    lm = len( m )
    for i in range( l - lk ):
        k.append( k[2 - lk] ^ k[9 - lk] ^ k[20 - lk] ^ m[i % lm] )
    return k
    
__PassWord = ''
    
def _Xor( k, s ):
    ""
    global __PassWord
    if k is None:
        k = __PassWord
    else:
        __PassWord = k
        
    if k == '':
        return s
    lk = len( k )
    if lk <= 22:
        k = k * ( 21 / lk + 1 )
        
    RealK = GetRealK( map( ord, k ), len( s ), k )
    return ''.join( map( chr, map( int.__xor__, RealK, map( ord, s ))))
    

def EncryptPriKey( k, priKStr ):
    ""
    encrypted = _Xor( k, priKStr[32:-30] )
    return priKStr[:32] + encodestring( encrypted ) + priKStr[-30:]
    

def DecryptPriKey( k, priKStr ):
    ""
    RealPriK = _Xor( k, decodestring( priKStr[32:-30] ))
    return priKStr[:32] + RealPriK + priKStr[-30:]

