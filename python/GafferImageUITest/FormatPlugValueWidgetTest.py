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
import GafferUI
import GafferImage
import GafferImageUI

class FormatPlugValueWidgetTest( unittest.TestCase ) :

	def testCreation( self ):

		# Create a node to make sure that we have a default format...
		s = Gaffer.ScriptNode()
		n = GafferImage.Grade()
		s.addChild( n )

		# Get the format names
		formatNames = GafferImage.Format.formatNames()

		# Create the plug's ui element.
		fw = GafferImageUI.FormatPlugValueWidget( s["defaultFormat"], lazy=False )

		# Now compare the format names against those in the UI element.
		self.assertEqual( len( fw ), len( formatNames ) )

	def testAccessors( self ) :

		# Create a node to make sure that we have a default format...
		s = Gaffer.ScriptNode()
		n = GafferImage.Grade()
		s.addChild( n )

		# Create the plug's ui element.
		fw = GafferImageUI.FormatPlugValueWidget( s["defaultFormat"], lazy=False )

		# Test the accessors
		formatNameAndValue = fw[0]
		self.assertTrue( isinstance( formatNameAndValue[0], str ) )
		self.assertTrue( isinstance( formatNameAndValue[1], GafferImage.Format ) )
		self.assertEqual( fw[ formatNameAndValue[0] ], formatNameAndValue[1] )
		self.assertEqual( fw[ formatNameAndValue[1] ], formatNameAndValue[0] )

	def __testFormatValue( self ) :
		return GafferImage.Format( 1234, 5678, 1.4 )

	def __testFormatName( self ) :
		return '1234x5678 1.400'

if __name__ == "__main__":
	unittest.main()
