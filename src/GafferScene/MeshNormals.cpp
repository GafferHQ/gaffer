//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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
//      * Neither the name of John Haddon nor the names of
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

#include "GafferScene/MeshNormals.h"

#include "IECoreScene/MeshAlgo.h"
#include "IECoreScene/MeshPrimitive.h"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( MeshNormals );

size_t MeshNormals::g_firstPlugIndex = 0;

MeshNormals::MeshNormals( const std::string &name )
	:	ObjectProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "interpolation", Plug::In, PrimitiveVariable::Vertex, /* min */ PrimitiveVariable::Uniform, /* max */ PrimitiveVariable::FaceVarying ) );
	addChild( new IntPlug( "weighting", Plug::In, (int)MeshAlgo::NormalWeighting::Angle, /* min */ (int)MeshAlgo::NormalWeighting::Equal, /* max */ (int)MeshAlgo::NormalWeighting::Area ) );
	addChild( new FloatPlug( "thresholdAngle", Plug::In, 40, /* min */ 0.0f, /* max */ 180.0f ) );
	addChild( new StringPlug( "position", Plug::In, "P" ) );
	addChild( new StringPlug( "normal", Plug::In, "N" ) );
}

MeshNormals::~MeshNormals()
{
}

Gaffer::IntPlug *MeshNormals::interpolationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *MeshNormals::interpolationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *MeshNormals::weightingPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *MeshNormals::weightingPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::FloatPlug *MeshNormals::thresholdAnglePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::FloatPlug *MeshNormals::thresholdAnglePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *MeshNormals::positionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *MeshNormals::positionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *MeshNormals::normalPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *MeshNormals::normalPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::ValuePlug::CachePolicy MeshNormals::processedObjectComputeCachePolicy() const
{
	return ValuePlug::CachePolicy::TaskCollaboration;
}

bool MeshNormals::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		input == interpolationPlug() ||
		input == weightingPlug() ||
		input == thresholdAnglePlug() ||
		input == positionPlug() ||
		input == normalPlug()
	;
}

void MeshNormals::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ObjectProcessor::hashProcessedObject( path, context, h );
	interpolationPlug()->hash( h );
	weightingPlug()->hash( h );
	thresholdAnglePlug()->hash( h );
	positionPlug()->hash( h );
	normalPlug()->hash( h );
}

IECore::ConstObjectPtr MeshNormals::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const MeshPrimitive *mesh = runTimeCast<const MeshPrimitive>( inputObject );
	if( !mesh )
	{
		return inputObject;
	}

	std::string normal = normalPlug()->getValue();
	PrimitiveVariable::Interpolation interpolation = (PrimitiveVariable::Interpolation) interpolationPlug()->getValue();
	MeshAlgo::NormalWeighting weighting = (MeshAlgo::NormalWeighting) weightingPlug()->getValue();
	float thresholdAngle = thresholdAnglePlug()->getValue();
	std::string position = positionPlug()->getValue();

	MeshPrimitivePtr meshWithNormals = runTimeCast<MeshPrimitive>( mesh->copy() );

	if( interpolation == PrimitiveVariable::Uniform )
	{
		meshWithNormals->variables[ normal ] = MeshAlgo::calculateUniformNormals(
			meshWithNormals.get(), position
		);
	}
	else if( interpolation == PrimitiveVariable::Vertex || interpolation == PrimitiveVariable::Varying )
	{
		meshWithNormals->variables[ normal ] = MeshAlgo::calculateVertexNormals(
			meshWithNormals.get(), weighting, position
		);
	}
	else if( interpolation == PrimitiveVariable::FaceVarying )
	{
		meshWithNormals->variables[ normal ] = MeshAlgo::calculateFaceVaryingNormals(
			meshWithNormals.get(), weighting, thresholdAngle, position
		);
	}

	return meshWithNormals;
}
