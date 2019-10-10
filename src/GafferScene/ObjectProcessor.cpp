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

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( ObjectProcessor );

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

void ObjectProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	if( !refCount() )
	{
		// Avoid calling pure virtual methods while we're still constructing.
		return;
	}

	if( affectsProcessedObject( input ) )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

bool ObjectProcessor::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return input == filterPlug() || input == inPlug()->objectPlug();
}

void ObjectProcessor::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashObject( path, context, outPlug(), h );
	inPlug()->objectPlug()->hash( h );
}

void ObjectProcessor::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( filterValue( context ) & IECore::PathMatcher::ExactMatch )
	{
		hashProcessedObject( path, context, h );
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
		ConstObjectPtr inputObject = inPlug()->objectPlug()->getValue();
		return computeProcessedObject( path, context, inputObject.get() );
	}
	else
	{
		return inPlug()->objectPlug()->getValue();
	}
}
