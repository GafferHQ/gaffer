//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/PrimitiveQuery.h"

#include "IECoreScene/Primitive.h"

#include "IECore/NullObject.h"

using namespace Gaffer;
using namespace GafferScene;

size_t PrimitiveQuery::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( PrimitiveQuery );

PrimitiveQuery::PrimitiveQuery( const std::string &name )
:	Gaffer::ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new BoolPlug( "enabled", Plug::In, true ) );
	addChild( new ScenePlug( "scene" ) );
	addChild( new Gaffer::StringPlug( "location" ) );
	addChild( new Gaffer::StringPlug( "type", Gaffer::Plug::Out ) );
	addChild( new Gaffer::IntPlug( "uniform", Gaffer::Plug::Out ) );
	addChild( new Gaffer::IntPlug( "vertex", Gaffer::Plug::Out ) );
	addChild( new Gaffer::IntPlug( "varying", Gaffer::Plug::Out ) );
	addChild( new Gaffer::IntPlug( "faceVarying", Gaffer::Plug::Out ) );
	addChild( new Gaffer::ObjectPlug( "primitive", Gaffer::Plug::Out, IECore::NullObject::defaultNullObject() ) );
}

PrimitiveQuery::~PrimitiveQuery()
{
}

Gaffer::BoolPlug *PrimitiveQuery::enabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

const Gaffer::BoolPlug *PrimitiveQuery::enabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

ScenePlug *PrimitiveQuery::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 1 );
}

const ScenePlug *PrimitiveQuery::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *PrimitiveQuery::locationPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *PrimitiveQuery::locationPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *PrimitiveQuery::typePlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *PrimitiveQuery::typePlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::IntPlug *PrimitiveQuery::uniformPlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::IntPlug *PrimitiveQuery::uniformPlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 4 );
}

Gaffer::IntPlug *PrimitiveQuery::vertexPlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::IntPlug *PrimitiveQuery::vertexPlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 5 );
}

Gaffer::IntPlug *PrimitiveQuery::varyingPlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::IntPlug *PrimitiveQuery::varyingPlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 6 );
}

Gaffer::IntPlug *PrimitiveQuery::faceVaryingPlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::IntPlug *PrimitiveQuery::faceVaryingPlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 7 );
}

Gaffer::ObjectPlug *PrimitiveQuery::primitivePlug()
{
	return getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::ObjectPlug *PrimitiveQuery::primitivePlug() const
{
	return getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 8 );
}

void PrimitiveQuery::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == enabledPlug() ||
		input == locationPlug() ||
		input == scenePlug()->existsPlug() ||
		input == scenePlug()->objectPlug()
	)
	{
		outputs.push_back( typePlug() );
		outputs.push_back( uniformPlug() );
		outputs.push_back( vertexPlug() );
		outputs.push_back( varyingPlug() );
		outputs.push_back( faceVaryingPlug() );
		outputs.push_back( primitivePlug() );
	}
}

void PrimitiveQuery::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if(
		output == typePlug() ||
		output == uniformPlug() ||
		output == vertexPlug() ||
		output == varyingPlug() ||
		output == faceVaryingPlug() ||
		output == primitivePlug()
	)
	{
		ComputeNode::hash( output, context, h );
		if( enabledPlug()->getValue() )
		{
			const std::string location = locationPlug()->getValue();
			if( !location.empty() )
			{
				const ScenePlug::ScenePath path = ScenePlug::stringToPath( location );
				const ScenePlug::PathScope scope( context, &path );
				if( scenePlug()->existsPlug()->getValue() )
				{
					scenePlug()->objectPlug()->hash( h );
				}
			}
		}
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void PrimitiveQuery::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if(
		output == typePlug() ||
		output == uniformPlug() ||
		output == vertexPlug() ||
		output == varyingPlug() ||
		output == faceVaryingPlug() ||
		output == primitivePlug()
	)
	{
		IECoreScene::ConstPrimitivePtr primitive;
		if( enabledPlug()->getValue() )
		{
			const std::string location = locationPlug()->getValue();
			if( !location.empty() )
			{
				const ScenePlug::ScenePath path = ScenePlug::stringToPath( location );
				const ScenePlug::PathScope scope( context, &path );
				if( scenePlug()->existsPlug()->getValue() )
				{
					primitive = IECore::runTimeCast<const IECoreScene::Primitive>( scenePlug()->objectPlug()->getValue() );
				}
			}
		}

		if( output == typePlug() )
		{
			static_cast<Gaffer::StringPlug *>( output )->setValue( primitive ? primitive->typeName() : "" );
		}
		else if( output == uniformPlug() )
		{
			static_cast<Gaffer::IntPlug *>( output )->setValue( primitive ? (int)primitive->variableSize( IECoreScene::PrimitiveVariable::Uniform ) : 0 );
		}
		else if( output == vertexPlug() )
		{
			static_cast<Gaffer::IntPlug *>( output )->setValue( primitive ? (int)primitive->variableSize( IECoreScene::PrimitiveVariable::Vertex ) : 0 );
		}
		else if( output == varyingPlug() )
		{
			static_cast<Gaffer::IntPlug *>( output )->setValue( primitive ? (int)primitive->variableSize( IECoreScene::PrimitiveVariable::Varying ) : 0 );
		}
		else if( output == faceVaryingPlug() )
		{
			static_cast<Gaffer::IntPlug *>( output )->setValue( primitive ? (int)primitive->variableSize( IECoreScene::PrimitiveVariable::FaceVarying ) : 0 );
		}
		else if( output == primitivePlug() )
		{
			static_cast<Gaffer::ObjectPlug *>( output )->setValue( primitive ? primitive : IECore::ConstObjectPtr( IECore::NullObject::defaultNullObject() ) );
		}
	}
	else
	{
		ComputeNode::compute( output, context );
	}
}
