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

#include "GafferScene/MeshToPoints.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/PointsPrimitive.h"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( MeshToPoints );

size_t MeshToPoints::g_firstPlugIndex = 0;

MeshToPoints::MeshToPoints( const std::string &name )
	:	Deformer( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "type", Plug::In, "particle" ) );
}

MeshToPoints::~MeshToPoints()
{
}

Gaffer::StringPlug *MeshToPoints::typePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *MeshToPoints::typePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

bool MeshToPoints::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		Deformer::affectsProcessedObject( input ) ||
		input == typePlug()
	;
}

void MeshToPoints::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Deformer::hashProcessedObject( path, context, h );
	typePlug()->hash( h );
}

IECore::ConstObjectPtr MeshToPoints::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const MeshPrimitive *mesh = runTimeCast<const MeshPrimitive>( inputObject );
	if( !mesh )
	{
		return inputObject;
	}

	IECoreScene::PointsPrimitivePtr result = new PointsPrimitive( mesh->variableSize( PrimitiveVariable::Vertex ) );
	for( PrimitiveVariableMap::const_iterator it = mesh->variables.begin(), eIt = mesh->variables.end(); it != eIt; ++it )
	{
		PrimitiveVariable::Interpolation interpolation = it->second.interpolation;
		switch( interpolation )
		{
			case PrimitiveVariable::Uniform :
			case PrimitiveVariable::FaceVarying :
				// Skip these, since they make no sense
				// on points.
				continue;
			case PrimitiveVariable::Varying :
				interpolation = PrimitiveVariable::Vertex;
				break;
			default :
				break;
		}

		result->variables[it->first] = PrimitiveVariable( interpolation, it->second.data );
	}

	result->variables["type"] = PrimitiveVariable( PrimitiveVariable::Constant, new StringData( typePlug()->getValue() ) );

	return result;
}
