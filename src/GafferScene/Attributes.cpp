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

#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/PlugAlgo.h"

#include <boost/algorithm/string/replace.hpp>
#include "boost/bind/bind.hpp"
#include "boost/logic/tribool.hpp"

using namespace std;
using namespace boost::placeholders;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

const InternedString g_defaultValue( "defaultValue" );

} // namespace

GAFFER_NODE_DEFINE_TYPE( Attributes );

size_t Attributes::g_firstPlugIndex = 0;

Attributes::Attributes( const std::string &name )
	:	AttributeProcessor( name, PathMatcher::EveryMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new CompoundDataPlug( "attributes" ) );
	addChild( new CompoundObjectPlug( "extraAttributes", Plug::In, new IECore::CompoundObject ) );
}


Attributes::Attributes( const std::string &name, const std::string &rendererPrefix )
	:	Attributes( name )
{
	const string targetPattern = fmt::format( "attribute:{}:*", rendererPrefix );
	for( const auto &target : Metadata::targetsWithMetadata( targetPattern, g_defaultValue ) )
	{
		if( auto valuePlug = MetadataAlgo::createPlugFromMetadata( "value", Plug::Direction::In, Plug::Flags::Default, target ) )
		{
			const std::string attributeName = target.string().substr( 10 );
			NameValuePlugPtr attributePlug = new NameValuePlug( attributeName, valuePlug, false, boost::replace_all_copy( attributeName, ".", "_" ) );
			attributesPlug()->addChild( attributePlug );
		}
	}
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

Gaffer::CompoundObjectPlug *Attributes::extraAttributesPlug()
{
	return getChild<Gaffer::CompoundObjectPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::CompoundObjectPlug *Attributes::extraAttributesPlug() const
{
	return getChild<Gaffer::CompoundObjectPlug>( g_firstPlugIndex + 1 );
}
bool Attributes::affectsProcessedAttributes( const Gaffer::Plug *input ) const
{
	return
		AttributeProcessor::affectsProcessedAttributes( input ) ||
		attributesPlug()->isAncestorOf( input ) ||
		input == extraAttributesPlug()
	;
}

void Attributes::hashProcessedAttributes( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( !attributesPlug()->children().size() && extraAttributesPlug()->isSetToDefault() )
	{
		return;
	}

	AttributeProcessor::hashProcessedAttributes( context, h );
	attributesPlug()->hash( h );
	extraAttributesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr Attributes::computeProcessedAttributes( const Gaffer::Context *context, const IECore::CompoundObject *inputAttributes ) const
{
	const CompoundDataPlug *ap = attributesPlug();
	IECore::ConstCompoundObjectPtr extraAttributes = extraAttributesPlug()->getValue();
	if( !ap->children().size() && extraAttributes->members().empty() )
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
	for( const auto &e : extraAttributes->members() )
	{
		result->members()[e.first] = e.second;
	}

	return result;
}
