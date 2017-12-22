##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
#      * Neither the name of Image Engine Design Inc nor the names of
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

import os
import imath

import IECore
import IECoreScene

import GafferTest
import GafferVDB
import GafferVDBTest

class SceneInterfaceTest( GafferVDBTest.VDBTestCase ) :
	def setUp( self ) :
		GafferVDBTest.VDBTestCase.setUp( self )
		self.sourcePath = os.path.join(self.dataDir, "smoke.vdb")
		self.sceneInterface = IECoreScene.SceneInterface.create( self.sourcePath, IECore.IndexedIO.OpenMode.Read )

	def testCanLoading( self ) :
		self.assertEqual( self.sceneInterface.hasObject(), True )
		self.assertEqual( self.sceneInterface.fileName(), self.sourcePath )
		self.assertEqual( self.sceneInterface.pathAsString(), "/" )
		self.assertEqual( self.sceneInterface.name(), "" )
		self.assertEqual( self.sceneInterface.hasBound(), True )

	def testSingleVDBChildName( self ) :
		self.assertEqual( self.sceneInterface.childNames(), ["vdb"] )

	def testCanGetChildVDBLocation( self ):
		self.assertEqual( self.sceneInterface.hasChild("vdb"), True)
		childSceneInterface = self.sceneInterface.child("vdb")
		self.assertEqual( childSceneInterface.childNames(), [])

	def testIdentityTransform( self ) :
		matrixArray = [
			1, 0, 0, 0,
			0, 1, 0, 0,
			0, 0, 1, 0,
			0, 0, 0, 1
		]

		m44 = imath.M44d( *matrixArray )
		m44Data = IECore.M44dData( m44 )

		transformData = self.sceneInterface.readTransform( 0.0 )
		self.assertEqual(transformData, m44Data)

		transform = self.sceneInterface.readTransformAsMatrix( 0.0 )
		self.assertEqual(transform, m44)

	def testCanReadBounds( self ) :
		bound = self.sceneInterface.readBound( 0.0 )

		expectedBound = imath.Box3d(
			imath.V3d( [-33.809524536132812, -12.380952835083008, -26.190475463867188] ),
			imath.V3d( [19.047618865966797, 93.333335876464844, 27.142856597900391] )
		)

		self.assertEqual(bound, expectedBound)

	def testCanReadVBObject( self ) :
		vdb = self.sceneInterface.child( "vdb" )
		vdbObject = vdb.readObject( 0.0 )

		self.assertTrue( isinstance( vdbObject, GafferVDB.VDBObject ) )
		self.assertEqual(vdbObject.gridNames(), ['density'])


	def testHashesDontChangeOverTime( self ) :
		self.assertEqual(
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.TransformHash, 0.0 ),
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.TransformHash, 1.0 )
		)

		self.assertEqual(
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.AttributesHash, 0.0 ),
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.AttributesHash, 1.0 )
		)

		self.assertEqual(
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.BoundHash, 0.0 ),
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.BoundHash, 1.0 )
		)

		self.assertEqual(
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.ObjectHash, 0.0 ),
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.ObjectHash, 1.0 )
		)

		self.assertEqual(
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.ChildNamesHash, 0.0 ),
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.ChildNamesHash, 1.0 )
		)

		self.assertEqual(
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.HierarchyHash, 0.0 ),
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.HierarchyHash, 1.0 )
		)

	def testHashesForRootAndVDBLocation( self ):
		childSceneInterface = self.sceneInterface.child("vdb")

		self.assertNotEqual(
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.ChildNamesHash, 0.0 ),
			childSceneInterface.hash( IECoreScene.SceneInterface.HashType.ChildNamesHash, 0.0 )
		)

		self.assertNotEqual(
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.ObjectHash, 0.0 ),
			childSceneInterface.hash( IECoreScene.SceneInterface.HashType.ObjectHash, 0.0 )
		)

		self.assertEqual(
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.BoundHash, 0.0 ),
			childSceneInterface.hash( IECoreScene.SceneInterface.HashType.BoundHash, 0.0 )
		)

	def testHashesDifferentFiles( self ):
		sourcePath = os.path.join(self.dataDir, "sphere.vdb")
		sphereRoot = IECoreScene.SceneInterface.create( sourcePath, IECore.IndexedIO.OpenMode.Read )

		self.assertEqual(
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.ChildNamesHash, 0.0 ),
			sphereRoot.hash( IECoreScene.SceneInterface.HashType.ChildNamesHash, 0.0 )
		)

		self.assertEqual(
			self.sceneInterface.child("vdb").hash( IECoreScene.SceneInterface.HashType.ChildNamesHash, 0.0 ),
			sphereRoot.child("vdb").hash( IECoreScene.SceneInterface.HashType.ChildNamesHash, 0.0 )
		)

		self.assertEqual(
			self.sceneInterface.hash( IECoreScene.SceneInterface.HashType.ObjectHash, 0.0 ),
			sphereRoot.hash( IECoreScene.SceneInterface.HashType.ObjectHash, 0.0 )
		)

		self.assertNotEqual(
			self.sceneInterface.child("vdb").hash( IECoreScene.SceneInterface.HashType.ObjectHash, 0.0 ),
			sphereRoot.child("vdb").hash( IECoreScene.SceneInterface.HashType.ObjectHash, 0.0 )
		)

	def testMissingChildBehaviour( self ) :
		with self.assertRaises(RuntimeError):
			self.sceneInterface.child("noChildHere", IECoreScene.SceneInterface.MissingBehaviour.ThrowIfMissing )

		c = self.sceneInterface.child("noChildHere", IECoreScene.SceneInterface.MissingBehaviour.NullIfMissing )
		self.assertEqual(c, None)

		with self.assertRaises(RuntimeError):
			c = self.sceneInterface.child("noChildHere", IECoreScene.SceneInterface.MissingBehaviour.CreateIfMissing )

	def testHasChild( self ) :
		self.assertTrue( self.sceneInterface.hasChild("vdb") )
		self.assertFalse( self.sceneInterface.hasChild("noChild") )

		vdb = self.sceneInterface.child( "vdb" )
		self.assertFalse( vdb.hasChild("noChild") )


if __name__ == "__main__":
	unittest.main()

