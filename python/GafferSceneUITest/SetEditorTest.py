##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
import GafferScene
import GafferUITest

from GafferSceneUI import _GafferSceneUI

class SetEditorTest( GafferUITest.TestCase ) :

	def testSetPathSimpleChildren( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "A B C D" )

		context = Gaffer.Context()
		path = _GafferSceneUI._SetEditor.SetPath( plane["out"], context, "/" )
		self.assertTrue( path.isValid() )
		self.assertFalse( path.isLeaf() )

		children = path.children()
		self.assertEqual( [ str( c ) for c in children ], [ "/A", "/B", "/C", "/D" ] )
		for child in children :
			self.assertIsInstance( child, _GafferSceneUI._SetEditor.SetPath )
			self.assertTrue( child.getContext().isSame( context ) )
			self.assertTrue( child.getScene().isSame( plane["out"] ) )
			self.assertTrue( child.isLeaf() )
			self.assertTrue( child.isValid() )
			self.assertEqual( child.children(), [] )

	def testSetPathNamespacedChildren( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "A A:B A:C D E:F:G" )

		path = _GafferSceneUI._SetEditor.SetPath( plane["out"], Gaffer.Context(), "/" )
		self.assertTrue( path.isValid() )
		self.assertFalse( path.isLeaf() )

		for parent, expectedChildren, setName in [
			( "/", [ "/A", "/D", "/E" ], None ),
			( "/A", [ "/A/A:B", "/A/A:C" ], "A" ),
			( "/A/A:B", [], "A:B" ),
			( "/A/A:C", [], "A:C" ),
			( "/D", [], "D" ),
			( "/E", [ "/E/F" ], None ),
			( "/E/F", [ "/E/F/E:F:G" ], None ),
			( "/E/F/E:F:G", [], "E:F:G" ),
		] :

			path.setFromString( parent )
			self.assertTrue( path.isValid() )

			children = path.children()
			self.assertEqual( path.isLeaf(), not children )
			self.assertEqual( [ str( c ) for c in children ], expectedChildren )

			self.assertEqual( path.property( "setPath:setName" ), setName )

	def testSetPathIsValid( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "A A:B A:C D E:F:G" )

		path = _GafferSceneUI._SetEditor.SetPath( plane["out"], Gaffer.Context(), "/" )
		self.assertTrue( path.isValid() )
		self.assertFalse( path.isLeaf() )

		for parent, valid in [
			( "/", True ),
			( "/A", True ),
			( "/A/A:B", True ),
			( "/A/A:C", True ),
			( "/D", True ),
			( "/E", True ),
			( "/E/F", True ),
			( "/E/F/E:F:G", True ),
			( "/F", False ),
			( "/A/A:D", False ),
			( "/D/D:A", False ),
		] :

			path.setFromString( parent )
			self.assertEqual( path.isValid(), valid )

	def testSetPathIsLeaf( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "A A:B A:C D E:F:G" )

		path = _GafferSceneUI._SetEditor.SetPath( plane["out"], Gaffer.Context(), "/" )
		self.assertTrue( path.isValid() )
		self.assertFalse( path.isLeaf() )

		for parent, leaf in [
			( "/", False ),
			( "/A", False ),
			( "/A/A:B", True ),
			( "/A/A:C", True ),
			( "/D", True ),
			( "/E", False ),
			( "/E/F", False ),
			( "/E/F/E:F:G", True ),
			( "/F", False ),
			( "/A/A:D", False ),
			( "/D/D:A", False ),
		] :

			path.setFromString( parent )
			self.assertEqual( path.isLeaf(), leaf )

	def testSetPathMemberCount( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "A A:B A:C D E:F:G" )

		planeB = GafferScene.Plane()
		planeB["sets"].setValue( "A A:C D F" )

		p = GafferScene.Parent()
		p["parent"].setValue( "/" )
		p["in"].setInput( plane["out"] )
		p["children"]["child0"].setInput( planeB["out"] )

		path = _GafferSceneUI._SetEditor.SetPath( p["out"], Gaffer.Context(), "/" )
		self.assertTrue( path.isValid() )
		self.assertFalse( path.isLeaf() )

		for parent, count in [
			( "/", None ),
			( "/A", 2 ),
			( "/A/A:B", 1 ),
			( "/A/A:C", 2 ),
			( "/D", 2 ),
			( "/E", None ),
			( "/E/F", None ),
			( "/E/F/E:F:G", 1 ),
			( "/F", 1 ),
			( "/A/A:D", None ),
			( "/D/D:A", None ),
		] :

			path.setFromString( parent )
			self.assertEqual( path.property( "setPath:memberCount" ), count )

	def testSetPathCancellation( self ) :

		plane = GafferScene.Plane()
		path = _GafferSceneUI._SetEditor.SetPath( plane["out"], Gaffer.Context(), "/" )

		canceller = IECore.Canceller()
		canceller.cancel()

		with self.assertRaises( IECore.Cancelled ) :
			path.children( canceller )

		with self.assertRaises( IECore.Cancelled ) :
			path.isValid( canceller )

		with self.assertRaises( IECore.Cancelled ) :
			path.isLeaf( canceller )

	def testSearchFilter( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "A B C D" )

		context = Gaffer.Context()
		path = _GafferSceneUI._SetEditor.SetPath( plane["out"], context, "/" )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A", "/B", "/C", "/D" ] )

		searchFilter = _GafferSceneUI._SetEditor.SearchFilter()
		searchFilter.setMatchPattern( "A" )
		path.setFilter( searchFilter )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A" ] )

		searchFilter.setMatchPattern( "A D" )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A", "/D" ] )

	def testSearchFilterRemovesEmptyParents( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "A B:E C:F D" )

		context = Gaffer.Context()
		path = _GafferSceneUI._SetEditor.SetPath( plane["out"], context, "/" )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A", "/B", "/C", "/D" ] )

		searchFilter = _GafferSceneUI._SetEditor.SearchFilter()
		searchFilter.setMatchPattern( "*:F" )
		path.setFilter( searchFilter )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/C" ] )

		searchFilter.setMatchPattern( "*:E *:F" )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/B", "/C" ] )

	def testEmptySetFilter( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "A A:E B C D" )

		emptySet = GafferScene.Set()
		emptySet["name"].setValue( "EMPTY A:EMPTY" )
		emptySet["in"].setInput( plane["out"] )

		context = Gaffer.Context()
		path = _GafferSceneUI._SetEditor.SetPath( emptySet["out"], context, "/" )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A", "/B", "/C", "/D", "/EMPTY" ] )

		emptySetFilter = _GafferSceneUI._SetEditor.EmptySetFilter()
		path.setFilter( emptySetFilter )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A", "/B", "/C", "/D" ] )

		emptySetFilter.setEnabled( False )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A", "/B", "/C", "/D", "/EMPTY" ] )

		path.setFromString( "/A" )
		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A/A:E", "/A/A:EMPTY" ] )

		emptySetFilter.setEnabled( True )
		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A/A:E" ] )
