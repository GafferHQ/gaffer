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

		import math
		import imath

		k = Gaffer.Animation.Key()
		self.assertEqual( k.getTime(), 0 )
		self.assertEqual( k.getValue(), 0 )
		self.assertEqual( k.getInterpolation(), Gaffer.Animation.defaultInterpolation() )
		self.assertEqual( k.getTieMode(), Gaffer.Animation.defaultTieMode() )
		self.assertFalse( k.isActive() )
		self.assertIsNone( k.parent() )
		ti = k.tangentIn()
		tf = k.tangentOut()
		self.assertEqual( ti.getSlope(), Gaffer.Animation.defaultSlope() )
		self.assertEqual( ti.getScale(), Gaffer.Animation.defaultScale() )
		self.assertEqual( tf.getSlope(), Gaffer.Animation.defaultSlope() )
		self.assertEqual( tf.getScale(), Gaffer.Animation.defaultScale() )
		self.assertEqual( ti.getPosition(), imath.V2d( k.getTime(), k.getValue() ) )
		self.assertEqual( tf.getPosition(), imath.V2d( k.getTime(), k.getValue() ) )
		self.assertEqual( ti.getPosition( relative = True ), imath.V2d( 0.0, 0.0 ) )
		self.assertEqual( tf.getPosition( relative = True ), imath.V2d( 0.0, 0.0 ) )

		a = math.pi
		b = math.e
		k = Gaffer.Animation.Key( a, b, Gaffer.Animation.Interpolation.Constant )
		self.assertFloat32Equal( k.getTime(), a )
		self.assertFloat32Equal( k.getValue(), b )
		self.assertEqual( k.getInterpolation(), Gaffer.Animation.Interpolation.Constant )
		self.assertFalse( k.isActive() )
		self.assertIsNone( k.parent() )
		ti = k.tangentIn()
		tf = k.tangentOut()
		self.assertEqual( ti.getPosition(), imath.V2d( k.getTime(), k.getValue() ) )
		self.assertEqual( tf.getPosition(), imath.V2d( k.getTime(), k.getValue() ) )
		self.assertEqual( ti.getPosition( relative = True ), imath.V2d( 0.0, 0.0 ) )
		self.assertEqual( tf.getPosition( relative = True ), imath.V2d( 0.0, 0.0 ) )

		k.setTime( b )
		k.setValue( a )
		k.setInterpolation( Gaffer.Animation.Interpolation.Linear )

		self.assertFloat32Equal( k.getTime(), b )
		self.assertFloat32Equal( k.getValue(), a )
		self.assertEqual( k.getInterpolation(), Gaffer.Animation.Interpolation.Linear )

	def testKeyRepr( self ) :

		def assertKeysEqual( k0, k1 ) :

			self.assertEqual( k0.getTime(), k1.getTime() )
			self.assertEqual( k0.getValue(), k1.getValue() )
			self.assertEqual( k0.getInterpolation(), k1.getInterpolation() )

		k = Gaffer.Animation.Key()
		assertKeysEqual( k, eval( repr( k ) ) )

		k = Gaffer.Animation.Key( 0, 1, Gaffer.Animation.Interpolation.Constant )
		assertKeysEqual( k, eval( repr( k ) ) )

		k = Gaffer.Animation.Key( 10, 4, Gaffer.Animation.Interpolation.ConstantNext )
		assertKeysEqual( k, eval( repr( k ) ) )

	def testKeyReprInfiniteSlope( self ) :

		pi = float( 'inf' )
		ni = float( '-inf' )
		k0 = Gaffer.Animation.Key( inSlope = pi, outSlope = ni )

		k1 = eval( repr( k0 ) )

		self.assertEqual(
			k0.tangentIn().getSlope(),
			k1.tangentIn().getSlope() )

		self.assertEqual(
			k0.tangentOut().getSlope(),
			k1.tangentOut().getSlope() )

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

		ck = curve.addKey( key )
		self.assertTrue( curve.hasKey( key.getTime() ) )
		self.assertTrue( curve.getKey( key.getTime() ).isSame( key ) )
		self.assertTrue( key.parent().isSame( curve ) )
		self.assertTrue( key.isActive() )
		self.assertIsNone( ck )

	def testAddKeyWithExistingKey( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k1 = Gaffer.Animation.Key( time = 1, value = 1 )
		k2 = Gaffer.Animation.Key( time = 1, value = 2 )

		curve.addKey( k1 )

		def assertPreconditions() :
			self.assertTrue( curve.getKey( 1 ).isSame( k1 ) )
			self.assertTrue( k2.parent() is None )
			self.assertTrue( k1.parent().isSame( curve ) )

		def assertPostconditions() :
			self.assertTrue( curve.getKey( 1 ).isSame( k2 ) )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertTrue( k1.parent() is None )

		assertPreconditions()
		with Gaffer.UndoScope( s ) :
			curve.addKey( k2 )
		assertPostconditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostconditions()

	def testAddKeyWithExistingKeyRemove( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k1 = Gaffer.Animation.Key( time = 1, value = 1 )
		k2 = Gaffer.Animation.Key( time = 1, value = 2 )
		k3 = Gaffer.Animation.Key( time = 1, value = 3 )

		curve.addKey( k1, removeActiveClashing = False )

		def assertConditionsA() :
			self.assertTrue( curve.getKey( 1 ).isSame( k1 ) )
			self.assertIsNone( k3.parent() )
			self.assertFalse( k3.isActive() )
			self.assertIsNone( k2.parent() )
			self.assertFalse( k2.isActive() )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertTrue( k1.isActive() )

		def assertConditionsB() :
			self.assertTrue( curve.getKey( 1 ).isSame( k2 ) )
			self.assertIsNone( k3.parent() )
			self.assertFalse( k3.isActive() )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertTrue( k2.isActive() )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertFalse( k1.isActive() )

		def assertConditionsC() :
			self.assertTrue( curve.getKey( 1 ).isSame( k3 ) )
			self.assertTrue( k3.parent().isSame( curve ) )
			self.assertTrue( k3.isActive() )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertFalse( k2.isActive() )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertFalse( k1.isActive() )

		assertConditionsA()
		with Gaffer.UndoScope( s ) :
			ck = curve.addKey( k2, removeActiveClashing = False )
			self.assertTrue( k1.isSame( ck ) )
		assertConditionsB()

		with Gaffer.UndoScope( s ) :
			ck = curve.addKey( k3, removeActiveClashing = False )
			self.assertTrue( k2.isSame( ck ) )
		assertConditionsC()

		s.undo()
		assertConditionsB()

		s.undo()
		assertConditionsA()

		s.redo()
		assertConditionsB()

		s.redo()
		assertConditionsC()

	def testAddInactiveKey( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k1 = Gaffer.Animation.Key( time = 1, value = 1 )
		k2 = Gaffer.Animation.Key( time = 1, value = 2 )

		curve.addKey( k1 )
		curve.addKey( k2, removeActiveClashing = False )

		def assertPreconditions() :
			self.assertTrue( curve.hasKey( 1 ) )
			self.assertTrue( curve.getKey( 1 ).isSame( k2 ) )
			self.assertIsNotNone( k2.parent() )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertIsNotNone( k1.parent() )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertFalse( k1.isActive() )
			self.assertTrue( k2.isActive() )

		def assertPostconditions() :
			self.assertTrue( curve.hasKey( 1 ) )
			self.assertTrue( curve.getKey( 1 ).isSame( k1 ) )
			self.assertIsNone( k2.parent() )
			self.assertIsNotNone( k1.parent() )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertTrue( k1.isActive() )
			self.assertFalse( k2.isActive() )
			self.assertTrue( s.undoAvailable() )

		# add key (which is already parented but inactive) should promote to active
		assertPreconditions()
		with Gaffer.UndoScope( s ) :
			ck = curve.addKey( k1 )
			self.assertTrue( k2.isSame( ck ) )
		assertPostconditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostconditions()

	def testAddInactiveKeyRemoveActiveClashingFalse( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k1 = Gaffer.Animation.Key( time = 1, value = 1 )
		k2 = Gaffer.Animation.Key( time = 1, value = 2 )

		curve.addKey( k1 )
		curve.addKey( k2, removeActiveClashing = False )

		def assertPreconditions() :
			self.assertTrue( curve.hasKey( 1 ) )
			self.assertTrue( curve.getKey( 1 ).isSame( k2 ) )
			self.assertIsNotNone( k2.parent() )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertIsNotNone( k1.parent() )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertFalse( k1.isActive() )
			self.assertTrue( k2.isActive() )

		def assertPostconditions() :
			self.assertTrue( curve.hasKey( 1 ) )
			self.assertTrue( curve.getKey( 1 ).isSame( k1 ) )
			self.assertIsNotNone( k2.parent() )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertIsNotNone( k1.parent() )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertTrue( k1.isActive() )
			self.assertFalse( k2.isActive() )
			self.assertTrue( s.undoAvailable() )

		# add key (which is already parented but inactive) should promote to active
		assertPreconditions()
		with Gaffer.UndoScope( s ) :
			ck = curve.addKey( k1, removeActiveClashing = False )
			self.assertTrue( k2.isSame( ck ) )
		assertPostconditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostconditions()

	def testAddKeySignals( self ) :

		ps = set()

		def added( curve, key ) :
			ps.add( key )

		def removed( curve, key ) :
			ps.remove( key )

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		c1 = curve.keyAddedSignal().connect( added )
		c2 = curve.keyRemovedSignal().connect( removed )

		k = Gaffer.Animation.Key( 0, 0 )

		def assertPreconditions() :
			self.assertNotIn( k, ps )

		def assertPostconditions() :
			self.assertIn( k, ps )

		assertPreconditions()
		with Gaffer.UndoScope( s ) :
			curve.addKey( k )
		assertPostconditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostconditions()

	def testRemoveKeySignals( self ) :

		ps = set()

		def added( curve, key ) :
			ps.add( key )

		def removed( curve, key ) :
			ps.remove( key )

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		c1 = curve.keyAddedSignal().connect( added )
		c2 = curve.keyRemovedSignal().connect( removed )

		k = Gaffer.Animation.Key( 0, 0 )

		curve.addKey( k )

		def assertPreconditions() :
			self.assertIn( k, ps )

		def assertPostconditions() :
			self.assertNotIn( k, ps )

		assertPreconditions()
		with Gaffer.UndoScope( s ) :
			curve.removeKey( k )
		assertPostconditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostconditions()

	def testGetKeyDirection( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f1"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["f2"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f1"] )

		# curve with no keys has no "In" and "Out" keys
		self.assertIsNone( curve.getKeyIn() )
		self.assertIsNone( curve.getKeyOut() )
		self.assertIsNone( curve.getKey( Gaffer.Animation.Direction.In ) )
		self.assertIsNone( curve.getKey( Gaffer.Animation.Direction.Out ) )

		# curve with single key. key is both "In" and "Out" key
		key = Gaffer.Animation.Key( 4, 5 )
		curve.addKey( key )
		self.assertIsNotNone( curve.getKeyIn() )
		self.assertTrue( curve.getKeyIn().isSame( key ) )
		self.assertIsNotNone( curve.getKeyOut() )
		self.assertTrue( curve.getKeyOut().isSame( key ) )
		self.assertIsNotNone( curve.getKey( Gaffer.Animation.Direction.In ) )
		self.assertTrue( curve.getKey( Gaffer.Animation.Direction.In ).isSame( key ) )
		self.assertIsNotNone( curve.getKey( Gaffer.Animation.Direction.Out ) )
		self.assertTrue( curve.getKey( Gaffer.Animation.Direction.Out ).isSame( key ) )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f2"] )

		# curve with multiple keys. "In" key has min time, "Out" key has max time
		keys = []
		import random
		r = random.Random( 0 )
		for i in range( 0, 11 ) :
			k = Gaffer.Animation.Key( r.uniform( -100.0, 100.0 ) )
			curve.addKey( k )
			keys.append( k )
		kmin = sorted( keys, key=lambda k : k.getTime(), reverse=False )[ 0 ]
		kmax = sorted( keys, key=lambda k : k.getTime(), reverse=True  )[ 0 ]
		self.assertIsNotNone( curve.getKeyIn() )
		self.assertTrue( curve.getKeyIn().isSame( kmin ) )
		self.assertIsNotNone( curve.getKey( Gaffer.Animation.Direction.In ) )
		self.assertTrue( curve.getKey( Gaffer.Animation.Direction.In ).isSame( kmin ) )
		self.assertIsNotNone( curve.getKeyOut() )
		self.assertTrue( curve.getKeyOut().isSame( kmax ) )
		self.assertTrue( curve.getKey( Gaffer.Animation.Direction.Out ).isSame( kmax ) )

	def testInsertKeyFirstNoValue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		time = 10
		self.assertFalse( curve.hasKey( time ) )
		value = curve.evaluate( time )
		k = curve.insertKey( time )
		self.assertIsNotNone( k )
		self.assertEqual( k.getValue(), value )
		self.assertTrue( curve.hasKey( time ) )

	def testInsertKeyBeforeFirstNoValue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		k = Gaffer.Animation.Key( 10, 2 )
		curve.addKey( k )

		time = 5
		self.assertFalse( curve.hasKey( time ) )
		value = curve.evaluate( time )
		k = curve.insertKey( time )
		self.assertIsNotNone( k )
		self.assertEqual( k.getValue(), value )
		self.assertTrue( curve.hasKey( time ) )

	def testInsertKeyAfterFinalNoValue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		k = Gaffer.Animation.Key( 10, 6 )
		curve.addKey( k )

		time = 15
		self.assertFalse( curve.hasKey( time ) )
		value = curve.evaluate( time )
		k = curve.insertKey( time )
		self.assertIsNotNone( k )
		self.assertEqual( k.getValue(), value )
		self.assertTrue( curve.hasKey( time ) )

	def testInsertKeyFirstValue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		time = 10
		value = 5

		def assertPreconditions() :
			self.assertFalse( curve.hasKey( time ) )

		def assertPostconditions() :
			self.assertEqual( k.getTime(), time )
			self.assertEqual( k.getValue(), value )
			self.assertEqual( k.getInterpolation(), Gaffer.Animation.defaultInterpolation() )
			self.assertIsNotNone( k.parent() )
			self.assertTrue( k.parent().isSame( curve ) )
			self.assertTrue( curve.hasKey( time ) )

		assertPreconditions()
		with Gaffer.UndoScope( s ) :
			k = curve.insertKey( time, value )
			self.assertIsNotNone( k )
		assertPostconditions()

		s.undo()
		assertPreconditions()
		self.assertIsNone( k.parent() )

		s.redo()
		assertPostconditions()

	def testInsertKeyBeforeFirstValue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		interpolation = Gaffer.Animation.Interpolation.Constant
		k = Gaffer.Animation.Key( 10, 5, interpolation )
		curve.addKey( k )

		time = 5
		value = 2

		def assertPreconditions() :
			self.assertFalse( curve.hasKey( time ) )

		def assertPostconditions() :
			self.assertEqual( ki.getTime(), time )
			self.assertEqual( ki.getValue(), value )
			self.assertEqual( ki.getInterpolation(), k.getInterpolation() )
			self.assertIsNotNone( ki.parent() )
			self.assertTrue( ki.parent().isSame( curve ) )
			self.assertTrue( curve.hasKey( time ) )

		assertPreconditions()
		with Gaffer.UndoScope( s ) :
			ki = curve.insertKey( time, value )
			self.assertIsNotNone( ki )
		assertPostconditions()

		s.undo()
		assertPreconditions()
		self.assertIsNone( ki.parent() )

		s.redo()
		assertPostconditions()

	def testInsertKeyAfterFinalValue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		interpolation = Gaffer.Animation.Interpolation.Constant
		k0 = Gaffer.Animation.Key( 0, 3 )
		k = Gaffer.Animation.Key( 10, 5, interpolation )
		curve.addKey( k0 )
		curve.addKey( k )

		time = 15
		value = 2

		def assertPreconditions() :
			self.assertFalse( curve.hasKey( time ) )

		def assertPostconditions() :
			self.assertEqual( ki.getTime(), time )
			self.assertEqual( ki.getValue(), value )
			self.assertEqual( ki.getInterpolation(), k.getInterpolation() )
			self.assertIsNotNone( ki.parent() )
			self.assertTrue( ki.parent().isSame( curve ) )
			self.assertTrue( curve.hasKey( time ) )

		assertPreconditions()
		with Gaffer.UndoScope( s ) :
			ki = curve.insertKey( time, value )
			self.assertIsNotNone( ki )
		assertPostconditions()

		s.undo()
		assertPreconditions()
		self.assertIsNone( ki.parent() )

		s.redo()
		assertPostconditions()

	def testInsertKeyExistingNoValue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		time = 10
		value = 2
		interpolation = Gaffer.Animation.Interpolation.Constant
		k = Gaffer.Animation.Key( time, value, interpolation )
		curve.addKey( k )

		self.assertTrue( curve.hasKey( time ) )
		self.assertTrue( curve.getKey( time ).isSame( k ) )

		with Gaffer.UndoScope( s ) :
			ki = curve.insertKey( time )

		self.assertIsNotNone( ki )
		self.assertTrue( k.isSame( ki ) )

		self.assertEqual( k.getValue(), value )
		self.assertEqual( k.getTime(), time )
		self.assertEqual( k.getInterpolation(), interpolation )
		self.assertIsNotNone( k.parent() )
		self.assertTrue( k.parent().isSame( curve ) )
		self.assertTrue( curve.hasKey( time ) )
		self.assertTrue( curve.getKey( time ).isSame( k ) )

		self.assertFalse( s.undoAvailable() )

	def testInsertKeyExistingValue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		time = 10
		value = 2
		interpolation = Gaffer.Animation.Interpolation.Constant
		k = Gaffer.Animation.Key( time, value, interpolation )
		curve.addKey( k )

		self.assertTrue( curve.hasKey( time ) )
		self.assertTrue( curve.getKey( time ).isSame( k ) )

		with Gaffer.UndoScope( s ) :
			ki = curve.insertKey( time, value )

		self.assertIsNotNone( ki )
		self.assertTrue( k.isSame( ki ) )

		self.assertEqual( k.getValue(), value )
		self.assertEqual( k.getTime(), time )
		self.assertEqual( k.getInterpolation(), interpolation )
		self.assertIsNotNone( k.parent() )
		self.assertTrue( k.parent().isSame( curve ) )
		self.assertTrue( curve.hasKey( time ) )
		self.assertTrue( curve.getKey( time ).isSame( k ) )

		self.assertFalse( s.undoAvailable() )

	def testInsertKeyExistingNewValue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		time = 10
		value = 2
		newValue = 10
		interpolation = Gaffer.Animation.Interpolation.Constant
		k = Gaffer.Animation.Key( time, value, interpolation )
		curve.addKey( k )

		def assertPreconditions() :
			self.assertTrue( curve.hasKey( time ) )
			self.assertTrue( curve.getKey( time ).isSame( k ) )
			self.assertEqual( k.getValue(), value )
			self.assertEqual( k.getTime(), time )
			self.assertEqual( k.getInterpolation(), interpolation )
			self.assertIsNotNone( k.parent() )
			self.assertTrue( k.parent().isSame( curve ) )

		def assertPostconditions() :
			self.assertEqual( k.getValue(), newValue )
			self.assertEqual( k.getTime(), time )
			self.assertEqual( k.getInterpolation(), interpolation )
			self.assertIsNotNone( k.parent() )
			self.assertTrue( k.parent().isSame( curve ) )
			self.assertTrue( curve.hasKey( time ) )
			self.assertTrue( curve.getKey( time ).isSame( k ) )
			self.assertTrue( s.undoAvailable() )

		assertPreconditions()
		with Gaffer.UndoScope( s ) :
			ki = curve.insertKey( time, newValue )
			self.assertIsNotNone( ki )
			self.assertTrue( k.isSame( ki ) )
		assertPostconditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostconditions()

	def testInsertKeyIntoSpanNoValue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		kl = Gaffer.Animation.Key( 10, 5, Gaffer.Animation.Interpolation.Constant )
		kh = Gaffer.Animation.Key( 20, 10, Gaffer.Animation.Interpolation.Linear )
		curve.addKey( kl )
		curve.addKey( kh )

		time = 15

		def assertPreconditions() :
			self.assertFalse( curve.hasKey( time ) )

		def assertPostconditions() :
			self.assertEqual( ki.getTime(), time )
			self.assertEqual( ki.getValue(), kl.getValue() )
			self.assertEqual( ki.getInterpolation(), kl.getInterpolation() )
			self.assertIsNotNone( ki.parent() )
			self.assertTrue( ki.parent().isSame( curve ) )
			self.assertTrue( curve.hasKey( time ) )

		assertPreconditions()
		with Gaffer.UndoScope( s ) :
			ki = curve.insertKey( time )
			self.assertIsNotNone( ki )
		assertPostconditions()

		s.undo()
		assertPreconditions()
		self.assertIsNone( ki.parent() )

		s.redo()
		assertPostconditions()

	def testInsertKeyIntoSpanValue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		kl = Gaffer.Animation.Key( 10, 5, Gaffer.Animation.Interpolation.Constant )
		kh = Gaffer.Animation.Key( 20, 10, Gaffer.Animation.Interpolation.Linear )
		curve.addKey( kl )
		curve.addKey( kh )

		time = 15
		value = 12

		def assertPreconditions() :
			self.assertFalse( curve.hasKey( time ) )

		def assertPostconditions() :
			self.assertEqual( ki.getTime(), time )
			self.assertEqual( ki.getValue(), value )
			self.assertEqual( ki.getInterpolation(), kl.getInterpolation() )
			self.assertIsNotNone( ki.parent() )
			self.assertTrue( ki.parent().isSame( curve ) )
			self.assertTrue( curve.hasKey( time ) )

		assertPreconditions()
		with Gaffer.UndoScope( s ) :
			ki = curve.insertKey( time, value )
			self.assertIsNotNone( ki )
		assertPostconditions()

		s.undo()
		assertPreconditions()
		self.assertIsNone( ki.parent() )

		s.redo()
		assertPostconditions()

	def testKeySetValue( self ) :

		import math

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		value = math.pi
		k = Gaffer.Animation.Key( 10, value )
		curve.addKey( k )

		self.assertTrue( k.isActive() )
		self.assertIsNotNone( k.parent() )
		self.assertTrue( k.parent().isSame( curve ) )
		self.assertFloat32Equal( k.getValue(), value )

		with Gaffer.UndoScope( s ) :
			k.setValue( value )

		self.assertFloat32Equal( k.getValue(), value )
		self.assertFalse( s.undoAvailable() )

		newValue = math.e
		with Gaffer.UndoScope( s ) :
			k.setValue( newValue )

		self.assertFloat32Equal( k.getValue(), newValue )
		self.assertTrue( s.undoAvailable() )

		s.undo()

		self.assertFloat32Equal( k.getValue(), value )
		self.assertTrue( s.redoAvailable() )

		s.redo()

		self.assertFloat32Equal( k.getValue(), newValue )

	def testKeySetValueSignal( self ) :

		ps = set()

		def changed( curve, key ) :
			ps.add( key )

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		c = curve.keyValueChangedSignal().connect( changed )

		k0 = Gaffer.Animation.Key( 0, 1 )
		k1 = Gaffer.Animation.Key( 2, 8 )

		curve.addKey( k0 )
		curve.addKey( k1 )

		value = 3
		k = Gaffer.Animation.Key( 1, value )
		curve.addKey( k )

		def assertPostconditions() :
			self.assertEqual( k.getValue(), newValue )
			self.assertTrue( s.undoAvailable() )
			self.assertIn( k, ps )
			self.assertNotIn( k0, ps )
			self.assertNotIn( k1, ps )

		newValue = 4
		with Gaffer.UndoScope( s ) :
			k.setValue( newValue )
		assertPostconditions()
		ps.clear()

		s.undo()
		self.assertEqual( k.getValue(), value )
		self.assertTrue( s.redoAvailable() )
		self.assertIn( k, ps )
		self.assertNotIn( k0, ps )
		self.assertNotIn( k1, ps )
		ps.clear()

		s.redo()
		assertPostconditions()

	def testKeySetInterpolation( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		interpolation = Gaffer.Animation.Interpolation.Constant
		k = Gaffer.Animation.Key( 10, 5, interpolation )
		curve.addKey( k )

		self.assertTrue( k.isActive() )
		self.assertIsNotNone( k.parent() )
		self.assertTrue( k.parent().isSame( curve ) )
		self.assertEqual( k.getInterpolation(), interpolation )

		with Gaffer.UndoScope( s ) :
			k.setInterpolation( interpolation )

		self.assertEqual( k.getInterpolation(), interpolation )
		self.assertFalse( s.undoAvailable() )

		newInterpolation = Gaffer.Animation.Interpolation.Linear
		with Gaffer.UndoScope( s ) :
			k.setInterpolation( newInterpolation )

		self.assertEqual( k.getInterpolation(), newInterpolation )
		self.assertTrue( s.undoAvailable() )

		s.undo()

		self.assertEqual( k.getInterpolation(), interpolation )
		self.assertTrue( s.redoAvailable() )

		s.redo()

		self.assertEqual( k.getInterpolation(), newInterpolation )

	def testKeySetInterpolationSignals( self ) :

		ps = set()

		def changed( curve, key ) :
			ps.add( key )

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		c = curve.keyInterpolationChangedSignal().connect( changed )

		k0 = Gaffer.Animation.Key( 0, 1 )
		k1 = Gaffer.Animation.Key( 12, 8 )

		curve.addKey( k0 )
		curve.addKey( k1 )

		interpolation = Gaffer.Animation.Interpolation.Constant
		k = Gaffer.Animation.Key( 10, 5, interpolation )
		curve.addKey( k )

		def assertPostconditions() :
			self.assertEqual( k.getInterpolation(), newInterpolation )
			self.assertTrue( s.undoAvailable() )
			self.assertIn( k, ps )
			self.assertNotIn( k0, ps )
			self.assertNotIn( k1, ps )

		self.assertTrue( k.isActive() )
		self.assertIsNotNone( k.parent() )
		self.assertTrue( k.parent().isSame( curve ) )
		self.assertEqual( k.getInterpolation(), interpolation )

		newInterpolation = Gaffer.Animation.Interpolation.Linear
		with Gaffer.UndoScope( s ) :
			k.setInterpolation( newInterpolation )
		assertPostconditions()
		ps.clear()

		s.undo()
		self.assertEqual( k.getInterpolation(), interpolation )
		self.assertTrue( s.redoAvailable() )
		self.assertIn( k, ps )
		self.assertNotIn( k0, ps )
		self.assertNotIn( k1, ps )
		ps.clear()

		s.redo()
		assertPostconditions()

	def testKeySetTime( self ) :

		import math

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		time = math.pi
		k = Gaffer.Animation.Key( time, 5 )
		curve.addKey( k )

		self.assertTrue( k.isActive() )
		self.assertIsNotNone( k.parent() )
		self.assertTrue( k.parent().isSame( curve ) )
		self.assertFloat32Equal( k.getTime(), time )

		with Gaffer.UndoScope( s ) :
			k.setTime( time )

		self.assertFloat32Equal( k.getTime(), time )
		self.assertFalse( s.undoAvailable() )

		newTime = math.e
		with Gaffer.UndoScope( s ) :
			k.setTime( newTime )

		self.assertFloat32Equal( k.getTime(), newTime )
		self.assertTrue( s.undoAvailable() )

		s.undo()

		self.assertFloat32Equal( k.getTime(), time )
		self.assertTrue( s.redoAvailable() )

		s.redo()

		self.assertFloat32Equal( k.getTime(), newTime )

	def testKeySetTimeSignals( self ) :

		ps = set()

		def changed( curve, key ) :
			ps.add( key )

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		c = curve.keyTimeChangedSignal().connect( changed )

		k0 = Gaffer.Animation.Key( 0, 1 )
		k1 = Gaffer.Animation.Key( 12, 8 )

		curve.addKey( k0 )
		curve.addKey( k1 )

		time = 10
		k = Gaffer.Animation.Key( 10, 5 )
		curve.addKey( k )

		self.assertTrue( k.isActive() )
		self.assertIsNotNone( k.parent() )
		self.assertTrue( k.parent().isSame( curve ) )
		self.assertEqual( k.getTime(), time )

		def assertPostconditions() :
			self.assertEqual( k.getTime(), newTime )
			self.assertTrue( s.undoAvailable() )
			self.assertIn( k, ps )
			self.assertNotIn( k0, ps )
			self.assertNotIn( k1, ps )

		newTime = 12
		with Gaffer.UndoScope( s ) :
			k.setTime( newTime )
		assertPostconditions()
		ps.clear()

		s.undo()
		self.assertEqual( k.getTime(), time )
		self.assertTrue( s.redoAvailable() )
		self.assertIn( k, ps )
		self.assertNotIn( k0, ps )
		self.assertNotIn( k1, ps )
		ps.clear()

		s.redo()
		assertPostconditions()

	def testKeySetTieMode( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		tieMode = Gaffer.Animation.TieMode.Manual
		k = Gaffer.Animation.Key( 10, 5, tieMode = tieMode )
		curve.addKey( k )

		self.assertTrue( k.isActive() )
		self.assertIsNotNone( k.parent() )
		self.assertTrue( k.parent().isSame( curve ) )
		self.assertEqual( k.getTieMode(), tieMode )

		with Gaffer.UndoScope( s ) :
			k.setTieMode( tieMode )

		self.assertEqual( k.getTieMode(), tieMode )
		self.assertFalse( s.undoAvailable() )

		newTieMode = Gaffer.Animation.TieMode.Slope
		with Gaffer.UndoScope( s ) :
			k.setTieMode( newTieMode )

		self.assertEqual( k.getTieMode(), newTieMode )
		self.assertTrue( s.undoAvailable() )

		s.undo()

		self.assertEqual( k.getTieMode(), tieMode )
		self.assertTrue( s.redoAvailable() )

		s.redo()

		self.assertEqual( k.getTieMode(), newTieMode )

	def testKeySetTieModeSlopeInCurve( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		tieMode = Gaffer.Animation.TieMode.Manual
		interpolation = Gaffer.Animation.Interpolation.Cubic
		inSlope = 20
		outSlope = 50
		k = Gaffer.Animation.Key( 10, 5, interpolation, inSlope = inSlope, outSlope = outSlope, tieMode = tieMode )
		curve.addKey( k )

		k0 = Gaffer.Animation.Key( 0, 1, interpolation )
		k1 = Gaffer.Animation.Key( 12, 8, interpolation )

		curve.addKey( k0 )
		curve.addKey( k1 )

		ti = k.tangentIn()
		tf = k.tangentOut()

		def assertPreconditions() :
			self.assertEqual( k.getTieMode(), tieMode )
			self.assertFalse( ti.slopeIsConstrained() )
			self.assertFalse( tf.slopeIsConstrained() )
			self.assertEqual( ti.getSlope(), inSlope )
			self.assertEqual( tf.getSlope(), outSlope )
			self.assertNotEqual( ti.getSlope(), tf.getSlope() )

		def assertPostconditions() :
			self.assertEqual( k.getTieMode(), newTieMode )
			self.assertFalse( ti.slopeIsConstrained() )
			self.assertFalse( tf.slopeIsConstrained() )
			self.assertEqual( ti.getSlope(), tf.getSlope() )
			self.assertTrue( s.undoAvailable() )

		newTieMode = Gaffer.Animation.TieMode.Slope
		assertPreconditions()
		with Gaffer.UndoScope( s ) :
			k.setTieMode( newTieMode )
		assertPostconditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostconditions()

	def testKeySetTieModeSignals( self ) :

		ps = set()

		def changed( curve, key ) :
			ps.add( key )

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		c = curve.keyTieModeChangedSignal().connect( changed )

		k0 = Gaffer.Animation.Key( 0, 1 )
		k1 = Gaffer.Animation.Key( 12, 8 )

		curve.addKey( k0 )
		curve.addKey( k1 )

		tieMode = Gaffer.Animation.TieMode.Manual
		k = Gaffer.Animation.Key( 10, 5, tieMode = tieMode )
		curve.addKey( k )

		self.assertTrue( k.isActive() )
		self.assertIsNotNone( k.parent() )
		self.assertTrue( k.parent().isSame( curve ) )
		self.assertEqual( k.getTieMode(), tieMode )

		def assertPostconditions() :
			self.assertEqual( k.getTieMode(), newTieMode )
			self.assertTrue( s.undoAvailable() )
			self.assertIn( k, ps )
			self.assertNotIn( k0, ps )
			self.assertNotIn( k1, ps )

		newTieMode = Gaffer.Animation.TieMode.Slope
		with Gaffer.UndoScope( s ) :
			k.setTieMode( newTieMode )
		assertPostconditions()
		ps.clear()

		s.undo()
		self.assertEqual( k.getTieMode(), tieMode )
		self.assertTrue( s.redoAvailable() )
		self.assertIn( k, ps )
		self.assertNotIn( k0, ps )
		self.assertNotIn( k1, ps )
		ps.clear()

		s.redo()
		assertPostconditions()

	def testKeyTangentSlopeIsConstrained( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k = Gaffer.Animation.Key( time = 0, interpolation = Gaffer.Animation.Interpolation.Linear )

		# unparented key's tangents do not have constrained slopes
		self.assertFalse( k.tangentIn().slopeIsConstrained() )
		self.assertFalse( k.tangentOut().slopeIsConstrained() )

		# add key to empty curve
		curve.addKey( k )

		# both tangents protrude from start/end of curve so slopes are unconstrained
		self.assertFalse( k.tangentIn().slopeIsConstrained() )
		self.assertFalse( k.tangentOut().slopeIsConstrained() )

		# add key with same time so original key becomes inactive (tangent slopes remain unconstrained)
		kd = Gaffer.Animation.Key( time = 0, interpolation = Gaffer.Animation.Interpolation.Linear )
		curve.addKey( kd, removeActiveClashing = False )
		self.assertTrue( kd.isActive() )
		self.assertFalse( k.isActive() )
		self.assertIsNotNone( k.parent() )
		self.assertTrue( k.parent().isSame( curve ) )
		self.assertFalse( k.tangentIn().slopeIsConstrained() )
		self.assertFalse( k.tangentOut().slopeIsConstrained() )

		# remove duplicate key so key becomes active again
		curve.removeKey( kd )
		self.assertTrue( k.isActive() )
		self.assertIsNotNone( k.parent() )
		self.assertTrue( k.parent().isSame( curve ) )

		# add previous key so that in tangent no longer protrudes from start of curve
		kp = Gaffer.Animation.Key( time = -1, interpolation = Gaffer.Animation.Interpolation.Linear )
		curve.addKey( kp )
		self.assertTrue( k.tangentIn().slopeIsConstrained() )
		self.assertFalse( k.tangentOut().slopeIsConstrained() )
		curve.removeKey( kp )

		# add next key so that out tangent no longer protrudes from end of curve
		kn = Gaffer.Animation.Key( time = 1, interpolation = Gaffer.Animation.Interpolation.Linear )
		curve.addKey( kn )
		self.assertFalse( k.tangentIn().slopeIsConstrained() )
		self.assertTrue( k.tangentOut().slopeIsConstrained() )
		curve.removeKey( kn )

		# add both prev and next keys
		curve.addKey( kp )
		curve.addKey( kn )
		self.assertTrue( k.tangentIn().slopeIsConstrained() )
		self.assertTrue( k.tangentOut().slopeIsConstrained() )

		# set interpolation mode of prev key to cubic
		kp.setInterpolation( Gaffer.Animation.Interpolation.Cubic )
		self.assertFalse( k.tangentIn().slopeIsConstrained() )
		self.assertTrue( k.tangentOut().slopeIsConstrained() )
		kp.setInterpolation( Gaffer.Animation.Interpolation.Linear )

		# set interpolation mode of key to cubic
		k.setInterpolation( Gaffer.Animation.Interpolation.Cubic )
		self.assertTrue( k.tangentIn().slopeIsConstrained() )
		self.assertFalse( k.tangentOut().slopeIsConstrained() )
		k.setInterpolation( Gaffer.Animation.Interpolation.Linear )

		# set interpolation mode of prev key and key to cubic
		kp.setInterpolation( Gaffer.Animation.Interpolation.Cubic )
		k.setInterpolation( Gaffer.Animation.Interpolation.Cubic )
		self.assertFalse( k.tangentIn().slopeIsConstrained() )
		self.assertFalse( k.tangentOut().slopeIsConstrained() )

	def testKeyTangentScaleIsConstrained( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k = Gaffer.Animation.Key( time = 0, interpolation = Gaffer.Animation.Interpolation.Linear )

		# unparented key's tangents do not have constrained scales
		self.assertFalse( k.tangentIn().scaleIsConstrained() )
		self.assertFalse( k.tangentOut().scaleIsConstrained() )

		# add key to empty curve
		curve.addKey( k )

		# both tangents protrude from start/end of curve so scales are unconstrained
		self.assertFalse( k.tangentIn().scaleIsConstrained() )
		self.assertFalse( k.tangentOut().scaleIsConstrained() )

		# add duplicate key with same time so original key becomes inactive (tangent scales remain unconstrained)
		kd = Gaffer.Animation.Key( time = 0, interpolation = Gaffer.Animation.Interpolation.Linear )
		curve.addKey( kd, removeActiveClashing = False )
		self.assertTrue( kd.isActive() )
		self.assertFalse( k.isActive() )
		self.assertIsNotNone( k.parent() )
		self.assertTrue( k.parent().isSame( curve ) )
		self.assertFalse( k.tangentIn().scaleIsConstrained() )
		self.assertFalse( k.tangentOut().scaleIsConstrained() )

		# remove duplicate key so key becomes active again
		curve.removeKey( kd )
		self.assertTrue( k.isActive() )
		self.assertIsNotNone( k.parent() )
		self.assertTrue( k.parent().isSame( curve ) )

		# add previous key so that in tangent no longer protrudes from start of curve
		kp = Gaffer.Animation.Key( time = -1, interpolation = Gaffer.Animation.Interpolation.Linear )
		curve.addKey( kp )
		self.assertTrue( k.tangentIn().scaleIsConstrained() )
		self.assertFalse( k.tangentOut().scaleIsConstrained() )
		curve.removeKey( kp )

		# add next key so that out tangent no longer protrudes from end of curve
		kn = Gaffer.Animation.Key( time = 1, interpolation = Gaffer.Animation.Interpolation.Linear )
		curve.addKey( kn )
		self.assertFalse( k.tangentIn().scaleIsConstrained() )
		self.assertTrue( k.tangentOut().scaleIsConstrained() )
		curve.removeKey( kn )

		# add both prev and next keys
		curve.addKey( kp )
		curve.addKey( kn )
		self.assertTrue( k.tangentIn().scaleIsConstrained() )
		self.assertTrue( k.tangentOut().scaleIsConstrained() )

		# set interpolation mode of prev key to bezier
		kp.setInterpolation( Gaffer.Animation.Interpolation.Bezier )
		self.assertFalse( k.tangentIn().scaleIsConstrained() )
		self.assertTrue( k.tangentOut().scaleIsConstrained() )
		kp.setInterpolation( Gaffer.Animation.Interpolation.Linear )

		# set interpolation mode of key to bezier
		k.setInterpolation( Gaffer.Animation.Interpolation.Bezier )
		self.assertTrue( k.tangentIn().scaleIsConstrained() )
		self.assertFalse( k.tangentOut().scaleIsConstrained() )
		k.setInterpolation( Gaffer.Animation.Interpolation.Linear )

		# set interpolation mode of prev key and key to bezier
		kp.setInterpolation( Gaffer.Animation.Interpolation.Bezier )
		k.setInterpolation( Gaffer.Animation.Interpolation.Bezier )
		self.assertFalse( k.tangentIn().scaleIsConstrained() )
		self.assertFalse( k.tangentOut().scaleIsConstrained() )

	def testKeyTangentSetSlope( self ) :

		# test set slope with tie mode manual
		k = Gaffer.Animation.Key( tieMode = Gaffer.Animation.TieMode.Manual )
		ti = k.tangentIn()
		tf = k.tangentOut()

		step = 10
		for slope in range( -100, 100 + step, step ) :
			ti.setSlope( slope )
			tf.setSlope( slope )
			self.assertEqual( ti.getSlope(), slope )
			self.assertEqual( tf.getSlope(), slope )

		# test set slope with tie mode slope
		k = Gaffer.Animation.Key( tieMode = Gaffer.Animation.TieMode.Slope )
		ti = k.tangentIn()
		tf = k.tangentOut()

		step = 10
		for slope in range( -100, 100 + step, step ) :
			ti.setSlope( slope )
			self.assertEqual( ti.getSlope(), slope )
			self.assertEqual( tf.getSlope(), slope )

		step = 10
		for slope in range( -100, 100 + step, step ) :
			tf.setSlope( slope )
			self.assertEqual( tf.getSlope(), slope )
			self.assertEqual( ti.getSlope(), slope )

		# test set slope with tie mode slope and scale
		k = Gaffer.Animation.Key( tieMode = Gaffer.Animation.TieMode.Scale )
		ti = k.tangentIn()
		tf = k.tangentOut()

		step = 10
		for slope in range( -100, 100 + step, step ) :
			ti.setSlope( slope )
			self.assertEqual( ti.getSlope(), slope )
			self.assertEqual( tf.getSlope(), slope )

		step = 10
		for slope in range( -100, 100 + step, step ) :
			tf.setSlope( slope )
			self.assertEqual( tf.getSlope(), slope )
			self.assertEqual( ti.getSlope(), slope )

	def testKeyTangentSetSlopeClampsScale( self ) :

		import math

		# test set slope clamps scale, initial slopes set to +/- infinity with infinite scale
		k = Gaffer.Animation.Key(
			inSlope = float( 'inf' ), inScale = float( 'inf' ),
			outSlope = float( '-inf' ), outScale = float( 'inf' ),
			tieMode = Gaffer.Animation.TieMode.Manual )
		ti = k.tangentIn()
		tf = k.tangentOut()

		self.assertEqual( ti.getSlope(), float( 'inf' ) )
		self.assertEqual( ti.getScale(), float( 'inf' ) )
		self.assertEqual( tf.getSlope(), float( '-inf' ) )
		self.assertEqual( tf.getScale(), float( 'inf' ) )

		# set slope to progressively lower absolute values checking that the scale is clamped
		# NOTE : important that slopes less than 1 are tested
		for i in reversed( range( 0, 11 ) ) :
			slope = i / 5.0
			ti.setSlope( slope )
			self.assertAlmostEqual( ti.getScale(), math.sqrt( slope * slope + 1.0 ), places = 9 )

		# set slope to progressively lower absolute values checking that the scale is clamped
		# NOTE : important that slopes less than 1 are tested
		for i in reversed( range( 0, 11 ) ) :
			slope = i / -5.0
			tf.setSlope( slope )
			self.assertAlmostEqual( tf.getScale(), math.sqrt( slope * slope + 1.0 ), places = 9 )

	def testKeyTangentSetSlopeInCurve( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k0 = Gaffer.Animation.Key(
			time = -1,
			interpolation = Gaffer.Animation.Interpolation.Linear )
		k1 = Gaffer.Animation.Key(
			time = 1,
			interpolation = Gaffer.Animation.Interpolation.Linear )
		curve.addKey( k0 )
		curve.addKey( k1 )

		# create key (manual tie mode) and get its tangents
		k = Gaffer.Animation.Key(
			time = 0,
			interpolation = Gaffer.Animation.Interpolation.Linear,
			tieMode = Gaffer.Animation.TieMode.Manual )
		ti = k.tangentIn()
		tf = k.tangentOut()

		# set tangent slopes
		ti.setSlope( 30 )
		self.assertEqual( ti.getSlope(), 30 )
		tf.setSlope( 45 )
		self.assertEqual( tf.getSlope(), 45 )

		# add key to curve
		curve.addKey( k )

		# slope of both tangents should now be constrained
		self.assertTrue( ti.slopeIsConstrained() )
		self.assertTrue( tf.slopeIsConstrained() )
		tis = ti.getSlope()
		tfs = tf.getSlope()

		# remove key from curve
		curve.removeKey( k )

		# tangent slope should now revert to values before they became constrained
		self.assertEqual( ti.getSlope(), 30 )
		self.assertEqual( tf.getSlope(), 45 )

		# add key back to curve
		curve.addKey( k )

		# now set tieMode of key to Slope
		k.setTieMode( Gaffer.Animation.TieMode.Slope )

		# slope of both tangents should now be effective as both tangent's slope is constrained
		self.assertTrue( ti.slopeIsConstrained() )
		self.assertEqual( ti.getSlope(), tis )
		self.assertTrue( tf.slopeIsConstrained() )
		self.assertEqual( tf.getSlope(), tfs )

		# remove key from curve
		curve.removeKey( k )

		# tangent slopes should be tied and therefore have same magnitude
		self.assertEqual( ti.getSlope(), tf.getSlope() )
		tiedSlope = ti.getSlope()

		# add key back to curve
		curve.addKey( k )

		# try to set tangent slope (should have no affect as slopes are constrained)
		self.assertTrue( ti.slopeIsConstrained() )
		ti.setSlope( 10 )
		self.assertEqual( ti.getSlope(), tis )
		self.assertTrue( tf.slopeIsConstrained() )
		tf.setSlope( 35 )
		self.assertEqual( tf.getSlope(), tfs )

		# remove key from curve
		curve.removeKey( k )

		# tangent slopes should still be tied and same as before they became constrained
		self.assertEqual( ti.getSlope(), tiedSlope )
		self.assertEqual( tf.getSlope(), tiedSlope )

	def testKeyTangentSetScale( self ) :

		import math

		k = Gaffer.Animation.Key( time = 0, inSlope = 0, outSlope = 0, tieMode = Gaffer.Animation.TieMode.Manual )
		ti = k.tangentIn()
		tf = k.tangentOut()

		# test set in tangent scale in range [0,1] with slope equal to zero (no clamp)
		for i in range( 0, 11 ) :
			scale = i / 10.0
			ti.setScale( scale )
			self.assertEqual( ti.getScale(), scale )

		# test set out tangent scale in range [0,1] with slope equal to zero (no clamp)
		for i in range( 0, 11 ) :
			scale = i / 10.0
			tf.setScale( scale )
			self.assertEqual( tf.getScale(), scale )

		# test set negative in tangent scale
		for i in range( 0, 11 ) :
			scale = i / -10.0
			ti.setScale( scale )
			self.assertEqual( ti.getScale(), 0.0 )

		# test set negative out tangent scale
		for i in range( 0, 11 ) :
			scale = i / -10.0
			tf.setScale( scale )
			self.assertEqual( tf.getScale(), 0.0 )

		# test set in tangent scale clamps based on existing slope
		for i in range( 0, 11 ) :
			slope = i / 5.0
			ti.setScale( 0 )
			ti.setSlope( slope )
			ti.setScale( float( 'inf' ) )
			self.assertEqual( ti.getSlope(), slope )
			self.assertAlmostEqual( ti.getScale(), math.sqrt( slope * slope + 1.0 ), places = 9 )

		# test set out tangent scale clamps based on existing slope
		for i in range( 0, 11 ) :
			slope = i / 5.0
			tf.setScale( 0 )
			tf.setSlope( slope )
			tf.setScale( float( 'inf' ) )
			self.assertEqual( tf.getSlope(), slope )
			self.assertAlmostEqual( tf.getScale(), math.sqrt( slope * slope + 1.0 ), places = 9 )

	def testKeyTangentSetScaleInCurve( self ) :

		import math

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k0 = Gaffer.Animation.Key(
			time = -1,
			interpolation = Gaffer.Animation.Interpolation.Linear )
		k1 = Gaffer.Animation.Key(
			time = 1,
			interpolation = Gaffer.Animation.Interpolation.Linear )
		curve.addKey( k0 )
		curve.addKey( k1 )

		# create key (manual tie mode) and get its tangents
		k = Gaffer.Animation.Key(
			time = 0,
			interpolation = Gaffer.Animation.Interpolation.Linear,
			tieMode = Gaffer.Animation.TieMode.Manual )
		ti = k.tangentIn()
		tf = k.tangentOut()

		# set tangent scales
		ti.setScale( 0.2 )
		self.assertEqual( ti.getScale(), 0.2 )
		tf.setScale( 0.3 )
		self.assertEqual( tf.getScale(), 0.3 )

		# add key to curve
		curve.addKey( k )

		# scale of both tangents should now be constrained.
		self.assertTrue( ti.scaleIsConstrained() )
		self.assertTrue( tf.scaleIsConstrained() )
		tis = ti.getScale()
		tfs = tf.getScale()

		# remove key from curve
		curve.removeKey( k )

		# tangent scale should now revert to values before they became constrained
		self.assertEqual( ti.getScale(), 0.2 )
		self.assertEqual( tf.getScale(), 0.3 )

		# add key back to curve
		curve.addKey( k )

		# now set tieMode of key to include scale
		k.setTieMode( Gaffer.Animation.TieMode.Scale )

		# scale of both tangents should now be constrained
		self.assertTrue( ti.scaleIsConstrained() )
		self.assertEqual( ti.getScale(), tis )
		self.assertTrue( tf.scaleIsConstrained() )
		self.assertEqual( tf.getScale(), tfs )

		# remove key from curve
		curve.removeKey( k )

		# tangent should have same scales (tying scale keeps them in proportion)
		self.assertEqual( ti.getScale(), 0.2 )
		self.assertEqual( tf.getScale(), 0.3 )

		# add key back to curve
		curve.addKey( k )

		# try setting tangent scales (whilst key in curve and scales constrained) should have no effect
		self.assertTrue( ti.scaleIsConstrained() )
		ti.setScale( 0.6 )
		self.assertEqual( ti.getScale(), tis )
		self.assertTrue( tf.scaleIsConstrained() )
		tf.setScale( 0.7 )
		self.assertEqual( tf.getScale(), tfs )

		# remove key from curve
		curve.removeKey( k )

		# tangent should be same as before they became constrained (setting scale whilst key in curve and scales constrained has no affect)
		self.assertEqual( ti.getScale(), 0.2 )
		self.assertEqual( tf.getScale(), 0.3 )

		# try setting tangent scales (whilst key not in curve) should have effect of keeping in proportion
		self.assertFalse( ti.scaleIsConstrained() )
		ti.setScale( 0.4 )
		self.assertEqual( ti.getScale(), 0.4 )
		self.assertEqual( tf.getScale(), 0.6 )
		self.assertFalse( tf.scaleIsConstrained() )
		tf.setScale( 0.75 )
		self.assertEqual( tf.getScale(), 0.75 )
		self.assertEqual( ti.getScale(), 0.5 )

	def testKeyTangentSetPosition( self ) :

		import math
		import imath

		k = Gaffer.Animation.Key( time = 13, value = 5.4, tieMode = Gaffer.Animation.TieMode.Manual )
		ti = k.tangentIn()
		tf = k.tangentOut()

		# set relative position of in tangent (no effect as key not parented)
		ti.setPosition( imath.V2d( 1, 1 ), relative = True )
		self.assertEqual( ti.getSlope(), Gaffer.Animation.defaultSlope() )
		self.assertEqual( ti.getScale(), Gaffer.Animation.defaultScale() )
		self.assertEqual( ti.getPosition( relative = True ), imath.V2d( 0, 0 ) )
		self.assertEqual( ti.getPosition(), imath.V2d( k.getTime(), k.getValue() ) )

		# set relative position of out tangent (no effect as key not parented)
		tf.setPosition( imath.V2d( 1, 1 ) )
		self.assertEqual( tf.getSlope(), Gaffer.Animation.defaultSlope() )
		self.assertEqual( tf.getScale(), Gaffer.Animation.defaultScale() )
		self.assertEqual( tf.getPosition( relative = True ), imath.V2d( 0, 0 ) )
		self.assertEqual( tf.getPosition(), imath.V2d( k.getTime(), k.getValue() ) )

		# set slope and scale of in tangent
		ti.setSlope( 3 )
		ti.setScale( 1.1 )
		self.assertEqual( ti.getSlope(), 3 )
		self.assertEqual( ti.getScale(), 1.1 )

		# set slope and scale of out tangent
		tf.setSlope( 2 )
		tf.setScale( 1 )
		self.assertEqual( tf.getSlope(), 2 )
		self.assertEqual( tf.getScale(), 1 )

		# set relative position of in tangent (no effect as key not parented)
		ti.setPosition( imath.V2d( 1, 1 ), relative = True )
		self.assertEqual( ti.getSlope(), 3 )
		self.assertEqual( ti.getScale(), 1.1 )
		self.assertEqual( ti.getPosition( relative = True ), imath.V2d( 0, 0 ) )
		self.assertEqual( ti.getPosition( relative = False ), imath.V2d( k.getTime(), k.getValue() ) )

		# set absolute position of in tangent (no effect as key not parented)
		ti.setPosition( imath.V2d( 1, 1 ) )
		self.assertEqual( ti.getSlope(), 3 )
		self.assertEqual( ti.getScale(), 1.1 )
		self.assertEqual( ti.getPosition( relative = True ), imath.V2d( 0, 0 ) )
		self.assertEqual( ti.getPosition( relative = False ), imath.V2d( k.getTime(), k.getValue() ) )

		# set relative position of out tangent (no effect as key not parented)
		tf.setPosition( imath.V2d( 1, 1 ), relative = True )
		self.assertEqual( tf.getSlope(), 2 )
		self.assertEqual( tf.getScale(), 1 )
		self.assertEqual( tf.getPosition( relative = True ), imath.V2d( 0, 0 ) )
		self.assertEqual( tf.getPosition( relative = False ), imath.V2d( k.getTime(), k.getValue() ) )

		# set absolute position of out tangent (no effect as key not parented)
		tf.setPosition( imath.V2d( 1, 1 ) )
		self.assertEqual( tf.getSlope(), 2 )
		self.assertEqual( tf.getScale(), 1 )
		self.assertEqual( tf.getPosition( relative = True ), imath.V2d( 0, 0 ) )
		self.assertEqual( tf.getPosition( relative = False ), imath.V2d( k.getTime(), k.getValue() ) )

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
		self.assertTrue( key.isActive() )

		curve.removeKey( key )
		self.assertEqual( curve.getKey( key.getTime() ), None )
		self.assertEqual( curve.closestKey( 0 ), None )
		self.assertEqual( key.parent(), None )
		self.assertFalse( key.isActive() )

	def testRemoveKeyWithInactiveKey( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k1 = Gaffer.Animation.Key( time = 1, value = 1 )
		k2 = Gaffer.Animation.Key( time = 1, value = 2 )
		k3 = Gaffer.Animation.Key( time = 1, value = 3 )

		curve.addKey( k1, removeActiveClashing = False )
		curve.addKey( k2, removeActiveClashing = False )
		curve.addKey( k3, removeActiveClashing = False )

		def assertConditionsA() :
			self.assertTrue( curve.getKey( 1 ).isSame( k3 ) )
			self.assertTrue( k3.parent().isSame( curve ) )
			self.assertTrue( k3.isActive() )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertFalse( k2.isActive() )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertFalse( k1.isActive() )

		def assertConditionsB() :
			self.assertTrue( curve.getKey( 1 ).isSame( k2 ) )
			self.assertIsNone( k3.parent() )
			self.assertFalse( k3.isActive() )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertTrue( k2.isActive() )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertFalse( k1.isActive() )

		def assertConditionsC() :
			self.assertTrue( curve.getKey( 1 ).isSame( k1 ) )
			self.assertIsNone( k3.parent() )
			self.assertFalse( k3.isActive() )
			self.assertIsNone( k2.parent() )
			self.assertFalse( k2.isActive() )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertTrue( k1.isActive() )

		def assertConditionsD() :
			self.assertIsNone( curve.getKey( 1 ) )
			self.assertIsNone( k3.parent() )
			self.assertFalse( k3.isActive() )
			self.assertIsNone( k2.parent() )
			self.assertFalse( k2.isActive() )
			self.assertIsNone( k1.parent() )
			self.assertFalse( k1.isActive() )

		assertConditionsA()
		with Gaffer.UndoScope( s ) :
			curve.removeKey( k3 )
		assertConditionsB()

		with Gaffer.UndoScope( s ) :
			curve.removeKey( k2 )
		assertConditionsC()

		with Gaffer.UndoScope( s ) :
			curve.removeKey( k1 )
		assertConditionsD()

		s.undo()
		assertConditionsC()

		s.undo()
		assertConditionsB()

		s.undo()
		assertConditionsA()

		s.redo()
		assertConditionsB()

		s.redo()
		assertConditionsC()

		s.redo()
		assertConditionsD()

	def testRemoveInactiveKey( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k1 = Gaffer.Animation.Key( time = 1, value = 1 )
		k2 = Gaffer.Animation.Key( time = 1, value = 2 )
		k3 = Gaffer.Animation.Key( time = 1, value = 3 )

		curve.addKey( k1, removeActiveClashing = False )
		curve.addKey( k2, removeActiveClashing = False )
		curve.addKey( k3, removeActiveClashing = False )

		def assertConditionsA() :
			self.assertTrue( curve.getKey( 1 ).isSame( k3 ) )
			self.assertTrue( k3.parent().isSame( curve ) )
			self.assertTrue( k3.isActive() )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertFalse( k2.isActive() )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertFalse( k1.isActive() )

		def assertConditionsB() :
			self.assertTrue( curve.getKey( 1 ).isSame( k3 ) )
			self.assertTrue( k3.parent().isSame( curve ) )
			self.assertTrue( k3.isActive() )
			self.assertIsNone( k2.parent() )
			self.assertFalse( k2.isActive() )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertFalse( k1.isActive() )

		def assertConditionsC() :
			self.assertTrue( curve.getKey( 1 ).isSame( k1 ) )
			self.assertIsNone( k3.parent() )
			self.assertFalse( k3.isActive() )
			self.assertIsNone( k2.parent() )
			self.assertFalse( k2.isActive() )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertTrue( k1.isActive() )

		assertConditionsA()
		with Gaffer.UndoScope( s ) :
			curve.removeKey( k2 )
		assertConditionsB()

		with Gaffer.UndoScope( s ) :
			curve.removeKey( k3 )
		assertConditionsC()

		s.undo()
		assertConditionsB()

		s.undo()
		assertConditionsA()

		s.redo()
		assertConditionsB()

		s.redo()
		assertConditionsC()

	def testRemoveInactiveKeys( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		ka = set()
		ki = set()

		for i in range( -10, 10, 2 ) :
			k = Gaffer.Animation.Key( time = i, value = 1 )
			k1 = Gaffer.Animation.Key( time = i, value = 2 )
			k2 = Gaffer.Animation.Key( time = i, value = 3 )
			curve.addKey( k2, removeActiveClashing = False )
			curve.addKey( k1, removeActiveClashing = False )
			curve.addKey( k, removeActiveClashing = False )
			self.assertTrue( k.parent().isSame( curve ) )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertTrue( k.isActive() )
			self.assertFalse( k1.isActive() )
			self.assertFalse( k2.isActive() )
			ka.add( k )
			ki.add( k1 )
			ki.add( k2 )

		with Gaffer.UndoScope( s ) :
			curve.removeInactiveKeys()

		for k in ka :
			self.assertTrue( k.parent().isSame( curve ) )
			self.assertTrue( k.isActive() )

		for k in ki :
			self.assertIsNone( k.parent() )
			self.assertFalse( k.isActive() )

		s.undo()

		for k in ka :
			self.assertTrue( k.parent().isSame( curve ) )
			self.assertTrue( k.isActive() )

		for k in ki :
			self.assertTrue( k.parent().isSame( curve ) )
			self.assertFalse( k.isActive() )

		s.redo()

		for k in ka :
			self.assertTrue( k.parent().isSame( curve ) )
			self.assertTrue( k.isActive() )

		for k in ki :
			self.assertIsNone( k.parent() )
			self.assertFalse( k.isActive() )

	def testRemoveInactiveKeysAfterSetTime( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k1 = Gaffer.Animation.Key( time = 1, value = 1 )
		k2 = Gaffer.Animation.Key( time = 2, value = 1 )

		curve.addKey( k1 )
		curve.addKey( k2 )

		def assertConditionsA() :
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertTrue( k1.isActive() )
			self.assertTrue( k2.isActive() )

		def assertConditionsB() :
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertTrue( k1.isActive() )
			self.assertFalse( k2.isActive() )

		def assertConditionsC() :
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertIsNone( k2.parent() )
			self.assertTrue( k1.isActive() )
			self.assertFalse( k2.isActive() )

		# set time of first key so that second key becomes inactive
		assertConditionsA()
		with Gaffer.UndoScope( s ) :
			ck = k1.setTime( 2 )
			self.assertTrue( k2.isSame( ck ) )
		assertConditionsB()

		# remove inactive keys
		with Gaffer.UndoScope( s ) :
			curve.removeInactiveKeys()
		assertConditionsC()

		s.undo()
		assertConditionsB()

		s.undo()
		assertConditionsA()

		s.redo()
		assertConditionsB()

		s.redo()
		assertConditionsC()

	def testRemoveInactiveKeysOutsideUndoAfterSetTime( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k1 = Gaffer.Animation.Key( time = 1, value = 1 )
		k2 = Gaffer.Animation.Key( time = 2, value = 1 )

		curve.addKey( k1 )
		curve.addKey( k2 )

		self.assertTrue( k1.parent().isSame( curve ) )
		self.assertTrue( k2.parent().isSame( curve ) )
		self.assertTrue( k1.isActive() )
		self.assertTrue( k2.isActive() )

		# set time of first key so that second key becomes inactive
		with Gaffer.UndoScope( s ) :
			ck = k1.setTime( 2 )
			self.assertTrue( k2.isSame( ck ) )

		self.assertTrue( k1.parent().isSame( curve ) )
		self.assertTrue( k2.parent().isSame( curve ) )
		self.assertTrue( k1.isActive() )
		self.assertFalse( k2.isActive() )

		def assertPostConditions() :
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertIsNone( k2.parent() )
			self.assertTrue( k1.isActive() )
			self.assertFalse( k2.isActive() )

		# remove inactive keys outside undo system
		curve.removeInactiveKeys()
		assertPostConditions()

		# check that exception is thrown on undo as removeKey was not captured
		self.assertRaises( IECore.Exception, lambda : s.undo() )
		assertPostConditions()

		# check that exception is thrown if we try to undo again
		self.assertRaises( IECore.Exception, lambda : s.undo() )
		assertPostConditions()

	def testRemoveInactiveKeysThenAddOutsideUndoAfterSetTime( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k1 = Gaffer.Animation.Key( time = 1, value = 1 )
		k2 = Gaffer.Animation.Key( time = 2, value = 1 )

		curve.addKey( k1 )
		curve.addKey( k2 )

		self.assertTrue( k1.parent().isSame( curve ) )
		self.assertTrue( k2.parent().isSame( curve ) )
		self.assertTrue( k1.isActive() )
		self.assertTrue( k2.isActive() )

		# set time of first key so that second key becomes inactive
		with Gaffer.UndoScope( s ) :
			ck = k1.setTime( 2 )
			self.assertTrue( k2.isSame( ck ) )

		self.assertTrue( k1.parent().isSame( curve ) )
		self.assertTrue( k2.parent().isSame( curve ) )
		self.assertTrue( k1.isActive() )
		self.assertFalse( k2.isActive() )

		# remove inactive keys outside undo system
		curve.removeInactiveKeys()

		self.assertTrue( k1.parent().isSame( curve ) )
		self.assertIsNone( k2.parent() )
		self.assertTrue( k1.isActive() )
		self.assertFalse( k2.isActive() )

		def assertPostConditions() :
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertFalse( k1.isActive() )
			self.assertTrue( k2.isActive() )

		# then add second key back to same curve (first key becomes inactive)
		curve.addKey( k2, removeActiveClashing = False )
		assertPostConditions()

		# check that exception is thrown on undo as removeKey was not captured
		self.assertRaises( IECore.Exception, lambda : s.undo() )
		assertPostConditions()

		# check that exception is thrown if we try to undo again
		self.assertRaises( IECore.Exception, lambda : s.undo() )
		assertPostConditions()

	def testRemoveKeyOutsideUndoAfterSetTime( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k1 = Gaffer.Animation.Key( time = 1, value = 1 )
		k2 = Gaffer.Animation.Key( time = 2, value = 1 )

		curve.addKey( k1 )
		curve.addKey( k2 )

		self.assertTrue( k1.parent().isSame( curve ) )
		self.assertTrue( k2.parent().isSame( curve ) )
		self.assertTrue( k1.isActive() )
		self.assertTrue( k2.isActive() )

		# set time of first key so that second key becomes inactive
		with Gaffer.UndoScope( s ) :
			ck = k1.setTime( 2 )
			self.assertTrue( k2.isSame( ck ) )

		self.assertTrue( k1.parent().isSame( curve ) )
		self.assertTrue( k2.parent().isSame( curve ) )
		self.assertTrue( k1.isActive() )
		self.assertFalse( k2.isActive() )

		def assertPostConditions() :
			self.assertIsNone( k1.parent() )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertFalse( k1.isActive() )
			self.assertTrue( k2.isActive() )

		# remove active key outside undo system second key becomes active
		curve.removeKey( k1 )
		assertPostConditions()

		# check that exception is thrown on undo as removeKey was not captured
		self.assertRaises( IECore.Exception, lambda : s.undo() )
		assertPostConditions()

		# check that exception is thrown if we try to undo again
		self.assertRaises( IECore.Exception, lambda : s.undo() )
		assertPostConditions()

	def testAddKeyOutsideUndoAfterSetTime( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k1 = Gaffer.Animation.Key( time = 1, value = 1 )
		k2 = Gaffer.Animation.Key( time = 2, value = 1 )
		k3 = Gaffer.Animation.Key( time = 2, value = 1 )

		curve.addKey( k1 )
		curve.addKey( k2 )

		self.assertTrue( k1.parent().isSame( curve ) )
		self.assertTrue( k2.parent().isSame( curve ) )
		self.assertTrue( k1.isActive() )
		self.assertTrue( k2.isActive() )

		# set time of first key so that second key becomes inactive
		with Gaffer.UndoScope( s ) :
			ck = k1.setTime( 2 )
			self.assertTrue( k2.isSame( ck ) )

		self.assertTrue( k1.parent().isSame( curve ) )
		self.assertTrue( k2.parent().isSame( curve ) )
		self.assertTrue( k1.isActive() )
		self.assertFalse( k2.isActive() )

		def assertPostConditions() :
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertTrue( k3.parent().isSame( curve ) )
			self.assertFalse( k1.isActive() )
			self.assertFalse( k2.isActive() )
			self.assertTrue( k3.isActive() )

		# add third key with same time outside undo system so that first key becomes inactive
		curve.addKey( k3, removeActiveClashing = False )
		assertPostConditions()

		# check that exception is thrown on undo as addKey was not captured
		self.assertRaises( IECore.Exception, lambda : s.undo() )
		assertPostConditions()

		# check that exception is thrown if we try to undo again
		self.assertRaises( IECore.Exception, lambda : s.undo() )
		assertPostConditions()

	def testSetTimeOutsideUndoAfterSetTime( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k1 = Gaffer.Animation.Key( time = 1, value = 1 )
		k2 = Gaffer.Animation.Key( time = 2, value = 1 )
		k3 = Gaffer.Animation.Key( time = 2, value = 1 )

		curve.addKey( k1 )
		curve.addKey( k2 )

		self.assertTrue( k1.parent().isSame( curve ) )
		self.assertTrue( k2.parent().isSame( curve ) )
		self.assertTrue( k1.isActive() )
		self.assertTrue( k2.isActive() )
		self.assertEqual( k1.getTime(), 1 )
		self.assertEqual( k2.getTime(), 2 )

		# set time of first key so that second key becomes inactive
		with Gaffer.UndoScope( s ) :
			ck = k1.setTime( 2 )
			self.assertTrue( k2.isSame( ck ) )

		self.assertTrue( k1.parent().isSame( curve ) )
		self.assertTrue( k2.parent().isSame( curve ) )
		self.assertTrue( k1.isActive() )
		self.assertFalse( k2.isActive() )
		self.assertEqual( k1.getTime(), 2 )
		self.assertEqual( k2.getTime(), 2 )

		# add third key with same time outside undo system so that first key becomes inactive
		curve.addKey( k3, removeActiveClashing = False )

		self.assertTrue( k1.parent().isSame( curve ) )
		self.assertTrue( k2.parent().isSame( curve ) )
		self.assertTrue( k3.parent().isSame( curve ) )
		self.assertFalse( k1.isActive() )
		self.assertFalse( k2.isActive() )
		self.assertTrue( k3.isActive() )
		self.assertEqual( k1.getTime(), 2 )
		self.assertEqual( k2.getTime(), 2 )
		self.assertEqual( k3.getTime(), 2 )

		def assertPostConditions() :
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertTrue( k3.parent().isSame( curve ) )
			self.assertTrue( k1.isActive() )
			self.assertFalse( k2.isActive() )
			self.assertTrue( k3.isActive() )
			self.assertEqual( k1.getTime(), 0 )
			self.assertEqual( k2.getTime(), 2 )
			self.assertEqual( k3.getTime(), 2 )

		# then set time of first key outside undo system so that it is active but at a different time
		k1.setTime( 0 )
		assertPostConditions()

		# check that exception is thrown on undo as setTime was not captured
		self.assertRaises( IECore.Exception, lambda : s.undo() )
		assertPostConditions()

		# check that exception is thrown if we try to undo again
		self.assertRaises( IECore.Exception, lambda : s.undo() )
		assertPostConditions()

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

	def testConstant( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		curve.addKey( Gaffer.Animation.Key( 0, 0, Gaffer.Animation.Interpolation.Linear ) )
		curve.addKey( Gaffer.Animation.Key( 1, 1, Gaffer.Animation.Interpolation.Constant ) )
		curve.addKey( Gaffer.Animation.Key( 2, 2 ) )

		with Gaffer.Context() as c :
			# Linear interpolation from 0 to 1.
			for i in range( 0, 10 ) :
				c.setTime( i / 9.0 )
				self.assertAlmostEqual( s["n"]["user"]["f"].getValue(), c.getTime() )
			# Constant interpolation from 1 to 2
			for i in range( 0, 10 ) :
				c.setTime( 1 + i / 10.0 )
				self.assertEqual( s["n"]["user"]["f"].getValue(), 1 )
			c.setTime( 2 )
			self.assertEqual( s["n"]["user"]["f"].getValue(), 2 )

	def testConstantNext( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		curve.addKey( Gaffer.Animation.Key( 0, 0, Gaffer.Animation.Interpolation.Linear ) )
		curve.addKey( Gaffer.Animation.Key( 1, 1, Gaffer.Animation.Interpolation.ConstantNext ) )
		curve.addKey( Gaffer.Animation.Key( 2, 2 ) )

		with Gaffer.Context() as c :
			# Linear interpolation from 0 to 1.
			for i in range( 0, 10 ) :
				c.setTime( i / 9.0 )
				self.assertAlmostEqual( s["n"]["user"]["f"].getValue(), c.getTime() )
			# Constant next interpolation from 1 to 2
			c.setTime( 1 )
			self.assertEqual( s["n"]["user"]["f"].getValue(), 1 )
			for i in range( 1, 11 ) :
				c.setTime( 1 + i / 10.0 )
				self.assertEqual( s["n"]["user"]["f"].getValue(), 2 )

	def testSetExtrapolationIn( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f1"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["f2"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["f3"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		ps = set()

		def changed( curve, direction ) :
			ps.add( ( curve, direction ) )

		def assertPreconditions( curve ) :
			self.assertEqual( curve.getExtrapolationIn(), extrapolationIn )
			self.assertEqual( curve.getExtrapolationOut(), extrapolationOut )
			self.assertEqual( curve.getExtrapolation( Gaffer.Animation.Direction.In ), extrapolationIn )
			self.assertEqual( curve.getExtrapolation( Gaffer.Animation.Direction.Out ), extrapolationOut )

		def assertPostconditions( curve ) :
			self.assertEqual( curve.getExtrapolationIn(), newExtrapolationIn )
			self.assertEqual( curve.getExtrapolationOut(), extrapolationOut )
			self.assertEqual( curve.getExtrapolation( Gaffer.Animation.Direction.In ), newExtrapolationIn )
			self.assertEqual( curve.getExtrapolation( Gaffer.Animation.Direction.Out ), extrapolationOut )

		def assertSignaled( curve ) :
			self.assertIn( ( curve, Gaffer.Animation.Direction.In ), ps )
			self.assertNotIn( ( curve, Gaffer.Animation.Direction.Out ), ps )

		extrapolationIn = Gaffer.Animation.defaultExtrapolation()
		extrapolationOut = Gaffer.Animation.defaultExtrapolation()
		newExtrapolationIn = Gaffer.Animation.Extrapolation.Repeat

		curve1 = Gaffer.Animation.acquire( s["n"]["user"]["f1"] )
		connection = curve1.extrapolationChangedSignal().connect( changed )

		with Gaffer.UndoScope( s ) :
			curve1.setExtrapolationIn( extrapolationIn )
		assertPreconditions( curve1 )
		self.assertFalse( s.undoAvailable() )
		self.assertEqual( len( ps ), 0 )

		with Gaffer.UndoScope( s ) :
			curve1.setExtrapolation( Gaffer.Animation.Direction.In, extrapolationIn )
		assertPreconditions( curve1 )
		self.assertFalse( s.undoAvailable() )
		self.assertEqual( len( ps ), 0 )

		curve2 = Gaffer.Animation.acquire( s["n"]["user"]["f2"] )
		connection = curve2.extrapolationChangedSignal().connect( changed )

		with Gaffer.UndoScope( s ) :
			curve2.setExtrapolationIn( newExtrapolationIn )
		assertPostconditions( curve2 )
		self.assertTrue( s.undoAvailable() )
		assertSignaled( curve2 )
		ps.clear()

		s.undo()
		assertPreconditions( curve2 )
		self.assertTrue( s.redoAvailable() )
		assertSignaled( curve2 )
		ps.clear()

		s.redo()
		assertPostconditions( curve2 )
		assertSignaled( curve2 )
		ps.clear()

		curve3 = Gaffer.Animation.acquire( s["n"]["user"]["f3"] )
		connection = curve3.extrapolationChangedSignal().connect( changed )

		with Gaffer.UndoScope( s ) :
			curve3.setExtrapolation( Gaffer.Animation.Direction.In, newExtrapolationIn )
		assertPostconditions( curve3 )
		self.assertTrue( s.undoAvailable() )
		assertSignaled( curve3 )
		ps.clear()

		s.undo()
		assertPreconditions( curve3 )
		self.assertTrue( s.redoAvailable() )
		assertSignaled( curve3 )
		ps.clear()

		s.redo()
		assertPostconditions( curve3 )
		assertSignaled( curve3 )

	def testSetExtrapolationOut( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f1"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["f2"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["f3"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		ps = set()

		def changed( curve, direction ) :
			ps.add( ( curve, direction ) )

		def assertPreconditions( curve ) :
			self.assertEqual( curve.getExtrapolationIn(), extrapolationIn )
			self.assertEqual( curve.getExtrapolationOut(), extrapolationOut )
			self.assertEqual( curve.getExtrapolation( Gaffer.Animation.Direction.In ), extrapolationIn )
			self.assertEqual( curve.getExtrapolation( Gaffer.Animation.Direction.Out ), extrapolationOut )

		def assertPostconditions( curve ) :
			self.assertEqual( curve.getExtrapolationIn(), extrapolationIn )
			self.assertEqual( curve.getExtrapolationOut(), newExtrapolationOut )
			self.assertEqual( curve.getExtrapolation( Gaffer.Animation.Direction.In ), extrapolationIn )
			self.assertEqual( curve.getExtrapolation( Gaffer.Animation.Direction.Out ), newExtrapolationOut )

		def assertSignaled( curve ) :
			self.assertNotIn( ( curve, Gaffer.Animation.Direction.In ), ps )
			self.assertIn( ( curve, Gaffer.Animation.Direction.Out ), ps )

		extrapolationIn = Gaffer.Animation.defaultExtrapolation()
		extrapolationOut = Gaffer.Animation.defaultExtrapolation()
		newExtrapolationOut = Gaffer.Animation.Extrapolation.RepeatOffset

		curve1 = Gaffer.Animation.acquire( s["n"]["user"]["f1"] )
		connection = curve1.extrapolationChangedSignal().connect( changed )

		with Gaffer.UndoScope( s ) :
			curve1.setExtrapolationOut( extrapolationOut )
		assertPreconditions( curve1 )
		self.assertFalse( s.undoAvailable() )
		self.assertEqual( len( ps ), 0 )

		with Gaffer.UndoScope( s ) :
			curve1.setExtrapolation( Gaffer.Animation.Direction.Out, extrapolationOut )
		assertPreconditions( curve1 )
		self.assertFalse( s.undoAvailable() )
		self.assertEqual( len( ps ), 0 )

		curve2 = Gaffer.Animation.acquire( s["n"]["user"]["f2"] )
		connection = curve2.extrapolationChangedSignal().connect( changed )

		with Gaffer.UndoScope( s ) :
			curve2.setExtrapolationOut( newExtrapolationOut )
		assertPostconditions( curve2 )
		self.assertTrue( s.undoAvailable() )
		assertSignaled( curve2 )
		ps.clear()

		s.undo()
		assertPreconditions( curve2 )
		self.assertTrue( s.redoAvailable() )
		assertSignaled( curve2 )
		ps.clear()

		s.redo()
		assertPostconditions( curve2 )
		assertSignaled( curve2 )
		ps.clear()

		curve3 = Gaffer.Animation.acquire( s["n"]["user"]["f3"] )
		connection = curve3.extrapolationChangedSignal().connect( changed )

		with Gaffer.UndoScope( s ) :
			curve3.setExtrapolation( Gaffer.Animation.Direction.Out, newExtrapolationOut )
		assertPostconditions( curve3 )
		self.assertTrue( s.undoAvailable() )
		assertSignaled( curve3 )
		ps.clear()

		s.undo()
		assertPreconditions( curve3 )
		self.assertTrue( s.redoAvailable() )
		assertSignaled( curve3 )
		ps.clear()

		s.redo()
		assertPostconditions( curve3 )
		assertSignaled( curve3 )

	def testExtrapolationConstant( self ) :

		import math

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		curve.setExtrapolationIn( Gaffer.Animation.Extrapolation.Constant )
		curve.setExtrapolationOut( Gaffer.Animation.Extrapolation.Constant )

		valueIn = math.pi
		valueOut = math.e
		keyIn = Gaffer.Animation.Key( -5, value = valueIn )
		keyOut = Gaffer.Animation.Key( 5, value = valueOut )
		curve.addKey( keyIn )
		curve.addKey( keyOut )

		import random
		r = random.Random( 0 )
		for i in range( 0, 11 ) :
			time = r.uniform( 0.0, 1000.0 )
			self.assertFloat32Equal( valueIn, curve.evaluate( keyIn.getTime() - time ) )
			self.assertFloat32Equal( valueOut, curve.evaluate( keyOut.getTime() + time ) )

	def testExtrapolationLinear( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		curve.setExtrapolationIn( Gaffer.Animation.Extrapolation.Linear )
		curve.setExtrapolationOut( Gaffer.Animation.Extrapolation.Linear )

		valueIn = 4.567
		valueOut = -7.564
		slopeIn = 1.234
		slopeOut = -0.3245
		keyIn = Gaffer.Animation.Key( -5, value = valueIn, inSlope = slopeIn, tieMode = Gaffer.Animation.TieMode.Manual )
		keyOut = Gaffer.Animation.Key( 5, value = valueOut, outSlope = slopeOut, tieMode = Gaffer.Animation.TieMode.Manual )
		curve.addKey( keyIn )
		curve.addKey( keyOut )

		import random
		r = random.Random( 0 )
		for i in range( 0, 11 ) :
			time = r.uniform( 0.0, 100.0 )
			self.assertAlmostEqual( valueIn - time * slopeIn, curve.evaluate( keyIn.getTime() - time ), places = 5 )
			self.assertAlmostEqual( valueOut + time * slopeOut, curve.evaluate( keyOut.getTime() + time ), places = 5 )

	def testExtrapolationRepeat( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		curve.setExtrapolationIn( Gaffer.Animation.Extrapolation.Repeat )
		curve.setExtrapolationOut( Gaffer.Animation.Extrapolation.Repeat )

		keyIn = Gaffer.Animation.Key( 23, value = 1, interpolation = Gaffer.Animation.Interpolation.Linear )
		keyOut = Gaffer.Animation.Key( 25, value = 3, interpolation = Gaffer.Animation.Interpolation.Linear )
		curve.addKey( keyIn )
		curve.addKey( keyOut )

		# NOTE : At exact multiple of [in|out] key the curve repeats. ensure that the extrapolated
		#        value is equal to the value of the key in the direction of extrapolation.
		for i in range( 1, 22, 2 ) :
			self.assertEqual( keyIn.getValue(), curve.evaluate( float( i ) ) )
		for i in range( 27, 45, 2 ) :
			self.assertEqual( keyOut.getValue(), curve.evaluate( float( i ) ) )

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
		curve.setExtrapolationIn( Gaffer.Animation.Extrapolation.Oscillate )
		curve.setExtrapolationOut( Gaffer.Animation.Extrapolation.Mirror )

		def assertKeysEqual( k0, k1 ) :

			self.assertEqual( k0.getTime(), k1.getTime() )
			self.assertEqual( k0.getValue(), k1.getValue() )
			self.assertEqual( k0.getInterpolation(), k1.getInterpolation() )

		def assertAnimation( script ) :

			curve = Gaffer.Animation.acquire( script["n"]["user"]["f"] )
			assertKeysEqual( curve.getKey( 0 ),  Gaffer.Animation.Key( 0, 0, Gaffer.Animation.Interpolation.Linear ) )
			assertKeysEqual( curve.getKey( 1 ),  Gaffer.Animation.Key( 1, 1, Gaffer.Animation.Interpolation.Linear ) )
			self.assertEqual( curve.getExtrapolationIn(), Gaffer.Animation.Extrapolation.Oscillate )
			self.assertEqual( curve.getExtrapolationOut(), Gaffer.Animation.Extrapolation.Mirror )
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

		op2Curve.addKey( Gaffer.Animation.Key( 0, 0, Gaffer.Animation.Interpolation.Constant ) )
		op2Curve.addKey( Gaffer.Animation.Key( 1, 1, Gaffer.Animation.Interpolation.Constant ) )

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

		def assertPreconditions() :
			self.assertTrue( curve.getKey( 1 ).isSame( k1 ) )
			self.assertTrue( curve.getKey( 2 ).isSame( k2 ) )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertTrue( k1.isActive() )
			self.assertTrue( k2.isActive() )

		def assertPostconditions() :
			self.assertTrue( curve.getKey( 1 ).isSame( k2 ) )
			self.assertTrue( curve.getKey( 2 ) is None )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertFalse( k1.isActive() )
			self.assertTrue( k2.isActive() )

		assertPreconditions()
		with Gaffer.UndoScope( s ) :
			ck = k2.setTime( 1 )
			self.assertTrue( k1.isSame( ck ) )
		assertPostconditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostconditions()

	def testModifyKeyReplacesExistingKeyWithInactiveKeys( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		k0 = Gaffer.Animation.Key( time = 1 )
		k1 = Gaffer.Animation.Key( time = 1 )
		k2 = Gaffer.Animation.Key( time = 2 )
		k3 = Gaffer.Animation.Key( time = 2 )

		curve.addKey( k0, removeActiveClashing = False )
		curve.addKey( k1, removeActiveClashing = False )
		curve.addKey( k3, removeActiveClashing = False )
		curve.addKey( k2, removeActiveClashing = False )

		def assertPreconditions() :
			self.assertTrue( curve.getKey( 1 ).isSame( k1 ) )
			self.assertTrue( curve.getKey( 2 ).isSame( k2 ) )
			self.assertTrue( k0.parent().isSame( curve ) )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertTrue( k3.parent().isSame( curve ) )
			self.assertFalse( k0.isActive() )
			self.assertTrue( k1.isActive() )
			self.assertTrue( k2.isActive() )
			self.assertFalse( k3.isActive() )

		def assertPostconditions() :
			self.assertTrue( curve.getKey( 1 ).isSame( k2 ) )
			self.assertTrue( curve.getKey( 2 ).isSame( k3 ) )
			self.assertTrue( k0.parent().isSame( curve ) )
			self.assertTrue( k1.parent().isSame( curve ) )
			self.assertTrue( k2.parent().isSame( curve ) )
			self.assertTrue( k3.parent().isSame( curve ) )
			self.assertFalse( k0.isActive() )
			self.assertFalse( k1.isActive() )
			self.assertTrue( k2.isActive() )
			self.assertTrue( k3.isActive() )

		assertPreconditions()
		with Gaffer.UndoScope( s ) :
			ck = k2.setTime( 1 )
			self.assertTrue( k1.isSame( ck ) )
		assertPostconditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostconditions()

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

		def assertKeysEqual( k0, k1 ) :

			self.assertEqual( k0.getTime(), k1.getTime() )
			self.assertEqual( k0.getValue(), k1.getValue() )
			self.assertEqual( k0.getInterpolation(), k1.getInterpolation() )

		for frame in range( 0, 10000 ) :
			context.setFrame( frame )
			assertKeysEqual(
				curve.getKey( context.getTime() ),
				Gaffer.Animation.Key( context.getTime(), context.getTime(), Gaffer.Animation.Interpolation.Linear )
			)

	def testSerialisationCreatedInVersion0_60( self ) :

		import os

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/animationVersion-0.60.9.0.gfr" )
		s.load()

		def assertAnimation( script ) :

			self.assertEqual( s["Animation"]["curves"]["curve0"].getKey( 0 ).getTime(), 0 )
			self.assertEqual( s["Animation"]["curves"]["curve0"].getKey( 0 ).getValue(), 0 )
			self.assertEqual( s["Animation"]["curves"]["curve0"].getKey( 0 ).getInterpolation(), Gaffer.Animation.Interpolation.Linear )
			self.assertEqual( s["Animation"]["curves"]["curve0"].getKey( 1 ).getTime(), 1 )
			self.assertEqual( s["Animation"]["curves"]["curve0"].getKey( 1 ).getValue(), 1 )
			self.assertEqual( s["Animation"]["curves"]["curve0"].getKey( 1 ).getInterpolation(), Gaffer.Animation.Interpolation.Linear )

			self.assertEqual( s["Animation"]["curves"]["curve1"].getKey( 0 ).getTime(), 0 )
			self.assertEqual( s["Animation"]["curves"]["curve1"].getKey( 0 ).getValue(), 0 )
			self.assertEqual( s["Animation"]["curves"]["curve1"].getKey( 0 ).getInterpolation(), Gaffer.Animation.Interpolation.Constant )
			self.assertEqual( s["Animation"]["curves"]["curve1"].getKey( 1 ).getTime(), 1 )
			self.assertEqual( s["Animation"]["curves"]["curve1"].getKey( 1 ).getValue(), 1 )
			self.assertEqual( s["Animation"]["curves"]["curve1"].getKey( 1 ).getInterpolation(), Gaffer.Animation.Interpolation.Constant )

		assertAnimation( s )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		assertAnimation( s2 )

	def testKeySetTimeLastSpan( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f4 = 4.0 / 24.0
		f5 = 5.0 / 24.0
		f7 = 7.0 / 24.0

		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k2 = Gaffer.Animation.Key( time = f4, interpolation = Gaffer.Animation.Interpolation.Step, tieMode = Gaffer.Animation.TieMode.Slope )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k4 = Gaffer.Animation.Key( time = f7, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( k1 )
		curve.addKey( k2 )
		curve.addKey( k3 )
		curve.addKey( k4 )

		ti4 = k4.tangentIn()
		tf4 = k4.tangentOut()

		# set the in tangent slope of the final key
		ti4.setSlope( 60 )
		self.assertEqual( ti4.getSlope(), 60 )
		self.assertEqual( tf4.getSlope(), 60 )

		# set time of second key so that key lies in final span and interpolation affects in tangent of final key
		f6 = 6.0 / 24.0
		k2.setTime( f6 )

		# ensure in tangent slope of fourth key is now flat as its affected by step interpolation
		self.assertEqual( ti4.getSlope(), 0 )

		# set time of second key back to 5 so that final key is again affected by cubic interpolation
		k2.setTime( f4 )

		# ensure in tangent slope of fourth key has reverted to its value before being affected by step interpolation
		self.assertEqual( ti4.getSlope(), 60 )

	def testKeySetTimeWhenTwoKeysInCurve( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f4 = 4.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k2 = Gaffer.Animation.Key( time = f4, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( k1 )
		curve.addKey( k2 )

		ti1 = k1.tangentIn()
		tf1 = k1.tangentOut()
		ti2 = k2.tangentIn()
		tf2 = k2.tangentOut()

		# check that in tangent of first key is unconstrained
		self.assertFalse( ti1.slopeIsConstrained() )
		self.assertFalse( tf1.slopeIsConstrained() )

		# check that out tangent of last key is unconstrained
		self.assertFalse( ti2.slopeIsConstrained() )
		self.assertFalse( tf2.slopeIsConstrained() )

		# set out tangent slope of first key to 30
		tf1.setSlope( 30 )
		self.assertEqual( ti1.getSlope(), 30 )
		self.assertEqual( tf1.getSlope(), 30 )

		# set in tangent slope of last key to -60
		ti2.setSlope( -60 )
		self.assertEqual( ti2.getSlope(), -60 )
		self.assertEqual( tf2.getSlope(), -60 )

		# now set time of first key to lower value and check slopes of tangents are the same
		f1 = 1.0 / 24.0
		k1.setTime( f1 )
		self.assertEqual( ti1.getSlope(), 30 )
		self.assertEqual( tf1.getSlope(), 30 )
		self.assertEqual( ti2.getSlope(), -60 )
		self.assertEqual( tf2.getSlope(), -60 )

		# now set time of last key to higher value and check slopes of tangents are the same
		f6 = 6.0 / 24.0
		k2.setTime( f6 )
		self.assertEqual( ti1.getSlope(), 30 )
		self.assertEqual( tf1.getSlope(), 30 )
		self.assertEqual( ti2.getSlope(), -60 )
		self.assertEqual( tf2.getSlope(), -60 )

	def testKeySetTimeJumpNextWithInterpolationConstrainedSlopeWithTieModeSlope( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f3 = 3.0 / 24.0
		f5 = 5.0 / 24.0
		f6 = 6.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Step, tieMode = Gaffer.Animation.TieMode.Slope )
		k2 = Gaffer.Animation.Key( time = f3, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k4 = Gaffer.Animation.Key( time = f6, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( k1 )
		curve.addKey( k2 )
		curve.addKey( k3 )
		curve.addKey( k4 )

		ti3 = k3.tangentIn()
		tf3 = k3.tangentOut()

		# set the tangent slope of the third key to 60
		ti3.setSlope( 60 )
		self.assertEqual( ti3.getSlope(), 60 )
		self.assertEqual( tf3.getSlope(), 60 )

		# set time of key 1 so that key 3 in tangent affected by step interpolator
		f4 = 4.0 / 24.0
		k1.setTime( f4 )
		self.assertEqual( curve.previousKey( k3.getTime() ), k1 )
		self.assertTrue( ti3.slopeIsConstrained() )
		self.assertFalse( tf3.slopeIsConstrained() )

		# ensure out tangent slope of third key not affected
		self.assertEqual( tf3.getSlope(), 60 )

	def testKeySetTimeJumpNextWithInterpolationConstrainedScaleWithTieModeScale( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f3 = 3.0 / 24.0
		f5 = 5.0 / 24.0
		f6 = 6.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Step, tieMode = Gaffer.Animation.TieMode.Manual )
		k2 = Gaffer.Animation.Key( time = f3, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )
		k4 = Gaffer.Animation.Key( time = f6, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )

		curve.addKey( k1 )
		curve.addKey( k2 )
		curve.addKey( k3 )
		curve.addKey( k4 )

		ti3 = k3.tangentIn()
		tf3 = k3.tangentOut()

		# set the tangent scale of the third key to 0.87
		ti3.setScale( 0.87 )
		tf3.setScale( 0.87 )
		self.assertEqual( ti3.getScale(), 0.87 )
		self.assertEqual( tf3.getScale(), 0.87 )

		# set tie mode to include scale
		k3.setTieMode( Gaffer.Animation.TieMode.Scale )

		# set time of key 1 so that key 3 in tangent affected by step interpolator
		f4 = 4.0 / 24.0
		k1.setTime( f4 )
		self.assertEqual( curve.previousKey( k3.getTime() ), k1 )
		self.assertTrue( ti3.scaleIsConstrained() )
		self.assertFalse( tf3.scaleIsConstrained() )

		# ensure out tangent scale of third key not affected
		self.assertEqual( tf3.getScale(), 0.87 )

	def testKeySetTimeJumpWithInterpolationConstrainedSlopeWithTieModeSlope( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f3 = 3.0 / 24.0
		f5 = 5.0 / 24.0
		f7 = 7.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k2 = Gaffer.Animation.Key( time = f3, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Step, tieMode = Gaffer.Animation.TieMode.Slope )
		k4 = Gaffer.Animation.Key( time = f7, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( k1 )
		curve.addKey( k2 )
		curve.addKey( k3 )
		curve.addKey( k4 )

		ti2 = k2.tangentIn()
		tf2 = k2.tangentOut()

		# set the tangent slope of the second key to 60
		ti2.setSlope( 60 )
		self.assertEqual( ti2.getSlope(), 60 )
		self.assertEqual( tf2.getSlope(), 60 )

		# set time of key 2 so that key 2 in tangent affected by step interpolator
		f6 = 6.0 / 24.0
		k2.setTime( f6 )
		self.assertEqual( curve.previousKey( k2.getTime() ), k3 )
		self.assertTrue( ti2.slopeIsConstrained() )
		self.assertFalse( tf2.slopeIsConstrained() )

		# ensure out tangent slope of second key not affected
		self.assertEqual( tf2.getSlope(), 60 )

	def testKeySetTimeJumpWithInterpolationUnconstrainedSlopeWithTieModeSlope( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f3 = 3.0 / 24.0
		f5 = 5.0 / 24.0
		f7 = 7.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Step, tieMode = Gaffer.Animation.TieMode.Slope )
		k2 = Gaffer.Animation.Key( time = f3, interpolation = Gaffer.Animation.Interpolation.Cubic, inSlope=0, outSlope=0, tieMode = Gaffer.Animation.TieMode.Slope )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k4 = Gaffer.Animation.Key( time = f7, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( k1 )
		curve.addKey( k2 )
		curve.addKey( k3 )
		curve.addKey( k4 )

		ti2 = k2.tangentIn()
		tf2 = k2.tangentOut()

		# set the out tangent slope of the second key to 60, in slope constrained so should not be affected
		tf2.setSlope( 60 )
		self.assertTrue( ti2.slopeIsConstrained() )
		self.assertFalse( tf2.slopeIsConstrained() )
		self.assertEqual( ti2.getSlope(), 0 )
		self.assertEqual( tf2.getSlope(), 60 )

		# set time of second key so that second key in tangent affected by cubic interpolator
		f6 = 6.0 / 24.0
		k2.setTime( f6 )
		self.assertEqual( curve.previousKey( k2.getTime() ), k3 )
		self.assertFalse( ti2.slopeIsConstrained() )
		self.assertFalse( tf2.slopeIsConstrained() )

		# ensure in tangent slope of second key has been tied correctly to out tangent slope of second key
		self.assertEqual( ti2.getSlope(), 60 )
		self.assertEqual( tf2.getSlope(), 60 )

	def testKeySetTimeJumpWithInterpolationUnconstrainedNextSlopeWithTieModeSlope( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f3 = 3.0 / 24.0
		f5 = 5.0 / 24.0
		f7 = 7.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k2 = Gaffer.Animation.Key( time = f3, interpolation = Gaffer.Animation.Interpolation.Step, tieMode = Gaffer.Animation.TieMode.Slope )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Cubic, inSlope=0, outSlope=0, tieMode = Gaffer.Animation.TieMode.Slope )
		k4 = Gaffer.Animation.Key( time = f7, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( k1 )
		curve.addKey( k2 )
		curve.addKey( k3 )
		curve.addKey( k4 )

		ti3 = k3.tangentIn()
		tf3 = k3.tangentOut()

		# set the out tangent slope of the third key to 60, in slope constrained so should not be affected
		tf3.setSlope( 60 )
		self.assertTrue( ti3.slopeIsConstrained() )
		self.assertFalse( tf3.slopeIsConstrained() )
		self.assertEqual( ti3.getSlope(), 0 )
		self.assertEqual( tf3.getSlope(), 60 )

		# set time of key 1 so that key 3 in tangent affected by cubic interpolator
		f4 = 4.0 / 24.0
		k1.setTime( f4 )
		self.assertEqual( curve.previousKey( k3.getTime() ), k1 )
		self.assertFalse( ti3.slopeIsConstrained() )
		self.assertFalse( tf3.slopeIsConstrained() )

		# ensure in tangent slope of third key has been tied correctly to out tangent slope of third key
		self.assertEqual( ti3.getSlope(), 60 )
		self.assertEqual( tf3.getSlope(), 60 )

	def testKeySetTimeNextWithInterpolationConstrainedScaleWithTieModeScale( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f3 = 3.0 / 24.0
		f5 = 5.0 / 24.0
		f7 = 7.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )
		k2 = Gaffer.Animation.Key( time = f3, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Step, tieMode = Gaffer.Animation.TieMode.Manual )
		k4 = Gaffer.Animation.Key( time = f7, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )

		curve.addKey( k1 )
		curve.addKey( k2 )
		curve.addKey( k3 )
		curve.addKey( k4 )

		ti2 = k2.tangentIn()
		tf2 = k2.tangentOut()

		# set the tangent scale of the second key to 0.87
		ti2.setScale( 0.87 )
		tf2.setScale( 0.87 )
		self.assertEqual( ti2.getScale(), 0.87 )
		self.assertEqual( tf2.getScale(), 0.87 )

		# set tie mode to include scale
		k2.setTieMode( Gaffer.Animation.TieMode.Scale )

		# set time of key 2 so that key 2 in tangent affected by step interpolator
		f6 = 6.0 / 24.0
		k2.setTime( f6 )
		self.assertEqual( curve.previousKey( k2.getTime() ), k3 )
		self.assertTrue( ti2.scaleIsConstrained() )
		self.assertFalse( tf2.scaleIsConstrained() )

		# ensure out tangent scale of second key not affected
		self.assertEqual( tf2.getScale(), 0.87 )

	def testKeySetTimeToFinalKeyThenAfter( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f4 = 4.0 / 24.0
		f5 = 5.0 / 24.0
		kf = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k = Gaffer.Animation.Key( time = f4, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		kl = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( kf )
		curve.addKey( k )
		curve.addKey( kl )

		til = kl.tangentIn()
		tfl = kl.tangentOut()

		# check that out tangent of last key is unconstrained
		self.assertFalse( til.slopeIsConstrained() )
		self.assertFalse( tfl.slopeIsConstrained() )

		# set in tangent slope of last key to -60
		til.setSlope( -60 )
		self.assertEqual( til.getSlope(), -60 )
		self.assertEqual( tfl.getSlope(), -60 )

		# now set the time of the middle key to the same time as the last key this will inactivate the last key
		kc = k.setTime( kl.getTime() )
		self.assertEqual( k.getTime(), kl.getTime() )
		self.assertEqual( kl, kc )
		self.assertFalse( kl.isActive() )
		self.assertEqual( curve.getKey( kl.getTime() ), k )

		# now set the time of the middle key to time after the last key
		f6 = 6.0 / 24.0
		k.setTime( f6 )
		self.assertEqual( kl.parent(), curve )
		self.assertEqual( curve.getKey( kl.getTime() ), kl )

		# old last key is no longer final key of curve so both tangent slopes should be unconstrained and therefore tied
		self.assertFalse( til.slopeIsConstrained() )
		self.assertFalse( tfl.slopeIsConstrained() )
		self.assertEqual( til.getSlope(), -60 )
		self.assertEqual( tfl.getSlope(), -60 )

	def testKeySetTimeToFirstKeyThenBefore( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f4 = 4.0 / 24.0
		f5 = 5.0 / 24.0
		kf = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k = Gaffer.Animation.Key( time = f4, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		kl = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( kf )
		curve.addKey( k )
		curve.addKey( kl )

		tif = kf.tangentIn()
		tff = kf.tangentOut()

		# check that in tangent of first key is unconstrained
		self.assertFalse( tif.slopeIsConstrained() )
		self.assertFalse( tff.slopeIsConstrained() )

		# set out tangent slope of first key to 30
		tff.setSlope( 30 )
		self.assertEqual( tif.getSlope(), 30 )
		self.assertEqual( tff.getSlope(), 30 )

		# now set the time of the middle key to the same time as the first key this will inactivate the first key
		kc = k.setTime( kf.getTime() )
		self.assertEqual( k.getTime(), kf.getTime() )
		self.assertEqual( kf, kc )
		self.assertFalse( kf.isActive() )
		self.assertEqual( curve.getKey( kf.getTime() ), k )

		# now set the time of the middle key to time before the last key
		f1 = 1.0 / 24.0
		k.setTime( f1 )
		self.assertEqual( kf.parent(), curve )
		self.assertEqual( curve.getKey( kf.getTime() ), kf )

		# old first key is no longer first key of curve so both tangent slopes should be unconstrained and therefore tied
		self.assertFalse( tif.slopeIsConstrained() )
		self.assertFalse( tff.slopeIsConstrained() )
		self.assertEqual( tif.getSlope(), 30 )
		self.assertEqual( tff.getSlope(), 30 )

	def testKeySetTimeRemoveThenAddBackWithInterpolationConstrainedSlopeWithTieModeSlope( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f4 = 4.0 / 24.0
		f5 = 5.0 / 24.0
		f6 = 6.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k2 = Gaffer.Animation.Key( time = f4, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k4 = Gaffer.Animation.Key( time = f6, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( k1 )
		curve.addKey( k2 )
		curve.addKey( k3 )
		curve.addKey( k4 )

		ti2 = k2.tangentIn()
		tf2 = k2.tangentOut()

		ti3 = k3.tangentIn()
		tf3 = k3.tangentOut()

		# set the tangent slope of second key to 30
		ti2.setSlope( 30 )
		self.assertEqual( ti2.getSlope(), 30 )
		self.assertEqual( tf2.getSlope(), 30 )

		# set the tangent slope of the third key to 60
		ti3.setSlope( 60 )
		self.assertEqual( ti3.getSlope(), 60 )
		self.assertEqual( tf3.getSlope(), 60 )

		# set interpolation of third key to linear (does not use slope)
		k3.setInterpolation( Gaffer.Animation.Interpolation.Linear )
		self.assertFalse( ti3.slopeIsConstrained() )
		self.assertTrue( tf3.slopeIsConstrained() )
		self.assertEqual( ti3.getSlope(),  60 )

		# now set the time of the third key to the same time as the second key this will inactivate the second key
		kc = k3.setTime( k2.getTime() )
		self.assertEqual( k3.getTime(), k2.getTime() )
		self.assertEqual( k2, kc )
		self.assertFalse( k2.isActive() )
		self.assertEqual( curve.getKey( k2.getTime() ), k3 )

		# now set the time of the third key to time before the second key
		f3 = 3.0 / 24.0
		k3.setTime( f3 )
		self.assertEqual( k2.parent(), curve )
		self.assertEqual( k3.parent(), curve )
		self.assertEqual( curve.getKey( k2.getTime() ), k2 )
		self.assertEqual( curve.getKey( k3.getTime() ), k3 )

		# ensure in tangent slope of third key not affected
		self.assertEqual( ti3.getSlope(), 60 )

		# ensure out tangent slope of second key not affected
		self.assertEqual( tf2.getSlope(), 30 )

	def testKeySetTimeRemoveThenAddBackWithInterpolationConstrainedScaleWithTieModeScale( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f4 = 4.0 / 24.0
		f5 = 5.0 / 24.0
		f6 = 6.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )
		k2 = Gaffer.Animation.Key( time = f4, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )
		k4 = Gaffer.Animation.Key( time = f6, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )

		curve.addKey( k1 )
		curve.addKey( k2 )
		curve.addKey( k3 )
		curve.addKey( k4 )

		ti2 = k2.tangentIn()
		tf2 = k2.tangentOut()

		ti3 = k3.tangentIn()
		tf3 = k3.tangentOut()

		# set the tangent scale of second key to 0.75
		ti2.setScale( 0.75 )
		tf2.setScale( 0.75 )
		self.assertEqual( ti2.getScale(), 0.75 )
		self.assertEqual( tf2.getScale(), 0.75 )

		# set the tangent scale of the third key to 0.85
		ti3.setScale( 0.85 )
		tf3.setScale( 0.85 )
		self.assertEqual( ti3.getScale(), 0.85 )
		self.assertEqual( tf3.getScale(), 0.85 )

		# set tie modes to include scale
		k2.setTieMode( Gaffer.Animation.TieMode.Scale )
		k3.setTieMode( Gaffer.Animation.TieMode.Scale )

		# set interpolation of third key to linear (does not use scale)
		k3.setInterpolation( Gaffer.Animation.Interpolation.Linear )
		self.assertFalse( ti3.scaleIsConstrained() )
		self.assertTrue( tf3.scaleIsConstrained() )
		self.assertEqual( ti3.getScale(), 0.85 )

		# now set the time of the third key to the same time as the second key this will inactivate the second key
		kc = k3.setTime( k2.getTime() )
		self.assertEqual( k3.getTime(), k2.getTime() )
		self.assertEqual( k2, kc )
		self.assertFalse( k2.isActive() )
		self.assertEqual( curve.getKey( k2.getTime() ), k3 )

		# now set the time of the third key to time before the second key
		f3 = 3.0 / 24.0
		k3.setTime( f3 )
		self.assertEqual( k2.parent(), curve )
		self.assertEqual( k3.parent(), curve )
		self.assertEqual( curve.getKey( k2.getTime() ), k2 )
		self.assertEqual( curve.getKey( k3.getTime() ), k3 )

		# ensure in tangent scale of third key not affected
		self.assertEqual( ti3.getScale(), 0.85 )

		# ensure out tangent scale of second key not affected
		self.assertEqual( tf2.getScale(), 0.75 )

	def testKeySetTimeTwoKeysFinalBeforeFirst( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f4 = 4.0 / 24.0

		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k2 = Gaffer.Animation.Key( time = f4, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( k1 )
		curve.addKey( k2 )

		ti1 = k1.tangentIn()
		tf1 = k1.tangentOut()

		ti2 = k2.tangentIn()
		tf2 = k2.tangentOut()

		# set the out tangent slope of the first key
		self.assertFalse( ti1.slopeIsConstrained() )
		self.assertFalse( tf1.slopeIsConstrained() )
		tf1.setSlope( 30 )
		self.assertEqual( ti1.getSlope(), 30 )
		self.assertEqual( tf1.getSlope(), 30 )

		# set the in tangent slope of the final key
		self.assertFalse( ti2.slopeIsConstrained() )
		self.assertFalse( tf2.slopeIsConstrained() )
		ti2.setSlope( 60 )
		self.assertEqual( ti2.getSlope(), 60 )
		self.assertEqual( tf2.getSlope(), 60 )

		# set time of second key (final key) so it becomes the first key
		f0 = 0.0 / 24.0
		k2.setTime( f0 )

		# ensure in tangent slope of key one matches out tangent slope
		self.assertEqual( ti1.getSlope(), 30 )
		self.assertEqual( tf1.getSlope(), 30 )

		# ensure out tangent slope of key two matches in tangent slope
		self.assertEqual( ti2.getSlope(), 60 )
		self.assertEqual( tf2.getSlope(), 60 )

	def testKeySetTimeTwoKeysFirstAfterFinal( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f4 = 4.0 / 24.0

		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k2 = Gaffer.Animation.Key( time = f4, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( k1 )
		curve.addKey( k2 )

		ti1 = k1.tangentIn()
		tf1 = k1.tangentOut()

		ti2 = k2.tangentIn()
		tf2 = k2.tangentOut()

		# set the out tangent slope of the first key
		tf1.setSlope( 30 )
		self.assertEqual( ti1.getSlope(), 30 )
		self.assertEqual( tf1.getSlope(), 30 )

		# set the in tangent slope of the final key
		ti2.setSlope( 60 )
		self.assertEqual( ti2.getSlope(), 60 )
		self.assertEqual( tf2.getSlope(), 60 )

		# set time of key one (first key) so it becomes the final key
		f6 = 6.0 / 24.0
		k1.setTime( f6 )

		# ensure in tangent slope of key one matches out tangent slope
		self.assertEqual( ti1.getSlope(), 30 )
		self.assertEqual( tf1.getSlope(), 30 )

		# ensure out tangent slope of key two matches in tangent slope
		self.assertEqual( ti2.getSlope(), 60 )
		self.assertEqual( tf2.getSlope(), 60 )

	def testKeySetInterpolationToConstrainedSlopeWithTieModeSlope( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f4 = 4.0 / 24.0
		f5 = 5.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k2 = Gaffer.Animation.Key( time = f4, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( k1 )
		curve.addKey( k2 )
		curve.addKey( k3 )

		ti2 = k2.tangentIn()
		tf2 = k2.tangentOut()

		# set the tangent slope of the middle key
		ti2.setSlope( 60 )
		self.assertEqual( ti2.getSlope(), 60 )
		self.assertEqual( tf2.getSlope(), 60 )

		# set interpolation of middle key to linear (does not use slope)
		k2.setInterpolation( Gaffer.Animation.Interpolation.Linear )
		self.assertFalse( ti2.slopeIsConstrained() )
		self.assertTrue( tf2.slopeIsConstrained() )

		# ensure in tangent slope of middle key not affected
		self.assertEqual( ti2.getSlope(), 60 )

	def testKeySetInterpolationToConstrainedScaleWithTieModeScale( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f4 = 4.0 / 24.0
		f5 = 5.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )
		k2 = Gaffer.Animation.Key( time = f4, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )

		curve.addKey( k1 )
		curve.addKey( k2 )
		curve.addKey( k3 )

		ti2 = k2.tangentIn()
		tf2 = k2.tangentOut()

		# set the tangent scale of the middle key
		ti2.setScale( 0.5 )
		tf2.setScale( 0.5 )
		self.assertEqual( ti2.getScale(), 0.5 )
		self.assertEqual( tf2.getScale(), 0.5 )

		# set tie mode to include scale
		k2.setTieMode( Gaffer.Animation.TieMode.Scale )

		# set interpolation of middle key to linear (does not use scale)
		k2.setInterpolation( Gaffer.Animation.Interpolation.Linear )
		self.assertFalse( ti2.scaleIsConstrained() )
		self.assertTrue( tf2.scaleIsConstrained() )

		# ensure in tangent scale of middle key not affected
		self.assertEqual( ti2.getScale(), 0.5 )

	def testKeyAddWithInterpolationConstrainedSlopeWithTieModeSlope( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f3 = 3.0 / 24.0
		f5 = 5.0 / 24.0
		f6 = 6.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k2 = Gaffer.Animation.Key( time = f3, interpolation = Gaffer.Animation.Interpolation.Linear, tieMode = Gaffer.Animation.TieMode.Slope )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k4 = Gaffer.Animation.Key( time = f6, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( k1 )
		curve.addKey( k3 )
		curve.addKey( k4 )

		ti3 = k3.tangentIn()
		tf3 = k3.tangentOut()

		# set the tangent slope of the third key to 60
		ti3.setSlope( 60 )
		self.assertEqual( ti3.getSlope(), 60 )
		self.assertEqual( tf3.getSlope(), 60 )

		# add key 2 with linear interpolation so that key 3 in tangent slope is no longer unconstrained
		curve.addKey( k2 )
		self.assertEqual( k2.parent(), curve )
		self.assertEqual( curve.getKey( k2.getTime() ), k2 )
		self.assertTrue( ti3.slopeIsConstrained() )
		self.assertFalse( tf3.slopeIsConstrained() )

		# ensure out tangent slope of third key not affected
		self.assertEqual( tf3.getSlope(), 60 )

	def testKeyAddWithInterpolationConstrainedScaleWithTieModeScale( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f3 = 3.0 / 24.0
		f5 = 5.0 / 24.0
		f6 = 6.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )
		k2 = Gaffer.Animation.Key( time = f3, interpolation = Gaffer.Animation.Interpolation.Linear, tieMode = Gaffer.Animation.TieMode.Manual )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )
		k4 = Gaffer.Animation.Key( time = f6, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )

		curve.addKey( k1 )
		curve.addKey( k3 )
		curve.addKey( k4 )

		ti3 = k3.tangentIn()
		tf3 = k3.tangentOut()

		# set the tangent scale of the third key to 0.87
		ti3.setScale( 0.87 )
		tf3.setScale( 0.87 )
		self.assertEqual( ti3.getScale(), 0.87 )
		self.assertEqual( tf3.getScale(), 0.87 )

		# set tie mode to include scale
		k3.setTieMode( Gaffer.Animation.TieMode.Scale )

		# add key 2 with linear interpolation so that key 3 in tangent scale is no longer unconstrained
		curve.addKey( k2 )
		self.assertEqual( k2.parent(), curve )
		self.assertEqual( curve.getKey( k2.getTime() ), k2 )
		self.assertTrue( ti3.scaleIsConstrained() )
		self.assertFalse( tf3.scaleIsConstrained() )

		# ensure out tangent scale of third key not affected
		self.assertEqual( tf3.getScale(), 0.87 )

	def testKeyAddWithInterpolationConstrainedSlopeEnsureTieSlopeNext( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f3 = 3.0 / 24.0
		f5 = 5.0 / 24.0
		f6 = 6.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Step, tieMode = Gaffer.Animation.TieMode.Slope )
		k2 = Gaffer.Animation.Key( time = f3, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Cubic, inSlope=0.0, outSlope=0.0, tieMode = Gaffer.Animation.TieMode.Slope )
		k4 = Gaffer.Animation.Key( time = f6, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( k1 )
		curve.addKey( k3 )
		curve.addKey( k4 )

		ti3 = k3.tangentIn()
		tf3 = k3.tangentOut()

		# in tangent of third key affected by step interpolation so slope should be constrained
		self.assertTrue( ti3.slopeIsConstrained() )
		self.assertEqual( ti3.getSlope(), 0 )

		# out tangent of third key affected by cubic interpolation so slope should be unconstrained
		self.assertFalse( tf3.slopeIsConstrained() )
		self.assertEqual( tf3.getSlope(), 0 )

		# set the out tangent slope of the third key to 60 in tangent slope should not be updated
		tf3.setSlope( 60 )
		self.assertEqual( ti3.getSlope(), 0 )
		self.assertEqual( tf3.getSlope(), 60 )

		# now add second key so that in tangent is affected by cubic interpolation and in tangent
		# slope of third key is unconstrained
		curve.addKey( k2 )
		self.assertEqual( k2.parent(), curve )
		self.assertEqual( curve.getKey( k2.getTime() ), k2 )
		self.assertFalse( ti3.slopeIsConstrained() )
		self.assertFalse( tf3.slopeIsConstrained() )

		# check that in tangent slope of third key that is now unconstrained is tied correctly to its opposite tangent
		self.assertEqual( ti3.getSlope(), 60 )

	def testKeyRemoveWithInterpolationConstrainedSlopeWithTieModeSlope( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f3 = 3.0 / 24.0
		f5 = 5.0 / 24.0
		f6 = 6.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Step, tieMode = Gaffer.Animation.TieMode.Slope )
		k2 = Gaffer.Animation.Key( time = f3, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k4 = Gaffer.Animation.Key( time = f6, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( k1 )
		curve.addKey( k2 )
		curve.addKey( k3 )
		curve.addKey( k4 )

		ti3 = k3.tangentIn()
		tf3 = k3.tangentOut()

		# set the tangent slope of the third key to 60
		ti3.setSlope( 60 )
		self.assertEqual( ti3.getSlope(), 60 )
		self.assertEqual( tf3.getSlope(), 60 )

		# remove key 2 so that key 3 in tangent affected by step interpolator
		curve.removeKey( k2 )
		self.assertIsNone( k2.parent() )
		self.assertEqual( curve.previousKey( k3.getTime() ), k1 )
		self.assertTrue( ti3.slopeIsConstrained() )
		self.assertFalse( tf3.slopeIsConstrained() )

		# ensure out tangent slope of third key not affected
		self.assertEqual( tf3.getSlope(), 60 )

	def testKeyRemoveWithInterpolationConstrainedScaleWithTieModeScale( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f3 = 3.0 / 24.0
		f5 = 5.0 / 24.0
		f6 = 6.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Step, tieMode = Gaffer.Animation.TieMode.Manual )
		k2 = Gaffer.Animation.Key( time = f3, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )
		k4 = Gaffer.Animation.Key( time = f6, interpolation = Gaffer.Animation.Interpolation.Bezier, tieMode = Gaffer.Animation.TieMode.Manual )

		curve.addKey( k1 )
		curve.addKey( k2 )
		curve.addKey( k3 )
		curve.addKey( k4 )

		ti3 = k3.tangentIn()
		tf3 = k3.tangentOut()

		# set the tangent scale of the third key to 0.87
		ti3.setScale( 0.87 )
		tf3.setScale( 0.87 )
		self.assertEqual( ti3.getScale(), 0.87 )
		self.assertEqual( tf3.getScale(), 0.87 )

		# set tie mode to include scale
		k3.setTieMode( Gaffer.Animation.TieMode.Scale )

		# remove key 2 so that key 3 in tangent affected by step interpolator
		curve.removeKey( k2 )
		self.assertIsNone( k2.parent() )
		self.assertEqual( curve.previousKey( k3.getTime() ), k1 )
		self.assertTrue( ti3.scaleIsConstrained() )
		self.assertFalse( tf3.scaleIsConstrained() )

		# ensure out tangent scale of third key not affected
		self.assertEqual( tf3.getScale(), 0.87 )

	def testKeyRemoveWithInterpolationConstrainedSlopeEnsureTieSlopeNext( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		curve = Gaffer.Animation.acquire( s["n"]["op1"] )

		f2 = 2.0 / 24.0
		f3 = 3.0 / 24.0
		f5 = 5.0 / 24.0
		f6 = 6.0 / 24.0
		k1 = Gaffer.Animation.Key( time = f2, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )
		k2 = Gaffer.Animation.Key( time = f3, interpolation = Gaffer.Animation.Interpolation.Step, tieMode = Gaffer.Animation.TieMode.Slope )
		k3 = Gaffer.Animation.Key( time = f5, interpolation = Gaffer.Animation.Interpolation.Cubic, inSlope=0.0, outSlope=0.0, tieMode = Gaffer.Animation.TieMode.Slope )
		k4 = Gaffer.Animation.Key( time = f6, interpolation = Gaffer.Animation.Interpolation.Cubic, tieMode = Gaffer.Animation.TieMode.Slope )

		curve.addKey( k1 )
		curve.addKey( k2 )
		curve.addKey( k3 )
		curve.addKey( k4 )

		ti3 = k3.tangentIn()
		tf3 = k3.tangentOut()

		# in tangent of third key affected by step interpolation so slope should be constrained
		self.assertTrue( ti3.slopeIsConstrained() )
		self.assertEqual( ti3.getSlope(), 0 )

		# out tangent of third key affected by cubic interpolation so slope should be unconstrained
		self.assertFalse( tf3.slopeIsConstrained() )
		self.assertEqual( tf3.getSlope(), 0 )

		# set the out tangent slope of the third key to 60 in tangent slope should not be updated
		tf3.setSlope( 60 )
		self.assertEqual( ti3.getSlope(), 0 )
		self.assertEqual( tf3.getSlope(), 60 )

		# remove second key so that in tangent of third key now affected by cubic interpolation of first key
		curve.removeKey( k2 )
		self.assertIsNone( k2.parent() )
		self.assertEqual( curve.previousKey( k3.getTime() ), k1 )
		self.assertFalse( ti3.slopeIsConstrained() )
		self.assertFalse( tf3.slopeIsConstrained() )

		# check that in tangent slope of third key that is now unconstrained is tied correctly to its opposite tangent
		self.assertEqual( ti3.getSlope(), 60 )

if __name__ == "__main__":
	unittest.main()
