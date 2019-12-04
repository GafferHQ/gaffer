//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/DeleteChannels.h"

#include "IECore/StringAlgo.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;

namespace GafferImage
{

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( DeleteChannels );

size_t DeleteChannels::g_firstPlugIndex = 0;

DeleteChannels::DeleteChannels( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "mode", Plug::In, Delete, Delete, Keep ) );
	addChild( new StringPlug( "channels" ) );

	// Direct pass-through for the things we don't ever change.
	// This not only simplifies our implementation, but it is also
	// faster to compute.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->deepPlug()->setInput( inPlug()->deepPlug() );
	outPlug()->sampleOffsetsPlug()->setInput( inPlug()->sampleOffsetsPlug() );
	outPlug()->channelDataPlug()->setInput( inPlug()->channelDataPlug() );
}

DeleteChannels::~DeleteChannels()
{
}

Gaffer::IntPlug *DeleteChannels::modePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *DeleteChannels::modePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *DeleteChannels::channelsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *DeleteChannels::channelsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

void DeleteChannels::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if(
		input == inPlug()->channelNamesPlug() ||
		input == modePlug() ||
		input == channelsPlug()
	)
	{
		outputs.push_back( outPlug()->channelNamesPlug() );
	}
}

void DeleteChannels::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelNames( output, context, h );

	inPlug()->channelNamesPlug()->hash( h );
	modePlug()->hash( h );
	channelsPlug()->hash( h );
}

IECore::ConstStringVectorDataPtr DeleteChannels::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const Mode mode = static_cast<Mode>( modePlug()->getValue() );
	const string channels = channelsPlug()->getValue();

	ConstStringVectorDataPtr inChannelNamesData = inPlug()->channelNamesPlug()->getValue();
	const vector<string> inChannelNames = inChannelNamesData->readable();

	StringVectorDataPtr resultData = new StringVectorData();
	vector<string> &result = resultData->writable();

	for( vector<string>::const_iterator it = inChannelNames.begin(), eIt = inChannelNames.end(); it != eIt; ++it )
	{
		const bool match = StringAlgo::matchMultiple( *it, channels );
		if( match == ( mode == Keep ) )
		{
			result.push_back( *it );
		}
	}

	return resultData;
}

} // namespace GafferImage
