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

import gc
import inspect
import os
import subprocess
import threading
import time
import imath
import six

import IECore

import Gaffer
import GafferTest

class ValuePlugTest( GafferTest.TestCase ) :

	def testCacheMemoryLimit( self ) :

		n = GafferTest.CachingTestNode()

		n["in"].setValue( "d" )

		v1 = n["out"].getValue( _copy=False )
		v2 = n["out"].getValue( _copy=False )

		self.assertEqual( v1, v2 )
		self.assertEqual( v1, IECore.StringData( "d" ) )

		# the objects should be one and the same, as the second computation
		# should have shortcut and returned a cached result.
		self.assertTrue( v1.isSame( v2 ) )

		Gaffer.ValuePlug.setCacheMemoryLimit( 0 )

		v3 = n["out"].getValue( _copy=False )
		self.assertEqual( v3, IECore.StringData( "d" ) )

		# the objects should be different, as we cleared the cache.
		self.assertFalse( v3.isSame( v2 ) )

		Gaffer.ValuePlug.setCacheMemoryLimit( self.__originalCacheMemoryLimit )

		v1 = n["out"].getValue( _copy=False )
		v2 = n["out"].getValue( _copy=False )

		self.assertEqual( v1, v2 )
		self.assertEqual( v1, IECore.StringData( "d" ) )

		# the objects should be one and the same, as we reenabled the cache.
		self.assertTrue( v1.isSame( v2 ) )

		Gaffer.ValuePlug.clearCache()
		self.assertEqual( Gaffer.ValuePlug.cacheMemoryUsage(), 0 )

		v3 = n["out"].getValue( _copy=False )
		self.assertFalse( v3.isSame( v2 ) )

		v4 = n["out"].getValue( _copy=False )
		self.assertTrue( v4.isSame( v3 ) )

	def testSettable( self ) :

		p1 = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.In )
		self.assertTrue( p1.settable() )

		p2 = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		self.assertFalse( p2.settable() )

		p1.setInput( p2 )
		self.assertFalse( p1.settable() )

	def testUncacheabilityPropagates( self ) :

		n = GafferTest.CachingTestNode()
		n["in"].setValue( "pig" )

		p1 = Gaffer.ObjectPlug( "p1", Gaffer.Plug.Direction.In, IECore.IntData( 10 ) )
		p2 = Gaffer.ObjectPlug( "p2", Gaffer.Plug.Direction.In, IECore.IntData( 20 ) )
		p3 = Gaffer.ObjectPlug( "p3", Gaffer.Plug.Direction.In, IECore.IntData( 30 ) )

		p1.setInput( n["out"] )
		p2.setInput( p1 )
		p3.setInput( p2 )

		o2 = p2.getValue( _copy = False )
		o3 = p3.getValue( _copy = False )

		self.assertEqual( o2, IECore.StringData( "pig" ) )
		self.assertEqual( o3, IECore.StringData( "pig" ) )
		self.assertTrue( o2.isSame( o3 ) ) # they share cache entries

		n["out"].setFlags( Gaffer.Plug.Flags.Cacheable, False )

		o2 = p2.getValue( _copy = False )
		o3 = p3.getValue( _copy = False )

		self.assertEqual( o2, IECore.StringData( "pig" ) )
		self.assertEqual( o3, IECore.StringData( "pig" ) )
		self.assertFalse( o2.isSame( o3 ) ) # they shouldn't share cache entries

	def testSetValueSignalsDirtiness( self ) :

		n = Gaffer.Node()
		n["p"] = Gaffer.IntPlug()

		cs = GafferTest.CapturingSlot( n.plugDirtiedSignal() )

		n["p"].setValue( 10 )

		self.assertEqual( len( cs ), 1 )
		self.assertTrue( cs[0][0].isSame( n["p"] ) )

		n["p"].setValue( 10 )

		self.assertEqual( len( cs ), 1 )

	def testDirtyCountPlug( self ) :

		# The dirtyCount is relative to the current dirtyCountEpoch
		refPlug = Gaffer.ValuePlug()
		epoch = refPlug.dirtyCount()


		i = Gaffer.IntPlug()
		self.assertEqual( i.dirtyCount(), epoch + 0 )
		i.setValue( 10 )
		self.assertEqual( i.dirtyCount(), epoch + 1 )
		i.setValue( 20 )
		self.assertEqual( i.dirtyCount(), epoch + 2 )

		i2 = Gaffer.IntPlug()
		v = Gaffer.ValuePlug()

		self.assertEqual( i2.dirtyCount(), epoch + 0 )
		self.assertEqual( v.dirtyCount(), epoch + 0 )

		# Need to parent to a node before dirtying based on plug reparenting will work
		n = Gaffer.Node()
		n.addChild( v )

		self.assertEqual( v.dirtyCount(), epoch + 1 )
		self.assertEqual( i2.dirtyCount(), epoch + 0 )

		# Parenting dirties both parent and child
		v.addChild( i2 )
		self.assertEqual( v.dirtyCount(), epoch + 2 )
		self.assertEqual( i2.dirtyCount(), epoch + 1 )

		# Setting the value of the child should also dirty the parent
		i2.setValue( 10 )
		self.assertEqual( v.dirtyCount(), epoch + 3 )
		self.assertEqual( i2.dirtyCount(), epoch + 2 )

	def testCopyPasteDoesntRetainComputedValues( self ) :

		s = Gaffer.ScriptNode()

		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()

		s["add1"]["op1"].setValue( 2 )
		s["add1"]["op2"].setValue( 3 )
		s["add2"]["op1"].setInput( s["add1"]["sum"] )
		s["add2"]["op2"].setValue( 0 )

		self.assertEqual( s["add2"]["sum"].getValue(), 5 )

		ss = s.serialise( filter = Gaffer.StandardSet( [ s["add2"] ] ) )

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertTrue( s["add2"]["op1"].getInput() is None )
		self.assertEqual( s["add2"]["op1"].getValue(), 0 )
		self.assertEqual( s["add2"]["sum"].getValue(), 0 )

	def testSerialisationOmitsDefaultValues( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		self.assertEqual( s["n"]["op1"].getValue(), s["n"]["op1"].defaultValue() )
		self.assertEqual( s["n"]["op2"].getValue(), s["n"]["op2"].defaultValue() )

		self.assertFalse( "setValue" in s.serialise() )

		s["n"]["op1"].setValue( 10 )

		self.assertTrue( "[\"op1\"].setValue" in s.serialise() )

	def testFloatPlugOmitsDefaultValues( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertFalse( "setValue" in s.serialise() )

		s["n"]["f"].setValue( 10.1 )

		self.assertTrue( "[\"f\"].setValue" in s.serialise() )

	def testBoolPlugOmitsDefaultValues( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["f"] = Gaffer.BoolPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertFalse( "setValue" in s.serialise() )

		s["n"]["f"].setValue( True )

		self.assertTrue( "[\"f\"].setValue" in s.serialise() )

	def testBoolPlugOmitsDefaultValuesWhenDefaultIsTrue( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["f"] = Gaffer.BoolPlug( defaultValue = True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertFalse( "setValue" in s.serialise() )

		s["n"]["f"].setValue( False )

		self.assertTrue( "[\"f\"].setValue" in s.serialise() )

	def testCreateCounterpart( self ) :

		p = Gaffer.ValuePlug()
		p["i"] = Gaffer.IntPlug()
		p["f"] = Gaffer.FloatPlug()

		p2 = p.createCounterpart( "p2", Gaffer.Plug.Direction.In )
		self.assertEqual( p2.keys(), [ "i", "f" ] )
		self.assertTrue( isinstance( p2["i"], Gaffer.IntPlug ) )
		self.assertTrue( isinstance( p2["f"], Gaffer.FloatPlug ) )
		self.assertTrue( isinstance( p2, Gaffer.ValuePlug ) )

	def testPrecomputedHashOptimisation( self ) :

		n = GafferTest.CachingTestNode()
		n["in"].setValue( "a" )

		a1 = n["out"].getValue( _copy = False )
		self.assertEqual( a1, IECore.StringData( "a" ) )
		self.assertEqual( n.numHashCalls, 1 )

		# We apply some leeway in our test for how many hash calls are
		# made - a good ValuePlug implementation will probably avoid
		# unecessary repeated calls in most cases, but it's not
		# what this unit test is about.
		a2 = n["out"].getValue( _copy = False )
		self.assertTrue( a2.isSame( a1 ) )
		self.assertTrue( n.numHashCalls == 1 or n.numHashCalls == 2 )

		h = n["out"].hash()
		self.assertTrue( n.numHashCalls >= 1 and n.numHashCalls <= 3 )
		numHashCalls = n.numHashCalls

		# What we care about is that calling getValue() with a precomputed hash
		# definitely doesn't recompute the hash again.
		a3 = n["out"].getValue( _copy = False, _precomputedHash = h )
		self.assertEqual( n.numHashCalls, numHashCalls )
		self.assertTrue( a3.isSame( a1 ) )

	def testSerialisationOfChildValues( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["v"] = Gaffer.ValuePlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["v"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["v"]["i"].setValue( 10 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"]["user"]["v"]["i"].getValue(), 10 )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.CompoundPlugNode()
		s["n2"] = GafferTest.CompoundPlugNode()

		s["n1"]["p"]["f"].setValue( 10 )
		s["n1"]["p"]["s"].setInput( s["n2"]["p"]["s"] )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n1"]["p"]["f"].getValue(), 10 )
		self.assertTrue( s["n1"]["p"]["s"].getInput().isSame( s["n2"]["p"]["s"] ) )

	def testDynamicSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()
		s["n1"]["p"] = Gaffer.ValuePlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n1"]["p"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n1"]["p"]["f"].setValue( 10 )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n1"]["p"]["f"].getValue(), 10 )

	def testMasterConnectionTracksChildConnections( self ) :

		c = Gaffer.ValuePlug( "c" )
		c["f1"] = Gaffer.FloatPlug()
		c["f2"] = Gaffer.FloatPlug()
		n = Gaffer.Node()
		n["c"] = c

		c2 = Gaffer.ValuePlug( "c" )
		c2["f1"] = Gaffer.FloatPlug()
		c2["f2"] = Gaffer.FloatPlug()
		n2 = Gaffer.Node()
		n2["c"] = c2

		n2["c"]["f1"].setInput( n["c"]["f1"] )
		n2["c"]["f2"].setInput( n["c"]["f2"] )
		self.assertTrue( n2["c"].getInput().isSame( n["c"] ) )

		n2["c"]["f2"].setInput( None )
		self.assertIsNone( n2["c"].getInput() )

		n2["c"]["f2"].setInput( n["c"]["f2"] )
		self.assertTrue( n2["c"].getInput().isSame( n["c"] ) )

		c["f3"] = Gaffer.FloatPlug()
		c2["f3"] = Gaffer.FloatPlug()

		self.assertIsNone( n2["c"].getInput() )

		n2["c"]["f3"].setInput( n["c"]["f3"] )
		self.assertTrue( n2["c"].getInput().isSame( n["c"] ) )

	def testInputChangedCrash( self ) :

		ca = Gaffer.ValuePlug( "ca" )
		ca["fa1"] = Gaffer.FloatPlug()
		ca["fa2"] = Gaffer.FloatPlug()
		na = Gaffer.Node()
		na["ca"] = ca

		cb = Gaffer.ValuePlug( "cb" )
		cb["fb1"] = Gaffer.FloatPlug()
		cb["fb2"] = Gaffer.FloatPlug()
		nb = Gaffer.Node()
		nb["cb"] = cb

		nb["cb"]["fb1"].setInput( na["ca"]["fa1"] )

		del ca, na, cb, nb
		while gc.collect() :
			pass
		IECore.RefCounted.collectGarbage()

	def testDirtyPropagation( self ) :

		n = GafferTest.CompoundPlugNode()

		dirtyPlugs = GafferTest.CapturingSlot( n.plugDirtiedSignal() )

		n["p"]["f"].setValue( 100 )

		self.assertEqual( len( dirtyPlugs ), 4 )

		self.assertTrue( dirtyPlugs[0][0].isSame( n["p"]["f"] ) )
		self.assertTrue( dirtyPlugs[1][0].isSame( n["p"] ) )
		self.assertTrue( dirtyPlugs[2][0].isSame( n["o"]["f"] ) )
		self.assertTrue( dirtyPlugs[3][0].isSame( n["o"] ) )

	def testPlugSetPropagation( self ) :

		c = Gaffer.ValuePlug()
		c["f1"] = Gaffer.FloatPlug()

		n = Gaffer.Node()
		n["c"] = c

		def setCallback( plug ) :

			if plug.isSame( c ) :
				self.set = True

		n.plugSetSignal().connect( setCallback, scoped = False )

		self.set = False

		c["f1"].setValue( 10 )

		self.assertTrue( self.set )

	def testMultipleLevelsOfPlugSetPropagation( self ) :

		c = Gaffer.ValuePlug( "c" )
		c["c1"] = Gaffer.ValuePlug()
		c["c1"]["f1"] = Gaffer.FloatPlug()

		n = Gaffer.Node()
		n["c"] = c

		def setCallback( plug ) :

			self.setPlugs.append( plug.getName() )

		n.plugSetSignal().connect( setCallback, scoped = False )

		self.setPlugs = []

		c["c1"]["f1"].setValue( 10 )

		self.assertEqual( len( self.setPlugs ), 3 )
		self.assertEqual( self.setPlugs, [ "f1", "c1", "c" ] )

	def testMultipleLevelsOfPlugSetPropagationWithDifferentParentingOrder( self ) :

		n = Gaffer.Node()
		n["c"] = Gaffer.ValuePlug()

		n["c"]["c1"] = Gaffer.ValuePlug()
		n["c"]["c1"]["f1"] = Gaffer.FloatPlug()

		def setCallback( plug ) :

			self.setPlugs.append( plug.getName() )

		n.plugSetSignal().connect( setCallback, scoped = False )

		self.setPlugs = []

		n["c"]["c1"]["f1"].setValue( 10 )

		self.assertEqual( len( self.setPlugs ), 3 )
		self.assertIn( "c", self.setPlugs )
		self.assertIn( "c1", self.setPlugs )
		self.assertIn( "f1", self.setPlugs )

	def testAcceptsInput( self ) :

		i = Gaffer.ValuePlug()
		o = Gaffer.ValuePlug( direction=Gaffer.Plug.Direction.Out )
		s = Gaffer.StringPlug( direction=Gaffer.Plug.Direction.Out )

		i.addChild( Gaffer.IntPlug() )
		o.addChild( Gaffer.IntPlug( direction=Gaffer.Plug.Direction.Out ) )

		self.assertTrue( i.acceptsInput( o ) )
		self.assertFalse( i.acceptsInput( s ) )

	def testAcceptsNoneInput( self ) :

		p = Gaffer.ValuePlug( "hello" )
		self.assertTrue( p.acceptsInput( None ) )

	def testSerialisationOfMasterConnection( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.CompoundPlugNode()
		s["n2"] = GafferTest.CompoundPlugNode()

		s["n1"]["p"].setInput( s["n2"]["p"] )
		self.assertTrue( s["n1"]["p"].getInput().isSame( s["n2"]["p"] ) )
		self.assertTrue( s["n1"]["p"]["f"].getInput().isSame( s["n2"]["p"]["f"] ) )
		self.assertTrue( s["n1"]["p"]["s"].getInput().isSame( s["n2"]["p"]["s"] ) )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertTrue( s["n1"]["p"].getInput().isSame( s["n2"]["p"] ) )
		self.assertTrue( s["n1"]["p"]["f"].getInput().isSame( s["n2"]["p"]["f"] ) )
		self.assertTrue( s["n1"]["p"]["s"].getInput().isSame( s["n2"]["p"]["s"] ) )

	def testSetInputShortcut( self ) :

		n1 = Gaffer.Node()
		n1["c"] = Gaffer.Plug()

		n2 = Gaffer.Node()
		n2["c"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )

		cs = GafferTest.CapturingSlot( n1.plugInputChangedSignal() )
		self.assertEqual( len( cs ), 0 )

		n1["c"].setInput( n2["c"] )
		# we should get a signal the first time
		self.assertEqual( len( cs ), 1 )

		n1["c"].setInput( n2["c"] )
		# but the second time there should be no signal,
		# because it was the same.
		self.assertEqual( len( cs ), 1 )

	def testSetInputWithoutParent( self ) :

		c1 = Gaffer.Plug( direction=Gaffer.Plug.Direction.Out )
		c1["n"] = Gaffer.IntPlug( direction=Gaffer.Plug.Direction.Out )

		c2 = Gaffer.Plug()
		c2["n"] = Gaffer.IntPlug()

		c2.setInput( c1 )
		self.assertEqual( c2.getInput(), c1 )

	def testCanMakeSomeConnectionsWhenSizesDontMatch( self ) :

		n = Gaffer.Node()

		n["c1"] = Gaffer.ValuePlug( direction = Gaffer.Plug.Direction.In )
		n["c1"]["i"] = Gaffer.IntPlug()

		n["c2"] = Gaffer.ValuePlug( direction = Gaffer.Plug.Direction.Out )
		n["c2"]["i1"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		n["c2"]["i2"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )

		n["c1"]["i"].setInput( n["c2"]["i1"] )

		self.assertTrue( n["c1"]["i"].getInput().isSame( n["c2"]["i1"] ) )
		self.assertTrue( n["c1"].getInput().isSame( n["c2"] ) )

	def testSerialisationOfDynamicPlugsOnNondynamicParent( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.CompoundPlugNode()

		s["n"]["nonDynamicParent"]["dynamicPlug"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["nonDynamicParent"]["dynamicPlug"].setValue( 10 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"]["nonDynamicParent"]["dynamicPlug"].getValue(), 10 )

	def testChildAdditionEmitsPlugSet( self ) :

		n = Gaffer.Node()

		n["c"] = Gaffer.ValuePlug()
		n["c"]["d"] = Gaffer.ValuePlug()

		cs = GafferTest.CapturingSlot( n.plugSetSignal() )

		n["c"]["d"]["e"] = Gaffer.IntPlug()

		self.assertEqual( len( cs ), 2 )
		self.assertEqual( cs[0][0], n["c"]["d"] )
		self.assertEqual( cs[1][0], n["c"] )

	def testNoNonValuePlugChildren( self ) :

		v = Gaffer.ValuePlug()
		p = Gaffer.Plug()

		self.assertFalse( v.acceptsChild( p ) )
		self.assertRaises( RuntimeError, v.addChild, p )

	def testDerivingInPython( self ) :

		class TestValuePlug( Gaffer.ValuePlug ) :

			def __init__( self, name = "TestValuePlug", direction = Gaffer.Plug.Direction.In, flags = Gaffer.Plug.Flags.None_ ) :

				Gaffer.ValuePlug.__init__( self, name, direction, flags )

			def acceptsChild( self, child ) :

				if not Gaffer.ValuePlug.acceptsChild( self, child ) :
					return False

				return isinstance( child, Gaffer.IntPlug )

		IECore.registerRunTimeTyped( TestValuePlug )

		# check the constructor

		p = TestValuePlug()
		self.assertEqual( p.getName(), "TestValuePlug" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p.getFlags(), Gaffer.Plug.Flags.None_ )

		p = TestValuePlug( name = "p", direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( p.getName(), "p" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.Out )
		self.assertEqual( p.getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		# check that acceptsChild can be overridden

		p = TestValuePlug()

		self.assertRaises( RuntimeError, p.addChild, Gaffer.FloatPlug() )

		p.addChild( Gaffer.IntPlug() )

		# check that the fact the plug has been wrapped solves the object identity problem

		p = TestValuePlug()
		n = Gaffer.Node()
		n["p"] = p

		self.assertTrue( n["p"] is p )

	def testNullInputPropagatesToChildren( self ) :

		n = Gaffer.Node()
		n["user"]["c"] = Gaffer.ValuePlug()
		n["user"]["c"]["o"] = Gaffer.IntPlug()
		n["user"]["c"]["i"] = Gaffer.IntPlug()

		n["user"]["c"]["i"].setInput( n["user"]["c"]["o"] )
		self.assertTrue( n["user"]["c"]["i"].getInput().isSame( n["user"]["c"]["o"] ) )

		n["user"]["c"].setInput( None )
		self.assertTrue( n["user"]["c"]["i"].getInput() is None )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testCacheOverhead( self ) :

		m = GafferTest.MultiplyNode()
		m["product"].getValue()

		# This should be about the fastest we can pull an item from the cache - a single float that is already cached
		with GafferTest.TestRunner.PerformanceScope() :
			GafferTest.repeatGetValue( m["product"], 5000000 )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testContentionForOneItem( self ) :
		m = GafferTest.MultiplyNode()
		m["product"].getValue()

		with GafferTest.TestRunner.PerformanceScope() :
			GafferTest.parallelGetValue( m["product"], 10000000 )

	def testIsSetToDefault( self ) :

		n1 = GafferTest.AddNode()
		self.assertTrue( n1["op1"].isSetToDefault() )
		self.assertTrue( n1["op2"].isSetToDefault() )
		self.assertFalse( n1["sum"].isSetToDefault() )

		n1["op1"].setValue( 10 )
		self.assertFalse( n1["op1"].isSetToDefault() )
		self.assertTrue( n1["op2"].isSetToDefault() )

		n1["op1"].setToDefault()
		self.assertTrue( n1["op1"].isSetToDefault() )
		self.assertTrue( n1["op2"].isSetToDefault() )

		n2 = GafferTest.AddNode()
		self.assertTrue( n2["op1"].isSetToDefault() )
		self.assertTrue( n2["op2"].isSetToDefault() )
		self.assertFalse( n2["sum"].isSetToDefault() )

		n2["op1"].setInput( n1["op1"] )
		# Receiving a static value via an input. We know
		# it can have only one value for all contexts,
		# and can be confident that it is set to the default.
		self.assertTrue( n2["op1"].isSetToDefault() )
		self.assertEqual( n2["op1"].getValue(), n2["op1"].defaultValue() )
		n1["op1"].setValue( 1 )
		# Until it provides a non-default value, that is.
		self.assertFalse( n2["op1"].isSetToDefault() )

		n1["op1"].setValue( 0 )
		n2["op2"].setInput( n1["sum"] )
		# Driven by a compute, so not considered to be
		# at the default, even if it the result happens
		# to be equal in this context.
		self.assertFalse( n2["op2"].isSetToDefault() )
		self.assertEqual( n2["op2"].getValue(), n2["op2"].defaultValue() )

	def testCancellationDuringCompute( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		s["e"] = Gaffer.Expression()
		s["e"].setExpression( inspect.cleandoc(
			"""
			IECore.Canceller.check( context.canceller() )
			parent['n']['op1'] = 40
			"""
		) )

		canceller = IECore.Canceller()
		canceller.cancel()

		with Gaffer.Context( s.context(), canceller ) :
			with self.assertRaises( IECore.Cancelled ) :
				s["n"]["sum"].getValue()

		canceller = IECore.Canceller()

		with Gaffer.Context( s.context(), canceller ) :
			self.assertEqual( s["n"]["sum"].getValue(), 40 )

	def testClearHashCache( self ) :

		node = GafferTest.AddNode()
		node["sum"].getValue()

		with Gaffer.PerformanceMonitor() as m :
			node["sum"].getValue()
		self.assertEqual( m.plugStatistics( node["sum"] ).hashCount, 0 )

		Gaffer.ValuePlug.clearHashCache()
		with Gaffer.PerformanceMonitor() as m :
			node["sum"].getValue()
		self.assertEqual( m.plugStatistics( node["sum"] ).hashCount, 1 )

	def testResetDefault( self ) :

		script = Gaffer.ScriptNode()

		script["node"] = Gaffer.Node()
		script["node"]["user"]["i"] = Gaffer.IntPlug( defaultValue = 1, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		script["node"]["user"]["v"] = Gaffer.V3iPlug( defaultValue = imath.V3i( 1, 2, 3 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		def assertPreconditions( script ) :

			self.assertTrue( script["node"]["user"]["i"].isSetToDefault() )
			self.assertEqual( script["node"]["user"]["i"].defaultValue(), 1 )
			self.assertEqual( script["node"]["user"]["i"].getValue(), 1 )

			self.assertTrue( script["node"]["user"]["v"].isSetToDefault() )
			self.assertEqual( script["node"]["user"]["v"].defaultValue(), imath.V3i( 1, 2, 3 ) )
			self.assertEqual( script["node"]["user"]["v"].getValue(), imath.V3i( 1, 2, 3 ) )

		assertPreconditions( script )

		with Gaffer.UndoScope( script ) :

			script["node"]["user"]["i"].setValue( 2 )
			script["node"]["user"]["i"].resetDefault()

			script["node"]["user"]["v"].setValue( imath.V3i( 10, 11, 12 ) )
			script["node"]["user"]["v"].resetDefault()

		def assertPostconditions( script ) :

			self.assertTrue( script["node"]["user"]["i"].isSetToDefault() )
			self.assertEqual( script["node"]["user"]["i"].defaultValue(), 2 )
			self.assertEqual( script["node"]["user"]["i"].getValue(), 2 )

			self.assertTrue( script["node"]["user"]["v"].isSetToDefault() )
			self.assertEqual( script["node"]["user"]["v"].defaultValue(), imath.V3i( 10, 11, 12 ) )
			self.assertEqual( script["node"]["user"]["v"].getValue(), imath.V3i( 10, 11, 12 ) )

		script.undo()
		assertPreconditions( script )

		script.redo()
		assertPostconditions( script )

		script.undo()
		assertPreconditions( script )

		script.redo()
		assertPostconditions( script )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )
		assertPostconditions( script2 )

	def testCacheValidation( self ) :

		defaultHashCacheMode = Gaffer.ValuePlug.getHashCacheMode()
		Gaffer.ValuePlug.setHashCacheMode( Gaffer.ValuePlug.HashCacheMode.Checked )
		try:

			m = GafferTest.MultiplyNode( "test", True )
			m["op1"].setValue( 2 )
			m["op2"].setValue( 3 )
			self.assertEqual( m["product"].getValue(), 6 )

			m["op2"].setValue( 4 )
			exception = None
			try:
				m["product"].getValue()
			except Exception as e:
				exception = e

			self.assertEqual( type( exception ), Gaffer.ProcessException )
			self.assertEqual( str( exception ), "test.product : Detected undeclared dependency. Fix DependencyNode::affects() implementation." )

			# Make sure the plug with the actual issue is reported, when queried from a downstream network
			m2 = GafferTest.MultiplyNode( "second" )
			m2["op1"].setInput( m["product"] )
			m2["op2"].setValue( 5 )

			exception = None
			try:
				m2["product"].getValue()
			except Exception as e:
				exception = e

			self.assertEqual( type( exception ), Gaffer.ProcessException )
			self.assertEqual( str( exception ), "test.product : Detected undeclared dependency. Fix DependencyNode::affects() implementation." )

		finally:
			Gaffer.ValuePlug.setHashCacheMode( defaultHashCacheMode )

	def testDefaultHash( self ) :

		# Plug with single value

		self.assertNotEqual( Gaffer.IntPlug().defaultHash(), IECore.MurmurHash() )
		self.assertEqual( Gaffer.IntPlug().defaultHash(), Gaffer.IntPlug().defaultHash() )
		self.assertNotEqual( Gaffer.IntPlug().defaultHash(), Gaffer.IntPlug( defaultValue = 2 ).defaultHash() )
		self.assertEqual( Gaffer.IntPlug().defaultHash(), Gaffer.IntPlug().hash() )

		# Compound plugs

		self.assertNotEqual( Gaffer.V2iPlug().defaultHash(), IECore.MurmurHash() )
		self.assertEqual( Gaffer.V2iPlug().defaultHash(), Gaffer.V2iPlug().defaultHash() )
		self.assertNotEqual( Gaffer.V2iPlug().defaultHash(), Gaffer.V2iPlug( defaultValue = imath.V2i( 0, 1 ) ).defaultHash() )
		self.assertNotEqual( Gaffer.V2iPlug().defaultHash(), Gaffer.V3iPlug().defaultHash() )
		self.assertEqual( Gaffer.V2iPlug().defaultHash(), Gaffer.V2iPlug().hash() )

	def testExceptionDuringParallelEval( self ) :

		# This only caused a problem when using GAFFER_PYTHONEXPRESSION_CACHEPOLICY=TaskCollaboration
		# with a TaskMutex without a properly isolated task_group so that exceptions in one thread
		# can cancel the other.  We're adding a more specific test for this to TaskMutex, so we're not
		# expecting this to catch anything, but it's still a valid test

		m = GafferTest.MultiplyNode()

		m["e"] = Gaffer.Expression()
		m["e"].setExpression( inspect.cleandoc(
			"""
			if context["testVar"]%10 == 9:
				raise BaseException( "Foo" )
			parent['op1'] = 1
			"""
		) )

		with six.assertRaisesRegex( self, BaseException, "Foo" ):
			GafferTest.parallelGetValue( m["product"], 10000, "testVar" )

	def testCancellationOfSecondGetValueCall( self ) :

		## \todo Should just be checking `tbb.global_control.active_value( max_allowed_parallelism )`
		# to get the true limit set by `-threads` argument. But IECore's Python
		# binding of `global_control` doesn't expose that yet.
		if IECore.hardwareConcurrency() < 3 and "VALUEPLUGTEST_SUBPROCESS" not in os.environ :

			# This test requires at least 3 TBB threads (including the main
			# thread), because we need the second enqueued BackgroundTask to
			# start execution before the first one has completed. If we have
			# insufficient threads then we end up in deadlock, so to avoid this
			# we relaunch in a subprocess with sufficient threads.
			#
			# Note : deadlock only ensues because the first task will never
			# return without cancellation. This is an artificial situation, not
			# one that would occur in practical usage of Gaffer itself.

			print( "Running in subprocess due to insufficient TBB threads" )

			try :
				env = os.environ.copy()
				env["VALUEPLUGTEST_SUBPROCESS"] = "1"
				executable = "gaffer" if os.name != "nt" else "gaffer.cmd"
				subprocess.check_output(
					[ executable, "test", "-threads", "3", "GafferTest.ValuePlugTest.testCancellationOfSecondGetValueCall" ],
					stderr = subprocess.STDOUT,
					env = env
				)
			except subprocess.CalledProcessError as e :
				self.fail( e.output )

			return

		class InfiniteLoop( Gaffer.ComputeNode ) :

			def __init__( self, name = "InfiniteLoop", cachePolicy = Gaffer.ValuePlug.CachePolicy.Standard ) :

				Gaffer.ComputeNode.__init__( self, name )

				self.computeStartedCondition = threading.Condition()
				self.__cachePolicy = cachePolicy
				self["out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )

			# No need to implement `hash()` - because our result is constant (or
			# non-existent), the default hash is sufficient.

			def compute( self, output, context ) :

				with self.computeStartedCondition :
					self.computeStartedCondition.notify()

				if output == self["out"] :
					while True :
						IECore.Canceller.check( context.canceller() )

			def computeCachePolicy( self, output ) :

				return self.__cachePolicy

		IECore.registerRunTimeTyped( InfiniteLoop )

		for cachePolicy in (
			Gaffer.ValuePlug.CachePolicy.Legacy,
			Gaffer.ValuePlug.CachePolicy.Standard,
			Gaffer.ValuePlug.CachePolicy.TaskIsolation,
			# Omitting TaskCollaboration, because if our second compute joins as
			# a worker, there is currently no way we can recall it. See comments
			# in `LRUCachePolicy.TaskParallel.Handle.acquire`.
		) :

			node = InfiniteLoop( cachePolicy = cachePolicy )

			# Launch a compute in the background, and wait for it to start.

			with node.computeStartedCondition :
				backgroundTask1 = Gaffer.ParallelAlgo.callOnBackgroundThread( node["out"], lambda : node["out"].getValue() )
				node.computeStartedCondition.wait()

			# Launch a second compute in the background, wait for it to start, and
			# then make sure we can cancel it even though the compute is already in
			# progress on another thread.

			startedCondition = threading.Condition()

			def getValueExpectingCancellation() :

				with startedCondition :
					startedCondition.notify()

				with self.assertRaises( IECore.Cancelled ) :
					node["out"].getValue()

			with startedCondition :
				backgroundTask2 = Gaffer.ParallelAlgo.callOnBackgroundThread( node["out"], getValueExpectingCancellation )
				startedCondition.wait()

			backgroundTask2.cancelAndWait()
			backgroundTask1.cancelAndWait()

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__originalCacheMemoryLimit = Gaffer.ValuePlug.getCacheMemoryLimit()

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		Gaffer.ValuePlug.setCacheMemoryLimit( self.__originalCacheMemoryLimit )

if __name__ == "__main__":
	unittest.main()
