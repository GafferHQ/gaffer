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

		k = Gaffer.Animation.Key()
		self.assertEqual( k.getTime(), 0 )
		self.assertEqual( k.getValue(), 0 )
		self.assertEqual( k.getInterpolation(), Gaffer.Animation.defaultInterpolation() )
		self.assertFalse( k.isActive() )
		self.assertIsNone( k.parent() )

		a = math.pi
		b = math.e
		k = Gaffer.Animation.Key( a, b, Gaffer.Animation.Interpolation.Constant )
		self.assertFloat32Equal( k.getTime(), a )
		self.assertFloat32Equal( k.getValue(), b )
		self.assertEqual( k.getInterpolation(), Gaffer.Animation.Interpolation.Constant )
		self.assertFalse( k.isActive() )
		self.assertIsNone( k.parent() )

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

	def testInsertKeyFirstNoValue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		time = 10
		self.assertFalse( curve.hasKey( time ) )
		k = curve.insertKey( time )
		self.assertIsNone( k )
		self.assertFalse( curve.hasKey( time ) )

	def testInsertKeyBeforeFirstNoValue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		k = Gaffer.Animation.Key( 10, 5 )
		curve.addKey( k )

		time = 5
		self.assertFalse( curve.hasKey( time ) )
		k = curve.insertKey( time )
		self.assertIsNone( k )
		self.assertFalse( curve.hasKey( time ) )

	def testInsertKeyAfterFinalNoValue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )

		k = Gaffer.Animation.Key( 10, 5 )
		curve.addKey( k )

		time = 15
		self.assertFalse( curve.hasKey( time ) )
		k = curve.insertKey( time )
		self.assertIsNone( k )
		self.assertFalse( curve.hasKey( time ) )

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

		def assertKeysEqual( k0, k1 ) :

			self.assertEqual( k0.getTime(), k1.getTime() )
			self.assertEqual( k0.getValue(), k1.getValue() )
			self.assertEqual( k0.getInterpolation(), k1.getInterpolation() )

		def assertAnimation( script ) :

			curve = Gaffer.Animation.acquire( script["n"]["user"]["f"] )
			assertKeysEqual( curve.getKey( 0 ),  Gaffer.Animation.Key( 0, 0, Gaffer.Animation.Interpolation.Linear ) )
			assertKeysEqual( curve.getKey( 1 ),  Gaffer.Animation.Key( 1, 1, Gaffer.Animation.Interpolation.Linear ) )
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

if __name__ == "__main__":
	unittest.main()
