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

#include "Gaffer/PlugAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind.hpp"
#include "boost/logic/tribool.hpp"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

const std::string g_attributePrefix( "attribute:" );

} // namespace

GAFFER_NODE_DEFINE_TYPE( AttributeProcessor );

size_t AttributeProcessor::g_firstPlugIndex = 0;

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
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new BoolPlug( "global", Plug::In, false ) );

	// Fast pass-throughs for things we don't modify
	for( auto &p : Plug::Range( *outPlug() ) )
	{
		if( p != outPlug()->attributesPlug() )
		{
			p->setInput( inPlug()->getChild<Plug>( p->getName() ) );
		}
	}

	// Connect to signals we use to manage pass-throughs for globals
	// and attributes based on the value of `globalPlug()`.
	plugSetSignal().connect( boost::bind( &AttributeProcessor::plugSet, this, ::_1 ) );
	plugInputChangedSignal().connect( boost::bind( &AttributeProcessor::plugInputChanged, this, ::_1 ) );
}

AttributeProcessor::~AttributeProcessor()
{
}

Gaffer::BoolPlug *AttributeProcessor::globalPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex );
}

const Gaffer::BoolPlug *AttributeProcessor::globalPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex );
}

void AttributeProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	if(
		input == globalPlug() ||
		input == filterPlug() ||
		input == inPlug()->attributesPlug() ||
		affectsProcessedAttributes( input )
	)
	{
		// We can only affect a particular output if we haven't
		// connected it as a pass-through in `updateInternalConnections()`.
		if( !outPlug()->attributesPlug()->getInput() )
		{
			outputs.push_back( outPlug()->attributesPlug() );
		}
	}

	if(
		input == globalPlug() ||
		input == inPlug()->globalsPlug() ||
		affectsProcessedAttributes( input )
	)
	{
		// See above.
		if( !outPlug()->globalsPlug()->getInput() )
		{
			outputs.push_back( outPlug()->globalsPlug() );
		}
	}
}

bool AttributeProcessor::affectsProcessedAttributes( const Gaffer::Plug *input ) const
{
	return false;
}

void AttributeProcessor::hashProcessedAttributes( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

void AttributeProcessor::plugSet( Gaffer::Plug *plug )
{
	if( plug == globalPlug() )
	{
		updateInternalConnections();
	}
}

void AttributeProcessor::plugInputChanged( Gaffer::Plug *plug )
{
	if( plug == globalPlug() )
	{
		updateInternalConnections();
	}
}

void AttributeProcessor::updateInternalConnections()
{
	// Manage internal pass-throughs based on the value of the `globalPlug()`.
	boost::tribool global;
	if( PlugAlgo::dependsOnCompute( globalPlug() ) )
	{
		// Can vary from compute to compute.
		global = boost::indeterminate;
	}
	else
	{
		global = globalPlug()->getValue();
	}

	outPlug()->globalsPlug()->setInput(
		global || boost::indeterminate( global ) ? nullptr : inPlug()->globalsPlug()
	);
	outPlug()->attributesPlug()->setInput(
		!global || boost::indeterminate( global ) ? nullptr : inPlug()->attributesPlug()
	);
}

void AttributeProcessor::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	MurmurHash processedAttributesHash;
	if( globalPlug()->getValue() )
	{
		hashProcessedAttributes( context, processedAttributesHash );
	}

	if( processedAttributesHash != MurmurHash() )
	{
		FilteredSceneProcessor::hashGlobals( context, parent, h );
		inPlug()->globalsPlug()->hash( h );
		h.append( processedAttributesHash );
	}
	else
	{
		// We won't modify the globals - pass through the hash.
		h = inPlug()->globalsPlug()->hash();
	}
}

IECore::ConstCompoundObjectPtr AttributeProcessor::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstCompoundObjectPtr inputGlobals = inPlug()->globalsPlug()->getValue();
	if( !globalPlug()->getValue() )
	{
		return inputGlobals;
	}

	IECore::CompoundObjectPtr result = new CompoundObject;
	IECore::CompoundObjectPtr attributesToProcess = new CompoundObject;

	for( const auto &[name, value] : inputGlobals->members() )
	{
		if( boost::starts_with( name.string(), g_attributePrefix ) )
		{
			attributesToProcess->members()[name.string().substr( g_attributePrefix.size())] = value;
		}
		else
		{
			result->members()[name] = value;
		}
	}

	IECore::ConstCompoundObjectPtr processedAttributes = computeProcessedAttributes( context, attributesToProcess.get() );
	for( const auto &[name, value] : processedAttributes->members() )
	{
		result->members()[g_attributePrefix+name.string()] = value;
	}

	return result;
}

void AttributeProcessor::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	MurmurHash processedAttributesHash;
	if( !globalPlug()->getValue() && ( filterValue( context ) & IECore::PathMatcher::ExactMatch ) )
	{
		hashProcessedAttributes( context, processedAttributesHash );
	}

	if( processedAttributesHash != MurmurHash() )
	{
		FilteredSceneProcessor::hashAttributes( path, context, parent, h );
		inPlug()->attributesPlug()->hash( h );
		h.append( processedAttributesHash );
	}
	else
	{
		// pass through
		h = inPlug()->attributesPlug()->hash();
	}
}

IECore::ConstCompoundObjectPtr AttributeProcessor::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( !globalPlug()->getValue() && ( filterValue( context ) & IECore::PathMatcher::ExactMatch ) )
	{
		ConstCompoundObjectPtr inputAttributes = inPlug()->attributesPlug()->getValue();
		return computeProcessedAttributes( context, inputAttributes.get() );
	}
	else
	{
		return inPlug()->attributesPlug()->getValue();
	}
}
