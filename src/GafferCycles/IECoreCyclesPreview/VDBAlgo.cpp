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

IECORE_PUSH_DEFAULT_VISIBILITY
#include "openvdb/openvdb.h"
IECORE_POP_DEFAULT_VISIBILITY

// Cycles
IECORE_PUSH_DEFAULT_VISIBILITY
#include "kernel/types.h"
#include "scene/image.h"
#include "scene/image_vdb.h"
#include "scene/volume.h"
#include "util/param.h"
#include "util/types.h"
IECORE_POP_DEFAULT_VISIBILITY

using namespace std;
using namespace Imath;

using namespace IECore;
using namespace IECoreCycles;

namespace
{

class IEVolumeLoader : public ccl::VDBImageLoader
{
	public:
		IEVolumeLoader( const IECoreVDB::VDBObject *ieVolume, const string &gridName )
		: VDBImageLoader( gridName ),
		  m_ieVolume( ieVolume )
		{
			grid = m_ieVolume->findGrid( gridName );
			/// \todo For Cycles 3.3.x there is a precision value we can set for memory savings
		}

		const IECoreVDB::VDBObject *m_ieVolume;
};

ObjectAlgo::ConverterDescription<IECoreVDB::VDBObject> g_description( IECoreCycles::VDBAlgo::convert );

} // namespace


//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace IECoreCycles

{

namespace VDBAlgo

{

ccl::Object *convert( const IECoreVDB::VDBObject *vdbObject, const std::string &nodeName, ccl::Scene *scene )//, const float frame )
{
	ccl::TypeDesc ctype;// = ccl::TypeDesc::TypeUnknown;

	ccl::Object *cobject = new ccl::Object();
	cobject->name = ccl::ustring( nodeName.c_str() );
	ccl::Volume *volume = new ccl::Volume();

	volume->set_object_space( true );

	std::vector<std::string> gridNames = vdbObject->gridNames();

	for( const std::string& gridName : gridNames )
	{
		ccl::AttributeStandard std = ccl::ATTR_STD_NONE;

		if( ccl::ustring( gridName.c_str() ) == ccl::Attribute::standard_name( ccl::ATTR_STD_VOLUME_DENSITY ) )
		{
			std = ccl::ATTR_STD_VOLUME_DENSITY;
		}
		else if( ccl::ustring( gridName.c_str() ) == ccl::Attribute::standard_name( ccl::ATTR_STD_VOLUME_COLOR ) )
		{
			std = ccl::ATTR_STD_VOLUME_COLOR;
		}
		else if( ccl::ustring( gridName.c_str() ) == ccl::Attribute::standard_name( ccl::ATTR_STD_VOLUME_FLAME ) )
		{
			std = ccl::ATTR_STD_VOLUME_FLAME;
		}
		else if( ccl::ustring( gridName.c_str() ) == ccl::Attribute::standard_name( ccl::ATTR_STD_VOLUME_HEAT ) )
		{
			std = ccl::ATTR_STD_VOLUME_HEAT;
		}
		else if( ccl::ustring( gridName.c_str() ) == ccl::Attribute::standard_name( ccl::ATTR_STD_VOLUME_TEMPERATURE ) )
		{
			std = ccl::ATTR_STD_VOLUME_TEMPERATURE;
		}
		else if( ccl::ustring( gridName.c_str() ) == ccl::Attribute::standard_name( ccl::ATTR_STD_VOLUME_VELOCITY ) )
		{
			std = ccl::ATTR_STD_VOLUME_VELOCITY;
		}
		else if( ccl::ustring( gridName.c_str() ) == ccl::Attribute::standard_name( ccl::ATTR_STD_VOLUME_VELOCITY_X ) )
		{
			std = ccl::ATTR_STD_VOLUME_VELOCITY_X;
		}
		else if( ccl::ustring( gridName.c_str() ) == ccl::Attribute::standard_name( ccl::ATTR_STD_VOLUME_VELOCITY_Y ) )
		{
			std = ccl::ATTR_STD_VOLUME_VELOCITY_Y;
		}
		else if( ccl::ustring( gridName.c_str() ) == ccl::Attribute::standard_name( ccl::ATTR_STD_VOLUME_VELOCITY_Z ) )
		{
			std = ccl::ATTR_STD_VOLUME_VELOCITY_Z;
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
		}

		ccl::Attribute *attr = ( std != ccl::ATTR_STD_NONE ) ?
							volume->attributes.add( std ) :
							volume->attributes.add( ccl::ustring( gridName.c_str() ), ctype, ccl::ATTR_ELEMENT_VOXEL );

		ccl::ImageLoader *loader = new IEVolumeLoader( vdbObject, gridName );
		ccl::ImageParams params;
		params.frame = 0.0f;

		attr->data_voxel() = scene->image_manager->add_image( loader, params, false );
	}

	cobject->set_geometry( volume );

	return cobject;
}

ccl::Object *convert( const std::vector<const IECoreVDB::VDBObject *> &samples, const std::vector<float> &times, const int frameIdx, const std::string &nodeName, ccl::Scene *scene )
{
	return convert( samples.front(), nodeName, scene );
}

} // namespace VDBAlgo

} // namespace IECoreCycles
