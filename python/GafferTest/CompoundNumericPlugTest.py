##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import unittest
import imath

import IECore

import Gaffer
import GafferTest

class CompoundNumericPlugTest( GafferTest.TestCase ) :

	def testContructor( self ) :

		p = Gaffer.V3fPlug()
		self.assertEqual( p.getName(), "V3fPlug" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.In )

		p = Gaffer.V3fPlug( name="b", direction=Gaffer.Plug.Direction.Out )
		self.assertEqual( p.getName(), "b" )
		self.assertEqual( p.direction(), Gaffer.Plug.Direction.Out )

	def testChildRejection( self ) :

		p = Gaffer.V3fPlug()
		c = Gaffer.FloatPlug()
		self.assertRaises( Exception, p.addChild, c )

	def testChildNames( self ) :

		p = Gaffer.V3fPlug()
		p["x"].setValue( 1 )
		p["y"].setValue( 2 )
		p["z"].setValue( 3 )

		self.assertEqual( p.getValue(), imath.V3f( 1, 2, 3 ) )

	def testMinMaxValues( self ) :

		p = Gaffer.V3fPlug()
		self.failIf( p.hasMinValue() )
		self.failIf( p.hasMaxValue() )
		for a in ( "x", "y", "z" ) :
			self.failIf( p[a].hasMinValue() )
			self.failIf( p[a].hasMaxValue() )

		p = Gaffer.V3fPlug(
			minValue = imath.V3f( -1, -2, -3 ),
			maxValue = imath.V3f( 1, 2, 3 )
		)

		self.failUnless( p.hasMinValue() )
		self.failUnless( p.hasMaxValue() )
		for a in ( "x", "y", "z" ) :
			self.failUnless( p[a].hasMinValue() )
			self.failUnless( p[a].hasMaxValue() )

		minValue = p.minValue()
		maxValue = p.maxValue()
		self.assertEqual( minValue, imath.V3f( -1, -2, -3 ) )
		self.assertEqual( maxValue, imath.V3f( 1, 2, 3 ) )
		i = 0
		for a in ( "x", "y", "z" ) :
			self.assertEqual( p[a].minValue(), minValue[i] )
			self.assertEqual( p[a].maxValue(), maxValue[i] )
			i += 1

	def testDefaultValue( self ) :

		p = Gaffer.V3fPlug( defaultValue = imath.V3f( 1, 2, 3 ) )
		self.assertEqual( p.defaultValue(), imath.V3f( 1, 2, 3 ) )
		self.assertEqual( p["x"].defaultValue(), 1 )
		self.assertEqual( p["y"].defaultValue(), 2 )
		self.assertEqual( p["z"].defaultValue(), 3 )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		n = GafferTest.CompoundNumericNode()
		n["p"].setValue( imath.V3f( 1, 2, 3 ) )
		s["n"] = n

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n"]["p"].getValue(), imath.V3f( 1, 2, 3 ) )

	def testSerialisationWithConnection( self ) :

		s = Gaffer.ScriptNode()
		n1 = GafferTest.CompoundNumericNode()
		n2 = GafferTest.CompoundNumericNode()
		n1["p"].setInput( n2["p"] )
		s["n1"] = n1
		s["n2"] = n2

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.failUnless( s["n1"]["p"].getInput().isSame( s["n2"]["p"] ) )
		self.failUnless( s["n1"]["p"]["x"].getInput().isSame( s["n2"]["p"]["x"] ) )
		self.failUnless( s["n1"]["p"]["y"].getInput().isSame( s["n2"]["p"]["y"] ) )
		self.failUnless( s["n1"]["p"]["z"].getInput().isSame( s["n2"]["p"]["z"] ) )

	def testSerialisationWithPartialConnections( self ) :

		s = Gaffer.ScriptNode()
		n = GafferTest.CompoundNumericNode()
		a = GafferTest.AddNode()
		n["p"]["x"].setValue( 10 )
		n["p"]["y"].setInput( a["sum"] )
		s["n"] = n
		s["a"] = a

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n"]["p"]["x"].getValue(), 10 )
		self.failUnless( s["n"]["p"]["y"].getInput().isSame( s["a"]["sum"] ) )
		self.assertEqual( s["n"]["p"]["z"].getValue(), 0 )

	def testDynamicSerialisation( self ) :

		s = Gaffer.ScriptNode()
		n = Gaffer.Node()
		n["p"] = Gaffer.V3fPlug( flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p"].setValue( imath.V3f( 1, 2, 3 ) )
		s["n"] = n

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n"]["p"].getValue(), imath.V3f( 1, 2, 3 ) )

	def testDynamicSerialisationWithConnection( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()

		s["n1"]["p"] = Gaffer.V3fPlug( flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n2"]["p"] = Gaffer.V3fPlug( direction=Gaffer.Plug.Direction.In, flags=Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["n1"]["p"].setInput( s["n2"]["p"] )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.failUnless( s["n1"]["p"].getInput().isSame( s["n2"]["p"] ) )
		self.failUnless( s["n1"]["p"]["x"].getInput().isSame( s["n2"]["p"]["x"] ) )
		self.failUnless( s["n1"]["p"]["y"].getInput().isSame( s["n2"]["p"]["y"] ) )
		self.failUnless( s["n1"]["p"]["z"].getInput().isSame( s["n2"]["p"]["z"] ) )

	def testRunTimeTyped( self ) :

		p = Gaffer.Color3fPlug()
		self.failUnless( p.isInstanceOf( Gaffer.ValuePlug.staticTypeId() ) )
		self.failUnless( p.isInstanceOf( Gaffer.Plug.staticTypeId() ) )

		t = p.typeId()
		self.assertEqual( IECore.RunTimeTyped.baseTypeId( t ), Gaffer.ValuePlug.staticTypeId() )

	def testSetToDefault( self ) :

		p = Gaffer.V3fPlug( defaultValue = imath.V3f( 1, 2, 3 ) )
		self.assertEqual( p.getValue(), imath.V3f( 1, 2, 3 ) )

		p.setValue( imath.V3f( 4 ) )
		self.assertEqual( p.getValue(), imath.V3f( 4 ) )

		p.setToDefault()
		self.assertEqual( p.getValue(), imath.V3f( 1, 2, 3 ) )

	def testColor3fAcceptsColor4fInput( self ) :

		p4 = Gaffer.Color4fPlug( direction = Gaffer.Plug.Direction.Out )
		p3 = Gaffer.Color3fPlug()

		self.failUnless( p3.acceptsInput( p4 ) )

		p3.setInput( p4 )

		self.failUnless( p3.getInput().isSame( p4 ) )
		self.failUnless( p3[0].getInput().isSame( p4[0] ) )
		self.failUnless( p3[1].getInput().isSame( p4[1] ) )
		self.failUnless( p3[2].getInput().isSame( p4[2] ) )
		self.assertEqual( p4[3].outputs(), () )

	def testColor4fDoesntAcceptColor3fInput( self ) :

		p4 = Gaffer.Color4fPlug()
		p3 = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out )

		self.failIf( p4.acceptsInput( p3 ) )

		self.assertRaises( RuntimeError, p4.setInput, p3 )

	def testRepr( self ) :

		p1 = Gaffer.V3fPlug(
			"p",
			Gaffer.Plug.Direction.Out,
			imath.V3f( 1, 2, 3 ),
			imath.V3f( -1, -2, -3 ),
			imath.V3f( 10, 20, 30 ),
			Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.AcceptsInputs,
		)

		p2 = eval( repr( p1 ) )

		self.assertEqual( p1.getName(), p2.getName() )
		self.assertEqual( p1.direction(), p2.direction() )
		self.assertEqual( p1.defaultValue(), p2.defaultValue() )
		self.assertEqual( p1.minValue(), p2.minValue() )
		self.assertEqual( p1.maxValue(), p2.maxValue() )
		self.assertEqual( p1.getFlags(), p2.getFlags() )

	def testFlags( self ) :

		p = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.Serialisable )
		self.assertEqual( p.getFlags(), Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.Serialisable )
		self.assertEqual( p[0].getFlags(), Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.Serialisable )

	def testCreateCounterpart( self ) :

		p1 = Gaffer.V3fPlug(
			"p",
			Gaffer.Plug.Direction.Out,
			imath.V3f( 1, 2, 3 ),
			imath.V3f( -1, -2, -3 ),
			imath.V3f( 10, 20, 30 ),
			Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.AcceptsInputs,
		)

		p2 = p1.createCounterpart( "a", Gaffer.Plug.Direction.In )

		self.assertEqual( p2.getName(), "a" )
		self.assertEqual( p2.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p2.defaultValue(), p1.defaultValue() )
		self.assertEqual( p2.minValue(), p1.minValue() )
		self.assertEqual( p2.maxValue(), p1.maxValue() )

	def testComponentNames( self ) :

		for plugType, childNames in [
			( Gaffer.V2fPlug, [ "x", "y" ] ),
			( Gaffer.V3fPlug, [ "x", "y", "z" ] ),
			( Gaffer.V2iPlug, [ "x", "y" ] ),
			( Gaffer.V3iPlug, [ "x", "y", "z" ] ),
			( Gaffer.Color3fPlug, [ "r", "g", "b" ] ),
			( Gaffer.Color4fPlug, [ "r", "g", "b", "a" ] ),
		] :
			plug = plugType()
			self.assertEqual( plug.keys(), childNames )

	def testSettable( self ) :

		n = Gaffer.Node()
		n["p1"] = Gaffer.Color3fPlug()
		n["p2"] = Gaffer.Color3fPlug()

		self.assertTrue( n["p1"].settable() )
		self.assertTrue( n["p2"].settable() )

		n["p2"].setInput( n["p1"] )

		self.assertTrue( n["p1"].settable() )
		self.assertFalse( n["p2"].settable() )

		# partially connected plugs should not be considered
		# settable, because all the children are not settable

		n["p2"]["r"].setInput( None )
		self.assertEqual( n["p2"]["r"].getInput(), None )
		self.assertEqual( n["p2"].getInput(), None )

		self.assertTrue( n["p1"].settable() )
		self.assertFalse( n["p2"].settable() )

	def testGanging( self ) :

		p = Gaffer.Color4fPlug()

		self.assertFalse( p.isGanged() )
		self.assertTrue( p.canGang() )
		p.gang()
		self.assertTrue( p.isGanged() )
		self.assertTrue( p[0].getInput() is None )
		self.assertTrue( p[1].getInput().isSame( p[0] ) )
		self.assertTrue( p[2].getInput().isSame( p[0] ) )
		self.assertTrue( p[3].getInput() is None )

		p.ungang()
		for c in p.children() :
			self.assertTrue( c.getInput() is None )
		self.assertFalse( p.isGanged() )
		self.assertTrue( p.canGang() )

	def testNoRedundantSetValueCalls( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.V3fPlug()
		s["n"]["p"].setValue( imath.V3f( 1, 2, 3 ) )

		ss = s.serialise( filter = Gaffer.StandardSet( [ s["n"] ] ) )
		self.assertEqual( ss.count( "setValue" ), 1 )

		s["n"]["p"]["z"].setInput( s["n"]["p"]["y"] )

		ss = s.serialise( filter = Gaffer.StandardSet( [ s["n"] ] ) )
		self.assertEqual( ss.count( "setValue" ), 2 )
		self.assertEqual( ss.count( "setInput" ), 1 )

	def testNoRedundantSetInputCalls( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.CompoundNumericNode()
		s["n2"] = GafferTest.CompoundNumericNode()
		s["n2"]["p"].setInput( s["n1"]["p"] )

		ss = s.serialise()
		self.assertEqual( ss.count( "setInput" ), 1 )

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n2"]["p"].getInput(), s["n1"]["p"] )
		self.assertEqual( s["n2"]["p"]["x"].getInput(), s["n1"]["p"]["x"] )
		self.assertEqual( s["n2"]["p"]["y"].getInput(), s["n1"]["p"]["y"] )
		self.assertEqual( s["n2"]["p"]["z"].getInput(), s["n1"]["p"]["z"] )

	def testUndoMerging( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.V3fPlug()

		self.assertEqual( s["n"]["p"].getValue(), imath.V3f( 0 ) )
		self.assertFalse( s.undoAvailable() )

		with Gaffer.UndoScope( s, mergeGroup="test" ) :
			s["n"]["p"].setValue( imath.V3f( 1, 2, 3 ) )

		self.assertEqual( s["n"]["p"].getValue(), imath.V3f( 1, 2, 3 ) )
		self.assertTrue( s.undoAvailable() )

		with Gaffer.UndoScope( s, mergeGroup="test" ) :
			s["n"]["p"].setValue( imath.V3f( 4, 5, 6 ) )

		self.assertEqual( s["n"]["p"].getValue(), imath.V3f( 4, 5, 6 ) )
		self.assertTrue( s.undoAvailable() )

		with Gaffer.UndoScope( s, mergeGroup="test2" ) :
			s["n"]["p"].setValue( imath.V3f( 7, 8, 9 ) )

		self.assertEqual( s["n"]["p"].getValue(), imath.V3f( 7, 8, 9 ) )
		self.assertTrue( s.undoAvailable() )

		s.undo()

		self.assertEqual( s["n"]["p"].getValue(), imath.V3f( 4, 5, 6 ) )
		self.assertTrue( s.undoAvailable() )

		s.undo()

		self.assertEqual( s["n"]["p"].getValue(), imath.V3f( 0 ) )
		self.assertFalse( s.undoAvailable() )

	def testUndoMergingWithUnchangingComponents( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.V3fPlug()

		self.assertEqual( s["n"]["p"].getValue(), imath.V3f( 0 ) )
		self.assertFalse( s.undoAvailable() )

		with Gaffer.UndoScope( s, mergeGroup="test" ) :
			s["n"]["p"].setValue( imath.V3f( 1, 2, 0 ) )

		self.assertEqual( s["n"]["p"].getValue(), imath.V3f( 1, 2, 0 ) )
		self.assertTrue( s.undoAvailable() )

		with Gaffer.UndoScope( s, mergeGroup="test" ) :
			s["n"]["p"].setValue( imath.V3f( 2, 4, 0 ) )

		self.assertEqual( s["n"]["p"].getValue(), imath.V3f( 2, 4, 0 ) )
		self.assertTrue( s.undoAvailable() )

		s.undo()

		self.assertEqual( s["n"]["p"].getValue(), imath.V3f( 0 ) )
		self.assertFalse( s.undoAvailable() )

	def testSerialisationVerbosity( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.CompoundNumericNode()

		s["n"]["p"].setValue( imath.V3f( 9, 10, 11 ) )

		ss = s.serialise()
		self.assertTrue( '["p"].setValue' in ss )
		self.assertFalse( '["x"].setValue' in ss )
		self.assertFalse( '["y"].setValue' in ss )
		self.assertFalse( '["z"].setValue' in ss )

	def testIsSetToDefault( self ) :

		n = GafferTest.CompoundNumericNode()
		self.assertTrue( n["p"].isSetToDefault() )

		n["p"].setValue( imath.V3f( 4, 5, 6 ) )
		self.assertFalse( n["p"].isSetToDefault() )

		n["p"].setToDefault()
		self.assertTrue( n["p"].isSetToDefault() )

		n["p"].setValue( imath.V3f( 4, 5, 6 ) )
		self.assertFalse( n["p"].isSetToDefault() )

		n["p"].setValue( n["p"].defaultValue() )
		self.assertTrue( n["p"].isSetToDefault() )

if __name__ == "__main__":
	unittest.main()
