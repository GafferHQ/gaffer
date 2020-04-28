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

import os
import unittest
import imath

import IECore

import Gaffer
import GafferImage
import GafferImageTest

class AtomicFormatPlugTest( GafferImageTest.ImageTestCase ) :

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["f"] = GafferImage.AtomicFormatPlug( "testPlug", defaultValue = GafferImage.Format( 10, 5, .5  ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		se = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( se )

		self.assertTrue( s2["n"]["f"].isInstanceOf( GafferImage.AtomicFormatPlug ) )

	def testOffsetSerialize( self ) :

		format = GafferImage.Format( imath.Box2i( imath.V2i( -5, -11 ), imath.V2i( 13, 19 ) ), .5 )
		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["f"] = GafferImage.AtomicFormatPlug( "testPlug", defaultValue = format, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		se = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( se )

		self.assertEqual( s2["n"]["f"].getValue(), format )

	def testInputPlug( self ) :

		n = Gaffer.Node()
		f = GafferImage.AtomicFormatPlug("f", direction = Gaffer.Plug.Direction.In, flags = Gaffer.Plug.Flags.Default )
		n.addChild( f )
		s = Gaffer.ScriptNode()
		s.addChild( n )

		with s.context() :
			f1 = n["f"].getValue()

		# The default value of any input plug should be it's real value regardless of whether it is empty or not.
		self.assertEqual( f1, GafferImage.Format() )

	def testExpressions( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()
		s["n1"]["user"]["f"] = GafferImage.AtomicFormatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n2"]["user"]["f"] = GafferImage.AtomicFormatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'f = parent["n1"]["user"]["f"]; b = f.getDisplayWindow(); b.setMin( b.min() - imath.V2i( 10 ) ); b.setMax( b.max() + imath.V2i( 20 ) ); f.setPixelAspect( 0.5 ); f.setDisplayWindow( b ); parent["n2"]["user"]["f"] = f')

		s["n1"]["user"]["f"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 20, 30 ), imath.V2i( 100, 110 ) ), 1 ) )

		self.assertEqual( s["n2"]["user"]["f"].getValue(), GafferImage.Format( imath.Box2i( imath.V2i( 10, 20 ), imath.V2i( 120, 130 ) ), 0.5 ) )

	def testGetAndSetEmptyFormat( self ) :

		p = GafferImage.AtomicFormatPlug()
		p.setValue( GafferImage.Format() )
		self.assertEqual( p.getValue(), GafferImage.Format() )

	def testHashRepeatability( self ) :

		p = GafferImage.AtomicFormatPlug()
		p.setValue( GafferImage.Format( 1920, 1080 ) )

		allHashes = set()
		for i in range( 0, 1000 ) :
			allHashes.add( p.hash().toString() )

		self.assertEqual( len( allHashes ), 1 )

if __name__ == "__main__":
	unittest.main()
