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

import IECore

import Gaffer
import GafferTest
import GafferUITest
import GafferScene
import GafferSceneUI

class SetMembershipInspectorTest( GafferUITest.TestCase ) :

	def testName( self ) :

		plane = GafferScene.Plane()

		inspector = GafferSceneUI.Private.SetMembershipInspector( plane["out"], None, "planeSet" )
		self.assertEqual( inspector.name(), "planeSet" )

	@staticmethod
	def __inspect( scene, path, setName, editScope=None ) :

		editScopePlug = Gaffer.Plug()
		editScopePlug.setInput( editScope["enabled"] if editScope is not None else None )
		inspector = GafferSceneUI.Private.SetMembershipInspector( scene, editScopePlug, setName )
		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( path.split( "/" )[1:] )
			return inspector.inspect()

	def __assertExpectedResult(
		self,
		result,
		source,
		sourceType,
		editable,
		nonEditableReason = "",
		edit = None,
		editWarning = ""
	) :

		self.assertEqual( result.source(), source )
		self.assertEqual( result.sourceType(), sourceType )
		self.assertEqual( result.editable(), editable )

		if editable :
			self.assertEqual( nonEditableReason, "" )
			self.assertEqual( result.nonEditableReason(), "" )

			acquiredEdit = result.acquireEdit()
			self.assertIsNotNone( acquiredEdit )
			if result.editScope() :
				self.assertTrue( result.editScope().isAncestorOf( acquiredEdit ) )

			if edit is not None :
				self.assertEqual(
					acquiredEdit.fullName() if acquiredEdit is not None else "",
					edit.fullName() if edit is not None else ""
				)

			self.assertEqual( result.editWarning(), editWarning )

		else :
			self.assertIsNone( edit )
			self.assertEqual( editWarning, "" )
			self.assertEqual( result.editWarning(), "" )
			self.assertNotEqual( nonEditableReason, "" )
			self.assertEqual( result.nonEditableReason(), nonEditableReason )
			self.assertRaises( RuntimeError, result.acquireEdit )

	def testValue( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "planeSet" )

		self.assertEqual(
			self.__inspect( plane["out"], "/plane", "planeSet" ).value().value,
			True
		)

	def testFallbackValue( self ) :

		plane = GafferScene.Plane()
		group = GafferScene.Group()
		group["sets"].setValue( "planeSet" )
		group["in"][0].setInput( plane["out"] )

		inspection = self.__inspect( group["out"], "/group/plane", "planeSet" )
		self.assertEqual( inspection.value().value, True )
		self.assertEqual(
			inspection.sourceType(),
			GafferSceneUI.Private.Inspector.Result.SourceType.Fallback
		)

	def testSourceAndEdits( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["sets"].setValue( "planeSet" )

		s["group"] = GafferScene.Group()
		s["editScope1"] = Gaffer.EditScope()
		s["editScope2"] = Gaffer.EditScope()

		s["group"]["in"][0].setInput( s["plane"]["out"] )

		s["editScope1"].setup( s["group"]["out"] )
		s["editScope1"]["in"].setInput( s["group"]["out"] )

		s["editScope2"].setup( s["editScope1"]["out"] )
		s["editScope2"]["in"].setInput( s["editScope1"]["out"] )

		# Should be able to edit the plane directly.

		SourceType = GafferSceneUI.Private.Inspector.Result.SourceType

		self.__assertExpectedResult(
			self.__inspect( s["group"]["out"], "/group/plane", "planeSet", None ),
			source = s["plane"]["sets"],
			sourceType = SourceType.Other,
			editable = True,
			edit = s["plane"]["sets"]
		)

		# Even if there is an edit scope in the way

		self.__assertExpectedResult(
			self.__inspect( s["editScope1"]["out"], "/group/plane", "planeSet", None ),
			source = s["plane"]["sets"],
			sourceType = SourceType.Other,
			editable = True,
			edit = s["plane"]["sets"]
		)

		# We shouldn't be able to edit it if we've been told to use an EditScope and it isn't in the history
		self.__assertExpectedResult(
			self.__inspect( s["group"]["out"], "/group/plane", "planeSet", s["editScope1"] ),
			source = s["plane"]["sets"],
			sourceType = SourceType.Other,
			editable = False,
			nonEditableReason = "The target EditScope (editScope1) is not in the scene history."
		)

		# If it is in the history though, and we're told to use it, then we will.

		inspection = self.__inspect( s["editScope2"]["out"], "/group/plane", "planeSet", s["editScope2"] )
		self.assertIsNone(
			GafferScene.EditScopeAlgo.acquireSetEdits(
				s["editScope2"], "planeSet", createIfNecessary = False
			)
		)

		self.__assertExpectedResult(
			inspection,
			source = s["plane"]["sets"],
			sourceType = SourceType.Upstream,
			editable = True
		)

		planeEditScope2Edit = inspection.acquireEdit()

		self.assertIsNotNone( planeEditScope2Edit )
		self.assertEqual(
			planeEditScope2Edit,
			GafferScene.EditScopeAlgo.acquireSetEdits(
				s["editScope2"], "planeSet", createIfNecessary = False
			)
		)

		# If there's an edit downstream of the EditScope we're asked to use,
		# then we're allowed to be editable still

		inspection = self.__inspect( s["editScope2"]["out"], "/group/plane", "planeSet", s["editScope1"] )
		self.assertTrue( inspection.editable() )
		self.assertEqual( inspection.nonEditableReason(), "" )
		planeEditScope1Edit = inspection.acquireEdit()
		self.assertEqual(
			planeEditScope1Edit,
			GafferScene.EditScopeAlgo.acquireSetEdits(
				s["editScope1"], "planeSet", createIfNecessary = False
			)
		)
		self.assertEqual( inspection.editWarning(), "" )

		# If there is a source node inside an edit scope, make sure we use that

		s["editScope1"]["plane2"] = GafferScene.Plane()
		s["editScope1"]["plane2"]["sets"].setValue( "planeSet" )
		s["editScope1"]["plane2"]["name"].setValue( "plane2" )
		s["editScope1"]["parentPlane2"] = GafferScene.Parent()
		s["editScope1"]["parentPlane2"]["parent"].setValue( "/" )
		s["editScope1"]["parentPlane2"]["children"][0].setInput( s["editScope1"]["plane2"]["out"] )
		s["editScope1"]["parentPlane2"]["in"].setInput( s["editScope1"]["BoxIn"]["out"] )
		s["editScope1"]["SetMembershipEdits"]["in"].setInput( s["editScope1"]["parentPlane2"]["out"] )

		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "/plane2", "planeSet", s["editScope1"] ),
			source = s["editScope1"]["plane2"]["sets"],
			sourceType = SourceType.EditScope,
			editable = True,
			edit = s["editScope1"]["plane2"]["sets"]
		)

		# If there is a set node in the scope's processor, make sure we use that

		GafferScene.EditScopeAlgo.setSetMembership(
			s["editScope1"],
			IECore.PathMatcher( [ "/plane2" ] ),
			"planeSet",
			GafferScene.EditScopeAlgo.SetMembership.Added
		)
		plane2Edit = GafferScene.EditScopeAlgo.acquireSetEdits(
			s["editScope1"], "planeSet", createIfNecessary = False
		)
		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "/plane2", "planeSet", s["editScope1"] ),
			source = plane2Edit,
			sourceType = SourceType.EditScope,
			editable = True,
			edit = plane2Edit
		)

		# If there is a manual set node downstream of the scope's scene processor, make sure we use that

		s["editScope1"]["setPlane2"] = GafferScene.Set()
		s["editScope1"]["setPlane2"]["name"].setValue( "planeSet" )
		s["editScope1"]["setPlane2"]["mode"].setValue( GafferScene.Set.Mode.Add )
		s["editScope1"]["setPlane2"]["in"].setInput( s["editScope1"]["SetMembershipEdits"]["out"] )
		s["editScope1"]["setPlane2Filter"] = GafferScene.PathFilter()
		s["editScope1"]["setPlane2Filter"]["paths"].setValue( IECore.StringVectorData( [ "/plane2"] ) )
		s["editScope1"]["setPlane2"]["filter"].setInput( s["editScope1"]["setPlane2Filter"]["out"] )
		s["editScope1"]["BoxOut"]["in"].setInput( s["editScope1"]["setPlane2"]["out"] )

		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "/plane2", "planeSet", s["editScope1"] ),
			source = s["editScope1"]["setPlane2"]["name"],
			sourceType = SourceType.EditScope,
			editable = True,
			edit = s["editScope1"]["setPlane2"]["name"]
		)

		# If there is a manual set node outside of an edit scope, make sure we use that with no scope
		s["independentSet"] = GafferScene.Set()
		s["independentSet"]["name"].setValue( "planeSet" )
		s["independentSet"]["mode"].setValue( GafferScene.Set.Mode.Add )
		s["independentSet"]["in"].setInput( s["editScope2"]["out"] )

		s["independentSetFilter"] = GafferScene.PathFilter()
		s["independentSetFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )
		s["independentSet"]["filter"].setInput( s["independentSetFilter"]["out"] )

		self.__assertExpectedResult(
			self.__inspect( s["independentSet"]["out"], "/group/plane", "planeSet", None ),
			source = s["independentSet"]["name"],
			sourceType = SourceType.Other,
			editable = True,
			edit = s["independentSet"]["name"]
		)

		# Check editWarnings and nonEditableRasons

		self.__assertExpectedResult(
			self.__inspect( s["independentSet"]["out"], "/group/plane", "planeSet", s["editScope2"] ),
			source = s["independentSet"]["name"],
			sourceType = SourceType.Downstream,
			editable = True,
			edit = planeEditScope2Edit,
			editWarning = "SetMembership has edits downstream in independentSet."
		)

		s["editScope2"]["enabled"].setValue( False )

		self.__assertExpectedResult(
			self.__inspect( s["independentSet"]["out"], "/group/plane", "planeSet", s["editScope2"] ),
			source = s["independentSet"]["name"],
			sourceType = SourceType.Downstream,
			editable = False,
			nonEditableReason = "The target EditScope (editScope2) is disabled."
		)

		s["editScope2"]["enabled"].setValue( True )
		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"], True )

		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "/plane2", "planeSet", s["editScope2"] ),
			source = s["editScope1"]["setPlane2"]["name"],
			sourceType = SourceType.Upstream,
			editable = False,
			nonEditableReason = "editScope2 is locked."
		)

		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"], False )
		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"]["SetMembershipEdits"]["edits"], True )

		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "/plane2", "planeSet", s["editScope2"] ),
			source = s["editScope1"]["setPlane2"]["name"],
			sourceType = SourceType.Upstream,
			editable = False,
			nonEditableReason = "editScope2.SetMembershipEdits.edits is locked."
		)

		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"]["SetMembershipEdits"], True )
		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "/plane2", "planeSet", s["editScope2"] ),
			source = s["editScope1"]["setPlane2"]["name"],
			sourceType = SourceType.Upstream,
			editable = False,
			nonEditableReason = "editScope2.SetMembershipEdits is locked."
		)

	def testNonExistentLocation( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "planeSet" )
		self.assertIsNone( self.__inspect( plane["out"], "/nothingHere", "planeSet" ) )

	def testObjectSourceFallback( self ) :

		# ObjectSource nodes should always return their `sets` plug as a source. Otherwise,
		# creating a new set that doesn't yet exist would not be possible.

		plane = GafferScene.Plane()
		self.__assertExpectedResult(
			self.__inspect( plane["out"], "/plane", "planeSet" ),
			source = plane["sets"],
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Fallback,
			editable = True
		)

	def testDirtiedSignal( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "planeSet" )

		editScope1 = Gaffer.EditScope()
		editScope1.setup( plane["out"] )
		editScope1["in"].setInput( plane["out"] )

		editScope2 = Gaffer.EditScope()
		editScope2.setup( editScope1["out"] )
		editScope2["in"].setInput( editScope1["out"] )

		settings = Gaffer.Node()
		settings["editScope"] = Gaffer.Plug()

		inspector = GafferSceneUI.Private.SetMembershipInspector(
			editScope2["out"], settings["editScope"], "planeSet"
		)

		cs = GafferTest.CapturingSlot( inspector.dirtiedSignal() )

		# Changing the sets should dirty the inspector
		plane["sets"].setValue( "newPlaneSet" )
		self.assertEqual( len( cs ), 1 )

		# Changing the transform should not
		plane["transform"]["translate"]["x"].setValue( 10 )
		self.assertEqual( len( cs ), 1 )

		# Changing the EditScope should dirty the inspector
		settings["editScope"].setInput( editScope1["enabled"] )
		self.assertEqual( len( cs ), 2 )
		settings["editScope"].setInput( editScope2["enabled"] )
		self.assertEqual( len( cs ), 3 )
		settings["editScope"].setInput( None )
		self.assertEqual( len( cs ), 4 )

	def testReadOnlyMetadataSignalling( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "planeTest" )

		editScope = Gaffer.EditScope()
		editScope.setup( plane["out"] )
		editScope["in"].setInput( plane["out"] )

		settings = Gaffer.Node()
		settings["editScope"] = Gaffer.Plug()

		inspector = GafferSceneUI.Private.SetMembershipInspector(
			editScope["out"], settings["editScope"], "planeSet"
		)

		cs = GafferTest.CapturingSlot( inspector.dirtiedSignal() )

		Gaffer.MetadataAlgo.setReadOnly( editScope, True )
		Gaffer.MetadataAlgo.setReadOnly( editScope, False )
		self.assertEqual( len( cs ), 0 )  # Changes not relevant because we're not using the EditScope

		settings["editScope"].setInput( editScope["enabled"] )
		self.assertEqual( len( cs ), 1 )
		Gaffer.MetadataAlgo.setReadOnly( editScope, True )
		self.assertEqual( len( cs ), 2 )  # Change affects the result of `inspect().editable()`

	def testObjectSourceEditSetMembership( self ) :

		plane1 = GafferScene.Plane()

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )

		plane2 = GafferScene.Plane()

		parent = GafferScene.Parent()
		parent["parent"].setValue( "/" )
		parent["children"][0].setInput( group["out"] )
		parent["children"][1].setInput( plane2["out"] )

		editScopePlug = Gaffer.Plug()

		# Include in `planeSet`

		inspector = GafferSceneUI.Private.SetMembershipInspector( parent["out"], editScopePlug, "planeSet" )
		self.assertIsNotNone( inspector )

		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "group", "plane" ] )
			inspection = inspector.inspect()

		self.assertTrue( inspector.editSetMembership( inspection, "/group/plane", GafferScene.EditScopeAlgo.SetMembership.Added ) )

		planeSet = parent["out"].set( "planeSet" ).value

		for path, result in [
			( "/group/plane", IECore.PathMatcher.Result.ExactMatch ),
			( "/group", IECore.PathMatcher.Result.DescendantMatch ),
			( "/plane", IECore.PathMatcher.Result.NoMatch )
		] :
			self.assertEqual( planeSet.match( path ), result )

		# And remove it

		self.assertTrue( inspector.editSetMembership( inspection, "/group/plane", GafferScene.EditScopeAlgo.SetMembership.Removed ) )

		planeSet = parent["out"].set( "planeSet" ).value

		for path, result in [
			( "/group/plane", IECore.PathMatcher.Result.NoMatch ),
			( "/group", IECore.PathMatcher.Result.NoMatch ),
			( "/plane", IECore.PathMatcher.Result.NoMatch )
		] :
			self.assertEqual( planeSet.match( path ), result )

	def testEditScopeEditSetMembership( self ) :

		plane1 = GafferScene.Plane()

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )

		plane2 = GafferScene.Plane()

		parent = GafferScene.Parent()
		parent["parent"].setValue( "/" )
		parent["children"][0].setInput( group["out"] )
		parent["children"][1].setInput( plane2["out"] )

		editScope = Gaffer.EditScope()
		editScope.setup( parent["out"] )
		editScope["in"].setInput( parent["out"] )

		editScopePlug = Gaffer.Plug()
		editScopePlug.setInput( editScope["enabled"] )

		# Include in `planeSet`

		inspector = GafferSceneUI.Private.SetMembershipInspector( editScope["out"], editScopePlug, "planeSet" )

		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "group", "plane" ] )
			inspection = inspector.inspect()

		self.assertTrue( inspector.editSetMembership( inspection, "/group/plane", GafferScene.EditScopeAlgo.SetMembership.Added ) )

		planeSet = editScope["out"].set( "planeSet" ).value

		for path, result in [
			( "/group/plane", IECore.PathMatcher.Result.ExactMatch ),
			( "/group", IECore.PathMatcher.Result.DescendantMatch ),
			( "/plane", IECore.PathMatcher.Result.NoMatch )
		] :
			self.assertEqual( planeSet.match( path ), result )

		planeSet = parent["out"].set( "planeSet" ).value

		for path, result in [
			( "/group/plane", IECore.PathMatcher.Result.NoMatch ),
			( "/group", IECore.PathMatcher.Result.NoMatch ),
			( "/plane", IECore.PathMatcher.Result.NoMatch )
		] :
			self.assertEqual( planeSet.match( path ), result )

		# And remove it

		self.assertTrue( inspector.editSetMembership( inspection, "/group/plane", GafferScene.EditScopeAlgo.SetMembership.Removed ) )
		planeSet = parent["out"].set( "planeSet" ).value

		for path, result in [
			( "/group/plane", IECore.PathMatcher.Result.NoMatch ),
			( "/group", IECore.PathMatcher.Result.NoMatch ),
			( "/plane", IECore.PathMatcher.Result.NoMatch )
		] :
			self.assertEqual( planeSet.match( path ), result )

		planeSet = parent["out"].set( "planeSet" ).value

		for path, result in [
			( "/group/plane", IECore.PathMatcher.Result.NoMatch ),
			( "/group", IECore.PathMatcher.Result.NoMatch ),
			( "/plane", IECore.PathMatcher.Result.NoMatch )
		] :
			self.assertEqual( planeSet.match( path ), result )

	def testSetNodeEditSetMembership( self ) :

		# Modifying a `Set` node is beyond our powers

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane"] ) )

		setNode = GafferScene.Set()
		setNode["name"].setValue( "planeSet" )
		setNode["in"].setInput( plane["out"] )
		setNode["filter"].setInput( planeFilter["out"] )

		editScopePlug = Gaffer.Plug()

		inspector = GafferSceneUI.Private.SetMembershipInspector( setNode["out"], editScopePlug, "planeSet" )

		# Even if we know the source, we politely decline to make an edit

		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "plane" ] )
			inspection = inspector.inspect()

		self.assertEqual( inspection.source(), setNode["name"] )

		self.assertFalse( inspector.editSetMembership( inspection, "/plane", GafferScene.EditScopeAlgo.SetMembership.Removed ) )


if __name__ == "__main__" :
	unittest.main()