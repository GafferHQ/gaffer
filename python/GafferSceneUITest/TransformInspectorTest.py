##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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
import GafferUITest
import GafferScene
import GafferSceneUI

class TransformInspectorTest( GafferUITest.TestCase ) :

	def testName( self ) :

		sphere = GafferScene.Sphere()

		for space in GafferSceneUI.Private.TransformInspector.Space.values.values() :
			for component in GafferSceneUI.Private.TransformInspector.Component.values.values() :
				inspector = GafferSceneUI.Private.TransformInspector( sphere["out"], None, space, component )
				self.assertEqual( inspector.name(), f"{space} {component}" )

	def testValue( self ) :

		sphere = GafferScene.Sphere()
		sphere["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )
		sphere["transform"]["rotate"].setValue( imath.V3f( 45, 0, 0 ) )
		sphere["transform"]["scale"].setValue( imath.V3f( 2, 2, 2 ) )

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["transform"]["translate"].setValue( imath.V3f( 0, 1, 0 ) )
		group["transform"]["rotate"].setValue( imath.V3f( 0, 15, 0 ) )
		group["transform"]["scale"].setValue( imath.V3f( 2, 2, 2 ) )

		for space in GafferSceneUI.Private.TransformInspector.Space.values.values() :
			for component in GafferSceneUI.Private.TransformInspector.Component.values.values() :

				inspector = GafferSceneUI.Private.TransformInspector( group["out"], None, space, component )
				with Gaffer.Context() as context :
					context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/group/sphere" )
					value = inspector.inspect().value()

				if space == GafferSceneUI.Private.TransformInspector.Space.Local :
					matrix = group["out"].transform( "/group/sphere" )
				else :
					matrix = group["out"].fullTransform( "/group/sphere" )

				if component == GafferSceneUI.Private.TransformInspector.Component.Matrix :
					self.assertEqual( value, IECore.M44fData( matrix ) )
				else :
					s, h, r, t = imath.V3f(), imath.V3f(), imath.V3f(), imath.V3f()
					matrix.extractSHRT( s, h, r, t )
					match component :
						case GafferSceneUI.Private.TransformInspector.Component.Translate :
							self.assertEqual( value, IECore.V3fData( t ) )
						case GafferSceneUI.Private.TransformInspector.Component.Rotate :
							self.assertEqual( value, IECore.V3fData( IECore.radiansToDegrees( r ) ) )
						case GafferSceneUI.Private.TransformInspector.Component.Scale :
							self.assertEqual( value, IECore.V3fData( s ) )
						case GafferSceneUI.Private.TransformInspector.Component.Shear :
							self.assertEqual( value, IECore.V3fData( h ) )

	@staticmethod
	def __inspect( scene, path, space, component, editScope = None ) :

		editScopePlug = Gaffer.Plug()
		editScopePlug.setInput( editScope["enabled"] if editScope is not None else None )
		inspector = GafferSceneUI.Private.TransformInspector( scene, editScopePlug, space, component )
		with Gaffer.Context() as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( path )
			return inspector.inspect()

	def __assertExpectedSource( self, scene, path, expectedSource ) :

		for space in GafferSceneUI.Private.TransformInspector.Space.values.values() :
			for component in GafferSceneUI.Private.TransformInspector.Component.values.values() :

				inspection = self.__inspect( scene, path, space, component )
				source = inspection.source()
				if space == GafferSceneUI.Private.TransformInspector.Space.World :
					# World matrix is typically the result of concatenating a hierarchy
					# of matrices, so there can be no single source.
					self.assertIsNone( source )
					self.assertFalse( inspection.editable() )
					continue

				if expectedSource is None :
					self.assertIsNone( expectedSource )
				elif isinstance( expectedSource, Gaffer.TransformPlug ) :
					match component :
						case GafferSceneUI.Private.TransformInspector.Component.Matrix :
							self.assertTrue( source.isSame( expectedSource ) )
							self.assertTrue( inspection.editable() )
						case GafferSceneUI.Private.TransformInspector.Component.Translate :
							self.assertTrue( source.isSame( expectedSource["translate"] ) )
							self.assertTrue( inspection.editable() )
						case GafferSceneUI.Private.TransformInspector.Component.Rotate :
							self.assertTrue( source.isSame( expectedSource["rotate"] ) )
							self.assertTrue( inspection.editable() )
						case GafferSceneUI.Private.TransformInspector.Component.Scale :
							self.assertTrue( source.isSame( expectedSource["scale"] ) )
							self.assertTrue( inspection.editable() )
						case _ :
							self.assertIsNone( source )
							self.assertFalse( inspection.editable() )
				else :
					self.assertTrue( source.isSame( expectedSource ) )
					self.assertTrue( source.isSame( source.node()["out"]["transform"] ) )
					self.assertFalse( inspection.editable() )

	def testObjectSourceSource( self ) :

		sphere = GafferScene.Sphere()
		self.__assertExpectedSource( sphere["out"], "/", None )
		self.__assertExpectedSource( sphere["out"], "/sphere", sphere["transform"] )

	def testGroupSource( self ) :

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )

		self.__assertExpectedSource( group["out"], "/", None )
		self.__assertExpectedSource( group["out"], "/group", group["transform"] )
		self.__assertExpectedSource( group["out"], "/group/sphere", sphere["transform"] )

		group["enabled"].setValue( False )
		self.__assertExpectedSource( group["out"], "/", None )
		self.__assertExpectedSource( group["out"], "/sphere", sphere["transform"] )

	def testTransformSource( self ) :

		sphere = GafferScene.Sphere()

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "sphere" ] ) )

		transform = GafferScene.Transform()
		transform["in"].setInput( sphere["out"] )
		transform["filter"].setInput( sphereFilter["out"] )

		for space in transform.Space.values.values() :
			transform["space"].setValue( space )
			self.__assertExpectedSource(
				transform["out"], "/sphere",
				transform["transform"] if space == transform.Space.ResetLocal else transform["out"]["transform"]
			)

		transform["space"].setValue( transform.Space.ResetLocal )

		sphereFilter["enabled"].setValue( False )
		self.__assertExpectedSource( transform["out"], "/sphere", sphere["transform"] )

		sphereFilter["enabled"].setValue( True )
		transform["enabled"].setValue( False )
		self.__assertExpectedSource( transform["out"], "/sphere", sphere["transform"] )

	def testGridSource( self ) :

		grid = GafferScene.Grid()

		self.__assertExpectedSource( grid["out"], "/", None )
		self.__assertExpectedSource( grid["out"], "/grid", grid["transform"] )
		self.__assertExpectedSource( grid["out"], "/grid/centerLines", None )
		self.__assertExpectedSource( grid["out"], "/grid/gridLines", None )
		self.__assertExpectedSource( grid["out"], "/grid/borderLines", None )

	def testEditScopes( self ) :

		plane = GafferScene.Plane()
		plane["transform"]["scale"].setValue( imath.V3f( 2 ) )

		editScope = Gaffer.EditScope()
		editScope.setup( plane["out"] )
		editScope["in"].setInput( plane["out"] )

		# We refuse to make a new edit because that would edit components
		# other than the one we're inspecting.

		inspection = self.__inspect(
			editScope["out"], "/plane",
			GafferSceneUI.Private.TransformInspector.Space.Local,
			GafferSceneUI.Private.TransformInspector.Component.Translate,
			editScope
		)
		self.assertEqual( inspection.source(), plane["transform"]["translate"] )
		self.assertEqual( inspection.sourceType(), inspection.SourceType.Upstream )
		self.assertFalse( inspection.editable() )
		self.assertEqual( inspection.nonEditableReason(), "Edit creation not supported yet. Use the transform tools in the Viewer instead." )

		# But if an edit already exists, we'll use it.

		edit = GafferScene.EditScopeAlgo.acquireTransformEdit( editScope, "/plane" )

		inspection = self.__inspect(
			editScope["out"], "/plane",
			GafferSceneUI.Private.TransformInspector.Space.Local,
			GafferSceneUI.Private.TransformInspector.Component.Translate,
			editScope
		)
		self.assertEqual( inspection.source(), edit.translate )
		self.assertEqual( inspection.sourceType(), inspection.SourceType.EditScope )
		self.assertTrue( inspection.editable() )

if __name__ == "__main__" :
	unittest.main()
