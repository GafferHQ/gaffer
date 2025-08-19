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

import GafferSceneUI
from . import _GafferVDBUI

import IECoreVDB

import functools

def __gridMinValue( objectPlug, gridName ) :

	return _GafferVDBUI._gridMinMaxValue( objectPlug, gridName )["min"]

def __gridMaxValue( objectPlug, gridName ) :

	return _GafferVDBUI._gridMinMaxValue( objectPlug, gridName )["max"]

def __vdbInspectors( scene, editScope ) :

	result = []

	vdb = scene["object"].getValue()
	if not isinstance( vdb, IECoreVDB.VDBObject ) :
		return result

	for gridName in sorted( vdb.gridNames() ) :

		# All our inspectors use C++ functions provided by `GafferVDBUIModule.cpp`. We must
		# not even call `vdb.findGrid()` from Python, because we would get the non-const
		# version which would mark the grids as modified, causing `vdb.unmodifiedFromFile()`
		# to return `False`. Which in turn would make rendering less efficient than necessary.
		#
		# We can't register the inspectors from C++, because no C++ API for doing that has
		# been exposed yet.

		result.extend( [
			GafferSceneUI.SceneInspector.Inspection(
				f"Grids/{gridName}/Value Type",
				GafferSceneUI.Private.BasicInspector( scene["object"], editScope, functools.partial( _GafferVDBUI._gridValueType, gridName = gridName ) )
			),
			GafferSceneUI.SceneInspector.Inspection(
				f"Grids/{gridName}/Min Value",
				GafferSceneUI.Private.BasicInspector( scene["object"], editScope, functools.partial( __gridMinValue, gridName = gridName ) )
			),
			GafferSceneUI.SceneInspector.Inspection(
				f"Grids/{gridName}/Max Value",
				GafferSceneUI.Private.BasicInspector( scene["object"], editScope, functools.partial( __gridMaxValue, gridName = gridName ) )
			),
			GafferSceneUI.SceneInspector.Inspection(
				f"Grids/{gridName}/Active Voxels",
				GafferSceneUI.Private.BasicInspector( scene["object"], editScope, functools.partial( _GafferVDBUI._gridActiveVoxels, gridName = gridName ) )
			),
			GafferSceneUI.SceneInspector.Inspection(
				f"Grids/{gridName}/Voxel Bound",
				GafferSceneUI.Private.BasicInspector( scene["object"], editScope, functools.partial( _GafferVDBUI._gridVoxelBound, gridName = gridName ) )
			),
			GafferSceneUI.SceneInspector.Inspection(
				f"Grids/{gridName}/Memory Usage",
				GafferSceneUI.Private.BasicInspector( scene["object"], editScope, functools.partial( _GafferVDBUI._gridMemoryUsage, gridName = gridName ) )
			),
		] )

		for key in sorted( _GafferVDBUI._gridMetadataNames( scene["object"], gridName ) ) :
			result.append(
				GafferSceneUI.SceneInspector.Inspection(
					f"Grids/{gridName}/Metadata/{key}",
					GafferSceneUI.Private.BasicInspector( scene["object"], editScope, functools.partial( _GafferVDBUI._gridMetadata, gridName = gridName, metadataName = key ) )
				)
			)

	return result

GafferSceneUI.SceneInspector.registerInspectors( "Location/Object", __vdbInspectors )
