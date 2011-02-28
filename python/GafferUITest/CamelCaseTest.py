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

import unittest

import IECore

import Gaffer
from GafferUI.CamelCase import *

class CamelCaseTest( unittest.TestCase ) :

	def testSplit( self ) :
	
		self.assertEqual( split( "A" ), [ "A" ] )
		self.assertEqual( split( "a" ), [ "a" ] )
		self.assertEqual( split( "AB" ), [ "AB" ] )
		self.assertEqual( split( "ab" ), [ "ab" ] )
		self.assertEqual( split( "aB" ), [ "a", "B" ] )
		self.assertEqual( split( "Ab" ), [ "Ab" ] )
		self.assertEqual( split( "TIFFImageReader" ), [ "TIFF", "Image", "Reader" ] )
		self.assertEqual( split( "camelCase" ), [ "camel", "Case" ] )
		self.assertEqual( split( "hsvToRGB" ), [ "hsv", "To", "RGB" ] )
		
	def testJoin( self ) :
	
		self.assertEqual( join( [ "camel", "case" ], Caps.Unchanged ), "camelcase" )
		self.assertEqual( join( [ "camel", "case" ], Caps.First ), "Camelcase" )
		self.assertEqual( join( [ "camel", "case" ], Caps.All ), "CamelCase" )
		self.assertEqual( join( [ "camel", "case" ], Caps.AllExceptFirst ), "camelCase" )

		self.assertEqual( join( [ "TIFF", "image", "reader" ], Caps.Unchanged ), "TIFFimagereader" )
		self.assertEqual( join( [ "TIFF", "image", "reader" ], Caps.First ), "TIFFimagereader" )
		self.assertEqual( join( [ "TIFF", "image", "reader" ], Caps.All ), "TIFFImageReader" )
		self.assertEqual( join( [ "TIFF", "image", "reader" ], Caps.AllExceptFirst ), "tiffImageReader" )
		
	def testToSpaced( self ) :
	
		self.assertEqual( toSpaced( "camelCase" ), "Camel Case" )
		self.assertEqual( toSpaced( "camelCase", Caps.All ), "Camel Case" )
		self.assertEqual( toSpaced( "camelCase", Caps.First ), "Camel case" )
		self.assertEqual( toSpaced( "camelCase", Caps.AllExceptFirst ), "camel Case" )

		self.assertEqual( toSpaced( "TIFFImageReader" ), "TIFF Image Reader" )
		self.assertEqual( toSpaced( "TIFFImageReader", Caps.All ), "TIFF Image Reader" )
		self.assertEqual( toSpaced( "TIFFImageReader", Caps.First ), "TIFF image reader" )
		self.assertEqual( toSpaced( "TIFFImageReader", Caps.AllExceptFirst ), "tiff Image Reader" )
		
	def testFromSpaced( self ) :
	
		self.assertEqual( fromSpaced( "camel case" ), "CamelCase" )
		self.assertEqual( fromSpaced( "camel case", Caps.All ), "CamelCase" )
		self.assertEqual( fromSpaced( "camel case", Caps.First ), "Camelcase" )
		self.assertEqual( fromSpaced( "camel case", Caps.AllExceptFirst ), "camelCase" )
	
if __name__ == "__main__":
	unittest.main()
	
