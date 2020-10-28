//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "IECoreScene/Primitive.h"

#include "GafferScene/PrimitiveVariableExists.h"

#include "Gaffer/Context.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferScene;
using namespace Gaffer;

GAFFER_NODE_DEFINE_TYPE( PrimitiveVariableExists );

size_t PrimitiveVariableExists::g_firstPlugIndex = 0;

PrimitiveVariableExists::PrimitiveVariableExists( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "in", Gaffer::Plug::In ) );
	addChild( new StringPlug( "primitiveVariable", Gaffer::Plug::In, "P" ) );
	addChild( new BoolPlug( "out", Gaffer::Plug::Out ) );
}

PrimitiveVariableExists::~PrimitiveVariableExists()
{
}

ScenePlug *PrimitiveVariableExists::inPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *PrimitiveVariableExists::inPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

StringPlug *PrimitiveVariableExists::primitiveVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const StringPlug *PrimitiveVariableExists::primitiveVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

BoolPlug *PrimitiveVariableExists::outPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const BoolPlug *PrimitiveVariableExists::outPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

void PrimitiveVariableExists::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == inPlug()->objectPlug() || input == primitiveVariablePlug() )
	{
		outputs.push_back( outPlug() );
	}
}

void PrimitiveVariableExists::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );
	if( output == outPlug() )
	{
		if( context->get<InternedStringVectorData>( ScenePlug::scenePathContextName, nullptr ) )
		{
			h.append( primitiveVariablePlug()->hash() );
			h.append( inPlug()->objectPlug()->hash() );
		}
		else
		{
			h.append( false );
		}
	}
}

void PrimitiveVariableExists::compute( ValuePlug *output, const Context *context ) const
{
	if( output == outPlug() )
	{
		bool exists = false;
		if( context->get<InternedStringVectorData>( ScenePlug::scenePathContextName, nullptr ) )
		{
			ConstObjectPtr inObject = inPlug()->objectPlug()->getValue();

			const IECoreScene::Primitive* inPrimitive = runTimeCast<const IECoreScene::Primitive>( inObject.get() );
			if( inPrimitive )
			{
				std::string primitiveVariable = primitiveVariablePlug()->getValue();
				if( inPrimitive->variables.find( primitiveVariable ) != inPrimitive->variables.end() )
				{
					exists = true;
				}
			}
		}

		static_cast<Gaffer::BoolPlug *>( output )->setValue( exists );
	}
}
