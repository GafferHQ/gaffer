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
import os

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

		s["n"]["user"]["i"].setValue( IECore.Color3f( 1, 2, 3 ) )
		self.assertEqual( s["n"]["user"]["o"].getValue(), IECore.Color3f( 2, 4, 6 ) )

	def testV3fPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["o"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent.n.user.o = parent.n.user.i * 2;", "OSL" )

		s["n"]["user"]["i"].setValue( IECore.V3f( 1, 2, 3 ) )
		self.assertEqual( s["n"]["user"]["o"].getValue(), IECore.V3f( 2, 4, 6 ) )

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
		self.assertRaisesRegexp(
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

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			inspect.cleandoc(
				"""
				parent.n.user.f = context( "f", 1 );
				parent.n.user.i = context( "i", 1 );
				parent.n.user.c = context( "c", color( 1, 2, 3 ) );
				parent.n.user.v = context( "v", vector( 0, 1, 2 ) );
				parent.n.user.s = context( "s", "default" );
				"""
			),
			"OSL"
		)

		with Gaffer.Context() as c :

			self.assertEqual( s["n"]["user"]["f"].getValue(), 1 )
			self.assertEqual( s["n"]["user"]["i"].getValue(), 1 )
			self.assertEqual( s["n"]["user"]["c"].getValue(), IECore.Color3f( 1, 2, 3 ) )
			self.assertEqual( s["n"]["user"]["v"].getValue(), IECore.V3f( 0, 1, 2 ) )
			self.assertEqual( s["n"]["user"]["s"].getValue(), "default" )

			c["f"] = 10
			c["i"] = 11
			c["c"] = IECore.Color3fData( IECore.Color3f( 4, 5, 6 ) )
			c["v"] = IECore.V3fData( IECore.V3f( 1, 2, 3 ) )
			c["s"] = "non-default"

			self.assertEqual( s["n"]["user"]["f"].getValue(), 10 )
			self.assertEqual( s["n"]["user"]["i"].getValue(), 11 )
			self.assertEqual( s["n"]["user"]["c"].getValue(), IECore.Color3f( 4, 5, 6 ) )
			self.assertEqual( s["n"]["user"]["v"].getValue(), IECore.V3f( 1, 2, 3 ) )
			self.assertEqual( s["n"]["user"]["s"].getValue(), "non-default" )

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
		s["n"]["user"]["c"].setValue( IECore.Color3f( 1, 2, 3 ) )
		s["n"]["user"]["v"].setValue( IECore.V3f( 1, 2, 3 ) )
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
		self.assertRaisesRegexp( RuntimeError, ".*does not exist.*", s["e"].setExpression, 'parent.notANode.notAPlug = 2;', "OSL" )

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
		script["expression"].setExpression( 'parent.writer.fileName = "' + self.temporaryDirectory() + '/test.txt"', "OSL" )

		dispatcher = GafferDispatch.LocalDispatcher()
		dispatcher["jobsDirectory"].setValue( "/tmp/gafferOSLExpressionEngineTest/jobs" )
		dispatcher["executeInBackground"].setValue( True )
		dispatcher.dispatch( [ script["writer"] ] )

		dispatcher.jobPool().waitForAll()
		self.assertEqual( len( dispatcher.jobPool().failedJobs() ), 0 )

		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/test.txt" ) )

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

	def testHashIgnoresTimeWhenTimeNotReferenced( self ) :

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

if __name__ == "__main__":
	unittest.main()
