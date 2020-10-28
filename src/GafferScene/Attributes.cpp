//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferScene/Attributes.h"

#include "boost/bind.hpp"
#include "boost/logic/tribool.hpp"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( Attributes );

size_t Attributes::g_firstPlugIndex = 0;

Attributes::Attributes( const std::string &name )
	:	AttributeProcessor( name, PathMatcher::EveryMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new CompoundDataPlug( "attributes" ) );
	addChild( new BoolPlug( "global", Plug::In, false ) );
	addChild( new AtomicCompoundDataPlug( "extraAttributes", Plug::In, new IECore::CompoundData ) );

	// Connect to signals we use to manage pass-throughs for globals
	// and attributes based on the value of globalPlug().
	plugSetSignal().connect( boost::bind( &Attributes::plugSet, this, ::_1 ) );
	plugInputChangedSignal().connect( boost::bind( &Attributes::plugInputChanged, this, ::_1 ) );
}

Attributes::~Attributes()
{
}

Gaffer::CompoundDataPlug *Attributes::attributesPlug()
{
	return getChild<Gaffer::CompoundDataPlug>( g_firstPlugIndex );
}

const Gaffer::CompoundDataPlug *Attributes::attributesPlug() const
{
	return getChild<Gaffer::CompoundDataPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *Attributes::globalPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *Attributes::globalPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::AtomicCompoundDataPlug *Attributes::extraAttributesPlug()
{
	return getChild<Gaffer::AtomicCompoundDataPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::AtomicCompoundDataPlug *Attributes::extraAttributesPlug() const
{
	return getChild<Gaffer::AtomicCompoundDataPlug>( g_firstPlugIndex + 2 );
}

void Attributes::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	AttributeProcessor::affects( input, outputs );

	if(
		input == globalPlug() ||
		input == inPlug()->globalsPlug() ||
		attributesPlug()->isAncestorOf( input ) ||
		input == extraAttributesPlug()
	)
	{
		// We can only affect a particular output if we haven't
		// connected it as a pass-through in updateInternalConnections().
		if( !outPlug()->globalsPlug()->getInput() )
		{
			outputs.push_back( outPlug()->globalsPlug() );
		}
	}

}

void Attributes::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( globalPlug()->getValue() )
	{
		// We will modify the globals.
		AttributeProcessor::hashGlobals( context, parent, h );
		inPlug()->globalsPlug()->hash( h );
		attributesPlug()->hash( h );
		extraAttributesPlug()->hash( h );
	}
	else
	{
		// We won't modify the globals - pass through the hash.
		h = inPlug()->globalsPlug()->hash();
	}
}

IECore::ConstCompoundObjectPtr Attributes::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstCompoundObjectPtr inputGlobals = inPlug()->globalsPlug()->getValue();
	if( !globalPlug()->getValue() )
	{
		return inputGlobals;
	}

	const CompoundDataPlug *p = attributesPlug();
	IECore::CompoundObjectPtr result = new CompoundObject;
	// Since we're not going to modify any existing members (only add new ones),
	// and our result becomes const on returning it, we can directly reference
	// the input members in our result without copying. Be careful not to modify
	// them though!
	result->members() = inputGlobals->members();

	std::string name;
	for( NameValuePlugIterator it( p ); !it.done(); ++it )
	{
		IECore::DataPtr d = p->memberDataAndName( it->get(), name );
		if( d )
		{
			result->members()["attribute:" + name] = d;
		}
	}

	IECore::ConstCompoundDataPtr extraAttributesData = extraAttributesPlug()->getValue();
	const IECore::CompoundDataMap &extraAttributes = extraAttributesData->readable();
	for( IECore::CompoundDataMap::const_iterator it = extraAttributes.begin(), eIt = extraAttributes.end(); it != eIt; ++it )
	{
		result->members()["attribute:" + it->first.string()] = it->second.get();
	}

	return result;
}

bool Attributes::affectsProcessedAttributes( const Gaffer::Plug *input ) const
{
	if( outPlug()->attributesPlug()->getInput() )
	{
		// We've made a pass-through connection
		return false;
	}

	return
		AttributeProcessor::affectsProcessedAttributes( input ) ||
		attributesPlug()->isAncestorOf( input ) ||
		input == globalPlug() ||
		input == extraAttributesPlug()
	;
}

void Attributes::hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( ( attributesPlug()->children().empty() && extraAttributesPlug()->isSetToDefault() ) || globalPlug()->getValue() )
	{
		h = inPlug()->attributesPlug()->hash();
	}
	else
	{
		AttributeProcessor::hashProcessedAttributes( path, context, h );
		attributesPlug()->hash( h );
		extraAttributesPlug()->hash( h );
	}
}

IECore::ConstCompoundObjectPtr Attributes::computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, const IECore::CompoundObject *inputAttributes ) const
{
	const CompoundDataPlug *ap = attributesPlug();
	IECore::ConstCompoundDataPtr extraAttributesData = extraAttributesPlug()->getValue();
	const IECore::CompoundDataMap &extraAttributes = extraAttributesData->readable();

	if( !ap->children().size() && extraAttributes.empty() )
	{
		return inputAttributes;
	}

	/// \todo You might think that we wouldn't have to check this again
	/// because the base class would have used processesAttributes()
	/// to avoid even calling this function. But that isn't the case for
	/// some reason.
	if( globalPlug()->getValue() )
	{
		return inputAttributes;
	}

	CompoundObjectPtr result = new CompoundObject;
	// Since we're not going to modify any existing members (only add new ones),
	// and our result becomes const on returning it, we can directly reference
	// the input members in our result without copying. Be careful not to modify
	// them though!
	result->members() = inputAttributes->members();

	ap->fillCompoundObject( result->members() );

	for( IECore::CompoundDataMap::const_iterator it = extraAttributes.begin(), eIt = extraAttributes.end(); it != eIt; ++it )
	{
		result->members()[it->first] = it->second.get();
	}

	return result;
}

void Attributes::plugSet( Gaffer::Plug *plug )
{
	if( plug == globalPlug() )
	{
		updateInternalConnections();
	}
}

void Attributes::plugInputChanged( Gaffer::Plug *plug )
{
	if( plug == globalPlug() )
	{
		updateInternalConnections();
	}
}

void Attributes::updateInternalConnections()
{
	// Manage internal pass-throughs based on the value of the globalPlug().
	const Plug *p = globalPlug()->source<Gaffer::Plug>();
	boost::tribool global;
	if( p->direction() == Plug::Out && runTimeCast<const ComputeNode>( p->node() ) )
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
