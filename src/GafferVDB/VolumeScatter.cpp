//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Don Boogert. All rights reserved.
//  Copyright (c) 2023, Image Engine Design. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of Don Boogert nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
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


#include "GafferVDB/VolumeScatter.h"

#include "GafferVDB/Interrupter.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/PointsPrimitive.h"
#include "IECoreVDB/VDBObject.h"

#include "Imath/ImathRandom.h"

#include "openvdb/openvdb.h"
#include "openvdb/tools/PointScatter.h"

#include "pcg/pcg_random.hpp"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreVDB;
using namespace Gaffer;
using namespace GafferVDB;

IE_CORE_DEFINERUNTIMETYPED( VolumeScatter );

size_t VolumeScatter::g_firstPlugIndex = 0;

VolumeScatter::VolumeScatter( const std::string &name )
	: BranchCreator( name )
{
	storeIndexOfNextChild(g_firstPlugIndex);

	addChild( new StringPlug( "name", Plug::In, "scatter" ) );
	addChild( new StringPlug( "grid", Plug::In, "density" ) );
	addChild( new FloatPlug( "density", Plug::In, 1.0f, 0.0f ) );
	addChild( new StringPlug( "pointType", Plug::In, "gl:point" ) );
}

VolumeScatter::~VolumeScatter()
{
}

Gaffer::StringPlug *VolumeScatter::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 0 );
}

const Gaffer::StringPlug *VolumeScatter::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 0 );
}

Gaffer::StringPlug *VolumeScatter::gridPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *VolumeScatter::gridPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::FloatPlug *VolumeScatter::densityPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::FloatPlug *VolumeScatter::densityPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *VolumeScatter::pointTypePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *VolumeScatter::pointTypePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

bool VolumeScatter::affectsBranchBound( const Gaffer::Plug *input ) const
{
	return input == inPlug()->boundPlug();
}

void VolumeScatter::hashBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hashBranchBound( sourcePath, branchPath, context, h );
	h.append( inPlug()->boundHash( sourcePath ) );
}

Imath::Box3f VolumeScatter::computeBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	// We could do a potentially more accurate bound by getting the bound for just the grid we're using from
	// the vdb, but using the full bound from the vdb loader should be conservative, and it's rare that the grid
	// we're using wouldn't fill the whole vdb ( this also matches how other nodes like LevelSetToMesh
	// are currently working )
	Box3f b = inPlug()->bound( sourcePath );

	if( !b.isEmpty() )
	{
		// The PointsPrimitive we make has a default point width of 1,
		// so we must expand our bounding box to take that into account.
		b.min -= V3f( 0.5 );
		b.max += V3f( 0.5 );
	}
	return b;
}

bool VolumeScatter::affectsBranchTransform( const Gaffer::Plug *input ) const
{
	return false;
}

void VolumeScatter::hashBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hashBranchTransform( sourcePath, branchPath, context, h );
}

Imath::M44f VolumeScatter::computeBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	return M44f();
}

bool VolumeScatter::affectsBranchAttributes( const Gaffer::Plug *input ) const
{
	return false;
}

void VolumeScatter::hashBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hashBranchAttributes( sourcePath, branchPath, context, h );
}

IECore::ConstCompoundObjectPtr VolumeScatter::computeBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	return outPlug()->attributesPlug()->defaultValue();
}

bool VolumeScatter::affectsBranchObject( const Gaffer::Plug *input ) const
{
	return
		input == inPlug()->objectPlug() ||
		input == gridPlug() ||
		input == densityPlug() ||
		input == pointTypePlug()
	;
}

void VolumeScatter::hashBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 1 )
	{
		BranchCreator::hashBranchObject( sourcePath, branchPath, context, h );

		h.append( inPlug()->objectHash( sourcePath ) );
		gridPlug()->hash( h );
		densityPlug()->hash( h );
		pointTypePlug()->hash( h );
		return;
	}

	h = outPlug()->objectPlug()->defaultValue()->Object::hash();
}

namespace {

class PointsWriter {
public:

