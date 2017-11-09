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

import GafferTest

import GafferVDB
import IECore
import GafferVDBTest
import os

class SceneInterfaceTest( GafferVDBTest.VDBTestCase ) :
	def setUp( self ) :
		GafferVDBTest.VDBTestCase.setUp( self )
		self.sourcePath = os.path.join(self.dataDir, "utahteapot.vdb")
		self.sceneInterface = IECore.SceneInterface.create( self.sourcePath, IECore.IndexedIO.OpenMode.Read )

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
		transformData = self.sceneInterface.readTransform( 0.0 )
		transform = self.sceneInterface.readTransformAsMatrix( 0.0 )

		#todo check the transform

	def testCanReadBounds( self ) :
		bounds = self.sceneInterface.readBound( 0.0 )

		# print type( bounds )
		# print dir( bounds )
		#
		# print type( bounds.min )
		# print dir( bounds.min )

		# -50.055000305175781 -23.155000686645508 -30.854999542236328 48.055000305175781 23.155000686645508 30.854999542236328

		# print transformData
		# print transform
		# todo check the bounds
