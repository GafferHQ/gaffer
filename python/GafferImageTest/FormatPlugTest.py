##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

	def testConstructor( self ) :

		p = GafferImage.FormatPlug()
		self.assertEqual( p.getName(), "FormatPlug" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p.defaultValue(), GafferImage.Format() )
		self.assertEqual( p.getValue(), GafferImage.Format() )
		self.assertEqual( p.getFlags(), Gaffer.Plug.Flags.Default )

		p = GafferImage.FormatPlug(
			"p",
			Gaffer.Plug.Direction.Out,
			GafferImage.Format( 100, 200, 2 ),
			Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)
		self.assertEqual( p.getName(), "p" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.Out )
		self.assertEqual( p.defaultValue(), GafferImage.Format( 100, 200, 2 ) )
		self.assertEqual( p.getValue(), GafferImage.Format( 100, 200, 2 ) )
		self.assertEqual( p.getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

	def testChildren( self ) :

		p = GafferImage.FormatPlug()
		self.assertEqual( p.keys(), [ "displayWindow", "pixelAspect" ] )
		self.assertTrue( isinstance( p["displayWindow"], Gaffer.Box2iPlug ) )
		self.assertTrue( isinstance( p["pixelAspect"], Gaffer.FloatPlug ) )

		self.assertRaises( RuntimeError, p.addChild, Gaffer.IntPlug() )

	def testValue( self ) :

		p = GafferImage.FormatPlug()
		v = GafferImage.Format( IECore.Box2i( IECore.V2i( 11, 12 ), IECore.V2i( 100, 200 ) ), 2 )

		p.setValue( v )
		self.assertEqual( p.getValue(), v )
		self.assertEqual( p["displayWindow"].getValue(), v.getDisplayWindow() )
		self.assertEqual( p["pixelAspect"].getValue(), v.getPixelAspect() )

if __name__ == "__main__":
	unittest.main()
