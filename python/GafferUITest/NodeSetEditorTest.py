##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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
import weakref

import Gaffer
import GafferUI
import GafferUITest

class NodeSetEditorTest( GafferUITest.TestCase ) :

	def testDefaultsToNodeSelection( self ) :

		s = Gaffer.ScriptNode()

		ne = GafferUI.NodeEditor( s )
		self.assertTrue( ne.getNodeSet().isSame( s.selection() ) )

	def testSetNodeSet( self ) :

		s = Gaffer.ScriptNode()

		n = Gaffer.StandardSet()
		n2 = Gaffer.StandardSet()

		ne = GafferUI.NodeEditor( s )
		ne.setNodeSet( n )
		self.assertTrue( ne.getNodeSet().isSame( n ) )
		ne.setNodeSet( n2 )
		self.assertTrue( ne.getNodeSet().isSame( n2 ) )

	def testSetNodeSetDriver( self ) :

		s = Gaffer.ScriptNode()

		n1 = Gaffer.StandardSet()
		n2 = Gaffer.StandardSet()
		n3 = Gaffer.StandardSet()

		ne1 = GafferUI.NodeEditor( s )

		# Test default state
		self.assertEqual( ne1.drivenNodeSets(), {} )
		self.assertEqual( ne1.getNodeSetDriver(), ( None, "" ) )

		ne2 = GafferUI.NodeEditor( s )
		ne3 = GafferUI.NodeEditor( s )

		ne1.setNodeSet( n1 )
		ne2.setNodeSet( n2 )
		ne3.setNodeSet( n3 )

		ne2.setNodeSetDriver( ne1 )
		self.assertTrue( ne2.getNodeSet().isSame( ne1.getNodeSet() ) )
		self.assertTrue( ne2.getNodeSet().isSame( n1 ) )
		self.assertEqual( ne2.getNodeSetDriver(), ( ne1, GafferUI.NodeSetEditor.DriverModeNodeSet ) )
		self.assertDictEqual( ne1.drivenNodeSets(), { ne2 : GafferUI.NodeSetEditor.DriverModeNodeSet } )
		self.assertDictEqual( ne2.drivenNodeSets(), {} )

		ne3.setNodeSetDriver( ne2 )
		self.assertTrue( ne3.getNodeSet().isSame( ne2.getNodeSet() ) )
		self.assertTrue( ne3.getNodeSet().isSame( ne1.getNodeSet() ) )
		self.assertTrue( ne3.getNodeSet().isSame( n1 ) )
		self.assertEqual( ne3.getNodeSetDriver(), ( ne2, GafferUI.NodeSetEditor.DriverModeNodeSet ) )
		self.assertDictEqual( ne1.drivenNodeSets(), { ne2 : GafferUI.NodeSetEditor.DriverModeNodeSet } )
		self.assertDictEqual( ne1.drivenNodeSets( recurse = True ) , { ne2 : GafferUI.NodeSetEditor.DriverModeNodeSet, ne3 : GafferUI.NodeSetEditor.DriverModeNodeSet } )
		self.assertDictEqual( ne2.drivenNodeSets(), { ne3 : GafferUI.NodeSetEditor.DriverModeNodeSet } )
		self.assertDictEqual( ne3.drivenNodeSets(), {} )

		ne1.setNodeSet( n3 )
		self.assertTrue( ne1.getNodeSet().isSame( n3 ) )
		self.assertTrue( ne2.getNodeSet().isSame( n3 ) )
		self.assertTrue( ne3.getNodeSet().isSame( n3 ) )

		ne1.setNodeSet( n1 )

		# setNodeSet should clear driver link
		ne2.setNodeSet( n2 )
		self.assertFalse( ne2.getNodeSet().isSame( ne1.getNodeSet() ) )
		self.assertTrue( ne2.getNodeSet().isSame( n2 ) )
		self.assertTrue( ne3.getNodeSet().isSame( n2 ) )
		self.assertFalse( ne3.getNodeSet().isSame( ne1.getNodeSet() ) )
		self.assertEqual( ne2.getNodeSetDriver(), ( None, "" ) )
		self.assertDictEqual( ne1.drivenNodeSets(), {} )

		ne3.setNodeSetDriver( None )
		self.assertTrue( ne3.getNodeSet().isSame( n2 ) )
		self.assertEqual( ne3.getNodeSetDriver(), ( None, "" ) )
		self.assertDictEqual( ne2.drivenNodeSets(), {} )

		ne2.setNodeSetDriver( ne1 )
		ne3.setNodeSetDriver( ne1 )
		self.assertDictEqual( ne1.drivenNodeSets(), {
			ne2 : GafferUI.NodeSetEditor.DriverModeNodeSet,
			ne3 : GafferUI.NodeSetEditor.DriverModeNodeSet
		} )
		self.assertEqual( ne2.getNodeSetDriver(), ( ne1, GafferUI.NodeSetEditor.DriverModeNodeSet ) )
		self.assertEqual( ne3.getNodeSetDriver(), ( ne1, GafferUI.NodeSetEditor.DriverModeNodeSet ) )

		# Check passing in garbage
		with self.assertRaises( AssertionError ) :
			ne2.setNodeSetDriver( n1 )

	def testLinkLifetime( self ) :

		s = Gaffer.ScriptNode()

		ne1 = GafferUI.NodeEditor( s )
		ne2 = GafferUI.NodeEditor( s )

		ne2.setNodeSetDriver( ne1 )
		self.assertEqual( ne2.getNodeSetDriver(), ( ne1, GafferUI.NodeSetEditor.DriverModeNodeSet ) )

		del ne1
		self.assertEqual( ne2.getNodeSetDriver(), ( None, "" ) )

	def testEditorLifetime( self ) :

		s = Gaffer.ScriptNode()

		ne1 = GafferUI.NodeEditor( s )
		ne2 = GafferUI.NodeEditor( s )

		ne2.setNodeSetDriver( ne1 )

		weak2 = weakref.ref( ne2 )

		del ne2

		self.assertIsNone( weak2() )

	def testLoop( self ) :

		s = Gaffer.ScriptNode()

		ne1 = GafferUI.NodeEditor( s )
		ne2 = GafferUI.NodeEditor( s )
		ne3 = GafferUI.NodeEditor( s )

		ne2.setNodeSetDriver( ne1 )
		with self.assertRaises( ValueError ) :
			ne1.setNodeSetDriver( ne2 )
		self.assertEqual( ne1.getNodeSetDriver(), ( None, "" ) )

		ne2.setNodeSetDriver( ne1 )
		ne3.setNodeSetDriver( ne2 )
		with self.assertRaises( ValueError ) :
			ne1.setNodeSetDriver( ne3 )
		self.assertEqual( ne1.getNodeSetDriver(), ( None, "" ) )

	def testSignals( self ) :

		s = Gaffer.ScriptNode()

		n1 = Gaffer.StandardSet()
		n2 = Gaffer.StandardSet()

		ne1 = GafferUI.NodeEditor( s )
		ne2 = GafferUI.NodeEditor( s )

		weakne1 = weakref.ref( ne1 )

		signalData = {
			'ne1nodeSetMirror' : None,
			'ne2nodeSetMirror' : None,
			'ne1driverMirror' : ( None, "" ),
			'ne2driverMirror' : ( None, "" ),
			'ne1drivenMirror' : {},
			'ne2drivenMirror' : {}
		}

		def nodeSetChangedCallback( editor ) :
			d = editor.getNodeSet()
			if editor is weakne1() :
				signalData['ne1nodeSetMirror'] = d
			else :
				signalData['ne2nodeSetMirror'] = d

		def nodeSetDriverChangedCallback( editor ) :
			d = editor.getNodeSetDriver()
			if editor is weakne1() :
				signalData['ne1driverMirror']= d
			else :
				signalData['ne2driverMirror']= d

		def drivenChangedCallback( editor ) :
			d = editor.drivenNodeSets()
			if editor is weakne1() :
				signalData['ne1drivenMirror']= d
			else :
				signalData['ne2drivenMirror']= d

		c1 = ne1.nodeSetChangedSignal().connect( nodeSetChangedCallback )
		c2 = ne1.nodeSetDriverChangedSignal().connect( nodeSetDriverChangedCallback )
		c3 = ne1.drivenNodeSetsChangedSignal().connect( drivenChangedCallback )

		c4 = ne2.nodeSetChangedSignal().connect( nodeSetChangedCallback )
		c5 = ne2.nodeSetDriverChangedSignal().connect( nodeSetDriverChangedCallback )
		c6 = ne2.drivenNodeSetsChangedSignal().connect( drivenChangedCallback )

		ne1.setNodeSet( n1 )
		ne2.setNodeSet( n2 )

		self.assertEqual( ne1.getNodeSet(), signalData['ne1nodeSetMirror'] )
		self.assertEqual( ne2.getNodeSet(), signalData['ne2nodeSetMirror'] )

		ne2.setNodeSetDriver( ne1 )
		self.assertEqual( ne1.getNodeSet(), signalData['ne1nodeSetMirror'] )
		self.assertEqual( ne2.getNodeSet(), signalData['ne2nodeSetMirror'] )
		self.assertEqual( ne1.getNodeSetDriver(), signalData['ne1driverMirror'] )
		self.assertEqual( ne2.getNodeSetDriver(), signalData['ne2driverMirror'] )
		self.assertEqual( ne1.drivenNodeSets(), signalData['ne1drivenMirror'] )
		self.assertEqual( ne2.drivenNodeSets(), signalData['ne2drivenMirror'] )

		ne1.setNodeSet( n2 )
		self.assertEqual( ne1.getNodeSet(), signalData['ne1nodeSetMirror'] )
		self.assertEqual( ne2.getNodeSet(), signalData['ne2nodeSetMirror'] )
		self.assertEqual( ne1.getNodeSetDriver(), signalData['ne1driverMirror'] )
		self.assertEqual( ne2.getNodeSetDriver(), signalData['ne2driverMirror'] )
		self.assertEqual( ne1.drivenNodeSets(), signalData['ne1drivenMirror'] )
		self.assertEqual( ne2.drivenNodeSets(), signalData['ne2drivenMirror'] )

		ne2.setNodeSet( n1 )
		self.assertEqual( ne1.getNodeSet(), signalData['ne1nodeSetMirror'] )
		self.assertEqual( ne2.getNodeSet(), signalData['ne2nodeSetMirror'] )
		self.assertEqual( ne1.getNodeSetDriver(), signalData['ne1driverMirror'] )
		self.assertEqual( ne2.getNodeSetDriver(), signalData['ne2driverMirror'] )
		self.assertEqual( ne1.drivenNodeSets(), signalData['ne1drivenMirror'] )
		self.assertEqual( ne2.drivenNodeSets(), signalData['ne2drivenMirror'] )

		ne2.setNodeSetDriver( ne1 )
		ne2.setNodeSetDriver( None )
		self.assertEqual( ne1.getNodeSet(), signalData['ne1nodeSetMirror'] )
		self.assertEqual( ne2.getNodeSet(), signalData['ne2nodeSetMirror'] )
		self.assertEqual( ne1.getNodeSetDriver(), signalData['ne1driverMirror'] )
		self.assertEqual( ne2.getNodeSetDriver(), signalData['ne2driverMirror'] )
		self.assertEqual( ne1.drivenNodeSets(), signalData['ne1drivenMirror'] )
		self.assertEqual( ne2.drivenNodeSets(), signalData['ne2drivenMirror'] )

		ne2.setNodeSetDriver( ne1 )
		del c1, c2, c3, ne1
		self.assertEqual( ne2.getNodeSet(), signalData['ne2nodeSetMirror'] )
		self.assertEqual( ne2.getNodeSetDriver(), signalData['ne2driverMirror'] )
		self.assertEqual( ne2.drivenNodeSets(), signalData['ne2drivenMirror'] )

	def testSignalOrder( self ) :

		d = Gaffer.StandardSet()
		def dummyDriverModeCallback( editor, targetEditor ) :
			return d

		DummyMode = "Dummy"
		GafferUI.NodeSetEditor.registerNodeSetDriverMode( DummyMode, dummyDriverModeCallback )

		s = Gaffer.ScriptNode()

		ne1 = GafferUI.NodeEditor( s )
		ne2 = GafferUI.NodeEditor( s )

		ne2.setNodeSetDriver( ne1, DummyMode )
		self.assertTrue( ne2.getNodeSet().isSame( d ) )

		# People acting upon these signals need to know the order in which these signals
		# fire. We have to pick one way around (there are gotchas with either way). This is
		# to ensure we don't inadvertently change this ordering.

		def nodeSetChangedCallback( _ ) :
			self.assertTrue( ne2.getNodeSetDriver(), ( ne1, DummyMode ) )

		s2 = Gaffer.StandardSet()
		def driverChangedCallback( _ ) :
			self.assertTrue( ne2.getNodeSet().isSame( s2 ) )

		c1 = ne2.nodeSetChangedSignal().connect( nodeSetChangedCallback )
		c2 = ne2.nodeSetDriverChangedSignal().connect( driverChangedCallback )

		ne2.setNodeSet( s2 )

	def testDriverModes( self ) :

		d = Gaffer.StandardSet()
		def dummyDriverModeCallback( editor, targetEditor ) :
			return d

		DummyMode = "Dummy"
		GafferUI.NodeSetEditor.registerNodeSetDriverMode( DummyMode, dummyDriverModeCallback )

		s = Gaffer.ScriptNode()

		ne1 = GafferUI.NodeEditor( s )
		ne2 = GafferUI.NodeEditor( s )

		ne2.setNodeSetDriver( ne1 )
		self.assertEqual( ne2.getNodeSetDriver(), ( ne1, GafferUI.NodeSetEditor.DriverModeNodeSet ) )
		self.assertTrue( ne2.getNodeSet().isSame( s.selection() ) )

		ne2.setNodeSetDriver( ne1, DummyMode )
		self.assertEqual( ne2.getNodeSetDriver(), ( ne1, DummyMode ) )
		self.assertTrue( ne2.getNodeSet().isSame( d ) )

		ne1.setNodeSet( Gaffer.StandardSet() )
		self.assertTrue( ne2.getNodeSet().isSame( d ) )

if __name__ == "__main__":
	unittest.main()
