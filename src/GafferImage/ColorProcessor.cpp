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

#include "GafferImage/ColorProcessor.h"

#include "GafferImage/ImageAlgo.h"

#include "Gaffer/Context.h"

#include "IECore/StringAlgo.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

namespace
{

const IECore::InternedString g_layerNameKey( "image:colorProcessor:__layerName" );

} // namespace

GAFFER_NODE_DEFINE_TYPE( ColorProcessor );

size_t ColorProcessor::g_firstPlugIndex = 0;

ColorProcessor::ColorProcessor( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "channels", Plug::In, "[RGB]" ) );
	addChild( new BoolPlug( "processUnpremultiplied", Plug::In, false ) );

	addChild(
		new ObjectPlug(
			"__colorData",
			Gaffer::Plug::Out,
			new ObjectVector
		)
	);

	// We don't ever want to change the these, so we make pass-through connections.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->deepPlug()->setInput( inPlug()->deepPlug() );
	outPlug()->sampleOffsetsPlug()->setInput( inPlug()->sampleOffsetsPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
	outPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );
}

ColorProcessor::~ColorProcessor()
{
}



Gaffer::StringPlug *ColorProcessor::channelsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *ColorProcessor::channelsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *ColorProcessor::processUnpremultipliedPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *ColorProcessor::processUnpremultipliedPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::ObjectPlug *ColorProcessor::colorDataPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::ObjectPlug *ColorProcessor::colorDataPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 2 );
}

void ColorProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( affectsColorData( input ) )
	{
		outputs.push_back( colorDataPlug() );
	}
	else if(
		input == channelsPlug() ||
		input == colorDataPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void ColorProcessor::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );

	if( output == colorDataPlug() )
	{
		hashColorData( context, h );
	}
}

void ColorProcessor::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == colorDataPlug() )
	{
		ConstStringVectorDataPtr channelNamesData;
		bool unpremult;
		{
			ImagePlug::GlobalScope globalScope( context );
			channelNamesData = inPlug()->channelNamesPlug()->getValue();
			unpremult = processUnpremultipliedPlug()->getValue();
		}
		const vector<string> &channelNames = channelNamesData->readable();

		const string &layerName = context->get<string>( g_layerNameKey );

		FloatVectorDataPtr rgb[3];
		ConstFloatVectorDataPtr alpha;
		int samples = -1;
		{
			ImagePlug::ChannelDataScope channelDataScope( context );

			if( unpremult && ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameA ) )
			{
				channelDataScope.setChannelName( &ImageAlgo::channelNameA );
				alpha = inPlug()->channelDataPlug()->getValue();
			}

			int i = 0;
			for( const auto &baseName : { "R", "G", "B" } )
			{
				string channelName = ImageAlgo::channelName( layerName, baseName );
				if( ImageAlgo::channelExists( channelNames, channelName ) )
				{
					channelDataScope.setChannelName( &channelName );
					rgb[i] = inPlug()->channelDataPlug()->getValue()->copy();

					samples = rgb[i]->readable().size();

					if( unpremult && alpha )
					{
						const float *A = &alpha->readable().front();
						float *C = &rgb[i]->writable().front();
						for( int j = 0; j < samples; j++ )
						{
							if( *A != 0 )
							{
								*C /= *A;
							}
							A++;
							C++;
						}
					}
				}
				else
				{
					rgb[i] = nullptr;
				}
				i++;
			}

			if( samples == -1 )
			{
				throw IECore::Exception( "Cannot evaluate color data plug with no source channels" );
			}

			for( int k = 0; k < 3; k++ )
			{
				if( !rgb[k] )
				{
					rgb[k] = new FloatVectorData();
					rgb[k]->writable().resize( samples, 0.0f );
				}
			}

		}

		processColorData( context, rgb[0].get(), rgb[1].get(), rgb[2].get() );

		if( unpremult && alpha )
		{
			for( int i = 0; i < 3; i++ )
			{
				if( unpremult && alpha )
				{
					const float *A = &alpha->readable().front();
					float *C = &rgb[i]->writable().front();
					for( int j = 0; j < samples; j++ )
					{
						// Pixels with no alpha aren't touched by either the unpremult or repremult
						if( *A != 0 )
						{
							*C *= *A;
						}
						A++;
						C++;
					}
				}
			}
		}

		ObjectVectorPtr result = new ObjectVector();
		result->members().push_back( rgb[0] );
		result->members().push_back( rgb[1] );
		result->members().push_back( rgb[2] );

		static_cast<ObjectPlug *>( output )->setValue( result );
		return;
	}

	ImageProcessor::compute( output, context );
}

