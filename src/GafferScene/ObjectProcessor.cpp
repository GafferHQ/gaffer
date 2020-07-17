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

#include "GafferScene/ObjectProcessor.h"

#include "IECore/NullObject.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( ObjectProcessor );

size_t ObjectProcessor::g_firstPlugIndex;

ObjectProcessor::ObjectProcessor( const std::string &name, IECore::PathMatcher::Result filterDefault )
	:	FilteredSceneProcessor( name, filterDefault )
{
	init();
}

ObjectProcessor::ObjectProcessor( const std::string &name )
	:	ObjectProcessor( name, IECore::PathMatcher::NoMatch )
{
}

ObjectProcessor::ObjectProcessor( const std::string &name, size_t minInputs, size_t maxInputs )
	:	FilteredSceneProcessor( name, minInputs, maxInputs )
{
	init();
}

void ObjectProcessor::init()
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ObjectPlug( "__processedObject", Plug::Out, NullObject::defaultNullObject() ) );

	// Pass through things we don't want to change.
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
	outPlug()->childNamesPlug()->setInput( inPlug()->childNamesPlug() );
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
	outPlug()->setPlug()->setInput( inPlug()->setPlug() );
}

ObjectProcessor::~ObjectProcessor()
{
}

Gaffer::ObjectPlug *ObjectProcessor::processedObjectPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex );
}

const Gaffer::ObjectPlug *ObjectProcessor::processedObjectPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex );
}

void ObjectProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	if( affectsProcessedObject( input ) )
	{
		outputs.push_back( processedObjectPlug() );
	}
	else if( input == processedObjectPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

void ObjectProcessor::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == processedObjectPlug() )
	{
		const auto &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
		hashProcessedObject( path, context, h );
	}
	else
	{
		FilteredSceneProcessor::hash( output, context, h );
	}
}

void ObjectProcessor::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == processedObjectPlug() )
	{
		const auto &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
		ConstObjectPtr inputObject = inPlug()->objectPlug()->getValue();
		static_cast<ObjectPlug *>( output )->setValue( computeProcessedObject( path, context, inputObject.get() ) );
	}
	else
	{
		FilteredSceneProcessor::compute( output, context );
	}
}

Gaffer::ValuePlug::CachePolicy ObjectProcessor::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == processedObjectPlug() )
	{
		return processedObjectComputeCachePolicy();
	}
	else
	{
		return FilteredSceneProcessor::computeCachePolicy( output );
	}
}

bool ObjectProcessor::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return input == filterPlug() || input == inPlug()->objectPlug();
}

void ObjectProcessor::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hash( processedObjectPlug(), context, h );
	inPlug()->objectPlug()->hash( h );
}

Gaffer::ValuePlug::CachePolicy ObjectProcessor::processedObjectComputeCachePolicy() const
{
	return ValuePlug::CachePolicy::Legacy;
}

void ObjectProcessor::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( filterValue( context ) & IECore::PathMatcher::ExactMatch )
	{
		h = processedObjectPlug()->hash();
	}
	else
	{
		// pass through
		h = inPlug()->objectPlug()->hash();
	}
}

IECore::ConstObjectPtr ObjectProcessor::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( filterValue( context ) & IECore::PathMatcher::ExactMatch )
	{
		return processedObjectPlug()->getValue();
	}
	else
	{
		return inPlug()->objectPlug()->getValue();
	}
}
