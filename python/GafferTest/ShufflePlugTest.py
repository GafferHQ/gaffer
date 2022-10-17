##########################################################################
#
#  Copyright (c) 2020, Image Engine Design Inc. All rights reserved.
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
import six

import IECore

import Gaffer
import GafferTest

class ShufflePlugTest( GafferTest.TestCase ) :

	def testBasics( self ) :

		p = Gaffer.ShufflePlug( "test" )
		self.assertEqual( p["source"].defaultValue(), "" )
		self.assertEqual( p["enabled"].defaultValue(), True )
		self.assertEqual( p["destination"].defaultValue(), "" )
		self.assertEqual( p["deleteSource"].defaultValue(), False )
		self.assertEqual( p["replaceDestination"].defaultValue(), True )

		p = Gaffer.ShufflePlug( source = "foo", destination = "bar", deleteSource = True, enabled = False )
		self.assertEqual( p["source"].defaultValue(), "" )
		self.assertEqual( p["source"].getValue(), "foo" )
		self.assertEqual( p["enabled"].defaultValue(), True )
		self.assertEqual( p["enabled"].getValue(), False )
		self.assertEqual( p["destination"].defaultValue(), "" )
		self.assertEqual( p["destination"].getValue(), "bar" )
		self.assertEqual( p["deleteSource"].defaultValue(), False )
		self.assertEqual( p["deleteSource"].getValue(), True )
		self.assertEqual( p["replaceDestination"].defaultValue(), True )

		p2 = Gaffer.ShufflesPlug()
		self.assertFalse( p.acceptsChild( Gaffer.Plug() ) )
		self.assertFalse( p.acceptsInput( Gaffer.Plug() ) )
		p2.addChild( p )

		p3 = p2.createCounterpart( "p3", Gaffer.Plug.Direction.In )
		self.assertIsInstance( p3, Gaffer.ShufflesPlug )
		self.assertEqual( p3.getName(), "p3" )
		self.assertEqual( p3.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p3.keys(), p2.keys() )

	def testShuffles( self ) :

		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "foo", destination = "bar" ) )
		p.addChild( Gaffer.ShufflePlug( source = "baz", destination = "bongo" ) )

		# create one destination
		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ) } )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"foo" : IECore.FloatData( 0.5 ),
				"bar" : IECore.FloatData( 0.5 ),
			} )
		)

		# create both destinations
		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ) } )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"foo" : IECore.FloatData( 0.5 ),
				"bar" : IECore.FloatData( 0.5 ),
				"baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
				"bongo" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
			} )
		)

		# delete one source
		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ) } )
		p[0]["deleteSource"].setValue( True )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"bar" : IECore.FloatData( 0.5 ),
				"baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
				"bongo" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
			} )
		)

		# disable one shuffle
		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ) } )
		p[0]["enabled"].setValue( False )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"foo" : IECore.FloatData( 0.5 ),
				"baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
				"bongo" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
			} )
		)

	def testReuseSource( self ) :

		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "foo", destination = "bar" ) )
		p.addChild( Gaffer.ShufflePlug( source = "foo", destination = "baz" ) )

		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ) } )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"foo" : IECore.FloatData( 0.5 ),
				"bar" : IECore.FloatData( 0.5 ),
				"baz" : IECore.FloatData( 0.5 ),
			} )
		)

		# delete one source
		p[0]["deleteSource"].setValue( True )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"bar" : IECore.FloatData( 0.5 ),
				"baz" : IECore.FloatData( 0.5 ),
			} )
		)

		# delete it twice
		p[0]["deleteSource"].setValue( True )
		p[1]["deleteSource"].setValue( True )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"bar" : IECore.FloatData( 0.5 ),
				"baz" : IECore.FloatData( 0.5 ),
			} )
		)

	def testReuseDestination( self ) :

		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "foo", destination = "baz" ) )
		p.addChild( Gaffer.ShufflePlug( source = "bar", destination = "baz" ) )

		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "bar" : IECore.FloatData( 1.0 ) } )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"foo" : IECore.FloatData( 0.5 ),
				"bar" : IECore.FloatData( 1.0 ),
				"baz" : IECore.FloatData( 1.0 ),
			} )
		)

		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "bar", destination = "baz" ) )
		p.addChild( Gaffer.ShufflePlug( source = "foo", destination = "baz" ) )

		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "bar" : IECore.FloatData( 1.0 ) } )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"foo" : IECore.FloatData( 0.5 ),
				"bar" : IECore.FloatData( 1.0 ),
				"baz" : IECore.FloatData( 0.5 ),
			} )
		)

	def testIgnoreIdentity( self ) :

		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "*", destination = "bar" ) )

		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "bar" : IECore.FloatData( 1.0 ) } )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"foo" : IECore.FloatData( 0.5 ),
				"bar" : IECore.FloatData( 0.5 ),
			} )
		)

		# replace destination false
		p[0]["replaceDestination"].setValue( False )
		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "bar" : IECore.FloatData( 1.0 ) } )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"foo" : IECore.FloatData( 0.5 ),
				"bar" : IECore.FloatData( 1.0 ),
			} )
		)

	def testNoReShuffle( self ) :

		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "foo", destination = "bar" ) )
		# wont do anything unless "bar" is in the original sources
		p.addChild( Gaffer.ShufflePlug( source = "bar", destination = "baz" ) )

		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ) } )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"foo" : IECore.FloatData( 0.5 ),
				"bar" : IECore.FloatData( 0.5 ),
			} )
		)

		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ) } )
		p[0]["deleteSource"].setValue( True )
		# wont affect the new "bar" because  its not in the original sources
		p[1]["deleteSource"].setValue( True )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"bar" : IECore.FloatData( 0.5 ),
			} )
		)

	def testWildcards( self ) :

		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "*", destination = "bar:${source}:baz", deleteSource = True ) )

		source = IECore.CompoundObject( {
			"foo" : IECore.FloatData( 0.5 ),
			"foo1" : IECore.FloatData( 1.0 ),
			"foo2" : IECore.StringData( "bongo" )
		} )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"bar:foo:baz" : IECore.FloatData( 0.5 ),
				"bar:foo1:baz" : IECore.FloatData( 1.0 ),
				"bar:foo2:baz" : IECore.StringData( "bongo" ),
			} )
		)

		dest2 = p.shuffle( dest )
		self.assertEqual(
			dest2,
			IECore.CompoundObject( {
				"bar:bar:foo:baz:baz" : IECore.FloatData( 0.5 ),
				"bar:bar:foo1:baz:baz" : IECore.FloatData( 1.0 ),
				"bar:bar:foo2:baz:baz" : IECore.StringData( "bongo" ),
			} )
		)

		# without the ${source} variable in the destination, our "*" match causes collisions
		p[0]["destination"].setValue( "allValuesCollide" )
		six.assertRaisesRegex( self, RuntimeError, '.*cannot write from multiple sources to destination.*', p.shuffle, source )

		# other substitution variables can also cause collisions
		p[0]["destination"].setValue( "foo#" )
		six.assertRaisesRegex( self, RuntimeError, '.*cannot write from multiple sources to destination.*', p.shuffle, source )

	def testDrivenDestination( self ) :

		script = Gaffer.ScriptNode()
		script["n"] = Gaffer.Node()
		script["n"]["p"] = Gaffer.ShufflesPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		script["n"]["p"].addChild( Gaffer.ShufflePlug( name = "s", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		script["n"]["p"]["s"]["source"].setValue( "foo" )
		script["expr"] = Gaffer.Expression()
		script["expr"].setExpression( 'parent["n"]["p"]["s"]["destination"] = context["source"] + ":bar"' )

		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ) } )
		dest = script["n"]["p"].shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"foo" : IECore.FloatData( 0.5 ),
				"foo:bar" : IECore.FloatData( 0.5 ),
				"baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
			} )
		)

		# source with wildcard
		script["n"]["p"]["s"]["source"].setValue( "*" )
		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ) } )
		dest = script["n"]["p"].shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"foo" : IECore.FloatData( 0.5 ),
				"foo:bar" : IECore.FloatData( 0.5 ),
				"baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
				"baz:bar" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
			} )
		)

		# two attrs trying to write to the same target
		script["expr"].setExpression( 'parent["n"]["p"]["s"]["destination"] = "bar:" + context["notSource"]' )
		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ) } )
		with Gaffer.Context() as c :
			c["notSource"] = "bongo"
			six.assertRaisesRegex( self, RuntimeError, '.*cannot write from multiple sources to destination.*', script["n"]["p"].shuffle, source )

	def testDrivenSource( self ) :

		script = Gaffer.ScriptNode()
		script["n"] = Gaffer.Node()
		script["n"]["p"] = Gaffer.ShufflesPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		script["n"]["p"].addChild( Gaffer.ShufflePlug( name = "s", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		script["srcExpr"] = Gaffer.Expression()
		script["srcExpr"].setExpression( 'parent["n"]["p"]["s"]["source"] = context["source"]' )
		script["dstExpr"] = Gaffer.Expression()
		script["dstExpr"].setExpression( 'parent["n"]["p"]["s"]["destination"] = context["source"] + ":bar"' )

		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ) } )
		six.assertRaisesRegex( self, RuntimeError, '.*Context has no variable named \"source\".*', script["n"]["p"].shuffle, source )

		# source expression using predefined source variable
		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ) } )
		with Gaffer.Context() as c :
			c["source"] = "baz"
			dest = script["n"]["p"].shuffle( source )
			self.assertEqual(
				dest,
				IECore.CompoundObject( {
					"foo" : IECore.FloatData( 0.5 ),
					"baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
					"baz:bar" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
				} )
			)

	def testCantDeleteDestination( self ) :

		# the original bar is gone, but the new bar has value of foo
		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "bar", destination = "baz", deleteSource = True ) )
		p.addChild( Gaffer.ShufflePlug( source = "foo", destination = "bar" ) )
		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "bar" : IECore.FloatData( 1.0 ) } )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"foo" : IECore.FloatData( 0.5 ),
				"bar" : IECore.FloatData( 0.5 ),
				"baz" : IECore.FloatData( 1.0 ),
			} )
		)

		# even if delete comes last, the original bar is gone, but the new bar has value of foo
		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "foo", destination = "bar" ) )
		p.addChild( Gaffer.ShufflePlug( source = "bar", destination = "baz", deleteSource = True ) )
		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "bar" : IECore.FloatData( 1.0 ) } )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundObject( {
				"foo" : IECore.FloatData( 0.5 ),
				"bar" : IECore.FloatData( 0.5 ),
				"baz" : IECore.FloatData( 1.0 ),
			} )
		)

	def testAlternateDataTypes( self ) :

		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "foo", destination = "bar" ) )
		p.addChild( Gaffer.ShufflePlug( source = "baz", destination = "bongo" ) )

		source = IECore.CompoundData( { "foo" : 0.5, "baz" : imath.Color3f( 1, 2, 3 ) } )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundData( {
				"foo" : IECore.FloatData( 0.5 ),
				"bar" : IECore.FloatData( 0.5 ),
				"baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
				"bongo" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
			} )
		)

	def testReplaceDestination( self ) :

		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "foo", destination = "bar" ) )
		p.addChild( Gaffer.ShufflePlug( source = "baz", destination = "bongo" ) )
		p[0]["replaceDestination"].setValue( False )

		source = IECore.CompoundData( { "foo" : 0.5, "bar" : 1.5, "baz" : imath.Color3f( 1, 2, 3 ), "bongo" : imath.Color3f( 4, 5, 6 ) } )
		dest = p.shuffle( source )
		self.assertEqual(
			dest,
			IECore.CompoundData( {
				"foo" : IECore.FloatData( 0.5 ),
				"bar" : IECore.FloatData( 1.5 ),
				"baz" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
				"bongo" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
			} )
		)

	def testReplaceDestinationNoReuseDestination( self ) :

		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "*", destination = "bar" ) )

		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "bar" : IECore.FloatData( 1.0 ), "baz" : IECore.FloatData( 1.5 ) } )
		six.assertRaisesRegex( self, RuntimeError, '.*cannot write from multiple sources to destination.*', p.shuffle, source )

		# clashing destinations are detected regardless of replace destination
		p[0]["replaceDestination"].setValue( False )
		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "bar" : IECore.FloatData( 1.0 ), "baz" : IECore.FloatData( 1.5 ) } )
		six.assertRaisesRegex( self, RuntimeError, '.*cannot write from multiple sources to destination.*', p.shuffle, source )

	def testIdentityNoDeleteSource( self ) :

		# simple
		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "foo", destination = "foo", deleteSource = True ) )

		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "bar" : IECore.FloatData( 1.0 ) } )
		dest = p.shuffle( source )
		self.assertEqual( dest, source )

		# source wildcard
		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "*", destination = "foo", deleteSource = True ) )

		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ) } )
		dest = p.shuffle( source )
		self.assertEqual( dest, source )

		# source wildcard destination substitution
		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "*", destination = "${source}", deleteSource = True ) )

		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "bar" : IECore.FloatData( 1.0 ) } )
		dest = p.shuffle( source )
		self.assertEqual( dest, source )

		# no source wildcard destination substitution
		p = Gaffer.ShufflesPlug()
		p.addChild( Gaffer.ShufflePlug( source = "foo", destination = "${source}", deleteSource = True ) )

		source = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "bar" : IECore.FloatData( 1.0 ) } )
		dest = p.shuffle( source )
		self.assertEqual( dest, source )

if __name__ == "__main__":
	unittest.main()
