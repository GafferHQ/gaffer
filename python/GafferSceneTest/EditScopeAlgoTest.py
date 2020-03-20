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

import math
import unittest

import imath

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class EditScopeAlgoTest( GafferSceneTest.SceneTestCase ) :

	def testPruning( self ) :

		plane = GafferScene.Plane()
		cube = GafferScene.Cube()
		group = GafferScene.Group()

		group["in"][0].setInput( plane["out"] )
		group["in"][1].setInput( cube["out"] )

		scope = Gaffer.EditScope()
		scope.setup( group["out"] )
		scope["in"].setInput( group["out"] )

		self.assertEqual( len( list( GafferScene.SceneProcessor.Range( scope ) ) ), 0 )
		self.assertFalse( GafferScene.EditScopeAlgo.getPruned( scope, "/group/plane" ) )
		self.assertFalse( GafferScene.EditScopeAlgo.getPruned( scope, "/group/cube" ) )
		self.assertEqual( len( list( GafferScene.SceneProcessor.Range( scope ) ) ), 0 )
		self.assertTrue( GafferScene.SceneAlgo.exists( scope["out"], "/group/plane" ) )
		self.assertTrue( GafferScene.SceneAlgo.exists( scope["out"], "/group/cube" ) )

		GafferScene.EditScopeAlgo.setPruned( scope, "/group/plane", True )
		self.assertTrue( GafferScene.EditScopeAlgo.getPruned( scope, "/group/plane" ) )
		self.assertFalse( GafferScene.EditScopeAlgo.getPruned( scope, "/group/cube" ) )
		self.assertEqual( len( list( GafferScene.SceneProcessor.Range( scope ) ) ), 1 )
		self.assertEqual( scope["PruningEdits"]["paths"].getValue(), IECore.StringVectorData( [ "/group/plane" ] ) )
		self.assertFalse( GafferScene.SceneAlgo.exists( scope["out"], "/group/plane" ) )
		self.assertTrue( GafferScene.SceneAlgo.exists( scope["out"], "/group/cube" ) )

		GafferScene.EditScopeAlgo.setPruned( scope, IECore.PathMatcher( [ "/group/plane", "/group/cube" ] ), True )
		self.assertTrue( GafferScene.EditScopeAlgo.getPruned( scope, "/group/plane" ) )
		self.assertTrue( GafferScene.EditScopeAlgo.getPruned( scope, "/group/cube" ) )
		self.assertEqual( len( list( GafferScene.SceneProcessor.Range( scope ) ) ), 1 )
		self.assertEqual( scope["PruningEdits"]["paths"].getValue(), IECore.StringVectorData( [ "/group/cube", "/group/plane" ] ) )
		self.assertFalse( GafferScene.SceneAlgo.exists( scope["out"], "/group/plane" ) )
		self.assertFalse( GafferScene.SceneAlgo.exists( scope["out"], "/group/cube" ) )

		GafferScene.EditScopeAlgo.setPruned( scope, IECore.PathMatcher( [ "/group/plane", "/group/cube" ] ), False )
		self.assertFalse( GafferScene.EditScopeAlgo.getPruned( scope, "/group/plane" ) )
		self.assertFalse( GafferScene.EditScopeAlgo.getPruned( scope, "/group/cube" ) )
		self.assertEqual( len( list( GafferScene.SceneProcessor.Range( scope ) ) ), 1 )
		self.assertEqual( scope["PruningEdits"]["paths"].getValue(), IECore.StringVectorData() )
		self.assertTrue( GafferScene.SceneAlgo.exists( scope["out"], "/group/plane" ) )
		self.assertTrue( GafferScene.SceneAlgo.exists( scope["out"], "/group/cube" ) )

	def testPruningSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["editScope"] = Gaffer.EditScope()
		s["editScope"].setup( s["plane"]["out"] )

		GafferScene.EditScopeAlgo.setPruned( s["editScope"], "/plane", True )
		self.assertTrue( GafferScene.EditScopeAlgo.getPruned( s["editScope"], "/plane" ), True )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( GafferScene.EditScopeAlgo.getPruned( s2["editScope"], "/plane" ), True )

	def testTransform( self ) :

		plane = GafferScene.Plane()
		plane["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		editScope = Gaffer.EditScope()
		editScope.setup( plane["out"] )
		editScope["in"].setInput( plane["out"] )

		self.assertFalse( GafferScene.EditScopeAlgo.hasTransformEdit( editScope, "/plane" ) )
		self.assertIsNone( GafferScene.EditScopeAlgo.acquireTransformEdit( editScope, "/plane", createIfNecessary = False ) )
		self.assertEqual( len( list( GafferScene.SceneProcessor.Range( editScope ) ) ), 0 )
		self.assertEqual( editScope["out"].transform( "/plane" ), plane["transform"].matrix() )

		edit = GafferScene.EditScopeAlgo.acquireTransformEdit( editScope, "/plane" )
		self.assertIsInstance( edit, GafferScene.EditScopeAlgo.TransformEdit )
		self.assertTrue( GafferScene.EditScopeAlgo.hasTransformEdit( editScope, "/plane" ) )
		self.assertIsNotNone( GafferScene.EditScopeAlgo.acquireTransformEdit( editScope, "/plane", createIfNecessary = False ) )
		self.assertEqual( editScope["out"].transform( "/plane" ), imath.M44f() )
		edit.translate.setValue( imath.V3f( 2, 3, 4 ) )
		self.assertEqual( editScope["out"].transform( "/plane" ), imath.M44f().translate( imath.V3f( 2, 3, 4 ) ) )

		GafferScene.EditScopeAlgo.removeTransformEdit( editScope, "/plane" )
		self.assertFalse( GafferScene.EditScopeAlgo.hasTransformEdit( editScope, "/plane" ) )
		self.assertIsNone( GafferScene.EditScopeAlgo.acquireTransformEdit( editScope, "/plane", createIfNecessary = False ) )
		self.assertEqual( editScope["out"].transform( "/plane" ), plane["transform"].matrix() )

	def testTransformProcessorNotCreatedPrematurely( self ) :

		plane = GafferScene.Plane()
		plane["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		editScope = Gaffer.EditScope()
		editScope.setup( plane["out"] )
		editScope["in"].setInput( plane["out"] )

		self.assertFalse( "TransformEdits" in editScope )
		GafferScene.EditScopeAlgo.acquireTransformEdit( editScope, "/plane", createIfNecessary = False )
		self.assertFalse( "TransformEdits" in editScope )
		GafferScene.EditScopeAlgo.acquireTransformEdit( editScope, "/plane" )
		self.assertTrue( "TransformEdits" in editScope )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testTransformPerformance( self ) :

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 100, 10 ) )

		cube = GafferScene.Cube()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( ["/plane"] ) )

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["prototypes"].setInput( cube["out"] )
		instancer["filter"].setInput( planeFilter["out"] )

		editScope = Gaffer.EditScope()
		editScope.setup( instancer["out"] )
		editScope["in"].setInput( instancer["out"] )

		for name in instancer["out"].childNames( "/plane/instances/cube" ) :
			GafferScene.EditScopeAlgo.acquireTransformEdit(
				editScope, "/plane/instances/cube/{}".format( name )
			)

	def testTransformEditMethods( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		planeEdit = GafferScene.EditScopeAlgo.TransformEdit(
			plane["transform"]["translate"],
			plane["transform"]["rotate"],
			plane["transform"]["scale"],
			plane["transform"]["pivot"]
		)
		sphereEdit = GafferScene.EditScopeAlgo.TransformEdit(
			sphere["transform"]["translate"],
			sphere["transform"]["rotate"],
			sphere["transform"]["scale"],
			sphere["transform"]["pivot"]
		)

		self.assertEqual( planeEdit, planeEdit )
		self.assertFalse( planeEdit != planeEdit )
		self.assertEqual( sphereEdit, sphereEdit )
		self.assertFalse( sphereEdit != sphereEdit )
		self.assertNotEqual( sphereEdit, planeEdit )
		self.assertTrue( sphereEdit != planeEdit )

if __name__ == "__main__":
	unittest.main()
