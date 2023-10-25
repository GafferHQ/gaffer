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
import math
import imath
import re

import IECore

import Gaffer
import GafferDispatch
import GafferDispatchTest
import GafferOSL
import GafferOSLTest

class OSLExpressionEngineTest( GafferOSLTest.OSLTestCase ) :

	def testBoolPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.BoolPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["o"] = Gaffer.BoolPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.o = !parent.n.user.i;", "OSL" )

		s["n"]["user"]["i"].setValue( True )
		self.assertEqual( s["n"]["user"]["o"].getValue(), False )

		s["n"]["user"]["i"].setValue( False )
		self.assertEqual( s["n"]["user"]["o"].getValue(), True )

	def testFloatPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["o"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.o = parent.n.user.i + 1;", "OSL" )

		s["n"]["user"]["i"].setValue( 1 )
		self.assertEqual( s["n"]["user"]["o"].getValue(), 2 )

	def testIntPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["o"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.o = parent.n.user.i + 1;", "OSL" )

		s["n"]["user"]["i"].setValue( 1 )
		self.assertEqual( s["n"]["user"]["o"].getValue(), 2 )

	def testColorPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["o"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.o = parent.n.user.i * 2;", "OSL" )

		s["n"]["user"]["i"].setValue( imath.Color3f( 1, 2, 3 ) )
		self.assertEqual( s["n"]["user"]["o"].getValue(), imath.Color3f( 2, 4, 6 ) )

	def testV3fPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["o"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.o = parent.n.user.i * 2;", "OSL" )

		s["n"]["user"]["i"].setValue( imath.V3f( 1, 2, 3 ) )
		self.assertEqual( s["n"]["user"]["o"].getValue(), imath.V3f( 2, 4, 6 ) )

	def testM44fPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.M44fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["o"] = Gaffer.M44fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.o = parent.n.user.i * 2;", "OSL" )

		s["n"]["user"]["i"].setValue( imath.M44f( *range( 16 ) ) )
		self.assertEqual( s["n"]["user"]["o"].getValue(), imath.M44f( *range( 0, 32, 2 ) ) )

	def testStringPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["o"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.o = parent.n.user.i;", "OSL" )

		s["n"]["user"]["i"].setValue( "string" )
		self.assertEqual( s["n"]["user"]["o"].getValue(), "string" )

	def testUnsupportedPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["o"] = Gaffer.ObjectPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, defaultValue = IECore.NullObject.defaultNullObject() )

		s["e"] = Gaffer.Expression()
		self.assertRaisesRegex(
			RuntimeError, "Unsupported plug type \"Gaffer::ObjectPlug\"",
			s["e"].setExpression,
			"parent.n.user.o = 1",
			"OSL"
		)

	def testContextFrame( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["o"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.o = context( \"frame\" );", "OSL" )

		for i in range( 0, 10 ) :
			s.context().setFrame( i )
			with s.context() :
				self.assertEqual( s["n"]["user"]["o"].getValue(), i )

	def testContextTypes( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["c"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["v"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["s"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["b"] = Gaffer.BoolPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			inspect.cleandoc(
				"""
				parent.n.user.f = context( "f", 1 );
				parent.n.user.i = context( "i", 1 );
				parent.n.user.c = context( "c", color( 1, 2, 3 ) );
				parent.n.user.v = context( "v", vector( 0, 1, 2 ) );
				parent.n.user.s = context( "s", "default" );
				parent.n.user.b = context( "b", 0 );
				"""
			),
			"OSL"
		)

		with Gaffer.Context() as c :

			self.assertEqual( s["n"]["user"]["f"].getValue(), 1 )
			self.assertEqual( s["n"]["user"]["i"].getValue(), 1 )
			self.assertEqual( s["n"]["user"]["c"].getValue(), imath.Color3f( 1, 2, 3 ) )
			self.assertEqual( s["n"]["user"]["v"].getValue(), imath.V3f( 0, 1, 2 ) )
			self.assertEqual( s["n"]["user"]["s"].getValue(), "default" )
			self.assertEqual( s["n"]["user"]["b"].getValue(), False )

			c["f"] = 10
			c["i"] = 11
			c["c"] = imath.Color3f( 4, 5, 6 )
			c["v"] = imath.V3f( 1, 2, 3 )
			c["s"] = "non-default"
			c["b"] = IECore.BoolData( True )

			self.assertEqual( s["n"]["user"]["f"].getValue(), 10 )
			self.assertEqual( s["n"]["user"]["i"].getValue(), 11 )
			self.assertEqual( s["n"]["user"]["c"].getValue(), imath.Color3f( 4, 5, 6 ) )
			self.assertEqual( s["n"]["user"]["v"].getValue(), imath.V3f( 1, 2, 3 ) )
			self.assertEqual( s["n"]["user"]["s"].getValue(), "non-default" )
			self.assertEqual( s["n"]["user"]["b"].getValue(), True )

	def testContextVectorTypes( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		for i in range( 0, 5 ) :
			s["n"]["user"]["f" + str( i )] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			s["n"]["user"]["i" + str( i )] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			s["n"]["user"]["c" + str( i )] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			s["n"]["user"]["v" + str( i )] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			s["n"]["user"]["s" + str( i )] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			s["n"]["user"]["b" + str( i )] = Gaffer.BoolPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			inspect.cleandoc(
				"""
				parent.n.user.f0 = contextElement( "f", 0,  1 );
				parent.n.user.i0 = contextElement( "i", 0, 1 );
				parent.n.user.c0 = contextElement( "c", 0, color( 1, 2, 3 ) );
				parent.n.user.v0 = contextElement( "v", 0 );
				parent.n.user.s0 = contextElement( "s", 0, "default0" );

				parent.n.user.f1 = contextElement( "f", 1, 2 );
				parent.n.user.i1 = contextElement( "i", 1, 2 );
				parent.n.user.c1 = contextElement( "c", 1, color( 4, 5, 6 ) );
				parent.n.user.v1 = contextElement( "v", 1 );
				parent.n.user.s1 = contextElement( "s", 1, "default1" );

				parent.n.user.f2 = contextElement( "f", 2,  3 );
				parent.n.user.i2 = contextElement( "i", 2, 3 );
				parent.n.user.c2 = contextElement( "c", 2, color( 7, 8, 9 ) );
				parent.n.user.v2 = contextElement( "v", 2 );
				parent.n.user.s2 = contextElement( "s", 2, "default2" );

				parent.n.user.f3 = contextElement( "f", -1 );
				parent.n.user.i3 = contextElement( "i", -1 );
				parent.n.user.c3 = contextElement( "c", -1 );
				parent.n.user.v3 = contextElement( "v", -1 );
				parent.n.user.s3 = contextElement( "s", -1 );

				parent.n.user.f4 = contextElement( "f", -3 );
				parent.n.user.i4 = contextElement( "i", -3 );
				parent.n.user.c4 = contextElement( "c", -3 );
				parent.n.user.v4 = contextElement( "v", -3 );
				parent.n.user.s4 = contextElement( "s", -3 );
				"""
			),
			"OSL"
		)

		with Gaffer.Context() as c :

			self.assertEqual( s["n"]["user"]["f0"].getValue(), 1 )
			self.assertEqual( s["n"]["user"]["i0"].getValue(), 1 )
			self.assertEqual( s["n"]["user"]["c0"].getValue(), imath.Color3f( 1, 2, 3 ) )
			self.assertEqual( s["n"]["user"]["v0"].getValue(), imath.V3f( 0 ) )
			self.assertEqual( s["n"]["user"]["s0"].getValue(), "default0" )

			self.assertEqual( s["n"]["user"]["f1"].getValue(), 2 )
			self.assertEqual( s["n"]["user"]["i1"].getValue(), 2 )
			self.assertEqual( s["n"]["user"]["c1"].getValue(), imath.Color3f( 4, 5, 6 ) )
			self.assertEqual( s["n"]["user"]["v1"].getValue(), imath.V3f( 0 ) )
			self.assertEqual( s["n"]["user"]["s1"].getValue(), "default1" )

			self.assertEqual( s["n"]["user"]["f2"].getValue(), 3 )
			self.assertEqual( s["n"]["user"]["i2"].getValue(), 3 )
			self.assertEqual( s["n"]["user"]["c2"].getValue(), imath.Color3f( 7, 8, 9 ) )
			self.assertEqual( s["n"]["user"]["v2"].getValue(), imath.V3f( 0 ) )
			self.assertEqual( s["n"]["user"]["s2"].getValue(), "default2" )

			self.assertEqual( s["n"]["user"]["f3"].getValue(), 0 )
			self.assertEqual( s["n"]["user"]["i3"].getValue(), 0 )
			self.assertEqual( s["n"]["user"]["c3"].getValue(), imath.Color3f( 0 ) )
			self.assertEqual( s["n"]["user"]["v3"].getValue(), imath.V3f( 0 ) )
			self.assertEqual( s["n"]["user"]["s3"].getValue(), "" )

			self.assertEqual( s["n"]["user"]["f4"].getValue(), 0 )
			self.assertEqual( s["n"]["user"]["i4"].getValue(), 0 )
			self.assertEqual( s["n"]["user"]["c4"].getValue(), imath.Color3f( 0 ) )
			self.assertEqual( s["n"]["user"]["v4"].getValue(), imath.V3f( 0 ) )
			self.assertEqual( s["n"]["user"]["s4"].getValue(), "" )

			c["f"] = IECore.FloatVectorData( [ 10, 11 ] )
			c["i"] = IECore.IntVectorData( [ 11, 12 ] )
			c["c"] = IECore.Color3fVectorData( [ imath.Color3f( 10, 11, 12 ), imath.Color3f( 13, 14, 15 ) ] )
			c["v"] = IECore.V3fVectorData( [ imath.V3f( 9, 10, 11 ), imath.V3f( 12, 13, 14 ) ] )
			c["s"] = IECore.StringVectorData( [ "non-default0", "non-default1" ] )

			self.assertEqual( s["n"]["user"]["f0"].getValue(), 10 )
			self.assertEqual( s["n"]["user"]["i0"].getValue(), 11 )
			self.assertEqual( s["n"]["user"]["c0"].getValue(), imath.Color3f( 10, 11, 12 ) )
			self.assertEqual( s["n"]["user"]["v0"].getValue(), imath.V3f( 9, 10, 11 ) )
			self.assertEqual( s["n"]["user"]["s0"].getValue(), "non-default0" )

			self.assertEqual( s["n"]["user"]["f1"].getValue(), 11 )
			self.assertEqual( s["n"]["user"]["i1"].getValue(), 12 )
			self.assertEqual( s["n"]["user"]["c1"].getValue(), imath.Color3f( 13, 14, 15 ) )
			self.assertEqual( s["n"]["user"]["v1"].getValue(), imath.V3f( 12, 13, 14 ) )
			self.assertEqual( s["n"]["user"]["s1"].getValue(), "non-default1" )

			self.assertEqual( s["n"]["user"]["f2"].getValue(), 3 )
			self.assertEqual( s["n"]["user"]["i2"].getValue(), 3 )
			self.assertEqual( s["n"]["user"]["c2"].getValue(), imath.Color3f( 7, 8, 9 ) )
			self.assertEqual( s["n"]["user"]["v2"].getValue(), imath.V3f( 0 ) )
			self.assertEqual( s["n"]["user"]["s2"].getValue(), "default2" )

			self.assertEqual( s["n"]["user"]["f3"].getValue(), 11 )
			self.assertEqual( s["n"]["user"]["i3"].getValue(), 12 )
			self.assertEqual( s["n"]["user"]["c3"].getValue(), imath.Color3f( 13, 14, 15 ) )
			self.assertEqual( s["n"]["user"]["v3"].getValue(), imath.V3f( 12, 13, 14 ) )
			self.assertEqual( s["n"]["user"]["s3"].getValue(), "non-default1" )

			self.assertEqual( s["n"]["user"]["f4"].getValue(), 0 )
			self.assertEqual( s["n"]["user"]["i4"].getValue(), 0 )
			self.assertEqual( s["n"]["user"]["c4"].getValue(), imath.Color3f( 0 ) )
			self.assertEqual( s["n"]["user"]["v4"].getValue(), imath.V3f( 0 ) )
			self.assertEqual( s["n"]["user"]["s4"].getValue(), "" )

	def testScenePathContext( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["p1"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["p2"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["p3"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["p4"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			inspect.cleandoc(
				"""
				parent.n.user.p1 = contextElement( "scene:path", 0, "noPath1" );
				parent.n.user.p2 = contextElement( "scene:path", 1, "noPath2" );
				parent.n.user.p3 = contextElement( "scene:path", 2 );
				parent.n.user.p4 = contextElement( "scene:path", 3 );
				"""
			),
			"OSL"
		)

		with Gaffer.Context() as c :

			self.assertEqual( s["n"]["user"]["p1"].getValue(), "noPath1" )
			self.assertEqual( s["n"]["user"]["p2"].getValue(), "noPath2" )
			self.assertEqual( s["n"]["user"]["p3"].getValue(), "" )
			self.assertEqual( s["n"]["user"]["p4"].getValue(), "" )

			c["scene:path"] = IECore.InternedStringVectorData( [ "yellow", "brick", "road" ] )

			self.assertEqual( s["n"]["user"]["p1"].getValue(), "yellow" )
			self.assertEqual( s["n"]["user"]["p2"].getValue(), "brick" )
			self.assertEqual( s["n"]["user"]["p3"].getValue(), "road" )
			self.assertEqual( s["n"]["user"]["p4"].getValue(), "" )

	def testDefaultExpression( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["c"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["v"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["s"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["n"]["user"]["f"].setValue( 10 )
		s["n"]["user"]["i"].setValue( 10 )
		s["n"]["user"]["c"].setValue( imath.Color3f( 1, 2, 3 ) )
		s["n"]["user"]["v"].setValue( imath.V3f( 1, 2, 3 ) )
		s["n"]["user"]["s"].setValue( "s" )

		defaultExpressions = [ Gaffer.Expression.defaultExpression( p, "OSL" ) for p in s["n"]["user"].children() ]
		expectedValues = [ p.getValue() for p in s["n"]["user"].children() ]

		for p in s["n"]["user"].children() :
			p.setToDefault()

		s["e"] = Gaffer.Expression()
		for p, e, v in zip( s["n"]["user"].children(), defaultExpressions, expectedValues ) :
			s["e"].setExpression( e, "OSL" )
			self.assertEqual( p.getValue(), v )

	def testEmptyExpression( self ) :

		s = Gaffer.ScriptNode()
		s["e"] = Gaffer.Expression()

		s["e"].setExpression( "", "OSL" )
		self.assertEqual( s["e"].getExpression(), ( "", "OSL" ) )

	def testRevertToPreviousExpression( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["o"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.o = parent.n.user.i + 1;", "OSL" )
		self.assertEqual( s["n"]["user"]["o"].getValue(), 1 )

		s["e"].setExpression( "parent.n.user.o = parent.n.user.i + 2;", "OSL" )
		self.assertEqual( s["n"]["user"]["o"].getValue(), 2 )

		s["e"].setExpression( "parent.n.user.o = parent.n.user.i + 1;", "OSL" )
		self.assertEqual( s["n"]["user"]["o"].getValue(), 1 )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["o"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.o = parent.n.user.i + 1;", "OSL" )

		s["n"]["user"]["i"].setValue( 1 )
		self.assertEqual( s["n"]["user"]["o"].getValue(), 2 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"]["user"]["o"].getValue(), 2 )
		s2["n"]["user"]["i"].setValue( 2 )
		self.assertEqual( s2["n"]["user"]["o"].getValue(), 3 )

	def testIdentifier( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["o"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["s"] = Gaffer.SplineffPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "", "OSL" )

		# We should be able to set up an expression via script without needing to know
		# the convention for addressing plugs.
		s["e"].setExpression(
			"%s = %s + 1;" % ( s["e"].identifier( s["n"]["user"]["o"] ), s["e"].identifier( s["n"]["user"]["i"] ) ),
			"OSL"
		)
		self.assertEqual( s["n"]["user"]["o"].getValue(), 1 )

		# Plug type isn't supported, so should return empty string.
		self.assertEqual( s["e"].identifier( s["n"]["user"]["s"] ), "" )

	def testRenamePlugs( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["o"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.o = parent.n.user.i + 1;", "OSL" )

		self.assertEqual( s["n"]["user"]["o"].getValue(), 1 )

		s["n"]["user"]["i"].setName( "I" )
		s["n"]["user"]["o"].setName( "O" )

		self.assertEqual( s["n"]["user"]["O"].getValue(), 1 )
		self.assertEqual( s["e"].getExpression(), ( "parent.n.user.O = parent.n.user.I + 1;", "OSL" ) )

	def testInvalidExpression( self ) :

		s = Gaffer.ScriptNode()

		s["e"] = Gaffer.Expression()
		self.assertRaisesRegex( RuntimeError, ".*does not exist.*", s["e"].setExpression, 'parent.notANode.notAPlug = 2;', "OSL" )

	def testNoSemiColon( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.f = 10", "OSL" )

		self.assertEqual( s["n"]["user"]["f"].getValue(), 10 )

	def testStdOSL( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.f = M_PI", "OSL" )

		self.assertAlmostEqual( s["n"]["user"]["f"].getValue(), math.pi, 4 )

	def testBackgroundDispatch( self ) :

		script = Gaffer.ScriptNode()

		script["writer"] = GafferDispatchTest.TextWriter()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( f'parent.writer.fileName = "{ ( self.temporaryDirectory() / "test.txt" ).as_posix() }"', "OSL" )

		dispatcher = GafferDispatch.LocalDispatcher( jobPool = GafferDispatch.LocalDispatcher.JobPool() )
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() / "jobs" )
		dispatcher["executeInBackground"].setValue( True )
		dispatcher.dispatch( [ script["writer"] ] )

		dispatcher.jobPool().waitForAll()
		self.assertEqual( len( dispatcher.jobPool().failedJobs() ), 0 )

		self.assertTrue( ( self.temporaryDirectory() / "test.txt" ).exists() )

	def testTimeGlobalVariable( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.f = time", "OSL" )

		with Gaffer.Context() as c :
			c.setTime( 1 )
			self.assertEqual( s["n"]["user"]["f"].getValue(), 1 )
			c.setTime( 2 )
			self.assertEqual( s["n"]["user"]["f"].getValue(), 2 )

	def testIgnoresTimeWhenTimeNotReferenced( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.f = 1", "OSL" )

		with Gaffer.Context() as c :
			c.setTime( 1 )
			h1 = s["n"]["user"]["f"].hash()
			c.setTime( 2 )
			h2 = s["n"]["user"]["f"].hash()

		self.assertEqual( h1, h2 )

		with Gaffer.Context() as c :
			del c["frame"]
			self.assertEqual( s["n"]["user"]["f"].getValue(), 1 )

	def testDeleteOutputPlug( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = Gaffer.Node()
		s["n1"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["n2"] = Gaffer.Node()
		s["n2"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			inspect.cleandoc(
				"""
				parent.n1.user.f = 1;
				parent.n2.user.f = 2;
				"""
			),
			"OSL"
		)

		self.assertEqual( s["n2"]["user"]["f"].getValue(), 2 )
		del s["n1"]
		self.assertEqual( s["n2"]["user"]["f"].getValue(), 2 )

		s["e"].setExpression(
			"// I should be able to edit a broken expression\n" +
			s["e"].getExpression()[0],
			"OSL"
		)
		self.assertTrue( "_disconnectedFloat = 1" in s["e"].getExpression()[0] )

		self.assertEqual( s["n2"]["user"]["f"].getValue(), 2 )

	def testDeleteInputPlug( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = Gaffer.Node()
		s["n1"]["user"]["f1"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n1"]["user"]["f2"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["n2"] = Gaffer.Node()
		s["n2"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			inspect.cleandoc(
				"""
				parent.n2.user.f = parent.n1.user.f1 + parent.n1.user.f2;
				"""
			),
			"OSL"
		)

		s["n1"]["user"]["f1"].setValue( 2 )
		s["n1"]["user"]["f2"].setValue( 4 )
		self.assertEqual( s["n2"]["user"]["f"].getValue(), 6 )

		del s["n1"]["user"]["f1"]
		self.assertEqual( s["n2"]["user"]["f"].getValue(), 4 )

		s["e"].setExpression(
			"// I should be able to edit a broken expression\n" +
			s["e"].getExpression()[0],
			"OSL"
		)

		self.assertEqual( s["n2"]["user"]["f"].getValue(), 4 )

	def testMoreThanTenPlugs( self ) :

		s = Gaffer.ScriptNode()

		expression = ""
		for i in range( 0, 20 ) :

			aName = "A%d" % i
			bName = "B%d" % i

			s[aName] = Gaffer.Node()
			s[bName] = Gaffer.Node()

			s[aName]["user"]["p"] = Gaffer.IntPlug( defaultValue = i, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			s[bName]["user"]["p"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

			expression += "parent.%s.user.p = parent.%s.user.p;\n" % ( bName, aName )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( expression, "OSL" )

		self.assertEqual( s["e"].getExpression(), ( expression, "OSL" ) )

		for i in range( 0, 20 ) :
			self.assertEqual( s["B%d"%i]["user"]["p"].getValue(), i )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["e"].getExpression(), ( expression, "OSL" ) )

		for i in range( 0, 20 ) :
			self.assertEqual( s2["B%d"%i]["user"]["p"].getValue(), i )

	def testPlugNamesWithCommonPrefixes( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["ab"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["abc"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["abcd"] = Gaffer.V2iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		expression = inspect.cleandoc(
			"""
			parent.n.user.ab = 1;
			parent.n.user.a = 2;
			parent.n.user.abc = 3;
			parent.n.user.abcd.x = 4;
			"""
		)

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( expression, "OSL" )

		self.assertEqual( s["e"].getExpression(), ( expression, "OSL" ) )

		self.assertEqual( s["n"]["user"]["ab"].getValue(), 1 )
		self.assertEqual( s["n"]["user"]["a"].getValue(), 2 )
		self.assertEqual( s["n"]["user"]["abc"].getValue(), 3 )
		self.assertEqual( s["n"]["user"]["abcd"]["x"].getValue(), 4 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["e"].getExpression(), ( expression, "OSL" ) )

		self.assertEqual( s2["n"]["user"]["ab"].getValue(), 1 )
		self.assertEqual( s2["n"]["user"]["a"].getValue(), 2 )
		self.assertEqual( s2["n"]["user"]["abc"].getValue(), 3 )
		self.assertEqual( s2["n"]["user"]["abcd"]["x"].getValue(), 4 )

	def testStringComparison( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["bool"] = Gaffer.BoolPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["string"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( """parent.n.user.bool = "yes" == parent.n.user.string;""", "OSL" )

		self.assertFalse( s["n"]["user"]["bool"].getValue() )

		s["n"]["user"]["string"].setValue( "yes" )
		self.assertTrue( s["n"]["user"]["bool"].getValue() )

	def testComparisonIsNotAssignment( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["o"] = Gaffer.BoolPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( """parent.n.user.o = parent.n.user.i == 2;""", "OSL" )

		self.assertTrue( s["n"]["user"]["i"].getInput() is None )
		self.assertFalse( s["n"]["user"]["o"].getValue() )

		s["n"]["user"]["i"].setValue( 2 )
		self.assertTrue( s["n"]["user"]["o"].getValue() )

	def testStringContextVariableComparison( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		expression = inspect.cleandoc(
			"""
			string var = context( "str" );
			parent.n.user.i = var == "abc";
			"""
		)

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( expression, "OSL" )

		with Gaffer.Context() as c :

			c["str"] = "xyz"
			self.assertEqual( s["n"]["user"]["i"].getValue(), 0 )

			c["str"] = "abc"
			self.assertEqual( s["n"]["user"]["i"].getValue(), 1 )

	def testDuplicateDeserialise( self ) :

		s = Gaffer.ScriptNode()

		s["source"] = Gaffer.Node()
		s["source"]["p"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["source"]["p"].setValue( imath.V3f( 0.1, 0.2, 0.3 ) )

		s["dest"] = Gaffer.Node()
		s["dest"]["p"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			"parent.dest.p.x = parent.source.p.x + 1;\n" +
			"parent.dest.p.y = parent.source.p.y + 2;\n" +
			"parent.dest.p.z = parent.source.p.z + 3;\n",
			"OSL",
		)

		ss = s.serialise()

		s.execute( ss )
		s.execute( ss )

		self.assertEqual( s["dest"]["p"].getValue(), imath.V3f( 1.1, 2.2, 3.3 ) )
		self.assertEqual( s["dest1"]["p"].getValue(), imath.V3f( 1.1, 2.2, 3.3 ) )
		self.assertEqual( s["dest2"]["p"].getValue(), imath.V3f( 1.1, 2.2, 3.3 ) )

		# Working well so far, but we've had a bug that could be hidden by the caching.  Lets
		# try evaluating the plugs again, but flushing the cache each time

		Gaffer.ValuePlug.clearCache()
		self.assertEqual( s["dest"]["p"].getValue(), imath.V3f( 1.1, 2.2, 3.3 ) )
		self.assertEqual( s["dest1"]["p"].getValue(), imath.V3f( 1.1, 2.2, 3.3 ) )
		self.assertEqual( s["dest2"]["p"].getValue(), imath.V3f( 1.1, 2.2, 3.3 ) )

	def testIndependentOfOrderOfPlugNames( self ) :

		# We shouldn't depend on p0 being the first plug mentioned in the expression - as long as p0 is assigned
		# correctly, the expression should still work

		# Set up an expression with lots of plugs
		s = Gaffer.ScriptNode()

		exprLines = []
		for i in range( 10 ):
			s["source%i"%i] = Gaffer.Node()
			s["source%i"%i]["p"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			s["source%i"%i]["p"].setValue( imath.V3f( 0.1, 0.2, 0.3 ) + 0.3 * i )
			s["dest%i"%i] = Gaffer.Node()
			s["dest%i"%i]["p"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			for a in "xyz":
				exprLines.append(  "parent.dest%i.p.%s = parent.source%i.p.%s + 10 * %i;" % ( i, a, i, a, i ) )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "\n".join( exprLines ), "OSL" )

		for i in range( 10 ):
			self.assertAlmostEqual( s["dest%i"%i]["p"].getValue().x, 0.1 + 0.3 * i + 10 * i, places = 5 )
			self.assertAlmostEqual( s["dest%i"%i]["p"].getValue().y, 0.2 + 0.3 * i + 10 * i, places = 5 )
			self.assertAlmostEqual( s["dest%i"%i]["p"].getValue().z, 0.3 + 0.3 * i + 10 * i, places = 5 )

		# Now serialize it, and reverse the order of all the lines in the expression before deserializing it
		ss = s.serialise()

		ssLines = ss.split( "\n" )
		ssLinesEdited = []
		for l in ssLines:
			m = re.match( r"^__children\[\"e\"\]\[\"__expression\"\].setValue\( '(.*)' \)$", l )
			if not m:
				ssLinesEdited.append( l )
			else:
				lines = m.groups()[0].split( "\\n" );
				ssLinesEdited.append( "__children[\"e\"][\"__expression\"].setValue( '%s' )" % "\\n".join( lines[::-1] ) )

		del s
		s = Gaffer.ScriptNode()
		s.execute( "\n".join( ssLinesEdited) )

		for i in range( 10 ):
			self.assertAlmostEqual( s["dest%i"%i]["p"].getValue().x, 0.1 + 0.3 * i + 10 * i, places = 5 )
			self.assertAlmostEqual( s["dest%i"%i]["p"].getValue().y, 0.2 + 0.3 * i + 10 * i, places = 5 )
			self.assertAlmostEqual( s["dest%i"%i]["p"].getValue().z, 0.3 + 0.3 * i + 10 * i, places = 5 )

	def testException( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["g"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["ePython"] = Gaffer.Expression()
		s["ePython"].setExpression( "raise IECore.Exception( 'test string' ); parent['n']['user']['g'] = 4.0" )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.f = parent.n.user.g", "OSL" )

		self.assertRaisesRegex(
			Gaffer.ProcessException, "ePython.__execute : test string",
			s["n"]["user"]["f"].getValue
		)

if __name__ == "__main__":
	unittest.main()
