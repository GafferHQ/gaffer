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
		self.assertEqual( k.type, Gaffer.Animation.Type.Invalid )
		self.assertFalse( k )

		k = Gaffer.Animation.Key( 0, 1, Gaffer.Animation.Type.Step )
		self.assertTrue( k )
		self.assertEqual( k.time, 0 )
		self.assertEqual( k.value, 1 )
		self.assertEqual( k.type, Gaffer.Animation.Type.Step )

		k.time = 1
		k.value = 0
		k.type = Gaffer.Animation.Type.Linear
		self.assertEqual( k.time, 1 )
		self.assertEqual( k.value, 0 )
		self.assertEqual( k.type, Gaffer.Animation.Type.Linear )

		k2 = Gaffer.Animation.Key( k )
		self.assertEqual( k, k2 )
		k2.time = 10
		self.assertNotEqual( k, k2 )

	def testKeyRepr( self ) :

		k = Gaffer.Animation.Key()
		self.assertEqual( k, eval( repr( k ) ) )

		k = Gaffer.Animation.Key( 0, 1, Gaffer.Animation.Type.Step )
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
		self.assertFalse( curve.hasKey( key.time ) )

		curve.addKey( key )
		self.assertTrue( curve.hasKey( key.time ) )

		self.assertEqual( curve.getKey( key.time ), key )

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

	def testRemoveKey( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		key = Gaffer.Animation.Key( time = 10, value = 10 )
		curve.addKey( key )
		self.assertEqual( curve.getKey( key.time ), key )
		self.assertEqual( curve.closestKey( 0 ), key )

		curve.removeKey( key.time )
		self.assertFalse( curve.getKey( key.time ) )
		self.assertFalse( curve.closestKey( 0 ) )

	def testSingleKey( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		curve.addKey( Gaffer.Animation.Key( 0, 1, Gaffer.Animation.Type.Linear ) )

		with Gaffer.Context() as c :
			for t in range( -10, 10 ) :
				c.setTime( t )
				self.assertEqual( s["n"]["user"]["f"].getValue(), 1 )

	def testLinear( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		curve = Gaffer.Animation.acquire( s["n"]["user"]["f"] )
		curve.addKey( Gaffer.Animation.Key( 0, 1, Gaffer.Animation.Type.Linear ) )
		curve.addKey( Gaffer.Animation.Key( 1, 3, Gaffer.Animation.Type.Linear ) )

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
		curve.addKey( Gaffer.Animation.Key( 1, 1, Gaffer.Animation.Type.Linear ) )
		curve.addKey( Gaffer.Animation.Key( 2, 2, Gaffer.Animation.Type.Step ) )

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
		curve.addKey( Gaffer.Animation.Key( 0, 0, Gaffer.Animation.Type.Linear ) )
		curve.addKey( Gaffer.Animation.Key( 1, 1, Gaffer.Animation.Type.Linear ) )

		def assertAnimation( script ) :

			curve = Gaffer.Animation.acquire( script["n"]["user"]["f"] )
			self.assertEqual( curve.getKey( 0 ),  Gaffer.Animation.Key( 0, 0, Gaffer.Animation.Type.Linear ) )
			self.assertEqual( curve.getKey( 1 ),  Gaffer.Animation.Key( 1, 1, Gaffer.Animation.Type.Linear ) )
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

		with Gaffer.UndoContext( s ) :
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

		with Gaffer.UndoContext( s ) :
			curve.addKey( key1 )
			self.assertEqual( curve.getKey( 1 ), key1 )

		with Gaffer.UndoContext( s ) :
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
		self.assertEqual( curve.getKey( key.time ), key )

		with Gaffer.UndoContext( s ) :
			curve.removeKey( key.time )
			self.assertFalse( curve.hasKey( key.time ) )

		s.undo()
		self.assertEqual( curve.getKey( key.time ), key )

		s.redo()
		self.assertFalse( curve.hasKey( key.time ) )

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

		s["b"].promotePlug( s["b"]["n"]["op1"] )
		s["b"].promotePlug( s["b"]["n"]["sum"] )

		self.assertTrue( s["b"].canPromotePlug( s["b"]["n"]["op2"] ) )

		op2Curve = Gaffer.Animation.acquire( s["b"]["n"]["op2"] )

		# Cannot promote an animated plug, because it has an input.
		self.assertFalse( s["b"].canPromotePlug( s["b"]["n"]["op2"] ) )

		op2Curve.addKey( Gaffer.Animation.Key( 0, 0, Gaffer.Animation.Type.Step ) )
		op2Curve.addKey( Gaffer.Animation.Key( 1, 1, Gaffer.Animation.Type.Step ) )

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

if __name__ == "__main__":
	unittest.main()
