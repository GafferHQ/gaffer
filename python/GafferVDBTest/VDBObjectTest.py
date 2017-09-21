import GafferTest

import GafferVDB
import IECore
import GafferVDBTest
import os

class VDBObjectTest( GafferVDBTest.VDBTestCase ) :

	def setUp( self ) :
		GafferVDBTest.VDBTestCase.setUp( self )

	def testCanLoadVDBFromFile( self ) :
		sourcePath = os.path.join(self.dataDir, "sphere.vdb")
		vdbObject = GafferVDB.VDBObject(sourcePath)

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
				'file_mem_bytes': IECore.Int64Data( 5528004 ),
				'vector_type': IECore.StringData( 'invariant' )
			}
		)

		self.assertEqual(metadata, expected)


if __name__ == "__main__":
	unittest.main()

