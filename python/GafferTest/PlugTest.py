##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

from __future__ import with_statement

import unittest

import IECore

import Gaffer
import GafferTest

class PlugTest( GafferTest.TestCase ) :

	def testParenting( self ) :

		n = Gaffer.Node()
		p = Gaffer.Plug()
		self.assert_( p.parent() is None )
		self.assert_( p.node() is None )
		self.assert_( p.acceptsParent( n ) )
		n.addChild( p )
		self.assert_( p.parent().isSame( n ) )
		self.assert_( p.node().isSame( n ) )

	def testConnectionAcceptance( self ) :

		p1 = Gaffer.Plug( direction=Gaffer.Plug.Direction.In )
		p2 = Gaffer.Plug( direction=Gaffer.Plug.Direction.Out )
		self.assert_( p1.acceptsInput( p2 ) )

		p1 = Gaffer.Plug( direction=Gaffer.Plug.Direction.In )
		p2 = Gaffer.Plug( direction=Gaffer.Plug.Direction.In )
		self.assert_( p1.acceptsInput( p2 ) )

	def testConnection( self ) :

		n1 = Gaffer.Node()
		p1 = Gaffer.Plug()
		n1.addChild( p1 )
		self.assert_( p1.getInput() is None )
		self.assertEqual( p1.outputs(), () )

		n2 = Gaffer.Node()
		p2 = Gaffer.Plug()
		n2.addChild( p2 )
		self.assert_( p2.getInput() is None )
		self.assertEqual( p2.outputs(), () )

		p2.setInput( p1 )
		self.assert_( p2.getInput().isSame( p1 ) )
		self.assert_( len( p1.outputs() ), 1 )
		self.assert_( p1.outputs()[0].isSame( p2 ) )

		p2.setInput( None )
		self.assert_( p2.getInput() is None )
		self.assertEqual( p1.outputs(), () )

	def testConnectionSignals( self ) :

		def f( p ) :

			PlugTest.__connection = ( p, p.getInput() )

		n1 = Gaffer.Node()
		p1 = Gaffer.Plug( direction=Gaffer.Plug.Direction.Out )
		n1.addChild( p1 )

		n2 = Gaffer.Node()
		p2 = Gaffer.Plug( direction=Gaffer.Plug.Direction.In )
		n2.addChild( p2 )

		c = n2.plugInputChangedSignal().connect( f )
		p2.setInput( p1 )
		self.assert_( PlugTest.__connection[0].isSame( p2 ) )
		self.assert_( PlugTest.__connection[1].isSame( p1 ) )
		PlugTest.__connection = None
		p2.setInput( None )
		self.assert_( PlugTest.__connection[0].isSame( p2 ) )
		self.assert_( PlugTest.__connection[1] is None )

	def testDirectionality( self ) :

		p = Gaffer.Plug( direction=Gaffer.Plug.Direction.In )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.In )
		p = Gaffer.Plug( direction=Gaffer.Plug.Direction.Out )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.Out )

	def testFlags( self ) :

		p = Gaffer.Plug()
		self.assertEqual( p.getFlags(), Gaffer.Plug.Flags.Default )

		p = Gaffer.Plug( flags=Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( p.getFlags(), Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( p.getFlags( Gaffer.Plug.Flags.Dynamic ), True )

		p.setFlags( Gaffer.Plug.Flags.Dynamic, False )
		self.assertEqual( p.getFlags( Gaffer.Plug.Flags.Dynamic ), False )

	def testDerivingInPython( self ) :

		class TestPlug( Gaffer.Plug ) :

			def __init__( self, name = "TestPlug", direction = Gaffer.Plug.Direction.In, flags = Gaffer.Plug.Flags.Default ) :

				Gaffer.Plug.__init__( self, name, direction, flags )

				self.inputHasBeenSet = False

			def acceptsInput( self, plug ) :

				if not Gaffer.Plug.acceptsInput( self, plug ) :
					return False

				return isinstance( plug, ( TestPlug, type( None ) ) )

			def setInput( self, plug ) :

				Gaffer.Plug.setInput( self, plug )

				self.inputHasBeenSet = True

			def acceptsParent( self, potentialParent ) :

				if not Gaffer.Plug.acceptsParent( self, potentialParent ) :
					return False

				if isinstance( potentialParent, Gaffer.CompoundPlug ) :
					return False

				return True

			def createCounterpart( self, name, direction ) :

				return TestPlug( name, direction, self.getFlags() )

		IECore.registerRunTimeTyped( TestPlug )

		# check the constructor

		p1 = TestPlug( "testIn" )
		self.assertEqual( p1.getName(), "testIn" )
		self.assertEqual( p1.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p1.getFlags(), Gaffer.Plug.Flags.Default )

		n1 = Gaffer.Node()
		n1.addChild( p1 )
		self.assertEqual( n1["testIn"], p1 )

		n2 = Gaffer.Node()
		n2.addChild( TestPlug( name = "testOut", direction = Gaffer.Plug.Direction.Out ) )
		n2.addChild( Gaffer.IntPlug( name = "intOut", direction = Gaffer.Plug.Direction.Out ) )

		# check that accepts input and setInput can be overridden

		self.failUnless( n1["testIn"].acceptsInput( n2["testOut"] ) )
		self.failIf( n1["testIn"].acceptsInput( n2["intOut"] ) )

		self.assertRaises( RuntimeError, n1["testIn"].setInput, n2["intOut"] )
		self.assertEqual( n1["testIn"].inputHasBeenSet, False )

		n1["testIn"].setInput( n2["testOut"] )
		self.assertEqual( n1["testIn"].inputHasBeenSet, True )
		self.assertEqual( n1["testIn"].getInput(), n2["testOut"] )

		# check that acceptsParent can be overridden

		p2 = TestPlug()
		self.assertRaises( RuntimeError, Gaffer.CompoundPlug().addChild, p2 )

		# try making a counterpart

		p3 = p2.createCounterpart( "ll", Gaffer.Plug.Direction.Out )
		self.assertEqual( p3.getName(), "ll" )
		self.assertEqual( p3.direction(), Gaffer.Plug.Direction.Out )

	def testRemovePlugRemovesInputs( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()

		s["n1"]["o"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )

		s["n2"]["i"] = Gaffer.IntPlug()
		s["n2"]["c"] = Gaffer.CompoundPlug()
		s["n2"]["c"]["i"] = Gaffer.IntPlug()

		s["n2"]["i"].setInput( s["n1"]["o"] )
		s["n2"]["c"]["i"].setInput( s["n1"]["o"] )

		self.failUnless( s["n2"]["i"].getInput().isSame( s["n1"]["o"] ) )
		self.failUnless( s["n2"]["c"]["i"].getInput().isSame(  s["n1"]["o"] ) )
		self.assertEqual( len( s["n1"]["o"].outputs() ), 2 )

		with Gaffer.UndoScope( s ) :

			del s["n2"]["i"]
			del s["n2"]["c"]["i"]

		self.assertEqual( len( s["n1"]["o"].outputs() ), 0 )

		s.undo()

		self.failUnless( s["n2"]["i"].getInput().isSame( s["n1"]["o"] ) )
		self.failUnless( s["n2"]["c"]["i"].getInput().isSame(  s["n1"]["o"] ) )
		self.assertEqual( len( s["n1"]["o"].outputs() ), 2 )

	def testRemovePlugRemovesOutputs( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()

		s["n1"]["o"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )

		s["n2"]["i"] = Gaffer.IntPlug()

		s["n2"]["i"].setInput( s["n1"]["o"] )

		self.failUnless( s["n2"]["i"].getInput().isSame( s["n1"]["o"] ) )
		self.assertEqual( len( s["n1"]["o"].outputs() ), 1 )

		with Gaffer.UndoScope( s ) :

			removedPlug = s["n1"]["o"]
			del s["n1"]["o"]

		self.assertEqual( len( removedPlug.outputs() ), 0 )

		s.undo()

		self.failUnless( s["n2"]["i"].getInput().isSame( s["n1"]["o"] ) )
		self.assertEqual( len( s["n1"]["o"].outputs() ), 1 )
		self.failUnless( s["n1"]["o"].isSame( removedPlug ) )

	def testDefaultFlags( self ) :

		p = Gaffer.Plug()
		self.failUnless( p.getFlags( Gaffer.Plug.Flags.Serialisable ) )

	def testSerialisableFlag( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()

		self.failUnless( s["n"]["op1"].getFlags( Gaffer.Plug.Flags.Serialisable ) )

		s["n"]["op1"].setValue( 20 )
		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n"]["op1"].getValue(), 20 )

		s["n"]["op1"].setFlags( Gaffer.Plug.Flags.Serialisable, False )
		ss = s.serialise()

		self.failIf( "op1" in ss )

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n"]["op1"].getValue(), 0 )

	def testFlagSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n"]["p"].getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

	def testFlagsNeverSerialisedAsAll( self ) :

		# it's a terrible idea to serialise a set of flags that happen to be All
		# as All, rather than as the or-ing of the specific flags, because when new
		# flags are introduced in the future (and default to off) they will suddenly
		# pop on when loading old files.

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.All )

		ss = s.serialise()

		self.failIf( "All" in ss )

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n"]["p"].getFlags(), Gaffer.Plug.Flags.All )

	def testAcceptsInputsFlag( self ) :

		pOut = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )

		pIn1 = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.AcceptsInputs )
		self.assertEqual( pIn1.getFlags( Gaffer.Plug.Flags.AcceptsInputs ), False )
		self.assertEqual( pIn1.acceptsInput( pOut ), False )

		pIn2 = Gaffer.Plug()
		self.assertEqual( pIn2.getFlags( Gaffer.Plug.Flags.AcceptsInputs ), True )
		self.assertEqual( pIn2.acceptsInput( pOut ), True )

	def testReadOnlyDefaultsToOff( self ) :

		p = Gaffer.Plug()
		self.failIf( p.getFlags( Gaffer.Plug.Flags.ReadOnly ) )

	def testReadOnlyDisallowsInputs( self ) :

		self.failUnless( Gaffer.Plug.Flags.All & Gaffer.Plug.Flags.ReadOnly )

		p1 = Gaffer.Plug()
		p2 = Gaffer.Plug()
		self.failUnless( p1.acceptsInput( p2 ) )
		# read-only plugs can still be used as connection sources
		p2.setFlags( Gaffer.Plug.Flags.ReadOnly, True )
		self.failUnless( p1.acceptsInput( p2 ) )
		# but cannot be used as destinations
		self.failIf( p2.acceptsInput( p1 ) )
		self.assertRaises( RuntimeError, p2.setInput, p1 )

	def testOutputPlugsDisallowReadOnly( self ) :

		p = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		self.assertRaises( RuntimeError, p.setFlags, Gaffer.Plug.Flags.ReadOnly, True )

		self.assertRaises(
			RuntimeError,
			Gaffer.Plug,
			direction = Gaffer.Plug.Direction.Out,
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.ReadOnly
		)

	def testRepr( self ) :

		p1 = Gaffer.Plug(
			"p",
			Gaffer.Plug.Direction.Out,
			Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.AcceptsInputs,
		)

		p2 = eval( repr( p1 ) )

		self.assertEqual( p1.getName(), p2.getName() )
		self.assertEqual( p1.direction(), p2.direction() )
		self.assertEqual( p1.getFlags(), p2.getFlags() )

	def testCreateCounterpart( self ) :

		p = Gaffer.Plug(
			"p",
			Gaffer.Plug.Direction.Out,
			Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.AcceptsInputs,
		)

		p2 = p.createCounterpart( "p2", Gaffer.Plug.Direction.In )

		self.assertEqual( p2.getName(), "p2" )
		self.assertEqual( p2.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p2.getFlags(), p.getFlags() )

	def testCreateCounterpartWithChildren( self ) :

		p = Gaffer.Plug()
		p["i"] = Gaffer.IntPlug()
		p["f"] = Gaffer.FloatPlug()

		p2 = p.createCounterpart( "p2", Gaffer.Plug.Direction.In )
		self.assertEqual( p2.keys(), [ "i", "f" ] )
		self.assertTrue( isinstance( p2["i"], Gaffer.IntPlug ) )
		self.assertTrue( isinstance( p2["f"], Gaffer.FloatPlug ) )

	def testSource( self ) :

		p1 = Gaffer.Plug( "p1" )
		p2 = Gaffer.Plug( "p2" )
		p3 = Gaffer.Plug( "p3" )

		self.assertTrue( p1.source().isSame( p1 ) )
		self.assertTrue( p2.source().isSame( p2 ) )
		self.assertTrue( p3.source().isSame( p3 ) )

		p2.setInput( p1 )
		self.assertTrue( p1.source().isSame( p1 ) )
		self.assertTrue( p2.source().isSame( p1 ) )
		self.assertTrue( p3.source().isSame( p3 ) )

		p3.setInput( p2 )
		self.assertTrue( p1.source().isSame( p1 ) )
		self.assertTrue( p2.source().isSame( p1 ) )
		self.assertTrue( p3.source().isSame( p1 ) )

	def testRejectsInputFromSelf( self ) :

		p = Gaffer.Plug()
		self.assertFalse( p.acceptsInput( p ) )

	def testReadOnlySerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["p2"] = Gaffer.Plug( direction=Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["p"].setInput( s["n"]["p2"] )
		s["n"]["p"].setFlags( Gaffer.Plug.Flags.ReadOnly, True )
		ss = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		self.assertTrue( s2["n"]["p"].getInput().isSame( s2["n"]["p2"] ) )
		self.assertEqual( s2["n"]["p"].getFlags( Gaffer.Plug.Flags.ReadOnly ), True )

	def testReadOnlyRepr( self ) :

		p1 = Gaffer.Plug(
			"p",
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.ReadOnly,
		)

		p2 = eval( repr( p1 ) )

		self.assertEqual( p1.getName(), p2.getName() )
		self.assertEqual( p1.direction(), p2.direction() )
		self.assertEqual( p1.getFlags(), p2.getFlags() )

	def testNoFlagsRepr( self ) :

		p1 = Gaffer.Plug(
			"p",
			Gaffer.Plug.Direction.Out,
			Gaffer.Plug.Flags.None,
		)

		p2 = eval( repr( p1 ) )

		self.assertEqual( p1.getName(), p2.getName() )
		self.assertEqual( p1.direction(), p2.direction() )
		self.assertEqual( p1.getFlags(), p2.getFlags() )

	def testAllFlagPermutationsRepr( self ) :

		for i in range( 0, int( Gaffer.Plug.Flags.All ) + 1 ) :

			p1 = Gaffer.Plug(
				flags = Gaffer.Plug.Flags( i )
			)

			p2 = eval( repr( p1 ) )

			self.assertEqual( p1.getFlags(), p2.getFlags() )

	def testFlagReprAlwaysIncludesDefault( self ) :

		# we always need to serialise the flags by adding and removing things
		# from the default flags, so that if we add new default flags in the future,
		# they will default to on when loaded from file.

		for i in range( 0, int( Gaffer.Plug.Flags.All ) + 1 ) :

			if i == Gaffer.Plug.Flags.Default :
				continue

			p = Gaffer.Plug(
				flags = Gaffer.Plug.Flags( i )
			)
			self.assertTrue( "Gaffer.Plug.Flags.Default" in repr( p ) )

	def testRemoveOutputs( self ) :

		input = Gaffer.Plug()

		outputs = []
		for i in range( 0, 1000 ) :
			outputs.append( Gaffer.Plug() )
			outputs[-1].setInput( input )

		self.assertEqual( input.outputs(), tuple( outputs ) )
		for output in outputs :
			self.assertTrue( output.getInput().isSame( input ) )

		input.removeOutputs()

		self.assertEqual( input.outputs(), () )
		for output in outputs :
			self.assertTrue( output.getInput() is None )

	def testParentConnectionTracksChildConnections( self ) :

		n1 = Gaffer.Node()
		n1["p"] = Gaffer.Plug()
		n1["p"]["c1"] = Gaffer.Plug()
		n1["p"]["c2"] = Gaffer.Plug()

		n2 = Gaffer.Node()
		n2["p"] = Gaffer.Plug()
		n2["p"]["c1"] = Gaffer.Plug()
		n2["p"]["c2"] = Gaffer.Plug()

		n2["p"]["c1"].setInput( n1["p"]["c1"] )
		n2["p"]["c2"].setInput( n1["p"]["c2"] )
		self.failUnless( n2["p"].getInput().isSame( n1["p"] ) )

		n2["p"]["c2"].setInput( None )
		self.failUnless( n2["p"].getInput() is None )

		n2["p"]["c2"].setInput( n1["p"]["c2"] )
		self.failUnless( n2["p"].getInput().isSame( n1["p"] ) )

		n2["p"]["c3"] = Gaffer.Plug()

		self.failUnless( n2["p"].getInput() is None )

		n1["p"]["c3"] = Gaffer.Plug()
		n2["p"]["c3"].setInput( n1["p"]["c3"] )
		self.failUnless( n2["p"].getInput().isSame( n1["p"] ) )

	def testAncestorConnectionTracksDescendantConnections( self ) :

		a1 = Gaffer.Plug()
		a1["b1"] = Gaffer.Plug()
		a1["b1"]["c1"] = Gaffer.Plug()

		a2 = Gaffer.Plug()
		a2["b2"] = Gaffer.Plug()
		a2["b2"]["c2"] = Gaffer.Plug()

		a2["b2"]["c2"].setInput( a1["b1"]["c1"] )

		self.assertTrue( a2["b2"]["c2"].getInput().isSame( a1["b1"]["c1"] ) )
		self.assertTrue( a2["b2"].getInput().isSame( a1["b1"] ) )
		self.assertTrue( a2.getInput().isSame( a1 ) )

		a2["b2"]["c2"].setInput( None )

		self.assertTrue( a2["b2"]["c2"].getInput() is None )
		self.assertTrue( a2["b2"].getInput() is None )
		self.assertTrue( a2.getInput() is None )

	def testSerialisationWithChildren( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["p"]["c"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( isinstance( s2["n"]["p"]["c"], Gaffer.Plug ) )

	def testChildAdditionPropagatesToOutputs( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()

		s["n1"]["c"] = Gaffer.Plug()
		s["n2"]["c"] = Gaffer.Plug()

		s["n2"]["c"].setInput( s["n1"]["c"] )
		self.assertTrue( s["n2"]["c"].getInput().isSame( s["n1"]["c"] ) )

		def assertPreconditions() :

			self.assertEqual( s["n1"]["c"].keys(), [] )
			self.assertEqual( s["n2"]["c"].keys(), [] )
			self.assertTrue( s["n2"]["c"].getInput().isSame( s["n1"]["c"] ) )

		def assertPostconditions() :

			self.assertEqual( s["n1"]["c"].keys(), [ "i", "f" ] )
			self.assertEqual( s["n2"]["c"].keys(), [ "i", "f" ] )

			self.assertTrue( isinstance( s["n2"]["c"]["i"], Gaffer.IntPlug ) )
			self.assertTrue( s["n2"]["c"]["i"].getInput().isSame( s["n1"]["c"]["i"] ) )
			self.assertTrue( s["n2"]["c"].getInput().isSame( s["n1"]["c"] ) )

			self.assertTrue( isinstance( s["n2"]["c"]["f"], Gaffer.FloatPlug ) )
			self.assertTrue( s["n2"]["c"]["f"].getInput().isSame( s["n1"]["c"]["f"] ) )
			self.assertTrue( s["n2"]["c"].getInput().isSame( s["n1"]["c"] ) )

		assertPreconditions()

		with Gaffer.UndoScope( s ) :

			s["n1"]["c"].addChild( Gaffer.IntPlug( "i" ) )
			s["n1"]["c"].addChild( Gaffer.FloatPlug( "f" ) )

		assertPostconditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostconditions()

	def testChildRemovalPropagatesToOutputs( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()

		s["n1"]["c"] = Gaffer.Plug()
		s["n2"]["c"] = Gaffer.Plug()

		s["n1"]["c"]["f"] = Gaffer.FloatPlug()
		s["n2"]["c"]["f"] = Gaffer.FloatPlug()

		s["n1"]["c"]["i"] = Gaffer.FloatPlug()
		s["n2"]["c"]["i"] = Gaffer.FloatPlug()

		s["n2"]["c"].setInput( s["n1"]["c"] )

		def assertPreconditions() :

			self.assertEqual( s["n1"]["c"].keys(), [ "f", "i" ] )
			self.assertEqual( s["n2"]["c"].keys(), [ "f", "i" ] )

			self.assertTrue( s["n2"]["c"].getInput().isSame( s["n1"]["c"] ) )
			self.assertTrue( s["n2"]["c"]["i"].getInput().isSame( s["n1"]["c"]["i"] ) )
			self.assertTrue( s["n2"]["c"]["f"].getInput().isSame( s["n1"]["c"]["f"] ) )

		def assertPostconditions() :

			self.assertEqual( s["n1"]["c"].keys(), [] )
			self.assertEqual( s["n2"]["c"].keys(), [] )

			self.assertTrue( s["n2"]["c"].getInput().isSame( s["n1"]["c"] ) )

		assertPreconditions()

		with Gaffer.UndoScope( s ) :

			del s["n1"]["c"]["i"]
			del s["n1"]["c"]["f"]

		assertPostconditions()

		s.undo()

		assertPreconditions()

		s.redo()

		assertPostconditions()

	def testMixedInputsAndOutputsAsChildren( self ) :

		p = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.AcceptsInputs )
		p["in"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.In )
		p["out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )

	def testUndoSetFlags( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["p"] = Gaffer.IntPlug()

		self.assertFalse( s["n"]["user"]["p"].getFlags( Gaffer.Plug.Flags.ReadOnly ) )

		cs = GafferTest.CapturingSlot( s["n"].plugFlagsChangedSignal() )
		with Gaffer.UndoScope( s["n"]["user"]["p"].ancestor( Gaffer.ScriptNode ) ) :
			s["n"]["user"]["p"].setFlags( Gaffer.Plug.Flags.ReadOnly, True )
			self.assertTrue( s["n"]["user"]["p"].getFlags( Gaffer.Plug.Flags.ReadOnly ) )
			self.assertEqual( len( cs ), 1 )

		s.undo()
		self.assertFalse( s["n"]["user"]["p"].getFlags( Gaffer.Plug.Flags.ReadOnly ) )
		self.assertEqual( len( cs ), 2 )

		s.redo()
		self.assertTrue( s["n"]["user"]["p"].getFlags( Gaffer.Plug.Flags.ReadOnly ) )
		self.assertEqual( len( cs ), 3 )

	def testParentConnectionIgnoresOutOfOrderChildConnections( self ) :

		p1 = Gaffer.V2fPlug()
		p2 = Gaffer.V2fPlug()

		# p1.x -> p2.x, p1.y -> p2.y
		#
		# The parent should connect automatically too, because
		# the equivalent child connections have been performed
		# manually. By equivalent, we mean the same connections
		# which would have been made had we connected p1 -> p2.
		p2["x"].setInput( p1["x"] )
		p2["y"].setInput( p1["y"] )
		self.assertTrue( p2.getInput().isSame( p1 ) )

		p2.setInput( None )

		# p1.x -> p2.x, p1.x ->p2.y
		#
		# The parent should not connect automatically. Although
		# both children of p2 are driven from a child of p1,
		# they are not driven by the same plugs a call to
		# p2.setInput( p1 ) would have made.
		p2["x"].setInput( p1["x"] )
		p2["y"].setInput( p1["x"] )
		self.assertTrue( p2.getInput() is None )

		# p1.y -> p2.x, p1.x ->p2.y
		#
		# As above, parent should not connect automatically, because
		# the child connections are not equivalent to those which
		# would have been made by connecting the parent (order is wrong).
		p2["x"].setInput( p1["y"] )
		p2["y"].setInput( p1["x"] )
		self.assertTrue( p2.getInput() is None )

	def testIndirectInputChangedSignal( self ) :

		n = Gaffer.Node()
		n["p1"] = Gaffer.Plug()
		n["p2"] = Gaffer.Plug()
		n["p3"] = Gaffer.Plug()
		n["p4"] = Gaffer.Plug()

		cs = GafferTest.CapturingSlot( n.plugInputChangedSignal() )

		n["p4"].setInput( n["p3"] )
		self.assertEqual( len( cs ), 1 )
		self.assertEqual( cs[0], ( n["p4"], ) )

		del cs[:]

		# When the input to the input of a plug
		# changes, we emit inputChangedSignal()
		# for the whole chain, because the
		# effective source for all downstream
		# plugs has changed.

		n["p3"].setInput( n["p2"] )
		self.assertEqual( len( cs ), 2 )
		self.assertEqual( cs[0], ( n["p3"], ) )
		self.assertEqual( cs[1], ( n["p4"], ) )

		del cs[:]

		n["p2"].setInput( n["p1"] )
		self.assertEqual( len( cs ), 3 )
		self.assertEqual( cs[0], ( n["p2"], ) )
		self.assertEqual( cs[1], ( n["p3"], ) )
		self.assertEqual( cs[2], ( n["p4"], ) )

	def testChildPropagationToOutputPlugs( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["in"] = Gaffer.Plug()
		s["n"]["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		s["n"]["out"].setInput( s["n"]["in"] )

		def assertPreconditions() :

			self.assertEqual( s["n"]["in"].keys(), [] )
			self.assertEqual( s["n"]["out"].keys(), [] )
			self.assertTrue( s["n"]["out"].getInput().isSame( s["n"]["in"] ) )

		def assertPostconditions() :

			self.assertEqual( s["n"]["in"].keys(), [ "i", "f" ] )
			self.assertEqual( s["n"]["out"].keys(), [ "i", "f" ] )

			self.assertTrue( isinstance( s["n"]["out"]["i"], Gaffer.IntPlug ) )
			self.assertTrue( s["n"]["out"]["i"].direction(), Gaffer.Plug.Direction.Out )
			self.assertTrue( s["n"]["out"]["i"].getInput().isSame( s["n"]["in"]["i"] ) )
			self.assertTrue( s["n"]["out"].getInput().isSame( s["n"]["in"] ) )

			self.assertTrue( isinstance( s["n"]["out"]["f"], Gaffer.FloatPlug ) )
			self.assertTrue( s["n"]["out"]["f"].direction(), Gaffer.Plug.Direction.Out )
			self.assertTrue( s["n"]["out"]["f"].getInput().isSame( s["n"]["in"]["f"] ) )

		assertPreconditions()

		with Gaffer.UndoScope( s ) :

			s["n"]["in"].addChild( Gaffer.IntPlug( "i" ) )
			s["n"]["in"].addChild( Gaffer.FloatPlug( "f" ) )

		assertPostconditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostconditions()

	def testSerialisableFlagOnChildren( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["a"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		self.assertTrue( "a" in s2["n"]["user"] )

		s["n"]["user"].setFlags( Gaffer.Plug.Flags.Serialisable, False )

		s3 = Gaffer.ScriptNode()
		s3.execute( s.serialise() )
		self.assertFalse( "a" in s3["n"]["user"] )

	def testNullInputPropagatesToChildren( self ) :

		n = Gaffer.Node()
		n["user"]["c"] = Gaffer.Plug()
		n["user"]["c"]["o"] = Gaffer.IntPlug()
		n["user"]["c"]["i"] = Gaffer.IntPlug()

		n["user"]["c"]["i"].setInput( n["user"]["c"]["o"] )
		self.assertTrue( n["user"]["c"]["i"].getInput().isSame( n["user"]["c"]["o"] ) )

		n["user"]["c"].setInput( None )
		self.assertTrue( n["user"]["c"]["i"].getInput() is None )

	def testRemovePlugRemovesNestedInputs( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()

		s["n1"]["o"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )

		s["n2"]["c"] = Gaffer.Plug()
		s["n2"]["c"]["i"] = Gaffer.IntPlug()

		s["n2"]["c"]["i"].setInput( s["n1"]["o"] )
		self.failUnless( s["n2"]["c"]["i"].getInput().isSame(  s["n1"]["o"] ) )
		self.failUnless( s["n2"]["c"].getInput() is None )
		self.assertEqual( len( s["n1"]["o"].outputs() ), 1 )

		with Gaffer.UndoScope( s ) :
			del s["n2"]["c"]

		self.assertEqual( len( s["n1"]["o"].outputs() ), 0 )

		s.undo()

		self.failUnless( s["n2"]["c"]["i"].getInput().isSame(  s["n1"]["o"] ) )
		self.assertEqual( len( s["n1"]["o"].outputs() ), 1 )

if __name__ == "__main__":
	unittest.main()
