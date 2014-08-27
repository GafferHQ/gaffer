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

import unittest
import gc

import IECore
import Gaffer
import GafferTest

class CompoundPlugTest( GafferTest.TestCase ) :

	def testContructor( self ) :

		p = Gaffer.CompoundPlug()
		self.assertEqual( p.getName(), "CompoundPlug" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.In )

		p = Gaffer.V3fPlug( name="b", direction=Gaffer.Plug.Direction.Out )
		self.assertEqual( p.getName(), "b" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.Out )

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
		self.failUnless( s["n1"]["p"]["s"].getInput().isSame( s["n2"]["p"]["s"] ) )

	def testDynamicSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()
		s["n1"]["p"] = Gaffer.CompoundPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n1"]["p"]["f"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n1"]["p"]["f"].setValue( 10 )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n1"]["p"]["f"].getValue(), 10 )

	def testMasterConnectionTracksChildConnections( self ) :

		c = Gaffer.CompoundPlug( "c" )
		c["f1"] = Gaffer.FloatPlug()
		c["f2"] = Gaffer.FloatPlug()
		n = Gaffer.Node()
		n["c"] = c

		c2 = Gaffer.CompoundPlug( "c" )
		c2["f1"] = Gaffer.FloatPlug()
		c2["f2"] = Gaffer.FloatPlug()
		n2 = Gaffer.Node()
		n2["c"] = c2

		n2["c"]["f1"].setInput( n["c"]["f1"] )
		n2["c"]["f2"].setInput( n["c"]["f2"] )
		self.failUnless( n2["c"].getInput().isSame( n["c"] ) )

		n2["c"]["f2"].setInput( None )
		self.failUnless( n2["c"].getInput() is None )

		n2["c"]["f2"].setInput( n["c"]["f2"] )
		self.failUnless( n2["c"].getInput().isSame( n["c"] ) )

		c["f3"] = Gaffer.FloatPlug()
		c2["f3"] = Gaffer.FloatPlug()

		self.failUnless( n2["c"].getInput() is None )

		n2["c"]["f3"].setInput( n["c"]["f3"] )
		self.failUnless( n2["c"].getInput().isSame( n["c"] ) )


	def testInputChangedCrash( self ) :

		ca = Gaffer.CompoundPlug( "ca" )
		ca["fa1"] = Gaffer.FloatPlug()
		ca["fa2"] = Gaffer.FloatPlug()
		na = Gaffer.Node()
		na["ca"] = ca

		cb = Gaffer.CompoundPlug( "cb" )
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

		self.failUnless( dirtyPlugs[0][0].isSame( n["p"]["f"] ) )
		self.failUnless( dirtyPlugs[1][0].isSame( n["p"] ) )
		self.failUnless( dirtyPlugs[2][0].isSame( n["o"]["f"] ) )
		self.failUnless( dirtyPlugs[3][0].isSame( n["o"] ) )

	def testPlugSetPropagation( self ) :

		c = Gaffer.CompoundPlug()
		c["f1"] = Gaffer.FloatPlug()

		n = Gaffer.Node()
		n["c"] = c

		def setCallback( plug ) :

			if plug.isSame( c ) :
				self.set = True

		cn = n.plugSetSignal().connect( setCallback )

		self.set = False

		c["f1"].setValue( 10 )

		self.failUnless( self.set )

	def testMultipleLevelsOfPlugSetPropagation( self ) :

		c = Gaffer.CompoundPlug( "c" )
		c["c1"] = Gaffer.CompoundPlug()
		c["c1"]["f1"] = Gaffer.FloatPlug()

		n = Gaffer.Node()
		n["c"] = c

		def setCallback( plug ) :

			self.setPlugs.append( plug.getName() )

		cn = n.plugSetSignal().connect( setCallback )

		self.setPlugs = []

		c["c1"]["f1"].setValue( 10 )

		self.failUnless( len( self.setPlugs )==3 )
		self.assertEqual( self.setPlugs, [ "f1", "c1", "c" ] )

	def testMultipleLevelsOfPlugSetPropagationWithDifferentParentingOrder( self ) :

		n = Gaffer.Node()
		n["c"] = Gaffer.CompoundPlug()

		n["c"]["c1"] = Gaffer.CompoundPlug()
		n["c"]["c1"]["f1"] = Gaffer.FloatPlug()

		def setCallback( plug ) :

			self.setPlugs.append( plug.getName() )

		cn = n.plugSetSignal().connect( setCallback )

		self.setPlugs = []

		n["c"]["c1"]["f1"].setValue( 10 )

		self.failUnless( len( self.setPlugs )==3 )
		self.failUnless( "c" in self.setPlugs )
		self.failUnless( "c1" in self.setPlugs )
		self.failUnless( "f1" in self.setPlugs )

	def testAcceptsInput( self ) :

		i = Gaffer.CompoundPlug()
		o = Gaffer.CompoundPlug( direction=Gaffer.Plug.Direction.Out )
		s = Gaffer.StringPlug( direction=Gaffer.Plug.Direction.Out )

		i.addChild( Gaffer.IntPlug() )
		o.addChild( Gaffer.IntPlug( direction=Gaffer.Plug.Direction.Out ) )

		self.failUnless( i.acceptsInput( o ) )
		self.failIf( i.acceptsInput( s ) )

	def testDerivingInPython( self ) :

		class TestCompoundPlug( Gaffer.CompoundPlug ) :

			def __init__( self, name = "TestCompoundPlug", direction = Gaffer.Plug.Direction.In, flags = Gaffer.Plug.Flags.None ) :

				Gaffer.CompoundPlug.__init__( self, name, direction, flags )

			def acceptsChild( self, child ) :

				if not Gaffer.CompoundPlug.acceptsChild( self, child ) :
					return False

				return isinstance( child, Gaffer.IntPlug )

		IECore.registerRunTimeTyped( TestCompoundPlug )

		# check the constructor

		p = TestCompoundPlug()
		self.assertEqual( p.getName(), "TestCompoundPlug" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p.getFlags(), Gaffer.Plug.Flags.None )

		p = TestCompoundPlug( name = "p", direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( p.getName(), "p" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.Out )
		self.assertEqual( p.getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		# check that acceptsChild can be overridden

		p = TestCompoundPlug()

		self.assertRaises( RuntimeError, p.addChild, Gaffer.FloatPlug() )

		p.addChild( Gaffer.IntPlug() )

		# check that the fact the plug has been wrapped solves the object identity problem

		p = TestCompoundPlug()
		n = Gaffer.Node()
		n["p"] = p

		self.failUnless( n["p"] is p )

	def testAcceptsNoneInput( self ) :

		p = Gaffer.CompoundPlug( "hello" )
		self.failUnless( p.acceptsInput( None ) )

	def testRunTimeTyped( self ) :

		p = Gaffer.CompoundPlug( "hello" )
		self.failUnless( p.isInstanceOf( Gaffer.CompoundPlug.staticTypeId() ) )

		self.assertEqual( IECore.RunTimeTyped.baseTypeId( p.typeId() ), Gaffer.ValuePlug.staticTypeId() )

	def testSerialisationOfMasterConnection( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.CompoundPlugNode()
		s["n2"] = GafferTest.CompoundPlugNode()

		s["n1"]["p"].setInput( s["n2"]["p"] )
		self.failUnless( s["n1"]["p"].getInput().isSame( s["n2"]["p"] ) )
		self.failUnless( s["n1"]["p"]["f"].getInput().isSame( s["n2"]["p"]["f"] ) )
		self.failUnless( s["n1"]["p"]["s"].getInput().isSame( s["n2"]["p"]["s"] ) )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.failUnless( s["n1"]["p"].getInput().isSame( s["n2"]["p"] ) )
		self.failUnless( s["n1"]["p"]["f"].getInput().isSame( s["n2"]["p"]["f"] ) )
		self.failUnless( s["n1"]["p"]["s"].getInput().isSame( s["n2"]["p"]["s"] ) )

	def testSetInputShortcut( self ) :

		n1 = Gaffer.Node()
		n1["c"] = Gaffer.CompoundPlug()

		n2 = Gaffer.Node()
		n2["c"] = Gaffer.CompoundPlug( direction = Gaffer.Plug.Direction.Out )

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

		c1 = Gaffer.CompoundPlug( direction=Gaffer.Plug.Direction.Out )
		c1["n"] = Gaffer.IntPlug( direction=Gaffer.Plug.Direction.Out )

		c2 = Gaffer.CompoundPlug()
		c2["n"] = Gaffer.IntPlug()

		c2.setInput( c1 )
		self.assertEqual( c2.getInput(), c1 )

	def testCanMakeSomeConnectionsWhenSizesDontMatch( self ) :

		n = Gaffer.Node()

		n["c1"] = Gaffer.CompoundPlug( direction = Gaffer.Plug.Direction.In )
		n["c1"]["i"] = Gaffer.IntPlug()

		n["c2"] = Gaffer.CompoundPlug( direction = Gaffer.Plug.Direction.Out )
		n["c2"]["i1"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		n["c2"]["i2"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )

		n["c1"]["i"].setInput( n["c2"]["i1"] )

		self.failUnless( n["c1"]["i"].getInput().isSame( n["c2"]["i1"] ) )
		self.failUnless( n["c1"].getInput().isSame( n["c2"] ) )

	def testSerialisationOfDynamicPlugsOnNondynamicParent( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.CompoundPlugNode()

		s["n"]["nonDynamicParent"]["dynamicPlug"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["nonDynamicParent"]["dynamicPlug"].setValue( 10 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"]["nonDynamicParent"]["dynamicPlug"].getValue(), 10 )

	def testCreateCounterpart( self ) :

		c = Gaffer.CompoundPlug( "a", Gaffer.Plug.Direction.Out )
		c["b"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		c["c"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )

		c2 = c.createCounterpart( "aa", Gaffer.Plug.Direction.In )

		self.assertEqual( c2.getName(), "aa" )
		self.assertEqual( c2.direction(), Gaffer.Plug.Direction.In )

		self.assertEqual( c2["b"].direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( c2["c"].direction(), Gaffer.Plug.Direction.In )

	def testChildAdditionEmitsPlugSet( self ) :

		n = Gaffer.Node()

		n["c"] = Gaffer.CompoundPlug()
		n["c"]["d"] = Gaffer.CompoundPlug()

		cs = GafferTest.CapturingSlot( n.plugSetSignal() )

		n["c"]["d"]["e"] = Gaffer.IntPlug()

		self.assertEqual( len( cs ), 2 )
		self.assertEqual( cs[0][0], n["c"]["d"] )
		self.assertEqual( cs[1][0], n["c"] )

if __name__ == "__main__":
	unittest.main()

