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

class VDBObjectTest( GafferVDBTest.VDBTestCase ) :

	def setUp( self ) :
		GafferVDBTest.VDBTestCase.setUp( self )

	def testCanLoadVDBFromFile( self ) :
		sourcePath = os.path.join( self.dataDir, "sphere.vdb" )
		vdbObject = GafferVDB.VDBObject( sourcePath )

		gridNames = vdbObject.gridNames()
		self.assertEqual(gridNames, ['ls_sphere'])

		metadata = vdbObject.metadata('ls_sphere')

		expected = IECore.CompoundObject(
			{
				'name': IECore.StringData( 'ls_sphere' ),
				'file_voxel_count': IECore.Int64Data( 270638 ),
				'file_bbox_min': IECore.V3iData( IECore.V3i( -62, -62, -62 ) ),
				'file_bbox_max': IECore.V3iData( IECore.V3i( 62, 62, 62 ) ),
				'is_local_space': IECore.BoolData( 0 ),
				'is_saved_as_half_float': IECore.BoolData( 1 ),
				'value_type': IECore.StringData( 'float' ),
				'class': IECore.StringData( 'level set' ),
				'file_mem_bytes': IECore.Int64Data( 2643448 ),
				'vector_type': IECore.StringData( 'invariant' )
			}
		)

		self.assertEqual( metadata, expected )

	def testCanEstimateMemoryUsage( self ):
		sourcePath = os.path.join( self.dataDir, "smoke.vdb" )
		vdbObject = GafferVDB.VDBObject( sourcePath )

		self.assertEqual(788108, vdbObject.memoryUsage())
		vdbObject.forceRead("density")
		self.assertEqual(7022108, vdbObject.memoryUsage())

	def testCanRemoveGrid( self ) :
		sourcePath = os.path.join( self.dataDir, "smoke.vdb" )

		vdbObject = GafferVDB.VDBObject( sourcePath )
		self.assertEqual(vdbObject.gridNames(), ['density'])
		h1 = vdbObject.hash()
		vdbObject.removeGrid('density')
		self.assertEqual(vdbObject.gridNames(), [])

		h2 = vdbObject.hash()
		self.assertNotEqual(h1, h2)

		emptyVDBObject = GafferVDB.VDBObject()
		h3 = emptyVDBObject.hash()
		self.assertEqual(h3, h2)

	def testHashIdenticalForFileLoadedTwice( self ):
		sourcePath = os.path.join( self.dataDir, "smoke.vdb" )

		vdbObject1 = GafferVDB.VDBObject( sourcePath )
		vdbObject2 = GafferVDB.VDBObject( sourcePath )

		self.assertEqual( vdbObject1.hash(), vdbObject2.hash() )

	def testCopiedVDBObjectHasIdenticalHash( self ) :
		sourcePath = os.path.join( self.dataDir, "smoke.vdb" )
		vdbObject = GafferVDB.VDBObject( sourcePath )
		vdbObjectCopy = vdbObject.copy()

		self.assertEqual( vdbObject.hash(), vdbObjectCopy.hash() )

	def testCanCreateMemoryBufferForRendering( self ):
		sourcePath = os.path.join( self.dataDir, "smoke.vdb" )
		vdbObject = GafferVDB.VDBObject( sourcePath )
		memBuffer = vdbObject.memoryBuffer()

		self.assertEqual(len(memBuffer), 2585819)

		self.assertEqual(memBuffer[0],	ord(' '))
		self.assertEqual(memBuffer[1],	ord('B'))
		self.assertEqual(memBuffer[2],	ord('D'))
		self.assertEqual(memBuffer[3],	ord('V'))


if __name__ == "__main__":
	unittest.main()

