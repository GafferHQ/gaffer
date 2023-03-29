//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
//      * Neither the name of Image Engine Design Inc nor the names of
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

#include "GafferScene/DeleteFaces.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/MeshAlgo.h"
#include "IECoreScene/MeshPrimitive.h"

#include "boost/algorithm/string.hpp"

#include "fmt/format.h"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( DeleteFaces );

size_t DeleteFaces::g_firstPlugIndex = 0;

DeleteFaces::DeleteFaces( const std::string &name )
	:	Deformer( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "faces", Plug::In, "deleteFaces" ) );
	addChild( new BoolPlug( "invert", Plug::In, false ) );
	addChild( new BoolPlug( "ignoreMissingVariable", Plug::In, false ) );
}

DeleteFaces::~DeleteFaces()
{
}

Gaffer::StringPlug *DeleteFaces::facesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *DeleteFaces::facesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *DeleteFaces::invertPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1);
}

const Gaffer::BoolPlug *DeleteFaces::invertPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1);
}

Gaffer::BoolPlug *DeleteFaces::ignoreMissingVariablePlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *DeleteFaces::ignoreMissingVariablePlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

bool DeleteFaces::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		Deformer::affectsProcessedObject( input ) ||
		input == facesPlug() ||
		input == invertPlug() ||
		input == ignoreMissingVariablePlug()
	;
}

void DeleteFaces::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Deformer::hashProcessedObject( path, context, h );
	facesPlug()->hash( h );
	invertPlug()->hash( h );
	ignoreMissingVariablePlug()->hash( h );
}

IECore::ConstObjectPtr DeleteFaces::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const MeshPrimitive *mesh = runTimeCast<const MeshPrimitive>( inputObject );
	if( !mesh )
	{
		return inputObject;
	}

	std::string deletePrimVarName = facesPlug()->getValue();

	if( deletePrimVarName.empty() )
	{
		return inputObject;
	}

	PrimitiveVariableMap::const_iterator it = mesh->variables.find( deletePrimVarName );
	if( it == mesh->variables.end() )
	{
		if( ignoreMissingVariablePlug()->getValue() )
		{
			return inputObject;
		}

		throw InvalidArgumentException( fmt::format( "DeleteFaces : No primitive variable \"{}\" found", deletePrimVarName ) );
	}

	return MeshAlgo::deleteFaces( mesh, it->second, invertPlug()->getValue(), context->canceller() );
}
