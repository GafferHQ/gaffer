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

#include "GafferScene/StandardAttributes.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"

using namespace Gaffer;
using namespace GafferScene;

namespace
{

const IECore::InternedString g_defaultValue( "defaultValue" );
const std::string g_metadataTargets(
	"attribute:scene:visible attribute:doubleSided attribute:render:* attribute:gaffer:* " \
	"attribute:linkedLights attribute:shadowedLights attribute:filteredLights"
);

} // namespace

GAFFER_NODE_DEFINE_TYPE( StandardAttributes );

StandardAttributes::StandardAttributes( const std::string &name )
	:	Attributes( name )
{

	for( const auto &target : Metadata::targetsWithMetadata( g_metadataTargets, g_defaultValue ) )
	{
		if( auto valuePlug = MetadataAlgo::createPlugFromMetadata( "value", Plug::Direction::In, Plug::Flags::Default, target ) )
		{
			const std::string attributeName = target.string().substr( 10 );
			NameValuePlugPtr attributePlug = new NameValuePlug( attributeName, valuePlug, false, attributeName );
			attributesPlug()->addChild( attributePlug );
		}
	}

}

StandardAttributes::~StandardAttributes()
{
}
