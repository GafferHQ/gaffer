//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Context.h"
#include "GafferImage/ChannelDataProcessor.h"

using namespace Gaffer;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( ChannelDataProcessor );

size_t ChannelDataProcessor::g_firstPlugIndex = 0;

ChannelDataProcessor::ChannelDataProcessor( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	
	addChild(
		new ChannelMaskPlug(
			"channels",
			Gaffer::Plug::In,
			inPlug()->channelNamesPlug()->defaultValue(),
			~(Gaffer::Plug::Dynamic | Gaffer::Plug::ReadOnly)
		)
	);
	
}

ChannelDataProcessor::~ChannelDataProcessor()
{
}

GafferImage::ChannelMaskPlug *ChannelDataProcessor::channelMaskPlug()
{
	return getChild<ChannelMaskPlug>( g_firstPlugIndex );
}

const GafferImage::ChannelMaskPlug *ChannelDataProcessor::channelMaskPlug() const
{
	return getChild<ChannelMaskPlug>( g_firstPlugIndex );
}

void ChannelDataProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );
	
	if( input == inPlug()->formatPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == inPlug()->channelNamesPlug()
	)
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );	
	}

	if( input == channelMaskPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );		
	}
}

bool ChannelDataProcessor::channelEnabled( const std::string &channel ) const
{
	if ( !ImageProcessor::channelEnabled( channel ) )
	{
		return false;
	}

	// Grab the intersection of the channels from the "channels" plug and the image input to see which channels we are to operate on.
	IECore::ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
	std::vector<std::string> maskChannels = channelNamesData->readable();
	channelMaskPlug()->maskChannels( maskChannels );

	// Check to see if the channel that we wish to process is masked.
	return ( std::find( maskChannels.begin(), maskChannels.end(), channel ) != maskChannels.end() );
}

IECore::ConstFloatVectorDataPtr ChannelDataProcessor::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IECore::FloatVectorDataPtr outData = inPlug()->channelData( channelName, tileOrigin )->copy();
	processChannelData( context, parent, channelName, outData );
	return outData;
}

void ChannelDataProcessor::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->formatPlug()->hash();
}

void ChannelDataProcessor::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->dataWindowPlug()->hash();
}

void ChannelDataProcessor::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->channelNamesPlug()->hash();
}

GafferImage::Format ChannelDataProcessor::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->formatPlug()->getValue();
}

Imath::Box2i ChannelDataProcessor::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->dataWindowPlug()->getValue();
}

IECore::ConstStringVectorDataPtr ChannelDataProcessor::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inPlug()->channelNamesPlug()->getValue();
}