Gaffer::ValuePlug::CachePolicy ColorProcessor::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == outPlug()->channelDataPlug() )
	{
		// Because our implementation of computeChannelData() is so simple,
		// just copying data out of our intermediate colorDataPlug(), it is
		// actually quicker not to cache the result.
		return ValuePlug::CachePolicy::Uncached;
	}
	return ImageProcessor::computeCachePolicy( output );
}

void ColorProcessor::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const std::string &channels = channelsPlug()->getValue();
	const std::string &channel = context->get<std::string>( ImagePlug::channelNameContextName );
	const std::string &baseName = ImageAlgo::baseName( channel );

	if(
		( baseName != "R" && baseName != "G" && baseName != "B" ) ||
		!StringAlgo::matchMultiple( channel, channels )
	)
	{
		// Auxiliary channel, or not in channel mask. Pass through.
		h = inPlug()->channelDataPlug()->hash();
		return;
	}

	ImageProcessor::hashChannelData( output, context, h );
	h.append( baseName );
	{
		Context::EditableScope layerScope( context );
		std::string layerNameStr = ImageAlgo::layerName( channel );
		layerScope.set( g_layerNameKey, &layerNameStr );
		colorDataPlug()->hash( h );
	}
}

IECore::ConstFloatVectorDataPtr ColorProcessor::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const std::string &channels = channelsPlug()->getValue();
	const std::string &channel = context->get<std::string>( ImagePlug::channelNameContextName );
	const std::string &baseName = ImageAlgo::baseName( channel );

	if(
		( baseName != "R" && baseName != "G" && baseName != "B" ) ||
		!StringAlgo::matchMultiple( channel, channels )
	)
	{
		// Auxiliary channel, or not in channel mask. Pass through.
		return inPlug()->channelDataPlug()->getValue();
	}

	ConstObjectVectorPtr colorData;
	{
		Context::EditableScope layerScope( context );
		std::string layerNameStr = ImageAlgo::layerName( channel );
		layerScope.set( g_layerNameKey, &layerNameStr );
		colorData = boost::static_pointer_cast<const ObjectVector>( colorDataPlug()->getValue() );
	}
	return boost::static_pointer_cast<const FloatVectorData>( colorData->members()[ImageAlgo::colorIndex( baseName)] );
}

bool ColorProcessor::affectsColorData( const Gaffer::Plug *input ) const
{
	return input == inPlug()->channelDataPlug() || input == inPlug()->channelNamesPlug() || input == processUnpremultipliedPlug();
}

void ColorProcessor::hashColorData( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ConstStringVectorDataPtr channelNamesData;
	bool unpremult;
	{
		ImagePlug::GlobalScope globalScope( context );
		channelNamesData = inPlug()->channelNamesPlug()->getValue();
		unpremult = processUnpremultipliedPlug()->getValue();
	}
	const vector<string> &channelNames = channelNamesData->readable();

	const string &layerName = context->get<string>( g_layerNameKey );

	ImagePlug::ChannelDataScope channelDataScope( context );
	for( const auto &baseName : { "R", "G", "B" } )
	{
		string channelName = ImageAlgo::channelName( layerName, baseName );
		if( ImageAlgo::channelExists( channelNames, channelName ) )
		{
			channelDataScope.setChannelName( &channelName );
			inPlug()->channelDataPlug()->hash( h );
		}
		else
		{
			ImagePlug::blackTile()->hash( h );
		}
	}

	if( unpremult && ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameA ) )
	{
		channelDataScope.setChannelName( &ImageAlgo::channelNameA );
		inPlug()->channelDataPlug()->hash( h );
	}
}
