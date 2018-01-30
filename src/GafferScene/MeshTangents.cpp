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

IE_CORE_DEFINERUNTIMETYPED( MeshTangents );

size_t MeshTangents::g_firstPlugIndex = 0;

MeshTangents::MeshTangents( const std::string &name ) : SceneElementProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "uvSet", Plug::In, "uv" ) );
	addChild( new StringPlug( "position", Plug::In, "P" ) );
	addChild( new StringPlug( "uTangent", Plug::In, "uTangent" ) );
	addChild( new StringPlug( "vTangent", Plug::In, "vTangent" ) );
	addChild( new BoolPlug( "orthogonal", Plug::In, true ) );

	// Fast pass-throughs for things we don't modify
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
}

MeshTangents::~MeshTangents()
{
}

Gaffer::StringPlug *MeshTangents::uvSetPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *MeshTangents::uvSetPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *MeshTangents::positionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *MeshTangents::positionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *MeshTangents::uTangentPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *MeshTangents::uTangentPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *MeshTangents::vTangentPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *MeshTangents::vTangentPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::BoolPlug *MeshTangents::orthogonalPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::BoolPlug *MeshTangents::orthogonalPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

void MeshTangents::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( input == uvSetPlug() || input == positionPlug() || input == orthogonalPlug() || input == uTangentPlug() || input == vTangentPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

bool MeshTangents::processesObject() const
{
	return true;
}

void MeshTangents::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	uvSetPlug()->hash( h );
	positionPlug()->hash( h );
	orthogonalPlug()->hash( h );
	uTangentPlug()->hash( h );
	vTangentPlug()->hash( h );
}

IECore::ConstObjectPtr MeshTangents::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	const MeshPrimitive *mesh = runTimeCast<const MeshPrimitive>( inputObject.get() );
	if( !mesh )
	{
		return inputObject;
	}

	std::string uvSet = uvSetPlug()->getValue();
	std::string position = positionPlug()->getValue();
	bool ortho = orthogonalPlug()->getValue();

	std::string uTangent = uTangentPlug()->getValue();
	std::string vTangent = vTangentPlug()->getValue();

	std::pair<PrimitiveVariable, PrimitiveVariable> tangentPrimvars = MeshAlgo::calculateTangents( mesh, uvSet, ortho, position);
	MeshPrimitivePtr meshWithTangents = runTimeCast<MeshPrimitive>( mesh->copy() );

	meshWithTangents->variables[uTangent] = tangentPrimvars.first;
	meshWithTangents->variables[vTangent] = tangentPrimvars.second;

	return meshWithTangents;
}
