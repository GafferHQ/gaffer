##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2013, John Haddon. All rights reserved.
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
import imath

import IECore
import IECoreGL

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class StandardStyleTest( GafferUITest.TestCase ) :

	def testColorAccessors( self ) :

		s = GafferUI.StandardStyle()

		i = 0
		for n in GafferUI.StandardStyle.Color.names :

			if n=="LastColor" :
				continue

			c = imath.Color3f( i )
			v = getattr( GafferUI.StandardStyle.Color, n )
			s.setColor( v, c )
			self.assertEqual( s.getColor( v ), c )

			i += 1

	def testFontAccessors( self ) :

		s = GafferUI.StandardStyle()

		f = IECoreGL.FontLoader.defaultFontLoader().load( "VeraMono.ttf" )
		for n in GafferUI.Style.TextType.names :

			if n=="LastText" :
				continue

			v = getattr( GafferUI.Style.TextType, n )
			s.setFont( v, f )
			self.assertTrue( s.getFont( v ).isSame( f ) )

	def testChangedSignal( self ) :

		s = GafferUI.StandardStyle()

		cs = GafferTest.CapturingSlot( s.changedSignal() )
		self.assertEqual( len( cs ), 0 )

		s.setColor( GafferUI.StandardStyle.Color.BackgroundColor, imath.Color3f( 0 ) )
		self.assertEqual( len( cs ), 1 )
		self.assertTrue( cs[0][0].isSame( s ) )

		s.setColor( GafferUI.StandardStyle.Color.BackgroundColor, imath.Color3f( 1 ) )
		self.assertEqual( len( cs ), 2 )
		self.assertTrue( cs[1][0].isSame( s ) )

		s.setColor( GafferUI.StandardStyle.Color.BackgroundColor, imath.Color3f( 1 ) )
		self.assertEqual( len( cs ), 2 )

		f = IECoreGL.FontLoader.defaultFontLoader().load( "VeraMono.ttf" )
		s.setFont( GafferUI.Style.TextType.LabelText, f )
		self.assertEqual( len( cs ), 3 )
		self.assertTrue( cs[2][0].isSame( s ) )

		s.setFont( GafferUI.Style.TextType.LabelText, f )
		self.assertEqual( len( cs ), 3 )

if __name__ == "__main__":
	unittest.main()
