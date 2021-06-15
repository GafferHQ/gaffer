//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/MeshTangents.h"

#include "IECoreScene/MeshAlgo.h"
#include "IECoreScene/MeshPrimitive.h"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( MeshTangents );

size_t MeshTangents::g_firstPlugIndex = 0;

MeshTangents::MeshTangents( const std::string &name )
	:	ObjectProcessor( name, PathMatcher::EveryMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "mode", Plug::In, Mode::UV, /* min */ 0, /* max */ Mode::NumberOfModes ) );
	addChild( new BoolPlug( "orthogonal", Plug::In, true ) );
	addChild( new BoolPlug( "leftHanded", Plug::In, false ) );
	addChild( new StringPlug( "position", Plug::In, "P" ) );
	addChild( new StringPlug( "normal", Plug::In, "N" ) );
	addChild( new StringPlug( "uvSet", Plug::In, "uv" ) );
	addChild( new StringPlug( "uTangent", Plug::In, "uTangent" ) );
	addChild( new StringPlug( "vTangent", Plug::In, "vTangent" ) );
	addChild( new StringPlug( "tangent", Plug::In, "tangent" ) );
	addChild( new StringPlug( "biTangent", Plug::In, "biTangent" ) );
}

MeshTangents::~MeshTangents()
{
}

Gaffer::IntPlug *MeshTangents::modePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *MeshTangents::modePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *MeshTangents::orthogonalPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *MeshTangents::orthogonalPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *MeshTangents::leftHandedPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *MeshTangents::leftHandedPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *MeshTangents::positionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *MeshTangents::positionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *MeshTangents::normalPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *MeshTangents::normalPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringPlug *MeshTangents::uvSetPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringPlug *MeshTangents::uvSetPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

Gaffer::StringPlug *MeshTangents::uTangentPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::StringPlug *MeshTangents::uTangentPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

Gaffer::StringPlug *MeshTangents::vTangentPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::StringPlug *MeshTangents::vTangentPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 7 );
}

Gaffer::StringPlug *MeshTangents::tangentPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::StringPlug *MeshTangents::tangentPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 8 );
}

Gaffer::StringPlug *MeshTangents::biTangentPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::StringPlug *MeshTangents::biTangentPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 9 );
}

bool MeshTangents::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		input == uvSetPlug() ||
		input == positionPlug() ||
		input == orthogonalPlug() ||
		input == modePlug() ||
		input == leftHandedPlug() ||
		input == uTangentPlug() ||
		input == vTangentPlug() ||
		input == tangentPlug() ||
		input == biTangentPlug() ||
		input == normalPlug()
	;
}

void MeshTangents::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ObjectProcessor::hashProcessedObject( path, context, h );
	uvSetPlug()->hash( h );
	positionPlug()->hash( h );
	orthogonalPlug()->hash( h );
	leftHandedPlug()->hash( h );
	modePlug()->hash( h );
	uTangentPlug()->hash( h );
	vTangentPlug()->hash( h );
	tangentPlug()->hash( h );
	biTangentPlug()->hash( h );
	normalPlug()->hash( h );
}

IECore::ConstObjectPtr MeshTangents::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const MeshPrimitive *mesh = runTimeCast<const MeshPrimitive>( inputObject );
	if( !mesh )
	{
		return inputObject;
	}

	std::string position = positionPlug()->getValue();
	bool ortho = orthogonalPlug()->getValue();
	bool leftHanded = leftHandedPlug()->getValue();
	Mode mode = (Mode) modePlug()->getValue();

	MeshPrimitivePtr meshWithTangents = runTimeCast<MeshPrimitive>( mesh->copy() );
	std::pair<PrimitiveVariable, PrimitiveVariable> tangentPrimvars;

	if ( mode == Mode::UV )
	{
		std::string uvSet = uvSetPlug()->getValue();
		std::string uTangent = uTangentPlug()->getValue();
		std::string vTangent = vTangentPlug()->getValue();

		tangentPrimvars = MeshAlgo::calculateTangentsFromUV( mesh, uvSet, position, ortho, leftHanded, context->canceller() );

		meshWithTangents->variables[uTangent] = tangentPrimvars.first;
		meshWithTangents->variables[vTangent] = tangentPrimvars.second;
	}
	else
	{
		std::string normal = normalPlug()->getValue();
		std::string tangent = tangentPlug()->getValue();
		std::string biTangent = biTangentPlug()->getValue();

		if ( mode == Mode::FirstEdge )
		{
			tangentPrimvars = MeshAlgo::calculateTangentsFromFirstEdge( mesh, position, normal, ortho, leftHanded, context->canceller() );
		}
		else if ( mode == Mode::TwoEdges )
		{
			tangentPrimvars = MeshAlgo::calculateTangentsFromTwoEdges( mesh, position, normal, ortho, leftHanded, context->canceller() );
		}
		else
		{
			tangentPrimvars = MeshAlgo::calculateTangentsFromPrimitiveCentroid( mesh, position, normal, ortho, leftHanded, context->canceller() );
		}

		meshWithTangents->variables[tangent] = tangentPrimvars.first;
		meshWithTangents->variables[biTangent] = tangentPrimvars.second;
	}

	return meshWithTangents;
}
