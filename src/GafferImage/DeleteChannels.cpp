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

using namespace IECore;
using namespace Gaffer;

namespace GafferImage
{

IE_CORE_DEFINERUNTIMETYPED( DeleteChannels );

size_t DeleteChannels::g_firstPlugIndex = 0;

DeleteChannels::DeleteChannels( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "mode", Plug::In, Delete, Delete, Keep ) );

	addChild(
		new ChannelMaskPlug(
			"channels",
			Gaffer::Plug::In,
			inPlug()->channelNamesPlug()->defaultValue()
		)
	);

	// Direct pass-through for the things we don't ever change.
	// This not only simplifies our implementation, but it is also
	// faster to compute.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->deepStatePlug()->setInput( inPlug()->deepStatePlug() );
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

GafferImage::ChannelMaskPlug *DeleteChannels::channelsPlug()
{
	return getChild<ChannelMaskPlug>( g_firstPlugIndex + 1 );
}

const GafferImage::ChannelMaskPlug *DeleteChannels::channelsPlug() const
{
	return getChild<ChannelMaskPlug>( g_firstPlugIndex + 1 );
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
	StringVectorDataPtr result = new StringVectorData();

	int mode( modePlug()->getValue() );
	if( mode == Delete ) // Delete the selected channels
	{
		IECore::ConstStringVectorDataPtr inChannelsData = inPlug()->channelNamesPlug()->getValue();
		std::vector<std::string> inChannels( inChannelsData->readable() );
		IECore::ConstStringVectorDataPtr inSelectionData = channelsPlug()->getValue();
		const std::vector<std::string> &channelSelection( inSelectionData->readable() );

		std::vector<std::string>::iterator it( inChannels.begin() );
		while ( it != inChannels.end() )
		{
			if ( std::find( channelSelection.begin(), channelSelection.end(), (*it) ) != channelSelection.end() )
			{
				it = inChannels.erase( it );
			}
			else
			{
				++it;
			}
		}

		result->writable() = inChannels;
	}
	else // Keep the selected channels
	{
		IECore::ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
		std::vector<std::string> maskChannels( channelNamesData->readable() );
		channelsPlug()->maskChannels( maskChannels );
		result->writable() = maskChannels;
	}
	return result;
}

} // namespace GafferImage
