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
import inspect

import IECore

import Gaffer
import GafferImage
import GafferImageTest

class FormatPlugTest( GafferImageTest.ImageTestCase ) :

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

	def testDefaultFormatFromContext( self ) :

		constant = GafferImage.Constant()

		with Gaffer.Context() as context :

			# Even if we haven't specified a default context, we should still
			# be given something.
			self.assertFalse(
				GafferImage.empty(
					constant["out"]["format"].getValue().getDisplayWindow()
				)
			)

			# And if we specify something specific, we should get it.
			f = GafferImage.Format( 100, 200, 2 )
			GafferImage.FormatPlug.setDefaultFormat( context, f )
			self.assertEqual( GafferImage.FormatPlug.getDefaultFormat( context ), f )
			self.assertEqual( constant["out"]["format"].getValue(), f )

			f = GafferImage.Format( 200, 400, 1 )
			GafferImage.FormatPlug.setDefaultFormat( context, f )
			self.assertEqual( GafferImage.FormatPlug.getDefaultFormat( context ), f )
			self.assertEqual( constant["out"]["format"].getValue(), f )

	def testAcquireDefaultFormatPlug( self ) :

		s1 = Gaffer.ScriptNode()
		s2 = Gaffer.ScriptNode()

		p1A = GafferImage.FormatPlug.acquireDefaultFormatPlug( s1 )
		p1B = GafferImage.FormatPlug.acquireDefaultFormatPlug( s1 )

		p2A = GafferImage.FormatPlug.acquireDefaultFormatPlug( s2 )
		p2B = GafferImage.FormatPlug.acquireDefaultFormatPlug( s2 )

		self.assertTrue( p1A.isSame( p1B ) )
		self.assertTrue( p2A.isSame( p2B ) )
		self.assertFalse( p1A.isSame( p2A ) )

	def testDefaultFormatFromScript( self ) :

		s = Gaffer.ScriptNode()
		self.assertFalse( "defaultFormat" in s )

		s["c"] = GafferImage.Constant()
		self.assertTrue( "defaultFormat" in s )

		defaultFormatPlug = GafferImage.FormatPlug.acquireDefaultFormatPlug( s )
		self.assertTrue( defaultFormatPlug.isSame( s["defaultFormat"] ) )

		with s.context() :

			self.assertFalse(
				GafferImage.empty(
					s["c"]["out"]["format"].getValue().getDisplayWindow()
				)
			)

			f = GafferImage.Format( 100, 200, 2 )
			defaultFormatPlug.setValue( f )
			self.assertEqual( s["c"]["out"]["format"].getValue(), f )

			f = GafferImage.Format( 200, 400, 1 )
			defaultFormatPlug.setValue( f )
			self.assertEqual( s["c"]["out"]["format"].getValue(), f )

	def testDefaultFormatAfterScriptLoad( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Constant()

		f = GafferImage.Format( 100, 100 )
		GafferImage.FormatPlug.acquireDefaultFormatPlug( s ).setValue( f )
		with s.context() :
			self.assertEqual( s["c"]["out"]["format"].getValue(), f )

		s2 = Gaffer.ScriptNode( "s2" )
		s2.execute( s.serialise() )
		with s2.context() :
			self.assertEqual( s2["c"]["out"]["format"].getValue(), f )

	def testDefaultFormatFromScriptWithBox( self ) :

		s = Gaffer.ScriptNode()
		self.assertFalse( "defaultFormat" in s )

		s["b"] = Gaffer.Box()
		s["b"]["c"] = GafferImage.Constant()
		self.assertTrue( "defaultFormat" in s )

	def testExpressions( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()
		s["n1"]["user"]["f"] = GafferImage.FormatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n2"]["user"]["f"] = GafferImage.FormatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( inspect.cleandoc(
			"""
			f = parent["n1"]["user"]["f"]
			b = f.getDisplayWindow()
			b.min -= IECore.V2i( 10 )
			b.max += IECore.V2i( 20 )
			f.setPixelAspect( 0.5 )
			f.setDisplayWindow( b )
			parent["n2"]["user"]["f"] = f
			"""
		) )

		s["n1"]["user"]["f"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 20, 30 ), IECore.V2i( 100, 110 ) ), 1 ) )

		self.assertEqual( s["n2"]["user"]["f"].getValue(), GafferImage.Format( IECore.Box2i( IECore.V2i( 10, 20 ), IECore.V2i( 120, 130 ) ), 0.5 ) )

	def testDefaultExpression( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["f"] = GafferImage.FormatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		f = GafferImage.Format( 100, 200, 1 )
		s["n"]["f"].setValue( f )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( s["e"].defaultExpression( s["n"]["f"], "python" ) )

		self.assertTrue( s["n"]["f"].getInput().node().isSame( s["e"] ) )
		self.assertEqual( s["n"]["f"].getValue(), f )

	def testDefaultFormatHashRepeatability( self ) :

		allHashes = set()
		for i in range( 0, 1000 ) :
			c = Gaffer.Context()
			GafferImage.FormatPlug.setDefaultFormat( c, GafferImage.Format( 1920, 1080 ) )
			allHashes.add( str( c.hash() ) )

		self.assertEqual( len( allHashes ), 1 )

if __name__ == "__main__":
	unittest.main()
