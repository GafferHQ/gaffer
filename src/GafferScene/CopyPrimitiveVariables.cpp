//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, John Haddon. All rights reserved.
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

#include "GafferScene/CopyPrimitiveVariables.h"

#include "GafferScene/SceneAlgo.h"

#include "Gaffer/ArrayPlug.h"

#include "IECoreScene/Primitive.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( CopyPrimitiveVariables );

size_t CopyPrimitiveVariables::g_firstPlugIndex = 0;

CopyPrimitiveVariables::CopyPrimitiveVariables( const std::string &name )
	:	Deformer( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "source" ) );
	addChild( new StringPlug( "primitiveVariables", Plug::In, "" ) );
	addChild( new StringPlug( "sourceLocation" ) );
	addChild( new StringPlug( "prefix" ) );
}

CopyPrimitiveVariables::~CopyPrimitiveVariables()
{
}

GafferScene::ScenePlug *CopyPrimitiveVariables::sourcePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const GafferScene::ScenePlug *CopyPrimitiveVariables::sourcePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *CopyPrimitiveVariables::primitiveVariablesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *CopyPrimitiveVariables::primitiveVariablesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *CopyPrimitiveVariables::sourceLocationPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *CopyPrimitiveVariables::sourceLocationPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *CopyPrimitiveVariables::prefixPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *CopyPrimitiveVariables::prefixPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

bool CopyPrimitiveVariables::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return Deformer::affectsProcessedObject( input ) ||
		input == sourcePlug()->objectPlug() ||
		input == primitiveVariablesPlug() ||
		input == prefixPlug() ||
		input == sourceLocationPlug() ||
		input == sourcePlug()->existsPlug()
	;
}

void CopyPrimitiveVariables::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Deformer::hashProcessedObject( path, context, h );
	primitiveVariablesPlug()->hash( h );
	prefixPlug()->hash( h );

	boost::optional<ScenePath> sourceLocationPath;
	const string sourceLocation = sourceLocationPlug()->getValue();
	if( !sourceLocation.empty() )
	{
		/// \todo When we can use `std::optional` from C++17, `emplace()`
		/// will return a reference, allowing us to call
		/// `stringToPath( sourceLocation, sourceLocationPath.emplace() )`.
		sourceLocationPath.emplace();
		ScenePlug::stringToPath( sourceLocation, *sourceLocationPath );
	}

	if( !sourcePlug()->exists( sourceLocationPath ? *sourceLocationPath : path ) )
	{
		h = inPlug()->objectPlug()->hash();
		return;
	}

	if( sourceLocationPath )
	{
		h.append( sourcePlug()->objectHash( *sourceLocationPath ) );
	}
	else
	{
		sourcePlug()->objectPlug()->hash( h );
	}
}

IECore::ConstObjectPtr CopyPrimitiveVariables::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	auto primitive = runTimeCast<const Primitive>( inputObject );
	if( !primitive )
	{
		return inputObject;
	}

	const string primitiveVariables = primitiveVariablesPlug()->getValue();
	if( primitiveVariables.empty() )
	{
		return inputObject;
	}

	const string prefix = prefixPlug()->getValue();

	boost::optional<ScenePath> sourceLocationPath;
	const string sourceLocation = sourceLocationPlug()->getValue();
	if( !sourceLocation.empty() )
	{
		/// \todo When we can use `std::optional` from C++17, `emplace()`
		/// will return a reference, allowing us to call
		/// `stringToPath( sourceLocation, copyFromPath.emplace() )`.
		sourceLocationPath.emplace();
		ScenePlug::stringToPath( sourceLocation, *sourceLocationPath );
	}

	if( !sourcePlug()->exists( sourceLocationPath ? *sourceLocationPath : path ) )
	{
		return inputObject;
	}

	ConstObjectPtr sourceObject;
	if( sourceLocationPath )
	{
		sourceObject = sourcePlug()->object( *sourceLocationPath );
	}
	else
	{
		sourceObject = sourcePlug()->objectPlug()->getValue();
	}

	auto sourcePrimitive = runTimeCast<const Primitive>( sourceObject.get() );
	if( !sourcePrimitive )
	{
		return inputObject;
	}

	PrimitivePtr result = primitive->copy();
	for( auto &variable : sourcePrimitive->variables )
	{
		if( !StringAlgo::matchMultiple( variable.first, primitiveVariables ) )
		{
			continue;
		}
		if( !result->isPrimitiveVariableValid( variable.second ) )
		{
			string destinationPath; ScenePlug::pathToString( path, destinationPath );
			const string &sourcePath = sourceLocation.size() ? sourceLocation : destinationPath;
			throw IECore::Exception( boost::str(
				boost::format( "Cannot copy \"%1%\" from \"%2%\" to \"%3%\" because source and destination primitives have different topology" )
					% variable.first % destinationPath % sourcePath
			) );
		}
		result->variables[prefix + variable.first] = variable.second;
	}

	return result;
}

bool CopyPrimitiveVariables::adjustBounds() const
{
	if( !Deformer::adjustBounds() )
	{
		return false;
	}

	return StringAlgo::matchMultiple( "P", primitiveVariablesPlug()->getValue() ) && prefixPlug()->isSetToDefault();
}
