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

#include "GafferScene/AttributeProcessor.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( AttributeProcessor );

AttributeProcessor::AttributeProcessor( const std::string &name, IECore::PathMatcher::Result filterDefault )
	:	FilteredSceneProcessor( name, filterDefault )
{
	init();
}

AttributeProcessor::AttributeProcessor( const std::string &name )
	:	AttributeProcessor( name, PathMatcher::NoMatch )
{
}

AttributeProcessor::AttributeProcessor( const std::string &name, size_t minInputs, size_t maxInputs )
	:	FilteredSceneProcessor( name, minInputs, maxInputs )
{
	init();
}

void AttributeProcessor::init()
{
	// Fast pass-throughs for things we don't modify
	for( auto &p : Plug::Range( *outPlug() ) )
	{
		if( p != outPlug()->attributesPlug() )
		{
			p->setInput( inPlug()->getChild<Plug>( p->getName() ) );
		}
	}
}

AttributeProcessor::~AttributeProcessor()
{
}

void AttributeProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	if( affectsProcessedAttributes( input ) )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

bool AttributeProcessor::affectsProcessedAttributes( const Gaffer::Plug *input ) const
{
	return input == filterPlug() || input == inPlug()->attributesPlug();
}

void AttributeProcessor::hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashAttributes( path, context, outPlug(), h );
	inPlug()->attributesPlug()->hash( h );
}

void AttributeProcessor::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( filterValue( context ) & IECore::PathMatcher::ExactMatch )
	{
		hashProcessedAttributes( path, context, h );
	}
	else
	{
		// pass through
		h = inPlug()->attributesPlug()->hash();
	}
}

IECore::ConstCompoundObjectPtr AttributeProcessor::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( filterValue( context ) & IECore::PathMatcher::ExactMatch )
	{
		ConstCompoundObjectPtr inputAttributes = inPlug()->attributesPlug()->getValue();
		return computeProcessedAttributes( path, context, inputAttributes.get() );
	}
	else
	{
		return inPlug()->attributesPlug()->getValue();
	}
}