	PointsWriter()
		: pointsData(new IECore::V3fVectorData()), points( pointsData->writable() )
	{
	}

	void add(const openvdb::Vec3R &pos)
	{
		points.emplace_back(pos.x(), pos.y(), pos.z());
	}

	IECore::V3fVectorDataPtr pointsData;
	std::vector<Imath::V3f> & points;
};

} // namespace

IECore::ConstObjectPtr VolumeScatter::computeBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() != 1 )
	{
		return outPlug()->objectPlug()->defaultValue();
	}

	ConstVDBObjectPtr vdbObject = runTimeCast<const VDBObject>( inPlug()->object( sourcePath ) );
	if( !vdbObject )
	{
		return outPlug()->objectPlug()->defaultValue();
	}

	std::string gridName = gridPlug()->getValue();

	openvdb::GridBase::ConstPtr grid = vdbObject->findGrid( gridName );

	if ( !grid )
	{
		// The classic question: should we raising an exception here?
		// It would be much easier to debug failures if we raised errors, but a user might
		// also want to run this on a large number of objects with poor QC, and not want
		// to fail the whole render because one of them is bad. Maybe we should have a
		// toggle for whether to raise exceptions? Currently matching LevelSetToMesh
		// and just ignoring missing grids.
		return outPlug()->objectPlug()->defaultValue();
	}

	if( grid->getGridClass() == openvdb::GRID_LEVEL_SET )
	{
		throw IECore::Exception( "VolumeScatter does not yet support level sets" );
	}

	openvdb::FloatGrid::ConstPtr floatGrid = openvdb::GridBase::constGrid<openvdb::FloatGrid>( grid );
	if( !floatGrid )
	{
		throw IECore::Exception( "VolumeScatter requires a FloatGrid, does not support : " + grid->type() );

	}

	PointsWriter pointWriter;
	pcg32 generator( 42 );
	const float spread = 1.0f;
	Interrupter interrupter( context->canceller() );

	// This NonUniformScatter built into openvdb is kind of limited. The next step for this node would
	// probably be to make a local copy, so we could add features like:
	// * a min/max value to remap to 0/1 for when you want to select some of the volume without driving
	//   the density of points by the volume density.
	// * the option to normalize by the volume of the vdb, to produce an approximately constant number of points.
	// * support for level sets ( for every region neighbouring active voxels, if all adjacent voxels are under
	//   threshold, we just generate points as usual, but if some adjacent voxels are over threshold, we
	//   need to evaluate the interpolated value at each generated point to check if it is under threshold ).
	using NonUniformScatter = openvdb::tools::NonUniformPointScatter<
		PointsWriter, pcg32, Interrupter
	>;
	NonUniformScatter densityPointScatter(
		pointWriter, densityPlug()->getValue(), generator, spread, &interrupter
	);

	densityPointScatter( *floatGrid );

	if ( interrupter.wasInterrupted() )
	{
		throw IECore::Cancelled();
	}

	IECoreScene::PointsPrimitivePtr result = new IECoreScene::PointsPrimitive( pointWriter.pointsData );
	result->variables["type"] = IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new StringData( pointTypePlug()->getValue() ) );
	return result;
}

bool VolumeScatter::affectsBranchChildNames( const Gaffer::Plug *input ) const
{
	return input == namePlug();
}

void VolumeScatter::hashBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 0 )
	{
		BranchCreator::hashBranchChildNames( sourcePath, branchPath, context, h );
		namePlug()->hash( h );
	}
	else
	{
		h = outPlug()->childNamesPlug()->defaultValue()->Object::hash();
	}
}

IECore::ConstInternedStringVectorDataPtr VolumeScatter::computeBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() == 0 )
	{
		std::string name = namePlug()->getValue();
		if( name.empty() )
		{
			return outPlug()->childNamesPlug()->defaultValue();
		}
		InternedStringVectorDataPtr result = new InternedStringVectorData();
		result->writable().push_back( name );
		return result;
	}
	else
	{
		return outPlug()->childNamesPlug()->defaultValue();
	}
}
