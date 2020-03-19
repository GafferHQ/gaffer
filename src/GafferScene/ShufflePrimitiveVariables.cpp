//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/ShufflePrimitiveVariables.h"

#include "GafferScene/SceneAlgo.h"

#include "IECoreScene/Primitive.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( ShufflePrimitiveVariables );

size_t ShufflePrimitiveVariables::g_firstPlugIndex = 0;

ShufflePrimitiveVariables::ShufflePrimitiveVariables( const std::string &name ) : Deformer( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ShufflesPlug( "shuffles" ) );
}

ShufflePrimitiveVariables::~ShufflePrimitiveVariables()
{
}

Gaffer::ShufflesPlug *ShufflePrimitiveVariables::shufflesPlug()
{
	return getChild<Gaffer::ShufflesPlug>( g_firstPlugIndex );
}

const Gaffer::ShufflesPlug *ShufflePrimitiveVariables::shufflesPlug() const
{
	return getChild<Gaffer::ShufflesPlug>( g_firstPlugIndex );
}

bool ShufflePrimitiveVariables::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return Deformer::affectsProcessedObject( input ) || shufflesPlug()->isAncestorOf( input );
}

void ShufflePrimitiveVariables::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Deformer::hashProcessedObject( path, context, h );

	shufflesPlug()->hash( h );
}

IECore::ConstObjectPtr ShufflePrimitiveVariables::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	auto inputPrimitive = runTimeCast<const Primitive>( inputObject );
	if( !inputPrimitive )
	{
		return inputObject;
	}

	if( shufflesPlug()->children().empty() )
	{
		return inputObject;
	}

	PrimitivePtr result = inputPrimitive->copy();
	result->variables = shufflesPlug()->shuffle<PrimitiveVariableMap>( inputPrimitive->variables );

	return result;
}

bool ShufflePrimitiveVariables::adjustBounds() const
{
	if( !Deformer::adjustBounds() )
	{
		return false;
	}

	for( auto &child : shufflesPlug()->children() )
	{
		ShufflePlug *shuffle = static_cast<ShufflePlug *>( child.get() );

		// we should be scoping the $source variable here, but its unlikely to matter in practice
		if( shuffle->enabledPlug()->getValue() && shuffle->destinationPlug()->getValue() == "P" )
		{
			return true;
		}
	}

	return false;
}
