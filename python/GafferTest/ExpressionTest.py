##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import inspect
import unittest

import IECore

import Gaffer
import GafferTest

class ExpressionTest( GafferTest.TestCase ) :

	def test( self ) :

		s = Gaffer.ScriptNode()

		s["m1"] = GafferTest.MultiplyNode()
		s["m1"]["op1"].setValue( 10 )
		s["m1"]["op2"].setValue( 20 )

		s["m2"] = GafferTest.MultiplyNode()
		s["m2"]["op2"].setValue( 1 )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			"parent[\"m2\"][\"op1\"] = parent[\"m1\"][\"product\"] * 2",
			"python",
		)

		self.assertEqual( s["m2"]["product"].getValue(), 400 )

	def testContextAccess( self ) :

		s = Gaffer.ScriptNode()

		s["m"] = GafferTest.MultiplyNode()
		s["m"]["op1"].setValue( 1 )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			"parent[\"m\"][\"op2\"] = int( context[\"frame\"] * 2 )",
			"python"
		)

		context = Gaffer.Context()
		context.setFrame( 10 )
		with context :
			self.assertEqual( s["m"]["product"].getValue(), 20 )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["m1"] = GafferTest.MultiplyNode()
		s["m1"]["op1"].setValue( 10 )
		s["m1"]["op2"].setValue( 20 )

		s["m2"] = GafferTest.MultiplyNode()
		s["m2"]["op2"].setValue( 1 )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			"parent[\"m2\"][\"op1\"] = parent[\"m1\"][\"product\"] * 2",
			"python",
		)

		self.assertEqual( s["m2"]["product"].getValue(), 400 )
		self.assertTrue( s["m2"]["op1"].getInput().node().isSame( s["e"] ) )

		ss = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		self.assertEqual( s2["m2"]["product"].getValue(), 400 )
		self.assertTrue( s2["m2"]["op1"].getInput().node().isSame( s2["e"] ) )

		self.assertEqual(
			s2["e"].getExpression(),
			( "parent[\"m2\"][\"op1\"] = parent[\"m1\"][\"product\"] * 2", "python" ),
		)

	def testStringOutput( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.StringPlug()

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			"parent['n']['p'] = '#%d' % int( context['frame'] )",
			"python",
		)

		context = Gaffer.Context()
		for i in range( 0, 10 ) :
			context.setFrame( i )
			with context :
				self.assertEqual( s["n"]["p"].getValue(), "#%d" % i )

	def testLanguages( self ) :

		l = Gaffer.Expression.languages()
		self.failUnless( isinstance( l, tuple ) )
		self.failUnless( "python" in l )

	def testCreateExpressionWithWatchers( self ) :

		s = Gaffer.ScriptNode()

		def f( plug ) :

			plug.getValue()

		s["m1"] = GafferTest.MultiplyNode()

		c = s["m1"].plugDirtiedSignal().connect( f )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			"parent[\"m1\"][\"op1\"] = 2",
			"python"
		)

	def testCompoundNumericPlugs( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["v"] = Gaffer.V2fPlug()

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			'parent["n"]["v"]["x"] = parent["n"]["v"]["y"]',
			"python"
		)

		s["n"]["v"]["y"].setValue( 21 )

		self.assertEqual( s["n"]["v"]["x"].getValue(), 21 )

	def testInputsAsInputs( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["i1"] = Gaffer.IntPlug()
		s["n"]["i2"] = Gaffer.IntPlug()

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			'parent["n"]["i1"] = parent["n"]["i2"]',
			"python",
		)

		s["n"]["i2"].setValue( 11 )

		self.assertEqual( s["n"]["i1"].getValue(), 11 )

	def testDeleteExpressionText( self ) :

		s = Gaffer.ScriptNode()

		s["m1"] = GafferTest.MultiplyNode()
		s["m1"]["op1"].setValue( 10 )
		s["m1"]["op2"].setValue( 20 )

		s["m2"] = GafferTest.MultiplyNode()
		s["m2"]["op2"].setValue( 1 )

		s["e"] = Gaffer.Expression()
		s["e"]["engine"].setValue( "python" )

		s["e"].setExpression( "parent[\"m2\"][\"op1\"] = parent[\"m1\"][\"product\"] * 2" )

		self.failUnless( s["m2"]["op1"].getInput().node().isSame( s["e"] ) )
		self.assertEqual( s["m2"]["product"].getValue(), 400 )

		s["e"].setExpression( "" )
		self.failUnless( s["m2"]["op1"].getInput() is None )
		self.assertEqual( s["m2"]["product"].getValue(), 0 )

	def testContextGetFrameMethod( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		s["n"]["op1"].setValue( 0 )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			"parent['n']['op2'] = int( context.getFrame() )",
			"python",
		)

		with Gaffer.Context() as c :
			for i in range( 0, 10 ) :
				c.setFrame( i )
				self.assertEqual( s["n"]["sum"].getValue(), i )

	def testContextGetMethod( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		s["n"]["op1"].setValue( 0 )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			"parent['n']['op2'] = int( context.get( 'frame' ) )",
			"python"
		)

		with Gaffer.Context() as c :
			for i in range( 0, 10 ) :
				c.setFrame( i )
				self.assertEqual( s["n"]["sum"].getValue(), i )

	def testContextGetWithDefault( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		s["n"]["op1"].setValue( 0 )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			"parent['n']['op2'] = context.get( 'iDontExist', 101 )",
			"python"
		)

		self.assertEqual( s["n"]["sum"].getValue(), 101 )

	def testDirtyPropagation( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		s["n"]["op1"].setValue( 0 )

		s["e"] = Gaffer.Expression()

		dirtied = GafferTest.CapturingSlot( s["n"].plugDirtiedSignal() )
		s["e"].setExpression(
			"parent['n']['op2'] = context.get( 'iDontExist', 101 )",
			"python"
		)
		self.failUnless( s["n"]["sum"] in [ p[0] for p in dirtied ] )

		dirtied = GafferTest.CapturingSlot( s["n"].plugDirtiedSignal() )
		s["e"].setExpression( "", "python" )
		self.failUnless( s["n"]["sum"] in [ p[0] for p in dirtied ] )

	def testSerialisationCreationOrder( self ) :

		# Create a script where the expression node is created before the nodes it's targeting,
		# and make sure it still serialises/loads correctly.
		s = Gaffer.ScriptNode()

		s["e"] = Gaffer.Expression()

		s["m1"] = GafferTest.MultiplyNode()
		s["m1"]["op1"].setValue( 10 )
		s["m1"]["op2"].setValue( 20 )

		s["m2"] = GafferTest.MultiplyNode()
		s["m2"]["op2"].setValue( 1 )

		s["e"].setExpression(
			"parent[\"m2\"][\"op1\"] = parent[\"m1\"][\"product\"] * 2",
			"python"
		)
		self.assertEqual( s["m2"]["product"].getValue(), 400 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		self.assertEqual( s2["m2"]["product"].getValue(), 400 )

	def testSerialisationPlugAccumulation( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"].addChild( Gaffer.FloatPlug( "f", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent[\"n\"][\"user\"][\"f\"] = 2" )

		self.assertEqual( s["n"]["user"]["f"].getValue(), 2 )

		ss = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		self.assertEqual( s2["n"]["user"]["f"].getValue(), 2 )

		self.failUnless( s2["e"].getChild("out1") is None )
		self.failUnless( s2["e"].getChild("in1") is None )

	def testLegacyLoading( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/legacyExpression.gfr" )

		with IECore.CapturingMessageHandler() as mh :
			s.load( continueOnError = True )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertTrue( "rejects input " in mh.messages[0].message )

		s.context().setFrame( 3 )
		with s.context() :
			self.assertEqual( s["n"]["user"]["o"].getValue(), 6 )

	def testMultipleOutputs( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"].addChild( Gaffer.IntPlug( "p1", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.IntPlug( "p2", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			'parent["n"]["user"]["p1"] = 2; parent["n"]["user"]["p2"] = 3',
			"python",
		)

		self.assertEqual( s["n"]["user"]["p1"].getValue(), 2 )
		self.assertEqual( s["n"]["user"]["p2"].getValue(), 3 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"]["user"]["p1"].getValue(), 2 )
		self.assertEqual( s2["n"]["user"]["p2"].getValue(), 3 )

	def testStringVectorDataPlug( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"].addChild( Gaffer.StringVectorDataPlug( "p", defaultValue = IECore.StringVectorData(), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			'import IECore; parent["n"]["user"]["p"] = IECore.StringVectorData( [ "one", "two" ] )'
		)

		self.assertEqual( s["n"]["user"]["p"].getValue(), IECore.StringVectorData( [ "one", "two" ] ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"]["user"]["p"].getValue(), IECore.StringVectorData( [ "one", "two" ] ) )

	def testVectorAndColourOutputs( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"].addChild( Gaffer.V2fPlug( "v2f", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.V2iPlug( "v2i", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.V3fPlug( "v3f", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.V3iPlug( "v3i", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.Color3fPlug( "c3f", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.Color4fPlug( "c4f", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			'import IECore;'
			'parent["n"]["user"]["v2f"] = IECore.V2f( 1, 2 );'
			'parent["n"]["user"]["v2i"] = IECore.V2i( 3, 4 );'
			'parent["n"]["user"]["v3f"] = IECore.V3f( 4, 5, 6 );'
			'parent["n"]["user"]["v3i"] = IECore.V3i( 6, 7, 8 );'
			'parent["n"]["user"]["c3f"] = IECore.Color3f( 9, 10, 11 );'
			'parent["n"]["user"]["c4f"] = IECore.Color4f( 12, 13, 14, 15 );'
		)

		def assertExpectedValues( script ) :

			self.assertEqual( script["n"]["user"]["v2f"].getValue(), IECore.V2f( 1, 2 ) )
			self.assertEqual( script["n"]["user"]["v2i"].getValue(), IECore.V2i( 3, 4 ) )
			self.assertEqual( script["n"]["user"]["v3f"].getValue(), IECore.V3f( 4, 5, 6 ) )
			self.assertEqual( script["n"]["user"]["v3i"].getValue(), IECore.V3i( 6, 7, 8 ) )
			self.assertEqual( script["n"]["user"]["c3f"].getValue(), IECore.Color3f( 9, 10, 11 ) )
			self.assertEqual( script["n"]["user"]["c4f"].getValue(), IECore.Color4f( 12, 13, 14, 15 ) )

		assertExpectedValues( s )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		assertExpectedValues( s2 )

	def testBoxOutputs( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"].addChild( Gaffer.Box2fPlug( "b2f", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.Box2iPlug( "b2i", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.Box3fPlug( "b3f", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.Box3iPlug( "b3i", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			'import IECore;'
			'parent["n"]["user"]["b2f"] = IECore.Box2f( IECore.V2f( 1, 2 ), IECore.V2f( 3, 4 ) );'
			'parent["n"]["user"]["b2i"] = IECore.Box2i( IECore.V2i( 5, 6 ), IECore.V2i( 7, 8 ) );'
			'parent["n"]["user"]["b3f"] = IECore.Box3f( IECore.V3f( 9, 10, 11 ), IECore.V3f( 12, 13, 14 ) );'
			'parent["n"]["user"]["b3i"] = IECore.Box3i( IECore.V3i( 15, 16, 17 ), IECore.V3i( 18, 19, 20 ) );'
		)

		def assertExpectedValues( script ) :

			self.assertEqual( script["n"]["user"]["b2f"].getValue(), IECore.Box2f( IECore.V2f( 1, 2 ), IECore.V2f( 3, 4 ) ) )
			self.assertEqual( script["n"]["user"]["b2i"].getValue(), IECore.Box2i( IECore.V2i( 5, 6 ), IECore.V2i( 7, 8 ) ) )
			self.assertEqual( script["n"]["user"]["b3f"].getValue(), IECore.Box3f( IECore.V3f( 9, 10, 11 ), IECore.V3f( 12, 13, 14 ) ) )
			self.assertEqual( script["n"]["user"]["b3i"].getValue(), IECore.Box3i( IECore.V3i( 15, 16, 17 ), IECore.V3i( 18, 19, 20 ) ) )

		assertExpectedValues( s )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		assertExpectedValues( s2 )

	def testAssignOutputOnBranch( self ) :

		expressions = [

			"""
			if context.getFrame() > 10 :
				parent["n"]["user"]["b"] = True
			else :
				parent["n"]["user"]["b"] = False
			""",

			"""
			parent["n"]["user"]["b"] = False
			if context.getFrame() > 10 :
				parent["n"]["user"]["b"] = True
			""",

			"""
			if context.getFrame() > 10 :
				parent["n"]["user"]["b"] = True
			""",

		]

		for e in expressions :

			s = Gaffer.ScriptNode()

			s["n"] = Gaffer.Node()
			s["n"]["user"]["b"] = Gaffer.BoolPlug( defaultValue = False, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

			s["e"] = Gaffer.Expression()
			s["e"].setExpression( inspect.cleandoc( e ) )

			def assertExpectedValues( script ) :

				c = Gaffer.Context( script.context() )
				with c :
					c.setFrame( 1 )
					self.assertEqual( script["n"]["user"]["b"].getValue(), False )
					c.setFrame( 11 )
					self.assertEqual( script["n"]["user"]["b"].getValue(), True )

			assertExpectedValues( s )

			s2 = Gaffer.ScriptNode()
			s2.execute( s.serialise() )

			assertExpectedValues( s2 )

	def testMultipleReadsAndWrites( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["b"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( inspect.cleandoc(
			"""
			if context.getFrame() > 10 :
				parent["n"]["user"]["a"] = parent["n"]["user"]["b"]
			else :
				parent["n"]["user"]["a"] = parent["n"]["user"]["b"] * 2
			"""
		) )

		self.assertEqual( len( s["n"]["user"]["b"].outputs() ), 1 )
		self.assertEqual( len( s["e"]["__in"] ), 1 )
		self.assertEqual( len( s["e"]["__out"] ), 1 )

	def testNoUnecessaryRewiring( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["b"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["n"]["user"]["a"] = parent["n"]["user"]["b"] + 1' )

		self.assertEqual( s["n"]["user"]["a"].getValue(), 1 )

		ic = GafferTest.CapturingSlot( s["n"].plugInputChangedSignal() )
		ps = GafferTest.CapturingSlot( s["n"].plugSetSignal() )

		s["e"].setExpression( 'parent["n"]["user"]["a"] = parent["n"]["user"]["b"] + 2' )
		self.assertEqual( s["n"]["user"]["a"].getValue(), 2 )

		self.assertEqual( len( ic ), 0 )
		self.assertEqual( len( ps ), 0 )

	def testUndo( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["b"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["c"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["n"]["user"]["a"] = 1; parent["n"]["user"]["b"] = 2; parent["n"]["user"]["c"] = 3' )

		self.assertEqual( s["n"]["user"]["a"].getValue(), 1 )
		self.assertEqual( s["n"]["user"]["b"].getValue(), 2 )
		self.assertEqual( s["n"]["user"]["c"].getValue(), 3 )

		with Gaffer.UndoContext( s ) :

			s["e"].setExpression( 'parent["n"]["user"]["c"] = 1; parent["n"]["user"]["b"] = 2; parent["n"]["user"]["a"] = 3' )

		self.assertEqual( s["n"]["user"]["a"].getValue(), 3 )
		self.assertEqual( s["n"]["user"]["b"].getValue(), 2 )
		self.assertEqual( s["n"]["user"]["c"].getValue(), 1 )

		s.undo()

		self.assertEqual( s["n"]["user"]["a"].getValue(), 1 )
		self.assertEqual( s["n"]["user"]["b"].getValue(), 2 )
		self.assertEqual( s["n"]["user"]["c"].getValue(), 3 )

		s.redo()

		self.assertEqual( s["n"]["user"]["a"].getValue(), 3 )
		self.assertEqual( s["n"]["user"]["b"].getValue(), 2 )
		self.assertEqual( s["n"]["user"]["c"].getValue(), 1 )

	def testAtomicBoxPlugs( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["b2i"] = Gaffer.AtomicBox2iPlug()
		s["n"]["user"]["b2f"] = Gaffer.AtomicBox2fPlug()
		s["n"]["user"]["b3f"] = Gaffer.AtomicBox3fPlug()

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			'parent["n"]["user"]["b2i"] = IECore.Box2i( IECore.V2i( 1, 2 ), IECore.V2i( 3, 4 ) );'
			'parent["n"]["user"]["b2f"] = IECore.Box2f( IECore.V2f( 1, 2 ), IECore.V2f( 3, 4 ) );'
			'parent["n"]["user"]["b3f"] = IECore.Box3f( IECore.V3f( 1, 2, 3 ), IECore.V3f( 4, 5, 6 ) );',
		)

		self.assertEqual(
			s["n"]["user"]["b2i"].getValue(),
			IECore.Box2i( IECore.V2i( 1, 2 ), IECore.V2i( 3, 4 ) )
		)

		self.assertEqual(
			s["n"]["user"]["b2f"].getValue(),
			IECore.Box2f( IECore.V2f( 1, 2 ), IECore.V2f( 3, 4 ) )
		)

		self.assertEqual(
			s["n"]["user"]["b3f"].getValue(),
			IECore.Box3f( IECore.V3f( 1, 2, 3 ), IECore.V3f( 4, 5, 6 ) )
		)

	def testDisconnectOutput( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["n"]["user"]["a"] = 10' )

		self.assertEqual( s["n"]["user"]["a"].getValue(), 10 )

		s["n"]["user"]["a"].setInput( None )
		self.assertTrue( s["n"]["user"]["a"].getInput() is None )
		self.assertEqual( s["n"]["user"]["a"].getValue(), 0 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( s2["n"]["user"]["a"].getInput() is None )
		self.assertEqual( s2["n"]["user"]["a"].getValue(), 0 )

	def testDisconnectInput( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["b"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["b"].setValue( 1 )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["n"]["user"]["a"] = parent["n"]["user"]["b"]' )

		self.assertEqual( s["n"]["user"]["a"].getValue(), 1 )

		s["n"]["user"]["b"].removeOutputs()
		self.assertTrue( s["n"]["user"]["a"].getInput().node().isSame( s["e"] ) )
		self.assertEqual( s["n"]["user"]["a"].getValue(), 0 )
		self.assertEqual( len( s["n"]["user"]["b"].outputs() ), 0 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( s["n"]["user"]["a"].getInput().node().isSame( s["e"] ) )
		self.assertEqual( s2["n"]["user"]["a"].getValue(), 0 )
		self.assertEqual( len( s["n"]["user"]["b"].outputs() ), 0 )

	def testRenamePlugs( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["b"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["n"]["user"]["a"].setValue( 20 )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["n"]["user"]["b"] = parent["n"]["user"]["a"] * 2' )

		self.assertEqual( s["n"]["user"]["a"].getValue(), 20 )
		self.assertEqual( s["n"]["user"]["b"].getValue(), 40 )

		s["n"]["user"]["a"].setName( "A" )
		s["n"]["user"]["b"].setName( "B" )

		self.assertEqual( s["n"]["user"]["A"].getValue(), 20 )
		self.assertEqual( s["n"]["user"]["B"].getValue(), 40 )

		s["n"]["user"]["A"].setValue( 30 )

		self.assertEqual( s["n"]["user"]["A"].getValue(), 30 )
		self.assertEqual( s["n"]["user"]["B"].getValue(), 60 )

		self.assertEqual(
			s["e"].getExpression(),
			( 'parent["n"]["user"]["B"] = parent["n"]["user"]["A"] * 2', "python" )
		)

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"]["user"]["A"].getValue(), 30 )
		self.assertEqual( s2["n"]["user"]["B"].getValue(), 60 )

		s2["n"]["user"]["A"].setValue( 10 )

		self.assertEqual( s2["n"]["user"]["A"].getValue(), 10 )
		self.assertEqual( s2["n"]["user"]["B"].getValue(), 20 )

		self.assertEqual(
			s2["e"].getExpression(),
			( 'parent["n"]["user"]["B"] = parent["n"]["user"]["A"] * 2', "python" )
		)

	def testRenameNode( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["b"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["n"]["user"]["a"].setValue( 20 )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["n"]["user"]["b"] = parent["n"]["user"]["a"] * 2' )

		self.assertEqual( s["n"]["user"]["a"].getValue(), 20 )
		self.assertEqual( s["n"]["user"]["b"].getValue(), 40 )

		s["n"].setName( "N" )

		self.assertEqual( s["N"]["user"]["a"].getValue(), 20 )
		self.assertEqual( s["N"]["user"]["b"].getValue(), 40 )

		self.assertEqual(
			s["e"].getExpression(),
			( 'parent["N"]["user"]["b"] = parent["N"]["user"]["a"] * 2', "python" )
		)

		s["N"]["user"]["a"].setValue( 30 )

		self.assertEqual( s["N"]["user"]["a"].getValue(), 30 )
		self.assertEqual( s["N"]["user"]["b"].getValue(), 60 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["N"]["user"]["a"].getValue(), 30 )
		self.assertEqual( s2["N"]["user"]["b"].getValue(), 60 )

		s2["N"]["user"]["a"].setValue( 10 )

		self.assertEqual( s2["N"]["user"]["a"].getValue(), 10 )
		self.assertEqual( s2["N"]["user"]["b"].getValue(), 20 )

		self.assertEqual(
			s2["e"].getExpression(),
			( 'parent["N"]["user"]["b"] = parent["N"]["user"]["a"] * 2', "python" )
		)

	def testSingleQuotedNames( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["b"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["n"]["user"]["a"].setValue( 20 )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent['n']['user']['b'] = parent['n']['user']['a'] * 2" )

		self.assertEqual( s["n"]["user"]["a"].getValue(), 20 )
		self.assertEqual( s["n"]["user"]["b"].getValue(), 40 )

		s["n"].setName( "N" )
		s["N"]["user"]["a"].setName( "A" )
		s["N"]["user"]["b"].setName( "B" )

		self.assertEqual( s["N"]["user"]["A"].getValue(), 20 )
		self.assertEqual( s["N"]["user"]["B"].getValue(), 40 )

		self.assertEqual(
			s["e"].getExpression(),
			( 'parent["N"]["user"]["B"] = parent["N"]["user"]["A"] * 2', "python" )
		)

		s["N"]["user"]["A"].setValue( 30 )

		self.assertEqual( s["N"]["user"]["A"].getValue(), 30 )
		self.assertEqual( s["N"]["user"]["B"].getValue(), 60 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["N"]["user"]["A"].getValue(), 30 )
		self.assertEqual( s2["N"]["user"]["B"].getValue(), 60 )

		s2["N"]["user"]["A"].setValue( 10 )

		self.assertEqual( s2["N"]["user"]["A"].getValue(), 10 )
		self.assertEqual( s2["N"]["user"]["B"].getValue(), 20 )

		self.assertEqual(
			s2["e"].getExpression(),
			( 'parent["N"]["user"]["B"] = parent["N"]["user"]["A"] * 2', "python" )
		)

	def testLoadScriptFromVersion0_15( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/expressionVersion-0.15.0.0.gfr" )

		with IECore.CapturingMessageHandler() as mh :
			s.load( continueOnError = True )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertTrue( "rejects input " in mh.messages[0].message )

		self.assertEqual( s["n"]["user"]["b"].getValue(), 2 )
		self.assertTrue( s["n"]["user"]["b"].getInput().node().isSame( s["e"] ) )

	def testAPICompatibilityWithVersion0_15( self ) :

		# In version 0.15 and prior, an expression was created
		# by first setting the engine plug and then setting the
		# expression plug. For now we still need to provide
		# backwards compatibility with this method, even though
		# those plugs are now private.

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["b"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"]["engine"].setValue( "python" )
		s["e"]["expression"].setValue( inspect.cleandoc(
			"""
			if context.getFrame() > 10 :
				parent["n"]["user"]["a"] = parent["n"]["user"]["b"]
			else :
				parent["n"]["user"]["a"] = parent["n"]["user"]["b"] * 2
			"""
		) )

		self.assertEqual( len( s["n"]["user"]["b"].outputs() ), 1 )
		self.assertEqual( len( s["e"]["__in"] ), 1 )
		self.assertEqual( len( s["e"]["__out"] ), 1 )

	def testIdenticalExpressionWithDifferentPlugTypes( self ) :

		# IntPlug -> FloatPlug

		s1 = Gaffer.ScriptNode()

		s1["n"] = Gaffer.Node()
		s1["n"]["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s1["n"]["user"]["b"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s1["e"] = Gaffer.Expression()
		s1["e"].setExpression( 'parent["n"]["user"]["b"] = parent["n"]["user"]["a"]' )

		s1["n"]["user"]["a"].setValue( 1001 )
		self.assertEqual( s1["n"]["user"]["b"].getValue(), 1001 )

		# IntPlug -> IntPlug

		s2 = Gaffer.ScriptNode()

		s2["n"] = Gaffer.Node()
		s2["n"]["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s2["n"]["user"]["b"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s2["e"] = Gaffer.Expression()
		s2["e"].setExpression( 'parent["n"]["user"]["b"] = parent["n"]["user"]["a"]' )

		s2["n"]["user"]["a"].setValue( 1001 )
		self.assertEqual( s2["n"]["user"]["b"].getValue(), 1001 )

	def testYDrivingX( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["v"] = Gaffer.V2fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["n"]["user"]["v"]["x"] = parent["n"]["user"]["v"]["y"] * 2' )

		s["n"]["user"]["v"]["y"].setValue( 2 )
		self.assertEqual( s["n"]["user"]["v"]["x"].getValue(), 4 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		self.assertEqual( s2["n"]["user"]["v"]["x"].getValue(), 4 )

	def testExpressionChangedSignal( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["p"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		expressions = []
		def f( node ) :

			expressions.append( node.getExpression() )

		s["e"] = Gaffer.Expression()
		self.assertEqual( s["e"].getExpression(), ( "", "" ) )

		c = s["e"].expressionChangedSignal().connect( f )

		with Gaffer.UndoContext( s ) :
			s["e"].setExpression( 'parent["n"]["user"]["p"] = 10' )
			self.assertEqual( len( expressions ), 1 )
			self.assertEqual( expressions[0], ( 'parent["n"]["user"]["p"] = 10', "python" ) )

		s.undo()
		self.assertEqual( len( expressions ), 2 )
		self.assertEqual( expressions[1], ( "", "" ) )

		s.redo()
		self.assertEqual( len( expressions ), 3 )
		self.assertEqual( expressions[2], expressions[0] )

	def testDefaultExpression( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["p"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["p"].setValue( 10 )

		expression = Gaffer.Expression.defaultExpression( s["n"]["user"]["p"], "python" )
		s["n"]["user"]["p"].setValue( 0 )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( expression, "python" )

		self.assertEqual( s["n"]["user"]["p"].getValue(), 10 )

	def testInvalidExpression( self ) :

		s = Gaffer.ScriptNode()

		s["e"] = Gaffer.Expression()
		self.assertRaisesRegexp( RuntimeError, ".*does not exist.*", s["e"].setExpression, 'parent["notANode"]["notAPlug"] = 2' )

	def testRemoveOneOutputOfTwo( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["a1"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["a2"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["b1"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["b2"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["b1"].setValue( 1 )
		s["n"]["user"]["b2"].setValue( 2 )

		a1Expr = 'parent["n"]["user"]["a1"] = parent["n"]["user"]["b1"]'
		a2Expr = 'parent["n"]["user"]["a2"] = parent["n"]["user"]["b2"]'

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( a1Expr + "\n" + a2Expr )

		self.assertTrue( s["n"]["user"]["a1"].getInput().node().isSame( s["e"] ) )
		self.assertTrue( s["n"]["user"]["a2"].getInput().node().isSame( s["e"] ) )
		self.assertEqual( s["n"]["user"]["a1"].getValue(), 1 )
		self.assertEqual( s["n"]["user"]["a2"].getValue(), 2 )

		s["e"].setExpression( a1Expr )
		self.assertTrue( s["n"]["user"]["a1"].getInput().node().isSame( s["e"] ) )
		self.assertTrue( s["n"]["user"]["a2"].getInput() is None )
		self.assertEqual( s["n"]["user"]["a1"].getValue(), 1 )
		self.assertEqual( s["n"]["user"]["a2"].getValue(), 0 )

		s["e"].setExpression( a2Expr + "\n" + a1Expr )

		self.assertTrue( s["n"]["user"]["a1"].getInput().node().isSame( s["e"] ) )
		self.assertTrue( s["n"]["user"]["a2"].getInput().node().isSame( s["e"] ) )
		self.assertEqual( s["n"]["user"]["a1"].getValue(), 1 )
		self.assertEqual( s["n"]["user"]["a2"].getValue(), 2 )

		s["e"].setExpression( a2Expr )
		self.assertTrue( s["n"]["user"]["a1"].getInput() is None )
		self.assertTrue( s["n"]["user"]["a2"].getInput().node().isSame( s["e"] ) )
		self.assertEqual( s["n"]["user"]["a1"].getValue(), 0 )
		self.assertEqual( s["n"]["user"]["a2"].getValue(), 2 )

	def testReplaceFloatWithInt( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()

		s["e"].setExpression( 'parent["n"]["user"]["f"] = 10' )
		self.assertEqual( s["n"]["user"]["f"].getValue(), 10 )
		self.assertEqual( s["n"]["user"]["i"].getValue(), 0 )

		s["e"].setExpression( 'parent["n"]["user"]["i"] = 10' )
		self.assertEqual( s["n"]["user"]["f"].getValue(), 0 )
		self.assertEqual( s["n"]["user"]["i"].getValue(), 10 )

	def testSetExpressionShortcuts( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		cs = GafferTest.CapturingSlot( s["e"].expressionChangedSignal() )

		s["e"].setExpression( 'parent["n"]["user"]["i"] = 10' )
		self.assertEqual( len( cs ), 1 )

		s["e"].setExpression( 'parent["n"]["user"]["i"] = 10' )
		self.assertEqual( len( cs ), 1 )

		s["e"].setExpression( 'parent["n"]["user"]["i"] = 20' )
		self.assertEqual( len( cs ), 2 )

	def testTime( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["n"]["user"]["f"] = context.getTime()' )

		with Gaffer.Context() as c :
			c.setTime( 1 )
			self.assertEqual( s["n"]["user"]["f"].getValue(), 1 )
			c.setTime( 2 )
			self.assertEqual( s["n"]["user"]["f"].getValue(), 2 )

	def testFramesPerSecond( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["n"]["user"]["f"] = context.getFramesPerSecond()' )

		with Gaffer.Context() as c :
			c.setFramesPerSecond( 24 )
			self.assertEqual( s["n"]["user"]["f"].getValue(), 24 )
			c.setFramesPerSecond( 48 )
			self.assertEqual( s["n"]["user"]["f"].getValue(), 48 )

	def testHashIgnoresTimeWhenTimeNotReferenced( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["n"]["user"]["f"] = 1' )

		with Gaffer.Context() as c :
			c.setTime( 1 )
			h1 = s["n"]["user"]["f"].hash()
			c.setTime( 2 )
			h2 = s["n"]["user"]["f"].hash()

		self.assertEqual( h1, h2 )

	def testInPlugDoesntAcceptConnections( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = Gaffer.Node()
		s["n1"]["p"] = Gaffer.ValuePlug()
		s["n1"]["p"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["n2"] = Gaffer.Node()
		s["n2"]["p"] = Gaffer.ValuePlug()
		s["n2"]["p"]["f"]  = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["n2"]["p"]["f"] = parent["n1"]["p"]["f"]' )

		self.assertTrue( s["e"]["__in"].getInput() is None )

		s["n1"]["p"]["f2"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( len( s["e"]["__in"] ), 1 )

	def testDefaultExpressionForSupportedPlugs( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"].addChild( Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.BoolPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.V2fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.V2iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.V3iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.Color4fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.Box2fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.Box2iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.Box3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.Box3iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.IntVectorDataPlug( defaultValue = IECore.IntVectorData( [ 0, 1 ] ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.FloatVectorDataPlug( defaultValue = IECore.FloatVectorData( [ 0, 1 ] ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.StringVectorDataPlug( defaultValue = IECore.StringVectorData( [ "a", "b" ] ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.V3fVectorDataPlug( defaultValue = IECore.V3fVectorData( [ IECore.V3f( 1 ) ] ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		s["e"] = Gaffer.Expression()

		for plug in s["n"]["user"] :

			value = plug.getValue()
			s["e"].setExpression( s["e"].defaultExpression( plug, "python" ) )
			self.assertTrue( plug.getInput().node().isSame( s["e"] ) )
			self.assertEqual( plug.getValue(), value )

	def testNoDefaultExpressionForUnsupportedPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"].addChild(
			Gaffer.SplineffPlug(
				defaultValue = IECore.Splineff(
					IECore.CubicBasisf.linear(),
					(
						( 0, 0 ),
						( 1, 1 ),
					),
				),
				flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
			)
		)
		s["n"]["user"].addChild( Gaffer.TransformPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.Transform2DPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["n"]["user"].addChild( Gaffer.ValuePlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		s["e"] = Gaffer.Expression()

		for plug in s["n"]["user"] :
			self.assertEqual( s["e"].defaultExpression( plug, "python" ), "" )

	def testSetIntFromFloat( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent['n']['user']['i'] = context.getFrame()" )

		with Gaffer.Context() as c :

			c.setFrame( 0 )
			self.assertEqual( s["n"]["user"]["i"].getValue(), 0 )

			c.setFrame( 1 )
			self.assertEqual( s["n"]["user"]["i"].getValue(), 1 )

	def testParseFailureLeavesStateUnchanged( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent['n']['user']['i'] = context.getFrame()" )

		cs = GafferTest.CapturingSlot( s["e"].expressionChangedSignal() )

		with Gaffer.Context() as c :

			c.setFrame( 10 )
			self.assertEqual( s["n"]["user"]["i"].getValue(), 10 )
			c.setFrame( 20 )
			self.assertEqual( s["n"]["user"]["i"].getValue(), 20 )

		with Gaffer.UndoContext( s ) :

			self.assertRaisesRegexp(
				Exception,
				"SyntaxError",
				s["e"].setExpression,
				"i'm not valid python"
			)

		self.assertEqual( len( cs ), 0 )
		self.assertFalse( s.undoAvailable() )

		with Gaffer.Context() as c :

			c.setFrame( 11 )
			self.assertEqual( s["n"]["user"]["i"].getValue(), 11 )
			c.setFrame( 21 )
			self.assertEqual( s["n"]["user"]["i"].getValue(), 21 )

	def testNoReadWrite( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["p"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["e"] = Gaffer.Expression()
		self.assertRaisesRegexp(
			RuntimeError,
			"Cannot both read from and write to plug \"n.user.p\"",
			s["e"].setExpression,
			"parent['n']['user']['p'] = parent['n']['user']['p'] * 2"
		)

if __name__ == "__main__":
	unittest.main()
