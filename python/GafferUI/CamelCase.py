##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#  
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#  
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#  
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#  
##########################################################################

from IECore import Enum

Caps = Enum.create( "Unchanged", "First", "All", "AllExceptFirst" )

## \todo Remove now this is in cortex
def split( camelCase ) :

	if not len( camelCase ) :
		return []
	
	# split into words based on adjacent cases being the same	
	result = []
	current = ""
	prevUpper = camelCase[0].isupper()
	for c in camelCase :
		upper = c.isupper()
		if upper==prevUpper :
			current += c
		else :
			result.append( current )
			current = c
		prevUpper = upper
		
	result.append( current )
	
	# move last capital of previous word onto any lowercase words
	i = 1
	while i<len( result ) :
	
		if result[i].islower() and result[i-1][-1].isupper() :
			
			result[i] = result[i-1][-1] + result[i]
			if len( result[i-1] )==1 :
				del result[i-1]
				i-=1
			else :
				result[i-1] = result[i-1][:-1]
				
		i+=1
	
	return result
	
def join( words, caps=Caps.All, separator="" ) :

	cWords = []
	for i in range( 0, len( words ) ) :
		word = words[i]
		if caps!=Caps.Unchanged :
			if (caps==Caps.First and i==0) or caps==Caps.All or (caps==Caps.AllExceptFirst and i!=0) :
				if not word.isupper() :
					word = word.lower()
				word = word[0].upper() + word[1:]
			elif caps==Caps.AllExceptFirst and i==0 or (caps==Caps.First and i!=0):
				word = word.lower()
						
		cWords.append( word )
		
	return separator.join( cWords )

## Convert a CamelCase word to a string with spaces between words
def toSpaced( camelCase, caps=Caps.All ) :

	s = split( camelCase )
	return join( s, caps, " " )
	
	
## Convert a spaced word to a camel case string	
def fromSpaced( spaced, caps=Caps.All ) :

	s = spaced.split()
	return join( s, caps )
	
