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

import Gaffer
import GafferTest
import imath
import IECore

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

		Gaffer.Metadata.registerValue( GafferTest.SphereNode, "p.s", "test", 1 )
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

	def tearDown( self ) :

		for n in ( Gaffer.Node, GafferTest.AddNode ) :
			Gaffer.Metadata.deregisterValue( n, "metadataAlgoTest" )

if __name__ == "__main__":
	unittest.main()
