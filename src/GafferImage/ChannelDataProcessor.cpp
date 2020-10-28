//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/ChannelDataProcessor.h"

#include "GafferImage/ImageAlgo.h"

#include "IECore/StringAlgo.h"

using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( ChannelDataProcessor );

size_t ChannelDataProcessor::g_firstPlugIndex = 0;

ChannelDataProcessor::ChannelDataProcessor( const std::string &name, bool hasUnpremultPlug )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "channels", Gaffer::Plug::In, "[RGB]" ) );
	m_hasUnpremultPlug = hasUnpremultPlug;
	if( m_hasUnpremultPlug )
	{
		addChild( new BoolPlug( "processUnpremultiplied", Gaffer::Plug::In, false ) );
	}

	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->deepPlug()->setInput( inPlug()->deepPlug() );
	outPlug()->sampleOffsetsPlug()->setInput( inPlug()->sampleOffsetsPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
}

ChannelDataProcessor::~ChannelDataProcessor()
{
}

Gaffer::StringPlug *ChannelDataProcessor::channelsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *ChannelDataProcessor::channelsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *ChannelDataProcessor::processUnpremultipliedPlug()
{
	if( !m_hasUnpremultPlug )
	{
		throw IECore::Exception( "No processUnpremultiplied plug" );
	}
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *ChannelDataProcessor::processUnpremultipliedPlug() const
{
	if( !m_hasUnpremultPlug )
	{
		throw IECore::Exception( "No processUnpremultiplied plug" );
	}
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

void ChannelDataProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if(
		input == inPlug()->channelDataPlug() ||
		input == channelsPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}

	if( m_hasUnpremultPlug && input == processUnpremultipliedPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

bool ChannelDataProcessor::channelEnabled( const std::string &channel ) const
{
	if( !ImageProcessor::channelEnabled( channel ) )
	{
		return false;
	}

	return IECore::StringAlgo::matchMultiple( channel, channelsPlug()->getValue() );
}

void ChannelDataProcessor::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelData( output, context, h );

	inPlug()->channelDataPlug()->hash( h );

	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );


	IECore::ConstStringVectorDataPtr channelNamesData;
	bool unpremult = false;
	bool repremultByProcessedAlpha = false;
	if( m_hasUnpremultPlug && channelName != "A" )
	{
		ImagePlug::GlobalScope globalScope( context );
		unpremult = processUnpremultipliedPlug()->getValue();
		if( unpremult )
		{
			channelNamesData = inPlug()->channelNamesPlug()->getValue();
			repremultByProcessedAlpha = channelEnabled( "A" );
		}
	}

	h.append( unpremult );
	if( unpremult && ImageAlgo::channelExists( channelNamesData->readable(), "A" ) )
	{
		ImagePlug::ChannelDataScope s( context );
		s.setChannelName( "A" );
		inPlug()->channelDataPlug()->hash( h );
		if( repremultByProcessedAlpha )
		{
			outPlug()->channelDataPlug()->hash( h );
		}
	}
}


IECore::ConstFloatVectorDataPtr ChannelDataProcessor::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IECore::FloatVectorDataPtr outData = inPlug()->channelData( channelName, tileOrigin )->copy();

	IECore::ConstStringVectorDataPtr channelNamesData;
	bool unpremult = false;
	bool repremultByProcessedAlpha = false;
	if( m_hasUnpremultPlug && channelName != "A" )
	{
		ImagePlug::GlobalScope globalScope( context );
		unpremult = processUnpremultipliedPlug()->getValue();
		if( unpremult )
		{
			channelNamesData = inPlug()->channelNamesPlug()->getValue();
			repremultByProcessedAlpha = channelEnabled( "A" );
		}
	}

	IECore::ConstFloatVectorDataPtr alphaData;
	IECore::ConstFloatVectorDataPtr postAlphaData;
	if( unpremult && ImageAlgo::channelExists( channelNamesData->readable(), "A" ) )
	{
		ImagePlug::ChannelDataScope s( context );
		s.setChannelName( "A" );
		alphaData = inPlug()->channelDataPlug()->getValue();
		if( repremultByProcessedAlpha )
		{
			postAlphaData = outPlug()->channelDataPlug()->getValue();
		}
		else
		{
			postAlphaData = alphaData;
		}

		int size = alphaData->readable().size();
		const float *A = &alphaData->readable().front();
		float *O = &outData->writable().front();
		for( int j = 0; j < size; j++ )
		{
			if( *A != 0 )
			{
				*O /= *A;
			}
			A++;
			O++;
		}

	}
	processChannelData( context, parent, channelName, outData );
	if( unpremult && postAlphaData )
	{
		int size = postAlphaData->readable().size();
		const float *A = &postAlphaData->readable().front();
		float *O = &outData->writable().front();

		if( repremultByProcessedAlpha )
		{
			const float *preA = &alphaData->readable().front();
			for( int j = 0; j < size; j++ )
			{
				if( ! ( *A == 0 && *preA == 0 ) )
				{
					*O *= *A;
				}
				A++;
				O++;
				preA++;
			}
		}
		else
		{
			for( int j = 0; j < size; j++ )
			{
				if( *A != 0 )
				{
					*O *= *A;
				}
				A++;
				O++;
			}
		}

	}
	return outData;
}
