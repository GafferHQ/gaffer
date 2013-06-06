##########################################################################
#  
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

import GafferImage

class FormatPlugTest( unittest.TestCase ) :

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["f"] = GafferImage.FormatPlug( "testPlug", defaultValue = GafferImage.Format( 10, 5, .5  ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		se = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( se )

		self.failUnless( s2["n"]["f"].isInstanceOf( GafferImage.FormatPlug.staticTypeId() ) )
	
	def testInputPlug( self ) :
		n = Gaffer.Node()
		f = GafferImage.FormatPlug("f", direction = Gaffer.Plug.Direction.In, flags = Gaffer.Plug.Flags.Default )
		n.addChild( f )
		s = Gaffer.ScriptNode()
		s.addChild( n )
		
		with s.context() :
			f1 = n["f"].getValue()
		
		# The default value of any input plug should be it's real value regardless of whether it is empty or not.
		self.assertEqual( f1, GafferImage.Format() )
		
	def testDefaultFormatOutput( self ) :
		n = GafferImage.Constant()
		s = Gaffer.ScriptNode()
		s.addChild( n )
		
		# Get the default format
		defaultFormat = GafferImage.Format.getDefaultFormat( s )
		
		with s.context() :
			f1 = n["out"]["format"].getValue()
			
		# Check that the output of the constant node matches the default format...
		self.assertEqual( defaultFormat, f1 )
		
		# Now change the default format and check it again!
		GafferImage.Format.setDefaultFormat( s, GafferImage.Format( 100, 102, 1.3 ) )
		with s.context() :
			f1 = n["out"]["format"].getValue()
		
		# Check that the output of the constant node matches the default format...
		self.assertEqual( GafferImage.Format( 100, 102, 1.3 ), f1 )
		
if __name__ == "__main__":
	unittest.main()
