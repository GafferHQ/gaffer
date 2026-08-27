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

#include "GafferScene/StandardOptions.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/PlugAlgo.h"

#include "boost/container/flat_map.hpp"

using namespace Gaffer;
using namespace GafferScene;

namespace
{

const IECore::InternedString g_defaultValue( "defaultValue" );

const boost::container::flat_map<IECore::InternedString, IECore::ConstDataPtr> g_optionDefaultOverrides = {
	// Override defaults of overscan plugs. Our metadata registered default matches
	// the true default value of the option, but for legacy reasons these plugs
	// default to 0.1.
	{ "render:overscanTop", new IECore::FloatData( 0.1 ) },
	{ "render:overscanBottom", new IECore::FloatData( 0.1 ) },
	{ "render:overscanLeft", new IECore::FloatData( 0.1 ) },
	{ "render:overscanRight", new IECore::FloatData( 0.1 ) },
};

} // namespace

GAFFER_NODE_DEFINE_TYPE( StandardOptions );

StandardOptions::StandardOptions( const std::string &name )
	:	Options( name )
{

	for( const auto &target : Metadata::targetsWithMetadata( "option:render:* option:sampleMotion", g_defaultValue ) )
	{
		if( auto valuePlug = MetadataAlgo::createPlugFromMetadata( "value", Plug::Direction::In, Plug::Flags::Default, target ) )
		{
			const std::string optionName = target.string().substr( 7 );
			NameValuePlugPtr optionPlug = new NameValuePlug( optionName, valuePlug, false, optionName );
			optionsPlug()->addChild( optionPlug );
		}
	}

	for( auto &p : NameValuePlug::Range( *optionsPlug() ) )
	{
		auto it = g_optionDefaultOverrides.find( p->getName() );
		if( it != g_optionDefaultOverrides.end() )
		{
			Gaffer::PlugAlgo::setValueFromData( p->valuePlug<ValuePlug>(), it->second.get() );
			p->valuePlug<ValuePlug>()->resetDefault();
		}
	}

}

StandardOptions::~StandardOptions()
{
}
