##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferTest

class NameValuePlugTest( GafferTest.TestCase ) :

	def assertPlugSerialises( self, plug ):
		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["p"] = plug

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"]["p"].getName(), plug.getName() )
		self.assertEqual( s2["n"]["p"].direction(), plug.direction() )
		self.assertEqual( s2["n"]["p"].getFlags(), plug.getFlags() )

		self.assertEqual( s2["n"]["p"].keys(), plug.keys() )
		self.assertEqual( s2["n"]["p"]["value"].getValue(), plug["value"].getValue() )
		self.assertEqual( s2["n"]["p"]["value"].defaultValue(), plug["value"].defaultValue() )
		self.assertEqual( s2["n"]["p"]["name"].getValue(), plug["name"].getValue() )
		self.assertEqual( s2["n"]["p"]["name"].defaultValue(), plug["name"].defaultValue() )

		if "enable" in plug.keys():
			self.assertEqual( s2["n"]["p"]["enable"].getValue(), plug["enable"].getValue() )
			self.assertEqual( s2["n"]["p"]["enable"].defaultValue(), plug["enable"].defaultValue() )

		if isinstance( plug, Gaffer.IntPlug ):
			self.assertEqual( s2["n"]["p"]["value"].minValue(), plug.minValue() )
			self.assertEqual( s2["n"]["p"]["value"].maxValue(), plug.maxValue() )


	def assertCounterpart( self, plug ):
		p2 = plug.createCounterpart( "testName", Gaffer.Plug.Direction.Out )

		self.assertEqual( p2.getName(), "testName" )
		self.assertEqual( p2.direction(), Gaffer.Plug.Direction.Out )
		self.assertEqual( p2.getFlags(), plug.getFlags() )

		self.assertEqual( p2.keys(), plug.keys() )
		if "value" in plug.keys():
			self.assertEqual( p2["value"].getValue(), plug["value"].getValue() )
			self.assertEqual( p2["value"].defaultValue(), plug["value"].defaultValue() )

		if "name" in plug.keys():
			self.assertEqual( p2["name"].getValue(), plug["name"].getValue() )
			self.assertEqual( p2["name"].defaultValue(), plug["name"].defaultValue() )

		if "enable" in plug.keys():
			self.assertEqual( p2["enable"].getValue(), plug["enable"].getValue() )
			self.assertEqual( p2["enable"].defaultValue(), plug["enable"].defaultValue() )

		if isinstance( plug, Gaffer.IntPlug ):
			self.assertEqual( p2.minValue(), plug.minValue() )
			self.assertEqual( p2.maxValue(), plug.maxValue() )


	def test( self ) :

		constructed = {}
		constructed["defaults"] = {}
		constructed["specified"] = {}
		constructed["defaults"]["empty"] = Gaffer.NameValuePlug()
		constructed["defaults"]["partialEmpty"] = Gaffer.NameValuePlug()
		constructed["defaults"]["partialEmpty"].addChild( Gaffer.StringPlug( "name", defaultValue = "key") )

		# Note that if we specify the direction and flags without specifying argument names, this is ambiguous
		# with the later forms of the constructor.  I guess this is OK since the old serialised forms
		# of MemberPlug do include the argument names, and we want to deprecate this form anyway
		constructed["specified"]["empty"] = Gaffer.NameValuePlug( "foo", direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		constructed["specified"]["partialEmpty"] = Gaffer.NameValuePlug( "foo", direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		constructed["specified"]["partialEmpty"].addChild( Gaffer.StringPlug( "name", direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, defaultValue = "key" ) )

		constructed["defaults"]["fromData"] = Gaffer.NameValuePlug( "key", IECore.IntData(42) )
		constructed["specified"]["fromData"] = Gaffer.NameValuePlug( "key", IECore.IntData(42), "foo", Gaffer.Plug.Direction.Out, Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		constructed["defaults"]["fromPlug"] = Gaffer.NameValuePlug( "key", Gaffer.IntPlug( minValue = -3, maxValue = 5) )
		constructed["specified"]["fromPlug"] = Gaffer.NameValuePlug( "key", Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ), "foo" )

		constructed["defaults"]["fromDataEnable"] = Gaffer.NameValuePlug( "key", IECore.IntData(42), True )
		constructed["specified"]["fromDataEnable"] = Gaffer.NameValuePlug( "key", IECore.IntData(42), True, "foo", Gaffer.Plug.Direction.Out, Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		constructed["defaults"]["fromPlugEnable"] = Gaffer.NameValuePlug( "key", Gaffer.IntPlug(), True )
		constructed["specified"]["fromPlugEnable"] = Gaffer.NameValuePlug( "key", Gaffer.IntPlug( minValue = -7, maxValue = 15, direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) , True, "foo" )

		for k in [ "empty", "fromData", "fromPlug", "fromDataEnable", "fromPlugEnable" ]:
			defa = constructed["defaults"][k]
			spec = constructed["specified"][k]
			numChildren = 3 if "Enable" in k else 2
			if k == "empty":
				numChildren = 0
			self.assertEqual( len( spec.children() ), numChildren )
			self.assertEqual( len( defa.children() ), numChildren )

			self.assertEqual( defa.getName(), "NameValuePlug" )
			self.assertEqual( spec.getName(), "foo" )
			self.assertEqual( defa.direction(), Gaffer.Plug.Direction.In )
			self.assertEqual( spec.direction(), Gaffer.Plug.Direction.Out )
			self.assertEqual( defa.getFlags(), Gaffer.Plug.Flags.Default )
			self.assertEqual( spec.getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

			if k == "empty":
				self.assertNotIn( "name", defa )
				self.assertNotIn( "name", spec )
				self.assertNotIn( "value", defa )
				self.assertNotIn( "value", spec )
			elif k == "partialEmpty":
				self.assertEqual( defa["name"].getValue(),  "key" )
				self.assertEqual( spec["name"].getValue(),  "key" )
				self.assertNotIn( "value", defa )
				self.assertNotIn( "value", spec )
			else:
				self.assertEqual( defa["name"].getValue(),  "key" )
				self.assertEqual( spec["name"].getValue(),  "key" )

				if "fromPlug" in k:
					self.assertEqual( defa["value"].getValue(),  0 )
					self.assertEqual( spec["value"].getValue(),  0 )
				else:
					self.assertEqual( defa["value"].getValue(),  42 )
					self.assertEqual( spec["value"].getValue(),  42 )

			if k == "empty":
				# A completely empty NameValuePlug is invalid, but we have to partially
				# support it because old serialisation code will create these before
				# the addChild's run to create name and value
				self.assertCounterpart( defa )
				self.assertCounterpart( spec )

				# We shouldn't ever serialise invalid plugs though - if the children
				# haven't been created by the time we try to serialise, that's a bug
				self.assertRaises( RuntimeError, self.assertPlugSerialises, spec )
			elif k == "partialEmpty":
				# A NameValuePlug with a name but no value, on the other hand, is just
				# broken
				self.assertRaises( RuntimeError, self.assertPlugSerialises, spec )
				self.assertRaises( RuntimeError, self.assertCounterpart, defa )
				self.assertRaises( RuntimeError, self.assertCounterpart, spec )
			else:
				self.assertPlugSerialises( spec )
				self.assertCounterpart( defa )
				self.assertCounterpart( spec )

	def testBasicRepr( self ) :

		p = Gaffer.NameValuePlug( "key", IECore.StringData( "value" ) )
		self.assertEqual(
			repr( p ),
			'Gaffer.NameValuePlug( "key", Gaffer.StringPlug( "value", defaultValue = \'value\', ), "NameValuePlug", Gaffer.Plug.Flags.Default )'
		)

	def testEmptyPlugRepr( self ) :
		# Use the deprecated constructor to create a NameValuePlug without name or value
		p = Gaffer.NameValuePlug( "mm", direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertRaises( RuntimeError, repr, p )

	def testValueTypes( self ) :

		for v in [
				IECore.FloatVectorData( [ 1, 2, 3 ] ),
				IECore.IntVectorData( [ 1, 2, 3 ] ),
				IECore.StringVectorData( [ "1", "2", "3" ] ),
				IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 1, 5 ) ] ),
				IECore.Color3fVectorData( [ imath.Color3f( x ) for x in range( 1, 5 ) ] ),
				IECore.M44fVectorData( [ imath.M44f() * x for x in range( 1, 5 ) ] ),
				IECore.M33fVectorData( [ imath.M33f() * x for x in range( 1, 5 ) ] ),
				IECore.V2iVectorData( [ imath.V2i( x ) for x in range( 1, 5 ) ] ),
				IECore.V3fData( imath.V3f( 1, 2, 3 ) ),
				IECore.V2fData( imath.V2f( 1, 2 ) ),
				IECore.M44fData( imath.M44f( *range(16) ) ),
				IECore.Box2fData( imath.Box2f( imath.V2f( 0, 1 ), imath.V2f( 1, 2 ) ) ),
				IECore.Box2iData( imath.Box2i( imath.V2i( -1, 10 ), imath.V2i( 11, 20 ) ) ),
				IECore.Box3fData( imath.Box3f( imath.V3f( 0, 1, 2 ), imath.V3f( 3, 4, 5 ) ) ),
				IECore.Box3iData( imath.Box3i( imath.V3i( 0, 1, 2 ), imath.V3i( 3, 4, 5 ) ) ),
				IECore.InternedStringVectorData( [ "a", "b" ] )
				]:
			if 'value' in dir( v ):
				expected = v.value
			else:
				expected = v
			self.assertEqual( expected, Gaffer.NameValuePlug( "test", v )["value"].getValue() )

	def testTransformPlug( self ) :

		p = Gaffer.NameValuePlug( "a", Gaffer.TransformPlug() )
		self.assertEqual( p["value"].matrix(), imath.M44f() )

	def testAdditionalChildrenRejected( self ) :

		m = Gaffer.NameValuePlug( "a", IECore.IntData( 10 ) )
		self.assertRaises( RuntimeError, m.addChild, Gaffer.IntPlug() )
		self.assertRaises( RuntimeError, m.addChild, Gaffer.StringPlug( "name" ) )
		self.assertRaises( RuntimeError, m.addChild, Gaffer.IntPlug( "name" ) )
		self.assertRaises( RuntimeError, m.addChild, Gaffer.IntPlug( "value" ) )

	def testDefaultValues( self ) :

		m = Gaffer.NameValuePlug( "a", IECore.IntData( 10 ) )
		self.assertTrue( m["value"].defaultValue(), 10 )
		self.assertTrue( m["value"].getValue(), 10 )
		self.assertTrue( m["name"].defaultValue(), "a" )
		self.assertTrue( m["name"].getValue(), "a" )

		m = Gaffer.NameValuePlug( "b", IECore.FloatData( 20 ) )
		self.assertTrue( m["value"].defaultValue(), 20 )
		self.assertTrue( m["value"].getValue(), 20 )
		self.assertTrue( m["name"].defaultValue(), "b" )
		self.assertTrue( m["name"].getValue(), "b" )

		m = Gaffer.NameValuePlug( "c", IECore.StringData( "abc" ) )
		self.assertTrue( m["value"].defaultValue(), "abc" )
		self.assertTrue( m["value"].getValue(), "abc" )
		self.assertTrue( m["name"].defaultValue(), "c" )
		self.assertTrue( m["name"].getValue(), "c" )

	def testNonValuePlugs( self ) :

		p1 = Gaffer.NameValuePlug( "name", Gaffer.Plug(), name = "p1", defaultEnabled = False )
		p2 = p1.createCounterpart( "p2", Gaffer.Plug.Direction.In )

		self.assertTrue( p1.settable() )
		self.assertTrue( p2.settable() )

		p2.setInput( p1 )
		self.assertEqual( p2["name"].getInput(), p1["name"] )
		self.assertEqual( p2["value"].getInput(), p1["value"] )
		self.assertTrue( p1.settable() )
		self.assertFalse( p2.settable() )

		p2.setInput( None )
		self.assertTrue( p2.settable() )

		self.assertTrue( p1.isSetToDefault() )
		p1["name"].setValue( "nonDefault" )
		self.assertFalse( p1.isSetToDefault() )
		p1.setToDefault()
		self.assertTrue( p1.isSetToDefault() )

		p1["name"].setValue( "nonDefault" )
		p1["enabled"].setValue( True )
		p2.setFrom( p1 )
		self.assertEqual( p2["name"].getValue(), p1["name"].getValue() )
		self.assertEqual( p2["enabled"].getValue(), p1["enabled"].getValue() )

		self.assertEqual( p1.hash(), p2.hash() )
		p2["enabled"].setValue( False )
		self.assertNotEqual( p1.hash(), p2.hash() )

	def testDynamicFlags( self ) :

		def assertFlags( script ) :

			self.assertEqual( script["n"]["user"]["p1"].getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			self.assertEqual( script["n"]["user"]["p1"]["name"].getFlags(), Gaffer.Plug.Flags.Default )
			self.assertEqual( script["n"]["user"]["p1"]["value"].getFlags(), Gaffer.Plug.Flags.Default )

			c = script["n"]["user"]["p1"].createCounterpart( "c", Gaffer.Plug.Direction.In )
			self.assertEqual( c.getFlags(), script["n"]["user"]["p1"].getFlags() )

			self.assertEqual( script["n"]["user"]["p2"].getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			self.assertEqual( script["n"]["user"]["p2"]["name"].getFlags(), Gaffer.Plug.Flags.Default )
			self.assertEqual( script["n"]["user"]["p2"]["value"].getFlags(), Gaffer.Plug.Flags.Default )
			self.assertEqual( script["n"]["user"]["p2"]["enabled"].getFlags(), Gaffer.Plug.Flags.Default )

			c = script["n"]["user"]["p2"].createCounterpart( "c", Gaffer.Plug.Direction.In )
			self.assertEqual( c.getFlags(), script["n"]["user"]["p2"].getFlags() )

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["p1"] = Gaffer.NameValuePlug( "name1", Gaffer.IntPlug( defaultValue = 1 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["p2"] = Gaffer.NameValuePlug( "name2", Gaffer.IntPlug( defaultValue = 1 ), defaultEnabled = False, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		assertFlags( s )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		assertFlags( s2 )

		s3 = Gaffer.ScriptNode()
		s3.execute( s2.serialise() )
		assertFlags( s3 )

if __name__ == "__main__":
	unittest.main()
