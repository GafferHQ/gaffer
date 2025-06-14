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

#include "GafferScene/Options.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/PlugAlgo.h"

#include <boost/algorithm/string/replace.hpp>

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

const InternedString g_defaultValue( "defaultValue" );

} // namespace

GAFFER_NODE_DEFINE_TYPE( Options );

size_t Options::g_firstPlugIndex = 0;

Options::Options( const std::string &name )
	:	GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new CompoundDataPlug( "options" ) );
	addChild( new CompoundObjectPlug( "extraOptions", Plug::In, new IECore::CompoundObject ) );
}

Options::Options( const std::string &name, const std::string &rendererPrefix )
	:	Options( name )
{
	const string targetPattern = fmt::format( "option:{}:*", rendererPrefix );
	for( const auto &target : Metadata::targetsWithMetadata( targetPattern, g_defaultValue ) )
	{
		if( auto valuePlug = MetadataAlgo::createPlugFromMetadata( "value", Plug::Direction::In, Plug::Flags::Default, target ) )
		{
			const std::string optionName = target.string().substr( 7 );
			NameValuePlugPtr optionPlug = new NameValuePlug( optionName, valuePlug, false, boost::replace_all_copy( optionName, ".", "_" ) );
			optionsPlug()->addChild( optionPlug );
		}
	}
}

Options::~Options()
{
}

Gaffer::CompoundDataPlug *Options::optionsPlug()
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex );
}

const Gaffer::CompoundDataPlug *Options::optionsPlug() const
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex );
}

Gaffer::CompoundObjectPlug *Options::extraOptionsPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::CompoundObjectPlug *Options::extraOptionsPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 1 );
}

void Options::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if(
		optionsPlug()->isAncestorOf( input ) ||
		input == extraOptionsPlug()
	)
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void Options::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	optionsPlug()->hash( h );
	extraOptionsPlug()->hash( h );
	hashPrefix( context, h );
}

IECore::ConstCompoundObjectPtr Options::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{
	const CompoundDataPlug *p = optionsPlug();
	IECore::ConstCompoundObjectPtr extraOptions = extraOptionsPlug()->getValue();
	if( !p->children().size() && extraOptions->members().empty() )
	{
		return inputGlobals;
	}

	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	// Since we're not going to modify any existing members (only add new ones),
	// and our result becomes const on returning it, we can directly reference
	// the input members in our result without copying. Be careful not to modify
	// them though!
	result->members() = inputGlobals->members();

	const std::string prefix = computePrefix( context );

	std::string name;
	for( NameValuePlug::Iterator it( p ); !it.done(); ++it )
	{
		IECore::DataPtr d = p->memberDataAndName( it->get(), name );
		if( d )
		{
			result->members()[prefix + name] = d;
		}
	}
	for( const auto &e : extraOptions->members() )
	{
		result->members()[prefix + e.first.string()] = e.second;
	}

	return result;
}

void Options::hashPrefix( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

std::string Options::computePrefix( const Gaffer::Context *context ) const
{
	return "option:";
}
