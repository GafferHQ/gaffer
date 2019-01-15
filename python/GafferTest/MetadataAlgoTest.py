##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
import os

import imath

import IECore

import Gaffer
import GafferTest

class MetadataAlgoTest( GafferTest.TestCase ) :

	def testReadOnly( self ) :

		n = GafferTest.AddNode()

		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n["op1"] ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n["op1"] ), False )

		Gaffer.MetadataAlgo.setReadOnly( n["op1"], True )

		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n["op1"] ), True )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n["op1"] ), True )

		Gaffer.MetadataAlgo.setReadOnly( n, True )

		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n ), True )
		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n["op1"] ), True )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n ), True )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n["op1"] ), True )

		Gaffer.MetadataAlgo.setReadOnly( n["op1"], False )

		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n ), True )
		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n["op1"] ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n ), True )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n["op1"] ), True )

	def testChildNodesAreReadOnly( self ) :

		b = Gaffer.Box()

		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( b ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getChildNodesAreReadOnly( b ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( b ), False )

		p1 = Gaffer.IntPlug( "boxPlug", Gaffer.Plug.Direction.In )
		b.addChild( p1 )

		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( p1 ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( p1 ), False )

		n = GafferTest.AddNode()

		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n["op1"] ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n["op1"] ), False )

		b.addChild( n )

		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n["op1"] ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n["op1"] ), False )

		Gaffer.MetadataAlgo.setChildNodesAreReadOnly( b, True )

		self.assertEqual( Gaffer.MetadataAlgo.getChildNodesAreReadOnly( b ), True )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( b ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( p1 ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n["op1"] ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n ), True )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n["op1"] ), True )

		Gaffer.MetadataAlgo.setChildNodesAreReadOnly( b, False )

		self.assertEqual( Gaffer.MetadataAlgo.getChildNodesAreReadOnly( b ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( b ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( p1 ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getReadOnly( n["op1"] ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n ), False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnly( n["op1"] ), False )

	def testBookmarks( self ) :

		b = Gaffer.Box()
		b["n0"] = GafferTest.AddNode()
		b["n1"] = GafferTest.AddNode()

		self.assertEqual( Gaffer.MetadataAlgo.getBookmarked( b ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getBookmarked( b["n0"] ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getBookmarked( b["n1"] ), False )
		self.assertEqual( Gaffer.MetadataAlgo.bookmarks( b ), [] )

		Gaffer.MetadataAlgo.setBookmarked( b["n0"], True )

		self.assertEqual( Gaffer.MetadataAlgo.getBookmarked( b ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getBookmarked( b["n0"] ), True )
		self.assertEqual( Gaffer.MetadataAlgo.getBookmarked( b["n1"] ), False )
		self.assertEqual( Gaffer.MetadataAlgo.bookmarks( b ), [ b["n0"] ] )

		Gaffer.MetadataAlgo.setBookmarked( b["n1"], True )

		self.assertEqual( Gaffer.MetadataAlgo.getBookmarked( b ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getBookmarked( b["n0"] ), True )
		self.assertEqual( Gaffer.MetadataAlgo.getBookmarked( b["n1"] ), True )
		self.assertEqual( Gaffer.MetadataAlgo.bookmarks( b ), [ b["n0"], b["n1"] ] )

		Gaffer.MetadataAlgo.setBookmarked( b["n0"], False )

		self.assertEqual( Gaffer.MetadataAlgo.getBookmarked( b ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getBookmarked( b["n0"] ), False )
		self.assertEqual( Gaffer.MetadataAlgo.getBookmarked( b["n1"] ), True )
		self.assertEqual( Gaffer.MetadataAlgo.bookmarks( b ), [ b["n1"] ] )

		Gaffer.MetadataAlgo.setBookmarked( b, True )

		self.assertEqual( Gaffer.MetadataAlgo.getBookmarked( b ), True )
		self.assertTrue( b not in Gaffer.MetadataAlgo.bookmarks( b ) )

		s = Gaffer.ScriptNode()
		s.addChild( b )

		self.assertEqual( Gaffer.MetadataAlgo.getBookmarked( b ), True )
		self.assertEqual( Gaffer.MetadataAlgo.bookmarks( s ), [ b ] )

	def testAffected( self ) :

		n = GafferTest.CompoundPlugNode()

		affected = []
		ancestorAffected = []
		childAffected = []
		def plugValueChanged( nodeTypeId, plugPath, key, plug ) :
			affected.append( Gaffer.MetadataAlgo.affectedByChange( n["p"]["s"], nodeTypeId, plugPath, plug ) )
			ancestorAffected.append( Gaffer.MetadataAlgo.ancestorAffectedByChange( n["p"]["s"], nodeTypeId, plugPath, plug ) )
			childAffected.append( Gaffer.MetadataAlgo.childAffectedByChange( n["p"], nodeTypeId, plugPath, plug ) )

		c = Gaffer.Metadata.plugValueChangedSignal().connect( plugValueChanged )

		Gaffer.Metadata.registerValue( Gaffer.Node, "user", "test", 1 )
		self.assertEqual( affected, [ False ] )
		self.assertEqual( ancestorAffected, [ False ] )
		self.assertEqual( childAffected, [ False ] )

		Gaffer.Metadata.registerValue( GafferTest.StringInOutNode, "p.s", "test", 1 )
		self.assertEqual( affected, [ False, False ] )
		self.assertEqual( ancestorAffected, [ False, False ] )
		self.assertEqual( childAffected, [ False, False ] )

		Gaffer.Metadata.registerValue( GafferTest.CompoundPlugNode, "p.s", "test", 1 )
		self.assertEqual( affected, [ False, False, True ] )
		self.assertEqual( ancestorAffected, [ False, False, False ] )
		self.assertEqual( childAffected, [ False, False, True ] )

		Gaffer.Metadata.registerValue( GafferTest.CompoundPlugNode, "p", "test", 2 )
		self.assertEqual( affected, [ False, False, True, False ] )
		self.assertEqual( ancestorAffected, [ False, False, False, True ] )
		self.assertEqual( childAffected, [ False, False, True, False ] )

		del affected[:]
		del ancestorAffected[:]
		del childAffected[:]

		Gaffer.Metadata.registerValue( n["user"], "test", 3 )
		self.assertEqual( affected, [ False ] )
		self.assertEqual( ancestorAffected, [ False ] )
		self.assertEqual( childAffected, [ False ] )

		Gaffer.Metadata.registerValue( n["p"]["s"], "test", 4 )
		self.assertEqual( affected, [ False, True ] )
		self.assertEqual( ancestorAffected, [ False, False ] )
		self.assertEqual( childAffected, [ False, True ] )

		Gaffer.Metadata.registerValue( n["p"], "test", 5 )
		self.assertEqual( affected, [ False, True, False ] )
		self.assertEqual( ancestorAffected, [ False, False, True ] )
		self.assertEqual( childAffected, [ False, True, False ] )

	def testNodeAffected( self ) :

		n = Gaffer.Box()
		n["c"] = Gaffer.Node()

		affected = []
		childAffected = []
		def nodeValueChanged( nodeTypeId, key, node ) :
			affected.append( Gaffer.MetadataAlgo.affectedByChange( n, nodeTypeId, node ) )
			childAffected.append( Gaffer.MetadataAlgo.childAffectedByChange( n, nodeTypeId, node ) )

		c = Gaffer.Metadata.nodeValueChangedSignal().connect( nodeValueChanged )

		Gaffer.Metadata.registerValue( Gaffer.Node, "metadataAlgoTest", 1 )
		self.assertEqual( affected, [ True ] )
		self.assertEqual( childAffected, [ True ] )

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "metadataAlgoTest", 2 )
		self.assertEqual( affected, [ True, False ] )
		self.assertEqual( childAffected, [ True, False ] )

		Gaffer.Metadata.registerValue( n, "metadataAlgoTest", 3 )
		self.assertEqual( affected, [ True, False, True ] )
		self.assertEqual( childAffected, [ True, False, False ] )

		n["a"] = GafferTest.AddNode()
		Gaffer.Metadata.registerValue( n["a"], "metadataAlgoTest", 4 )
		self.assertEqual( affected, [ True, False, True, False ] )
		self.assertEqual( childAffected, [ True, False, False, True ] )

	def testAncestorNodeAffected( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()
		s["b2"] = Gaffer.Box()

		affected = []
		def nodeValueChanged( nodeTypeId, key, node ) :

			a = set()
			for g in ( s["b"]["n"]["op1"], s["b"]["n"], s["b"] ) :
				if Gaffer.MetadataAlgo.ancestorAffectedByChange( g, nodeTypeId, node ) :
					a.add( g )

			affected.append( a )

		c = Gaffer.Metadata.nodeValueChangedSignal().connect( nodeValueChanged )

		Gaffer.Metadata.registerValue( s["b"]["n"], "metadataAlgoTest", "test" )
		self.assertEqual( len( affected ), 1 )
		self.assertEqual( affected[-1], { s["b"]["n"]["op1"] } )

		Gaffer.Metadata.registerValue( s["b"], "metadataAlgoTest", "test" )
		self.assertEqual( len( affected ), 2 )
		self.assertEqual( affected[-1], { s["b"]["n"], s["b"]["n"]["op1"] } )

		Gaffer.Metadata.registerValue( s, "metadataAlgoTest", "test" )
		self.assertEqual( len( affected ), 3 )
		self.assertEqual( affected[-1], { s["b"], s["b"]["n"], s["b"]["n"]["op1"] } )

		Gaffer.Metadata.registerValue( Gaffer.Box, "metadataAlgoTest", "test" )

		Gaffer.Metadata.registerValue( s["b"], "metadataAlgoTest", "test" )
		self.assertEqual( len( affected ), 4 )
		self.assertEqual( affected[-1], { s["b"]["n"], s["b"]["n"]["op1"] } )

		Gaffer.Metadata.registerValue( s["b2"], "metadataAlgoTest", "test" )
		self.assertEqual( len( affected ), 5 )
		self.assertEqual( affected[-1], set() )

	def testCopy( self ) :

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "metadataAlgoTest", "test" )

		s = GafferTest.AddNode()
		Gaffer.Metadata.registerValue( s, "a", "a" )
		Gaffer.Metadata.registerValue( s, "a2", "a2" )
		Gaffer.Metadata.registerValue( s, "b", "b" )
		Gaffer.Metadata.registerValue( s, "c", "c", persistent = False )

		t = Gaffer.Node()
		Gaffer.MetadataAlgo.copy( s, t )
		self.assertEqual( set( Gaffer.Metadata.registeredValues( t ) ), { "metadataAlgoTest", "a", "a2", "b" } )

		t = Gaffer.Node()
		Gaffer.MetadataAlgo.copy( s, t, persistentOnly = False )
		self.assertEqual( set( Gaffer.Metadata.registeredValues( t ) ), { "metadataAlgoTest", "a", "a2", "b", "c" } )

		t = Gaffer.Node()
		Gaffer.MetadataAlgo.copy( s, t, exclude = "a*" )
		self.assertEqual( set( Gaffer.Metadata.registeredValues( t ) ), { "metadataAlgoTest", "b" } )

		t = Gaffer.Node()
		Gaffer.MetadataAlgo.copy( s, t, exclude = "a b" )
		self.assertEqual( set( Gaffer.Metadata.registeredValues( t ) ), { "metadataAlgoTest", "a2" } )

		t = Gaffer.Node()
		Gaffer.MetadataAlgo.copy( s, t )
		for k in Gaffer.Metadata.registeredValues( t ) :
			self.assertEqual( Gaffer.Metadata.value( t, k ), Gaffer.Metadata.value( s, k ) )

	def testCopyColorKeepExisting( self ) :

		plug1 = Gaffer.IntPlug()
		plug2 = Gaffer.IntPlug()

		connectionColor = imath.Color3f( 0.1 , 0.2 , 0.3 )
		noodleColor = imath.Color3f( 0.4, 0.5 , 0.6 )
		noodleColorExisting = imath.Color3f( 0.7, 0.8 , 0.9 )

		Gaffer.Metadata.registerValue( plug1, "connectionGadget:color", connectionColor )
		Gaffer.Metadata.registerValue( plug1, "nodule:color", noodleColor )

		Gaffer.Metadata.registerValue( plug2, "nodule:color", noodleColorExisting )

		Gaffer.MetadataAlgo.copyColors(plug1, plug2, overwrite = False )

		self.assertEqual( Gaffer.Metadata.value( plug2, "connectionGadget:color" ), connectionColor )
		self.assertEqual( Gaffer.Metadata.value( plug2, "nodule:color" ), noodleColorExisting )

	def testCopyColorForceOverWrite( self ) :

		plug1 = Gaffer.IntPlug()
		plug2 = Gaffer.IntPlug()

		connectionColor = imath.Color3f( 0.1 , 0.2 , 0.3 )
		noodleColor =  imath.Color3f( 0.4, 0.5 , 0.6 )
		noodleColorExisting = imath.Color3f( 0.7, 0.8 , 0.9 )

		Gaffer.Metadata.registerValue( plug1, "connectionGadget:color", connectionColor )
		Gaffer.Metadata.registerValue( plug1, "nodule:color", noodleColor )

		Gaffer.Metadata.registerValue( plug2, "nodule:color", noodleColorExisting )

		Gaffer.MetadataAlgo.copyColors(plug1, plug2, overwrite = True )

		self.assertEqual( Gaffer.Metadata.value( plug2, "connectionGadget:color" ), connectionColor )
		self.assertEqual( Gaffer.Metadata.value( plug2, "nodule:color" ), noodleColor )

	def testReadOnlyAffectedByChange( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()
		s["b2"] = Gaffer.Box()

		affected = []
		def nodeValueChanged( nodeTypeId, key, node ) :

			a = set()
			for g in ( s["b"]["n"]["op1"], s["b"]["n"], s["b"] ) :
				if Gaffer.MetadataAlgo.readOnlyAffectedByChange( g, nodeTypeId, key, node ) :
					a.add( g )

			affected.append( a )

		c1 = Gaffer.Metadata.nodeValueChangedSignal().connect( nodeValueChanged )

		def plugValueChanged( nodeTypeId, plugPath, key, plug ) :

			a = set()
			for g in ( s["b"]["n"]["op1"], s["b"]["n"], s["b"] ) :
				if Gaffer.MetadataAlgo.readOnlyAffectedByChange( g, nodeTypeId, plugPath, key, plug ) :
					a.add( g )

			affected.append( a )

		c2 = Gaffer.Metadata.plugValueChangedSignal().connect( plugValueChanged )

		Gaffer.Metadata.registerValue( s["b"]["n"]["op1"], "metadataAlgoTest", "test" )
		self.assertEqual( len( affected ), 1 )
		self.assertEqual( affected[-1], set() )

		Gaffer.MetadataAlgo.setReadOnly( s["b"]["n"]["op1"], True )
		self.assertEqual( len( affected ), 2 )
		self.assertEqual( affected[-1], { s["b"]["n"]["op1"] } )

		Gaffer.MetadataAlgo.setReadOnly( s["b"]["n"], True )
		self.assertEqual( len( affected ), 3 )
		self.assertEqual( affected[-1], { s["b"]["n"]["op1"], s["b"]["n"] } )

		Gaffer.MetadataAlgo.setChildNodesAreReadOnly( s["b"], True )
		self.assertEqual( len( affected ), 4 )
		self.assertEqual( affected[-1], { s["b"]["n"]["op1"], s["b"]["n"] } )

		Gaffer.MetadataAlgo.setChildNodesAreReadOnly( s["b2"], True )
		self.assertEqual( len( affected ), 5 )
		self.assertEqual( affected[-1], set() )

	def testUnbookmarkedNodesDontHaveMetadata( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		self.assertEqual( len( Gaffer.Metadata.registeredValues( s["n"], instanceOnly = True ) ), 0 )

		Gaffer.MetadataAlgo.setBookmarked( s["n"], True )
		self.assertEqual( len( Gaffer.Metadata.registeredValues( s["n"], instanceOnly = True ) ), 1 )

		Gaffer.MetadataAlgo.setBookmarked( s["n"], False )
		self.assertEqual( len( Gaffer.Metadata.registeredValues( s["n"], instanceOnly = True ) ), 0 )

	def testLoadLegacyBookmarks( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/legacyBookmarks.gfr" )
		s.load()

		self.assertTrue( Gaffer.MetadataAlgo.getBookmarked( s["Bookmarked"] ) )
		self.assertEqual( len( Gaffer.Metadata.registeredValues( s["Bookmarked"], instanceOnly = True ) ), 1 )
		self.assertFalse( Gaffer.MetadataAlgo.getBookmarked( s["Unbookmarked"] ) )
		self.assertEqual( len( Gaffer.Metadata.registeredValues( s["Unbookmarked"], instanceOnly = True ) ), 0 )
		self.assertTrue( Gaffer.MetadataAlgo.getBookmarked( s["OldBookmarked"] ) )
		self.assertEqual( len( Gaffer.Metadata.registeredValues( s["OldBookmarked"], instanceOnly = True ) ), 1 )

	def testNumericBookmarks( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()

		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, s["n1"] )

		self.assertEqual( Gaffer.MetadataAlgo.getNumericBookmark( s, 1 ), s["n1"] )
		self.assertEqual( Gaffer.MetadataAlgo.numericBookmark( s["n1"] ), 1 )

		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, s["n2"] )  # moving the bookmark

		self.assertEqual( Gaffer.MetadataAlgo.numericBookmark( s["n1"] ), 0 )
		self.assertEqual( Gaffer.MetadataAlgo.getNumericBookmark( s, 1 ), s["n2"] )
		self.assertEqual( Gaffer.MetadataAlgo.numericBookmark( s["n2"] ), 1 )

		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, None )

		self.assertEqual( Gaffer.MetadataAlgo.getNumericBookmark( s, 1 ), None )
		self.assertEqual( Gaffer.MetadataAlgo.numericBookmark( s["n2"] ), 0 )

	def testNumericBookmarkAffectedByChange( self ) :

		# The naming convention for valid numeric bookmarks is "numericBookmark<1-9>"
		for i in range( 1, 10 ) :
			self.assertTrue( Gaffer.MetadataAlgo.numericBookmarkAffectedByChange( "numericBookmark%s" % i ) )

		self.assertFalse( Gaffer.MetadataAlgo.numericBookmarkAffectedByChange( "numericBookmark0" ) )
		self.assertFalse( Gaffer.MetadataAlgo.numericBookmarkAffectedByChange( "numericBookmark-1" ) )
		self.assertFalse( Gaffer.MetadataAlgo.numericBookmarkAffectedByChange( "numericBookmark10" ) )
		self.assertFalse( Gaffer.MetadataAlgo.numericBookmarkAffectedByChange( "foo" ) )

	def testAffectedByPlugTypeRegistration( self ) :

		n = GafferTest.CompoundPlugNode()

		self.assertTrue( Gaffer.MetadataAlgo.affectedByChange( n["p"]["s"], Gaffer.StringPlug, changedPlugPath = "", changedPlug = None ) )
		self.assertFalse( Gaffer.MetadataAlgo.affectedByChange( n["p"]["s"], Gaffer.IntPlug, changedPlugPath = "", changedPlug = None ) )
		self.assertTrue( Gaffer.MetadataAlgo.affectedByChange( n["p"], Gaffer.Plug, changedPlugPath = "", changedPlug = None ) )

		self.assertTrue( Gaffer.MetadataAlgo.childAffectedByChange( n["p"], Gaffer.StringPlug, changedPlugPath = "", changedPlug = None ) )
		self.assertTrue( Gaffer.MetadataAlgo.childAffectedByChange( n["p"], Gaffer.FloatPlug, changedPlugPath = "", changedPlug = None ) )
		self.assertFalse( Gaffer.MetadataAlgo.childAffectedByChange( n["p"], Gaffer.IntPlug, changedPlugPath = "", changedPlug = None ) )
		self.assertFalse( Gaffer.MetadataAlgo.childAffectedByChange( n["p"]["s"], Gaffer.StringPlug, changedPlugPath = "", changedPlug = None ) )

		self.assertFalse( Gaffer.MetadataAlgo.ancestorAffectedByChange( n["p"], Gaffer.CompoundPlug, changedPlugPath = "", changedPlug = None ) )
		self.assertTrue( Gaffer.MetadataAlgo.ancestorAffectedByChange( n["p"]["s"], Gaffer.CompoundPlug, changedPlugPath = "", changedPlug = None ) )
		self.assertTrue( Gaffer.MetadataAlgo.ancestorAffectedByChange( n["p"]["s"], Gaffer.Plug, changedPlugPath = "", changedPlug = None ) )
		self.assertFalse( Gaffer.MetadataAlgo.ancestorAffectedByChange( n["p"]["s"], Gaffer.StringPlug, changedPlugPath = "", changedPlug = None ) )

	def testAffectedByPlugRelativeMetadata( self ) :

		n = GafferTest.CompoundNumericNode()

		self.assertTrue( Gaffer.MetadataAlgo.affectedByChange( n["p"]["x"], Gaffer.V3fPlug, changedPlugPath = "*", changedPlug = None ) )
		self.assertTrue( Gaffer.MetadataAlgo.affectedByChange( n["p"]["x"], Gaffer.V3fPlug, changedPlugPath = "[xyz]", changedPlug = None ) )
		self.assertTrue( Gaffer.MetadataAlgo.affectedByChange( n["p"]["x"], Gaffer.V3fPlug, changedPlugPath = "...", changedPlug = None ) )
		self.assertFalse( Gaffer.MetadataAlgo.affectedByChange( n["p"]["x"], Gaffer.V3fPlug, changedPlugPath = "x.c", changedPlug = None ) )
		self.assertFalse( Gaffer.MetadataAlgo.affectedByChange( n["p"]["x"], Gaffer.V3fPlug, changedPlugPath = "c", changedPlug = None ) )

		self.assertTrue( Gaffer.MetadataAlgo.childAffectedByChange( n["p"], Gaffer.V3fPlug, changedPlugPath = "[xyz]", changedPlug = None ) )
		self.assertFalse( Gaffer.MetadataAlgo.childAffectedByChange( n["p"], Gaffer.V3fPlug, changedPlugPath = "x.c", changedPlug = None ) )

	def tearDown( self ) :

		for n in ( Gaffer.Node, Gaffer.Box, GafferTest.AddNode ) :
			Gaffer.Metadata.deregisterValue( n, "metadataAlgoTest" )

if __name__ == "__main__":
	unittest.main()
