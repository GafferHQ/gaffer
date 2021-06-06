//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/MeshType.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/MeshAlgo.h"
#include "IECoreScene/MeshPrimitive.h"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( MeshType );

size_t MeshType::g_firstPlugIndex = 0;

MeshType::MeshType( const std::string &name )
	:	ObjectProcessor( name, PathMatcher::EveryMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "meshType", Plug::In, "" ) );
	addChild( new BoolPlug( "calculatePolygonNormals" ) );
	addChild( new BoolPlug( "overwriteExistingNormals" ) );
}

MeshType::~MeshType()
{
}

Gaffer::StringPlug *MeshType::meshTypePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *MeshType::meshTypePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *MeshType::calculatePolygonNormalsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *MeshType::calculatePolygonNormalsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *MeshType::overwriteExistingNormalsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *MeshType::overwriteExistingNormalsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

bool MeshType::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		input == meshTypePlug() ||
		input == calculatePolygonNormalsPlug() ||
		input == overwriteExistingNormalsPlug()
	;
}

void MeshType::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ObjectProcessor::hashProcessedObject( path, context, h );
	meshTypePlug()->hash( h );
	calculatePolygonNormalsPlug()->hash( h );
	overwriteExistingNormalsPlug()->hash( h );
}

IECore::ConstObjectPtr MeshType::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const MeshPrimitive *inputGeometry = runTimeCast<const MeshPrimitive>( inputObject );
	if( !inputGeometry )
	{
		return inputObject;
	}

	std::string meshType = meshTypePlug()->getValue();
	if( meshType == "" )
	{
		// unchanged
		return inputObject;
	}

	// Check if we need to recompute normals
	bool doNormals = false;
	if( calculatePolygonNormalsPlug()->getValue() && meshType == "linear" )
	{
		bool overwriteExisting = overwriteExistingNormalsPlug()->getValue();
		doNormals = overwriteExisting || inputGeometry->variables.find( "N" ) == inputGeometry->variables.end();
	}

	// If we don't need to change anything, don't bother duplicating the input
	if( inputGeometry->interpolation() == meshType && !doNormals )
	{
		return inputObject;
	}

	IECoreScene::MeshPrimitivePtr result = inputGeometry->copy();
	result->setInterpolation( meshType );
	if( meshType != "linear" )
	{
		IECoreScene::PrimitiveVariableMap::iterator varN = result->variables.find( "N" );
		if( varN != result->variables.end() )
		{
			result->variables.erase( varN );
		}
	}

	if( doNormals )
	{
		result->variables[ "N" ] = MeshAlgo::calculateNormals( result.get(), PrimitiveVariable::Interpolation::Vertex, "P", context->canceller() );
	}

	return result;
}
