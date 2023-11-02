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

		with self.assertRaisesRegex( Exception, r"did not match C\+\+ signature" ) :
			Gaffer.MetadataAlgo.readOnly( None )

	def testReadOnlyReason( self ) :

		b = Gaffer.Box()
		b["b"] = Gaffer.Box()

		n = GafferTest.AddNode()
		b["b"]["n"] = n

		self.assertIsNone( Gaffer.MetadataAlgo.readOnlyReason( n ) )
		self.assertIsNone( Gaffer.MetadataAlgo.readOnlyReason( n["op1"] ) )

		Gaffer.MetadataAlgo.setReadOnly( b, True )
		self.assertEqual( Gaffer.MetadataAlgo.readOnlyReason( n ), b )
		self.assertEqual( Gaffer.MetadataAlgo.readOnlyReason( n["op1"] ), b )

		Gaffer.MetadataAlgo.setReadOnly( b["b"], True )
		self.assertEqual( Gaffer.MetadataAlgo.readOnlyReason( n["op1"] ), b )

		Gaffer.MetadataAlgo.setReadOnly( b["b"]["n"], True )
		self.assertEqual( Gaffer.MetadataAlgo.readOnlyReason( n["op1"] ), b )

		Gaffer.MetadataAlgo.setReadOnly( b["b"]["n"]["op1"], True )
		self.assertEqual( Gaffer.MetadataAlgo.readOnlyReason( n["op1"] ), b )

		Gaffer.MetadataAlgo.setReadOnly( b, False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnlyReason( n["op1"] ), b["b"] )

		Gaffer.MetadataAlgo.setReadOnly( b["b"], False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnlyReason( n["op1"] ), n )

		Gaffer.MetadataAlgo.setReadOnly( b["b"]["n"], False )
		self.assertEqual( Gaffer.MetadataAlgo.readOnlyReason( n["op1"] ), n["op1"] )

		Gaffer.MetadataAlgo.setReadOnly( b["b"]["n"]["op1"], False )
		self.assertIsNone( Gaffer.MetadataAlgo.readOnlyReason( n["op1"] ) )

		with self.assertRaisesRegex( Exception, r"did not match C\+\+ signature" ) :
			Gaffer.MetadataAlgo.readOnlyReason( None )

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

		c = Gaffer.Metadata.plugValueChangedSignal().connect( plugValueChanged, scoped = True )

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

		c = Gaffer.Metadata.nodeValueChangedSignal().connect( nodeValueChanged, scoped = True )

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

		c = Gaffer.Metadata.nodeValueChangedSignal().connect( nodeValueChanged, scoped = True )

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

		def registeredTestValues( node ) :

			# We don't know what metadata might have been registered to the node
			# before we run, so here we strip out any values that we're not interested in.
			return set( Gaffer.Metadata.registeredValues( t ) ).intersection(
				{ "metadataAlgoTest", "a", "a2", "b", "c" }
			)

		t = Gaffer.Node()
		Gaffer.MetadataAlgo.copy( s, t )
		self.assertEqual( registeredTestValues( t ), { "metadataAlgoTest", "a", "a2", "b" } )

		t = Gaffer.Node()
		Gaffer.MetadataAlgo.copy( s, t, persistentOnly = False )
		self.assertEqual( registeredTestValues( t ), { "metadataAlgoTest", "a", "a2", "b", "c" } )

		t = Gaffer.Node()
		Gaffer.MetadataAlgo.copy( s, t, exclude = "a*" )
		self.assertEqual( registeredTestValues( t ), { "metadataAlgoTest", "b" } )

		t = Gaffer.Node()
		Gaffer.MetadataAlgo.copy( s, t, exclude = "a b" )
		self.assertEqual( registeredTestValues( t ), { "metadataAlgoTest", "a2" } )

		t = Gaffer.Node()
		Gaffer.MetadataAlgo.copy( s, t )
		for k in Gaffer.Metadata.registeredValues( t ) :
			self.assertEqual( Gaffer.Metadata.value( t, k ), Gaffer.Metadata.value( s, k ) )

		t = Gaffer.Node()
		Gaffer.MetadataAlgo.copyIf( s, t, lambda f, t, n : n.startswith( "a" ) )
		self.assertEqual( registeredTestValues( t ), { "a", "a2" } )

		t = Gaffer.Node()
		Gaffer.MetadataAlgo.copyIf( s, t, lambda f, t, n : n.startswith( "c" ) )
		self.assertEqual( registeredTestValues( t ), { "c" } )

	def testIsPromotable( self ) :

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "notPromotableTest:promotable", False )
		Gaffer.Metadata.registerValue( GafferTest.AddNode, "notPromotableTest", "no")
		Gaffer.Metadata.registerValue( GafferTest.AddNode, "promotableTest:promotable", True )
		Gaffer.Metadata.registerValue( GafferTest.AddNode, "promotableTest", "yes" )

		s = GafferTest.AddNode()
		t = Gaffer.Node()

		self.assertFalse( Gaffer.MetadataAlgo.isPromotable( s, t, "notPromotableTest" ) )
		self.assertFalse( Gaffer.MetadataAlgo.isPromotable( s, t, "notPromotableTest:promotable" ) )
		self.assertTrue( Gaffer.MetadataAlgo.isPromotable( s, t, "promotableTest") )
		self.assertFalse( Gaffer.MetadataAlgo.isPromotable( s, t, "promotableTest:promotable" ) )

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

		c1 = Gaffer.Metadata.nodeValueChangedSignal().connect( nodeValueChanged, scoped = True )

		def plugValueChanged( nodeTypeId, plugPath, key, plug ) :

			a = set()
			for g in ( s["b"]["n"]["op1"], s["b"]["n"], s["b"] ) :
				if Gaffer.MetadataAlgo.readOnlyAffectedByChange( g, nodeTypeId, plugPath, key, plug ) :
					a.add( g )

			affected.append( a )

		c2 = Gaffer.Metadata.plugValueChangedSignal().connect( plugValueChanged, scoped = True )

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
		self.assertEqual( len( Gaffer.Metadata.registeredValues( s["n"], Gaffer.Metadata.RegistrationTypes.Instance ) ), 0 )

		Gaffer.MetadataAlgo.setBookmarked( s["n"], True )
		self.assertEqual( len( Gaffer.Metadata.registeredValues( s["n"], Gaffer.Metadata.RegistrationTypes.Instance ) ), 1 )

		Gaffer.MetadataAlgo.setBookmarked( s["n"], False )
		self.assertEqual( len( Gaffer.Metadata.registeredValues( s["n"], Gaffer.Metadata.RegistrationTypes.Instance ) ), 0 )

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

	def testNumericBookmarksSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()

		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, s["n1"] )
		Gaffer.MetadataAlgo.setNumericBookmark( s, 2, s["n2"] )

		# Copying within script doesn't copy numeric bookmarks
		s.execute( s.serialise() )

		self.assertEqual( Gaffer.MetadataAlgo.getNumericBookmark( s, 1 ), s["n1"] )
		self.assertEqual( Gaffer.MetadataAlgo.getNumericBookmark( s, 2 ), s["n2"] )
		self.assertEqual( Gaffer.MetadataAlgo.numericBookmark( s["n3"] ), 0 )
		self.assertEqual( Gaffer.MetadataAlgo.numericBookmark( s["n4"] ), 0 )

		del s["n3"]
		del s["n4"]

		# Copying to new script preserves numeric bookmarks

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( Gaffer.MetadataAlgo.getNumericBookmark( s2, 1 ), s2["n1"] )
		self.assertEqual( Gaffer.MetadataAlgo.getNumericBookmark( s2, 2 ), s2["n2"] )

	def testNumericBookmarksInReferences( self ) :

		# Numeric bookmarks are removed when loading References.

		s = Gaffer.ScriptNode()
		s["box"] = Gaffer.Box()
		s["box"]["n"] = Gaffer.Node()

		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, s["box"]["n"] )

		s["box"].exportForReference( self.temporaryDirectory() / "bookmarked.grf" )

		# Bring reference back in
		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() / "bookmarked.grf" )

		# Clashing Metadata was completely removed
		self.assertEqual( Gaffer.Metadata.value( s["r"]["n"], "numericBookmark1" ), None )
		self.assertEqual( Gaffer.MetadataAlgo.numericBookmark( s["r"]["n"] ), 0 )
		self.assertEqual( Gaffer.MetadataAlgo.getNumericBookmark( s, 1 ), s["box"]["n"] )

		# Even without the clash, the metadata is removed

		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, None )

		s["r2"] = Gaffer.Reference()
		s["r2"].load( self.temporaryDirectory() / "bookmarked.grf" )

		self.assertEqual( Gaffer.Metadata.value( s["r2"]["n"], "numericBookmark1" ), None )
		self.assertEqual( Gaffer.MetadataAlgo.numericBookmark( s["r2"]["n"] ), 0 )
		self.assertEqual( Gaffer.MetadataAlgo.getNumericBookmark( s, 1 ), None )

	def testNumericBookmarksInReadOnlyBox( self ) :

		# Numeric bookmarks are removed when loading read-only boxes.

		s = Gaffer.ScriptNode()
		s["box"] = Gaffer.Box()
		s["box"]["n"] = Gaffer.Node()

		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, s["box"]["n"] )

		s["box"].exportForReference( self.temporaryDirectory() / "bookmarked.grf" )

		# Bring the box back in, not as a Reference, but as read-only Box
		s["b1"] = Gaffer.Box()
		Gaffer.MetadataAlgo.setChildNodesAreReadOnly( s["b1"], True )
		s.executeFile( self.temporaryDirectory() / "bookmarked.grf", parent = s["b1"], continueOnError = True)

		# Clashing Metadata was completely removed
		self.assertEqual( Gaffer.Metadata.value( s["b1"]["n"], "numericBookmark1" ), None )
		self.assertEqual( Gaffer.MetadataAlgo.numericBookmark( s["b1"]["n"] ), 0 )
		self.assertEqual( Gaffer.MetadataAlgo.getNumericBookmark( s, 1 ), s["box"]["n"] )

		# Even without the clash, the metadata is removed

		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, None )

		s["b2"] = Gaffer.Box()
		Gaffer.MetadataAlgo.setChildNodesAreReadOnly( s["b2"], True )
		s.executeFile( self.temporaryDirectory() / "bookmarked.grf", parent = s["b2"], continueOnError = True)

		self.assertEqual( Gaffer.Metadata.value( s["b2"]["n"], "numericBookmark1" ), None )
		self.assertEqual( Gaffer.MetadataAlgo.numericBookmark( s["b2"]["n"] ), 0 )
		self.assertEqual( Gaffer.MetadataAlgo.getNumericBookmark( s, 1 ), None )

		# But loading it without the read-only flag results in the bookmark being set

		s["b3"] = Gaffer.Box()
		s.executeFile( self.temporaryDirectory() / "bookmarked.grf", parent = s["b3"], continueOnError = True)

		self.assertEqual( Gaffer.Metadata.value( s["b3"]["n"], "numericBookmark1" ), True )
		self.assertEqual( Gaffer.MetadataAlgo.numericBookmark( s["b3"]["n"] ), 1 )
		self.assertEqual( Gaffer.MetadataAlgo.getNumericBookmark( s, 1 ), s["b3"]["n"] )

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

	def testAnnotations( self ) :

		n = Gaffer.Node()
		self.assertEqual( Gaffer.MetadataAlgo.annotations( n ), [] )
		self.assertIsNone( Gaffer.MetadataAlgo.getAnnotation( n, "test" ) )

		cs = GafferTest.CapturingSlot( Gaffer.Metadata.nodeValueChangedSignal( n ) )
		Gaffer.MetadataAlgo.addAnnotation( n, "test", Gaffer.MetadataAlgo.Annotation( "Hello world", imath.Color3f( 1, 0, 0 ) ) )
		self.assertTrue( len( cs ) )
		for x in cs :
			self.assertTrue( Gaffer.MetadataAlgo.annotationsAffectedByChange( x[1] ) )

		self.assertEqual( Gaffer.MetadataAlgo.annotations( n ), [ "test" ] )
		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( n, "test" ),
			Gaffer.MetadataAlgo.Annotation( "Hello world", imath.Color3f( 1, 0, 0 ) )
		)

		del cs[:]
		Gaffer.MetadataAlgo.addAnnotation( n, "test2", Gaffer.MetadataAlgo.Annotation( "abc", imath.Color3f( 0, 1, 0 ) ) )
		self.assertTrue( len( cs ) )
		for x in cs :
			self.assertTrue( Gaffer.MetadataAlgo.annotationsAffectedByChange( x[1] ) )

		self.assertEqual( Gaffer.MetadataAlgo.annotations( n ), [ "test", "test2" ] )
		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( n, "test2" ),
			Gaffer.MetadataAlgo.Annotation( "abc", imath.Color3f( 0, 1, 0 ) )
		)

		del cs[:]
		Gaffer.MetadataAlgo.removeAnnotation( n, "test" )
		self.assertTrue( len( cs ) )
		for x in cs :
			self.assertTrue( Gaffer.MetadataAlgo.annotationsAffectedByChange( x[1] ) )

		self.assertEqual( Gaffer.MetadataAlgo.annotations( n ), [ "test2" ] )
		self.assertIsNone( Gaffer.MetadataAlgo.getAnnotation( n, "test" ) )
		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( n, "test2" ),
			Gaffer.MetadataAlgo.Annotation( "abc", imath.Color3f( 0, 1, 0 ) )
		)

	def testAnnotationWithoutColor( self ) :

		n = Gaffer.Node()
		Gaffer.MetadataAlgo.addAnnotation( n, "test", Gaffer.MetadataAlgo.Annotation( text = "abc" ) )
		self.assertEqual( len( Gaffer.Metadata.registeredValues( n, Gaffer.Metadata.RegistrationTypes.Instance ) ), 1 )
		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( n, "test" ),
			Gaffer.MetadataAlgo.Annotation( text = "abc" )
		)

		Gaffer.MetadataAlgo.addAnnotation( n, "test", Gaffer.MetadataAlgo.Annotation( text = "xyz", color = imath.Color3f( 1 ) ) )
		self.assertEqual( len( Gaffer.Metadata.registeredValues( n, Gaffer.Metadata.RegistrationTypes.Instance ) ), 2 )
		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( n, "test" ),
			Gaffer.MetadataAlgo.Annotation( text = "xyz", color = imath.Color3f( 1 ) )
		)

		Gaffer.MetadataAlgo.addAnnotation( n, "test", Gaffer.MetadataAlgo.Annotation( text = "abc" ) )
		self.assertEqual( len( Gaffer.Metadata.registeredValues( n, Gaffer.Metadata.RegistrationTypes.Instance ) ), 1 )
		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( n, "test" ),
			Gaffer.MetadataAlgo.Annotation( text = "abc" )
		)

	def testAnnotationToBool( self ) :

		self.assertFalse( Gaffer.MetadataAlgo.Annotation() )
		self.assertTrue( Gaffer.MetadataAlgo.Annotation( "test" ) )

	def testAnnotationTemplates( self ) :

		defaultTemplates = Gaffer.MetadataAlgo.annotationTemplates()
		self.assertIsNone( Gaffer.MetadataAlgo.getAnnotationTemplate( "test" ) )

		a = Gaffer.MetadataAlgo.Annotation( "", imath.Color3f( 1, 0, 0 ) )
		Gaffer.MetadataAlgo.addAnnotationTemplate( "test", a )
		self.assertEqual( Gaffer.MetadataAlgo.getAnnotationTemplate( "test" ), a )
		self.assertEqual( Gaffer.MetadataAlgo.annotationTemplates(), defaultTemplates + [ "test" ] )

		n = Gaffer.Node()
		Gaffer.MetadataAlgo.addAnnotation( n, "test", Gaffer.MetadataAlgo.Annotation( "hi" ) )
		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( n, "test" ),
			Gaffer.MetadataAlgo.Annotation( "hi" ),
		)
		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( n, "test", inheritTemplate = True ),
			Gaffer.MetadataAlgo.Annotation( "hi", imath.Color3f( 1, 0, 0 ) ),
		)

		Gaffer.MetadataAlgo.removeAnnotationTemplate( "test" )
		self.assertIsNone( Gaffer.MetadataAlgo.getAnnotationTemplate( "test" ) )
		self.assertEqual( Gaffer.MetadataAlgo.annotationTemplates(), defaultTemplates )

		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( n, "test" ),
			Gaffer.MetadataAlgo.Annotation( "hi" ),
		)
		self.assertEqual(
			Gaffer.MetadataAlgo.getAnnotation( n, "test", inheritTemplate = True ),
			Gaffer.MetadataAlgo.Annotation( "hi" ),
		)

	def testNonUserAnnotationTemplates( self ) :

		defaultTemplates = Gaffer.MetadataAlgo.annotationTemplates()
		userOnlyDefaultTemplates = Gaffer.MetadataAlgo.annotationTemplates( userOnly = True )

		a = Gaffer.MetadataAlgo.Annotation( "", imath.Color3f( 1, 0, 0 ) )
		Gaffer.MetadataAlgo.addAnnotationTemplate( "test", a, user = False )

		self.assertEqual( Gaffer.MetadataAlgo.annotationTemplates(), defaultTemplates + [ "test" ] )
		self.assertEqual( Gaffer.MetadataAlgo.annotationTemplates( userOnly = True ), userOnlyDefaultTemplates )

		Gaffer.MetadataAlgo.addAnnotationTemplate( "test2", a, user = True )
		self.assertEqual( Gaffer.MetadataAlgo.annotationTemplates(), defaultTemplates + [ "test", "test2" ] )
		self.assertEqual( Gaffer.MetadataAlgo.annotationTemplates( userOnly = True ), userOnlyDefaultTemplates + [ "test2" ] )

	def testDeregisterRedundantValues( self ) :

		values = [ False, None, 1, 2 ] # False means "no registration", None means "None is registered as the value"
		for typeValue in values :
			for instanceValue in values :
				for nested in ( True, False ) :
					with self.subTest( typeValue = typeValue, instanceValue = instanceValue, nested = nested ) :

						node = GafferTest.AddNode()

						if typeValue is not False :
							Gaffer.Metadata.registerValue( GafferTest.AddNode, "metadataAlgoTest", typeValue )
						else :
							Gaffer.Metadata.deregisterValue( GafferTest.AddNode, "metadataAlgoTest" )

						if instanceValue is not False :
							Gaffer.Metadata.registerValue( node, "metadataAlgoTest", instanceValue )

						if typeValue is not False :
							self.assertEqual( Gaffer.Metadata.value( node, "metadataAlgoTest", registrationTypes = Gaffer.Metadata.RegistrationTypes.TypeId ), typeValue )

						if instanceValue is not False :
							self.assertEqual( Gaffer.Metadata.value( node, "metadataAlgoTest", registrationTypes = Gaffer.Metadata.RegistrationTypes.Instance ), instanceValue )

						if nested :
							nodeToPass = Gaffer.Box()
							nodeToPass.addChild( node )
						else :
							nodeToPass = node

						valueBefore = Gaffer.Metadata.value( node, "metadataAlgoTest" )
						Gaffer.MetadataAlgo.deregisterRedundantValues( nodeToPass )
						self.assertEqual( Gaffer.Metadata.value( node, "metadataAlgoTest" ), valueBefore )

						if typeValue == instanceValue :
							self.assertIsNone( Gaffer.Metadata.value( node, "metadataAlgoTest", registrationTypes = Gaffer.Metadata.RegistrationTypes.Instance ) )

	def tearDown( self ) :

		for n in ( Gaffer.Node, Gaffer.Box, GafferTest.AddNode ) :
			Gaffer.Metadata.deregisterValue( n, "metadataAlgoTest" )

if __name__ == "__main__":
	unittest.main()
