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
import GafferTest

class AnimationTest( GafferTest.TestCase ) :

	def testKey( self ) :

		k = Gaffer.Animation.Key()
		self.assertEqual( k.getTime(), 0 )
		self.assertEqual( k.getValue(), 0 )
		self.assertEqual( k.getInterpolation(), Gaffer.Animation.Interpolation.Linear )

		k = Gaffer.Animation.Key( 1, 2, Gaffer.Animation.Interpolation.Step )
		self.assertEqual( k.getTime(), 1 )
		self.assertEqual( k.getValue(), 2 )
		self.assertEqual( k.getInterpolation(), Gaffer.Animation.Interpolation.Step )

		self.assertEqual( k.parent(), None )

		k.setTime( 2 )
		k.setValue( 1 )
		k.setInterpolation( Gaffer.Animation.Interpolation.Linear )

		self.assertEqual( k.getTime(), 2 )
		self.assertEqual( k.getValue(), 1 )
		self.assertEqual( k.getInterpolation(), Gaffer.Animation.Interpolation.Linear )

	def testKeyRepr( self ) :

		k = Gaffer.Animation.Key()
		self.assertEqual( k, eval( repr( k ) ) )

		k = Gaffer.Animation.Key( 0, 1, Gaffer.Animation.Interpolation.Step )
		self.assertEqual( k, eval( repr( k ) ) )

	def testCanAnimate( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["b"] = Gaffer.BoolPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["s"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertTrue( Gaffer.Animation.canAnimate( s["n"]["user"]["f"] ) )
		self.assertTrue( Gaffer.Animation.canAnimate( s["n"]["user"]["i"] ) )
		self.assertTrue( Gaffer.Animation.canAnimate( s["n"]["user"]["b"] ) )
		self.assertFalse( Gaffer.Animation.canAnimate( s["n"]["user"]["s"] ) )

		# Can't key because it has an input.
		s["n"]["user"]["f"].setInput( s["n"]["user"]["i"] )
		self.assertFalse( Gaffer.Animation.canAnimate( s["n"]["user"]["f"] ) )

		# Can't key because there's no parent where we can
		# put the Animation node.
		n = Gaffer.Node()
		n["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertFalse( Gaffer.Animation.canAnimate( n["user"]["f"] ) )

	def testAcquire( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertFalse( Gaffer.Animation.isAnimated( s["n"]["user"]["f"] ) )
		self.assertTrue( Gaffer.Animation.canAnimate( s["n"]["user"]["f"] ) )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		self.assertTrue( isinstance( curve, Gaffer.Animation.CurvePlug ) )
		self.assertTrue( curve.isSame( Gaffer.Animation.acquire( s["n"]["user"]["f"] ) ) )
		self.assertTrue( curve.node().parent().isSame( s ) )

	def testAcquireSharesAnimationNodes( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = Gaffer.Node()
		s["n1"]["user"]["p1"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n1"]["user"]["p2"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["n2"] = Gaffer.Node()
		s["n2"]["user"]["p1"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n2"]["user"]["p2"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		n1p1 = Gaffer.Animation.acquire( s["n1"]["user"]["p1"] )
		n1p2 = Gaffer.Animation.acquire( s["n1"]["user"]["p2"] )

		n2p1 = Gaffer.Animation.acquire( s["n2"]["user"]["p1"] )
		n2p2 = Gaffer.Animation.acquire( s["n2"]["user"]["p2"] )

		self.assertTrue( n1p1.node().isSame( n1p2.node() ) )
		self.assertTrue( n2p1.node().isSame( n2p2.node() ) )
		self.assertFalse( n1p1.node().isSame( n2p1.node() ) )

	def testAddKey( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		key = Gaffer.Animation.Key( time = 10, value = 10 )
		self.assertFalse( curve.hasKey( key.getTime() ) )

		curve.addKey( key )
		self.assertTrue( curve.hasKey( key.getTime() ) )
		self.assertTrue( curve.getKey( key.getTime() ).isSame( key ) )
		self.assertTrue( key.parent().isSame( curve ) )

	def testAddKeyWithExistingKey( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k1 = Gaffer.Animation.Key( time = 1, value = 1 )
		k2 = Gaffer.Animation.Key( time = 1, value = 2 )

		curve.addKey( k1 )

		with Gaffer.UndoScope( s ) :
			curve.addKey( k2 )

		self.assertTrue( curve.getKey( 1 ).isSame( k2 ) )
		self.assertTrue( k2.parent().isSame( curve ) )
		self.assertTrue( k1.parent() is None )

		s.undo()

		self.assertTrue( curve.getKey( 1 ).isSame( k1 ) )
		self.assertTrue( k2.parent() is None )
		self.assertTrue( k1.parent().isSame( curve ) )

		s.redo()

		self.assertTrue( curve.getKey( 1 ).isSame( k2 ) )
		self.assertTrue( k2.parent().isSame( curve ) )
		self.assertTrue( k1.parent() is None )

	def testClosestKey( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		key0 = Gaffer.Animation.Key( 0, 0 )
		key1 = Gaffer.Animation.Key( 1, 1 )
		curve.addKey( key0 )
		curve.addKey( key1 )

		self.assertEqual( curve.closestKey( -1 ), key0 )
		self.assertEqual( curve.closestKey( -0.1 ), key0 )
		self.assertEqual( curve.closestKey( 0 ), key0 )
		self.assertEqual( curve.closestKey( 0.1 ), key0 )
		self.assertEqual( curve.closestKey( 0.49 ), key0 )
		self.assertEqual( curve.closestKey( 0.51 ), key1 )
		self.assertEqual( curve.closestKey( 0.75 ), key1 )
		self.assertEqual( curve.closestKey( 1 ), key1 )
		self.assertEqual( curve.closestKey( 1.1 ), key1 )

		self.assertEqual( curve.closestKey( -1, 1 ), key0 )
		self.assertEqual( curve.closestKey( -1, 0.9 ), None )

		self.assertEqual( curve.closestKey( 0.75, 1 ), key1 )
		self.assertEqual( curve.closestKey( 0.75, 0.2 ), None )

	def testRemoveKey( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		key = Gaffer.Animation.Key( time = 10, value = 10 )
		curve.addKey( key )
		self.assertTrue( curve.getKey( key.getTime() ).isSame( key ) )
		self.assertTrue( curve.closestKey( 0 ).isSame( key ) )
		self.assertTrue( key.parent().isSame( curve ) )

		curve.removeKey( key )
		self.assertEqual( curve.getKey( key.getTime() ), None )
		self.assertEqual( curve.closestKey( 0 ), None )
		self.assertEqual( key.parent(), None )

	def testSingleKey( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		curve.addKey( Gaffer.Animation.Key( 0, 1, Gaffer.Animation.Interpolation.Linear ) )

		with Gaffer.Context() as c :
			for t in range( -10, 10 ) :
				c.setTime( t )
				self.assertEqual( s["n"]["user"]["f"].getValue(), 1 )

	def testLinear( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		curve.addKey( Gaffer.Animation.Key( 0, 1, Gaffer.Animation.Interpolation.Linear ) )
		curve.addKey( Gaffer.Animation.Key( 1, 3, Gaffer.Animation.Interpolation.Linear ) )

		with Gaffer.Context() as c :
			for i in range( 0, 10 ) :
				c.setTime( i / 9.0 )
				self.assertAlmostEqual( s["n"]["user"]["f"].getValue(), 1 + c.getTime() * 2, 6 )

	def testStep( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		curve.addKey( Gaffer.Animation.Key( 0, 0 ) )
		curve.addKey( Gaffer.Animation.Key( 1, 1, Gaffer.Animation.Interpolation.Linear ) )
		curve.addKey( Gaffer.Animation.Key( 2, 2, Gaffer.Animation.Interpolation.Step ) )

		with Gaffer.Context() as c :
			# Linear interpolation from 0 to 1.
			for i in range( 0, 10 ) :
				c.setTime( i / 9.0 )
				self.assertAlmostEqual( s["n"]["user"]["f"].getValue(), c.getTime() )
			# Step interpolation from 1 to 2
			for i in range( 0, 10 ) :
				c.setTime( 1 + i / 10.0 )
				self.assertEqual( s["n"]["user"]["f"].getValue(), 1 )
			c.setTime( 2 )
			self.assertEqual( s["n"]["user"]["f"].getValue(), 2 )

	def testAffects( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		cs = GafferTest.CapturingSlot( s["n"].plugDirtiedSignal() )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		self.assertTrue( s["n"]["user"]["f"] in set( [ c[0] for c in cs ] ) )

		del cs[:]
		curve.addKey( Gaffer.Animation.Key( 1, 1 ) )
		self.assertTrue( s["n"]["user"]["f"] in set( [ c[0] for c in cs ] ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		curve.addKey( Gaffer.Animation.Key( 0, 0, Gaffer.Animation.Interpolation.Linear ) )
		curve.addKey( Gaffer.Animation.Key( 1, 1, Gaffer.Animation.Interpolation.Linear ) )

		def assertAnimation( script ) :

			curve = Gaffer.Animation.acquire( script["n"]["user"]["f"] )
			self.assertEqual( curve.getKey( 0 ),  Gaffer.Animation.Key( 0, 0, Gaffer.Animation.Interpolation.Linear ) )
			self.assertEqual( curve.getKey( 1 ),  Gaffer.Animation.Key( 1, 1, Gaffer.Animation.Interpolation.Linear ) )
			with Gaffer.Context() as c :
				for i in range( 0, 10 ) :
					c.setTime( i / 9.0 )
					self.assertAlmostEqual( script["n"]["user"]["f"].getValue(), c.getTime() )

		assertAnimation( s )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		assertAnimation( s2 )

	def testUndoAcquire( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertEqual( len( s.children( Gaffer.Node ) ), 1 )

		with Gaffer.UndoScope( s ) :
			curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
			self.assertEqual( len( s.children( Gaffer.Node ) ), 2 )

		s.undo()
		self.assertEqual( len( s.children( Gaffer.Node ) ), 1 )

		s.redo()
		self.assertEqual( len( s.children( Gaffer.Node ) ), 2 )

	def testUndoAddKey( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		self.assertFalse( curve.getKey( 0 ) )

		key1 = Gaffer.Animation.Key( 1, 0 )
		key2 = Gaffer.Animation.Key( 1, 1 )

		with Gaffer.UndoScope( s ) :
			curve.addKey( key1 )
			self.assertEqual( curve.getKey( 1 ), key1 )

		with Gaffer.UndoScope( s ) :
			curve.addKey( key2 )
			self.assertEqual( curve.getKey( 1 ), key2 )

		s.undo()
		self.assertEqual( curve.getKey( 1 ), key1 )

		s.undo()
		self.assertFalse( curve.getKey( 1 ) )

		s.redo()
		self.assertEqual( curve.getKey( 1 ), key1 )

		s.redo()
		self.assertEqual( curve.getKey( 1 ), key2 )

	def testUndoRemoveKey( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		key = Gaffer.Animation.Key( 0, 0 )
		curve.addKey( key )
		self.assertTrue( curve.getKey( key.getTime() ).isSame( key ) )

		with Gaffer.UndoScope( s ) :
			curve.removeKey( key )
			self.assertFalse( curve.hasKey( key.getTime() ) )
			self.assertEqual( key.parent(), None )

		s.undo()
		self.assertEqual( curve.getKey( key.getTime() ), key )
		self.assertTrue( key.parent().isSame( curve ) )

		s.redo()
		self.assertFalse( curve.hasKey( key.getTime() ) )
		self.assertEqual( key.parent(), None )

	def testUndoRemoveKeyTimeChangeOutsideCurve( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		self.assertFalse( curve.getKey( 0 ) )

		key1 = Gaffer.Animation.Key( 1, 0 )

		curve.addKey( key1 )
		self.assertEqual( curve.getKey( 1 ), key1 )

		with Gaffer.UndoScope( s ) :
			curve.removeKey( key1 )
			self.assertIsNone( curve.getKey( 1 ) )
			# NOTE : this operation is not captured by the undo system as key is not in curve
			key1.setTime( 2 )
			self.assertEqual( key1.getTime(), 2 )

		with Gaffer.UndoScope( s ) :
			curve.addKey( key1 )
			self.assertEqual( curve.getKey( 2 ), key1 )

		s.undo()
		self.assertIsNone( curve.getKey( 2 ) )

		# check that an exception is thrown on undo as setTime was not captured
		self.assertRaises( IECore.Exception, lambda : s.undo() )

		# check state is consistent with state before we tried to undo
		self.assertIsNone( curve.getKey( 2 ) )

		# check there is still an outstanding undo in queue
		self.assertTrue( s.undoAvailable() )

		# check that an exception is thrown again if we try to undo again
		self.assertRaises( IECore.Exception, lambda : s.undo() )

		# check state is consistent with state before we tried to undo
		self.assertIsNone( curve.getKey( 2 ) )

		# check there is still an outstanding undo in queue
		self.assertTrue( s.undoAvailable() )

		# check that we can redo the successful first undo
		s.redo()
		self.assertEqual( curve.getKey( 2 ), key1 )

	def testRedoAddKeyTimeChangeOutsideCurve( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		self.assertFalse( curve.getKey( 0 ) )

		key1 = Gaffer.Animation.Key( 1, 0 )

		with Gaffer.UndoScope( s ) :
			curve.addKey( key1 )
			self.assertEqual( curve.getKey( 1 ), key1 )

		s.undo()
		self.assertIsNone( curve.getKey( 1 ) )

		# NOTE : this operation is not captured by the undo system as key is not in curve
		key1.setTime( 2 )
		self.assertEqual( key1.getTime(), 2 )

		# check that an exception is thrown if we redo as setTime was not captured
		self.assertRaises( IECore.Exception, lambda : s.redo() )

		# check state is consistent with state before we tried to redo
		self.assertIsNone( curve.getKey( 1 ) )

		# check there is still an outstanding redo in queue
		self.assertTrue( s.redoAvailable() )

		# check that an exception is thrown again if we try to redo again
		self.assertRaises( IECore.Exception, lambda : s.redo() )

		# check state is consistent with state before we tried to undo
		self.assertIsNone( curve.getKey( 1 ) )

	def testNextAndPreviousKeys( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		key1 = Gaffer.Animation.Key( 0, 0 )
		key2 = Gaffer.Animation.Key( 1, 1 )
		key3 = Gaffer.Animation.Key( 2, 2 )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		curve.addKey( key1 )
		curve.addKey( key2 )
		curve.addKey( key3 )

		self.assertEqual( curve.nextKey( -1 ), key1 )
		self.assertEqual( curve.nextKey( 0 ), key2 )
		self.assertEqual( curve.nextKey( 0.5 ), key2 )
		self.assertEqual( curve.nextKey( 1 ), key3 )
		self.assertEqual( curve.nextKey( 1.5 ), key3 )
		self.assertFalse( curve.nextKey( 2 ) )

		self.assertFalse( curve.previousKey( -1 ) )
		self.assertFalse( curve.previousKey( 0 ) )
		self.assertEqual( curve.previousKey( 0.5 ), key1 )
		self.assertEqual( curve.previousKey( 1 ), key1 )
		self.assertEqual( curve.previousKey( 1.5 ), key2 )
		self.assertEqual( curve.previousKey( 2 ), key2 )
		self.assertEqual( curve.previousKey( 2.5 ), key3 )

	def testAnimationWithinAReference( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"] = GafferTest.AddNode()

		Gaffer.PlugAlgo.promote( s["b"]["n"]["op1"] )
		Gaffer.PlugAlgo.promote( s["b"]["n"]["sum"] )

		self.assertTrue( Gaffer.PlugAlgo.canPromote( s["b"]["n"]["op2"] ) )

		op2Curve = Gaffer.Animation.acquire( s["b"]["n"]["op2"] )

		# Cannot promote an animated plug, because it has an input.
		self.assertFalse( Gaffer.PlugAlgo.canPromote( s["b"]["n"]["op2"] ) )

		op2Curve.addKey( Gaffer.Animation.Key( 0, 0, Gaffer.Animation.Interpolation.Step ) )
		op2Curve.addKey( Gaffer.Animation.Key( 1, 1, Gaffer.Animation.Interpolation.Step ) )

		with Gaffer.Context() as c :
			self.assertEqual( s["b"]["sum"].getValue(), 0 )
			c.setTime( 1 )
			self.assertEqual( s["b"]["sum"].getValue(), 1 )

		fileName = self.temporaryDirectory() + "/reference.grf"
		s["b"].exportForReference( fileName )

		s["r"] = Gaffer.Reference()
		s["r"].load( fileName )

		with Gaffer.Context() as c :
			self.assertEqual( s["r"]["sum"].getValue(), 0 )
			c.setTime( 1 )
			self.assertEqual( s["r"]["sum"].getValue(), 1 )

		s["r"]["op1"].setValue( 2 )

		with Gaffer.Context() as c :
			self.assertEqual( s["r"]["sum"].getValue(), 2 )
			c.setTime( 1 )
			self.assertEqual( s["r"]["sum"].getValue(), 3 )

	def testModifyKey( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k = Gaffer.Animation.Key( time = 1, value = 2, interpolation = Gaffer.Animation.Interpolation.Linear )
		curve.addKey( k )
		curve.addKey( Gaffer.Animation.Key( 0.5 ) )

		self.assertTrue( curve.getKey( 1 ).isSame( k ) )

		cs = GafferTest.CapturingSlot( s["n"].plugDirtiedSignal() )
		with Gaffer.UndoScope( s ) :
			k.setTime( 0 )

		self.assertTrue( curve.getKey( 1 ) is None )
		self.assertTrue( curve.getKey( 0 ).isSame( k ) )
		self.assertEqual( k.getTime(), 0 )
		self.assertIn( s["n"]["op1"], { x[0] for x in cs } )

		del cs[:]
		s.undo()

		self.assertTrue( curve.getKey( 0 ) is None )
		self.assertTrue( curve.getKey( 1 ).isSame( k ) )
		self.assertEqual( k.getTime(), 1 )
		self.assertIn( s["n"]["op1"], { x[0] for x in cs } )

		del cs[:]
		s.redo()

		self.assertTrue( curve.getKey( 1 ) is None )
		self.assertTrue( curve.getKey( 0 ).isSame( k ) )
		self.assertEqual( k.getTime(), 0 )
		self.assertIn( s["n"]["op1"], { x[0] for x in cs } )

	def testModifyKeyReplacesExistingKey( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k1 = Gaffer.Animation.Key( time = 1 )
		k2 = Gaffer.Animation.Key( time = 2 )

		curve.addKey( k1 )
		curve.addKey( k2 )
		self.assertTrue( curve.getKey( 1 ).isSame( k1 ) )
		self.assertTrue( curve.getKey( 2 ).isSame( k2 ) )
		self.assertTrue( k1.parent().isSame( curve ) )
		self.assertTrue( k2.parent().isSame( curve ) )

		with Gaffer.UndoScope( s ) :
			k2.setTime( 1 )

		self.assertTrue( curve.getKey( 1 ).isSame( k2 ) )
		self.assertTrue( curve.getKey( 2 ) is None )
		self.assertTrue( k1.parent() is None )
		self.assertTrue( k2.parent().isSame( curve ) )

		s.undo()

		self.assertTrue( curve.getKey( 1 ).isSame( k1 ) )
		self.assertTrue( curve.getKey( 2 ).isSame( k2 ) )
		self.assertTrue( k1.parent().isSame( curve ) )
		self.assertTrue( k2.parent().isSame( curve ) )

		s.redo()

		self.assertTrue( curve.getKey( 1 ).isSame( k2 ) )
		self.assertTrue( curve.getKey( 2 ) is None )
		self.assertTrue( k1.parent() is None )
		self.assertTrue( k2.parent().isSame( curve ) )

	def testSerialisationRoundTripsExactly( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		context = Gaffer.Context()
		for frame in range( 0, 10000 ) :
			context.setFrame( frame )
			curve.addKey( Gaffer.Animation.Key( context.getTime(), context.getTime(), Gaffer.Animation.Interpolation.Linear ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		curve = Gaffer.Animation.acquire( s2["n"]["user"]["f"] )

		for frame in range( 0, 10000 ) :
			context.setFrame( frame )
			self.assertEqual(
				curve.getKey( context.getTime() ),
				Gaffer.Animation.Key( context.getTime(), context.getTime(), Gaffer.Animation.Interpolation.Linear )
			)

if __name__ == "__main__":
	unittest.main()
