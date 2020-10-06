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

import unittest
import weakref

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class NodeEditorTest( GafferUITest.TestCase ) :

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerformance( self ) :

		s = Gaffer.ScriptNode()
		s["smallNode"] = Gaffer.Node()

		bn = Gaffer.Node()
		s["bigNode"] = bn

		for i in range( 5 ) :
			for j in range( 5 ) :
				for k in range( 10 ) :
					p = Gaffer.IntPlug( defaultValue = i+j+k )
					Gaffer.Metadata.registerValue( p, "layout:section", "%d.%d" % ( i, j ) )
					bn.addChild( p )

		a =  Gaffer.StandardSet( [ s["smallNode"] ] )
		b =  Gaffer.StandardSet( [ s["bigNode"] ] )

		sw = GafferUI.ScriptWindow.acquire( s )
		ne = GafferUI.NodeEditor.acquire( s["smallNode"] )

		with GafferTest.TestRunner.PerformanceScope() :
			for i in range( 2 ) :
				ne.setNodeSet( a )
				ne.nodeUI()
				ne.setNodeSet( b )
				ne.nodeUI()

	def testAcquireReusesEditors( self ) :

		self.maxDiff = None

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()

		sw = GafferUI.ScriptWindow.acquire( s )

		ne = GafferUI.NodeEditor.acquire( s["n"] )
		self.assertTrue( GafferUI.NodeEditor.acquire( s["n"] ) is ne )

		self.assertIsInstance( ne, GafferUI.NodeEditor )
		self.assertIn( s["n"], ne.getNodeSet() )

	def testAcquireDeletesClosedWindows( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()

		sw = GafferUI.ScriptWindow.acquire( s )

		ne = GafferUI.NodeEditor.acquire( s["n"] )
		nw = ne.ancestor( GafferUI.Window )
		self.assertTrue( nw.parent() is sw )

		nww = weakref.ref( nw )
		nw.close()
		del nw

		self.assertEqual( sw.childWindows(), [] )
		self.waitForIdle()
		self.assertEqual( nww(), None )

		ne2 = GafferUI.NodeEditor.acquire( s["n"] )
		self.assertIsInstance( ne2, GafferUI.NodeEditor )

	def testAcquiredEditorsClosedOnNodeDelete( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()

		sw = GafferUI.ScriptWindow.acquire( s )

		ww = weakref.ref( GafferUI.NodeEditor.acquire( s["n"] ).ancestor( GafferUI.Window ) )
		self.assertIsInstance( ww(), GafferUI.Window )

		del s["n"]

		self.assertEqual( ww(), None )

	def testNodeUIAccessor( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()

		e = GafferUI.NodeEditor( s )

		self.assertEqual( e.nodeUI(), None )

		s.selection().add( s["n1"] )

		self.assertTrue( isinstance( e.nodeUI(), GafferUI.NodeUI ) )
		self.assertTrue( e.nodeUI().node().isSame( s["n1"] ) )

		s.selection().add( s["n2"] )

		self.assertTrue( isinstance( e.nodeUI(), GafferUI.NodeUI ) )
		self.assertTrue( e.nodeUI().node().isSame( s["n2"] ) )

		s.selection().remove( s["n2"] )

		self.assertTrue( isinstance( e.nodeUI(), GafferUI.NodeUI ) )
		self.assertTrue( e.nodeUI().node().isSame( s["n1"] ) )

		s.selection().remove( s["n1"] )

		self.assertEqual( e.nodeUI(), None )

if __name__ == "__main__":
	unittest.main()
