//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Alex Fuller. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#include "GafferCycles/IECoreCyclesPreview/VDBAlgo.h"

#include "GafferCycles/IECoreCyclesPreview/ObjectAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "openvdb/openvdb.h"

// Cycles
#include "kernel/kernel_types.h"
#include "render/image.h"
#include "render/mesh.h"
#include "util/util_param.h"
#include "util/util_types.h"

using namespace std;
using namespace Imath;

using namespace IECore;
using namespace IECoreCycles;

namespace
{

ObjectAlgo::ConverterDescription<IECoreVDB::VDBObject> g_description( IECoreCycles::VDBAlgo::convert );

} // namespace


//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace IECoreCycles

{

namespace VDBAlgo

{

ccl::Object *convert( const IECoreVDB::VDBObject *vdbObject, const std::string & name, const ccl::Scene *scene )
{
	ccl::ImageMetaData metadata;
	ccl::TypeDesc ctype;// = ccl::TypeDesc::TypeUnknown;

	ccl::Object *cobject = new ccl::Object();
	cobject->name = ccl::ustring(name.c_str());
	cobject->mesh = new ccl::Mesh();

	cobject->mesh->volume_isovalue = 0.0f;
	cobject->mesh->has_volume = true;
	ccl::AttributeSet& attributes = cobject->mesh->attributes;

	ccl::Attribute *attrTfm = attributes.add( ccl::ATTR_STD_GENERATED_TRANSFORM );
	ccl::Transform *tfm = attrTfm->data_transform();
	Imath::Box3f bound = vdbObject->bound();
	ccl::float3 loc = SocketAlgo::setVector( bound.center() );
	ccl::float3 size = SocketAlgo::setVector( bound.size() );

	if ( size.x != 0.0f )
		size.x = 0.5f / size.x;
	if ( size.y != 0.0f )
		size.y = 0.5f / size.y;
	if ( size.z != 0.0f )
		size.z = 0.5f / size.z;

	loc = loc * size - ccl::make_float3( 0.5f, 0.5f, 0.5f );
	*tfm = ccl::transform_translate( -loc ) * ccl::transform_scale( size * 2.0f );

	ccl::Attribute *attr = nullptr;
	std::vector<std::string> gridNames = vdbObject->gridNames();

	for( const std::string& gridName : gridNames )
	{
		if( gridName == "density" )
		{
			attr = attributes.add( ccl::ATTR_STD_VOLUME_DENSITY, ccl::ustring(gridName.c_str()) );
		}
		else if( gridName == "color" )
		{
			attr = attributes.add( ccl::ATTR_STD_VOLUME_COLOR, ccl::ustring(gridName.c_str()) );
		}
		else if( gridName == "flame" )
		{
			attr = attributes.add( ccl::ATTR_STD_VOLUME_FLAME, ccl::ustring(gridName.c_str()) );
		}
		else if( gridName == "heat" )
		{
			attr = attributes.add( ccl::ATTR_STD_VOLUME_HEAT, ccl::ustring(gridName.c_str()) );
		}
		else if( gridName == "temperature" )
		{
			attr = attributes.add( ccl::ATTR_STD_VOLUME_TEMPERATURE, ccl::ustring(gridName.c_str()) );
		}
		else if( gridName == "velocity" )
		{
			attr = attributes.add( ccl::ATTR_STD_VOLUME_VELOCITY, ccl::ustring(gridName.c_str()) );
			cobject->mesh->use_volume_motion_blur = true;
		}
		else
		{
			openvdb::GridBase::ConstPtr grid = vdbObject->findGrid( gridName );
			if( grid->isType<openvdb::BoolGrid>() )
			{
				ctype = ccl::TypeDesc::TypeInt;
			}
			else if( grid->isType<openvdb::DoubleGrid>() )
			{
				ctype = ccl::TypeDesc::TypeFloat;
			}
			else if( grid->isType<openvdb::FloatGrid>() )
			{
				ctype = ccl::TypeDesc::TypeFloat;
			}
			else if( grid->isType<openvdb::Int32Grid>() )
			{
				ctype = ccl::TypeDesc::TypeInt;
			}
			else if( grid->isType<openvdb::Int64Grid>() )
			{
				ctype = ccl::TypeDesc::TypeInt;
			}
			else if( grid->isType<openvdb::Vec3DGrid>() )
			{
				ctype = ccl::TypeDesc::TypeVector;
			}
			else if( grid->isType<openvdb::Vec3IGrid>() )
			{
				ctype = ccl::TypeDesc::TypeVector;
			}
			else if( grid->isType<openvdb::Vec3SGrid>() )
			{
				ctype = ccl::TypeDesc::TypeVector;
			}
			attr = attributes.add( ccl::ustring(gridName.c_str()), ctype, ccl::ATTR_ELEMENT_VOXEL );
		}

		ccl::VoxelAttribute *voxelData = attr->data_voxel();

		voxelData->manager = scene->image_manager;
		voxelData->slot = scene->image_manager->add_image(
			vdbObject->fileName(),
			gridName,
			nullptr,
			false,
			0.0f, // frame
			ccl::INTERPOLATION_LINEAR,
			ccl::EXTENSION_CLIP,
			ccl::IMAGE_ALPHA_AUTO, //alpha_type
			ccl::u_colorspace_raw, //colorspace
			true,
			cobject->mesh->volume_isovalue,
			metadata
			);
	}

	return cobject;
}

} // namespace VDBAlgo

} // namespace IECoreCycles
