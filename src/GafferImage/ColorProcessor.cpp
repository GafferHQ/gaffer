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
#include "Gaffer/StringAlgo.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

namespace
{

const IECore::InternedString g_layerNameKey( "image:colorProcessor:__layerName" );

} // namespace

IE_CORE_DEFINERUNTIMETYPED( ColorProcessor );

size_t ColorProcessor::g_firstPlugIndex = 0;

ColorProcessor::ColorProcessor( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "channels", Plug::In, "[RGB]" ) );

	addChild(
		new ObjectPlug(
			"__colorData",
			Gaffer::Plug::Out,
			new ObjectVector
		)
	);

	// Because our implementation of computeChannelData() is so simple,
	// just copying data out of our intermediate colorDataPlug(), it is
	// actually quicker not to cache the result.
	outPlug()->channelDataPlug()->setFlags( Plug::Cacheable, false );

	// We don't ever want to change the these, so we make pass-through connections.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
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

Gaffer::ObjectPlug *ColorProcessor::colorDataPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::ObjectPlug *ColorProcessor::colorDataPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 1 );
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
		const string &layerName = context->get<string>( g_layerNameKey );

		FloatVectorDataPtr r, g, b;
		{
			ImagePlug::ChannelDataScope channelDataScope( context );
			channelDataScope.setChannelName( ImageAlgo::channelName( layerName, "R" ) );
			r = inPlug()->channelDataPlug()->getValue()->copy();
			channelDataScope.setChannelName( ImageAlgo::channelName( layerName, "G" ) );
			g = inPlug()->channelDataPlug()->getValue()->copy();
			channelDataScope.setChannelName( ImageAlgo::channelName( layerName, "B" ) );
			b = inPlug()->channelDataPlug()->getValue()->copy();
		}

		processColorData( context, r.get(), g.get(), b.get() );

		ObjectVectorPtr result = new ObjectVector();
		result->members().push_back( r );
		result->members().push_back( g );
		result->members().push_back( b );

		static_cast<ObjectPlug *>( output )->setValue( result );
		return;
	}

	ImageProcessor::compute( output, context );
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
		layerScope.set( g_layerNameKey, ImageAlgo::layerName( channel ) );
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
		layerScope.set( g_layerNameKey, ImageAlgo::layerName( channel ) );
		colorData = boost::static_pointer_cast<const ObjectVector>( colorDataPlug()->getValue() );
	}
	return boost::static_pointer_cast<const FloatVectorData>( colorData->members()[ImageAlgo::colorIndex( baseName)] );
}

bool ColorProcessor::affectsColorData( const Gaffer::Plug *input ) const
{
	return input == inPlug()->channelDataPlug();
}

void ColorProcessor::hashColorData( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const string &layerName = context->get<string>( g_layerNameKey );

	ImagePlug::ChannelDataScope channelDataScope( context );
	channelDataScope.setChannelName( ImageAlgo::channelName( layerName, "R" ) );
	inPlug()->channelDataPlug()->hash( h );
	channelDataScope.setChannelName( ImageAlgo::channelName( layerName, "G" ) );
	inPlug()->channelDataPlug()->hash( h );
	channelDataScope.setChannelName( ImageAlgo::channelName( layerName, "B" ) );
	inPlug()->channelDataPlug()->hash( h );
}
