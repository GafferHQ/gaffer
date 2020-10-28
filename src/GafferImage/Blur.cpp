//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, John Haddon. All rights reserved.
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
//      * Neither the name of Image Engine Design nor the names of
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

#include "GafferImage/Blur.h"

#include "GafferImage/FilterAlgo.h"
#include "GafferImage/Resample.h"

#include "Gaffer/StringPlug.h"

using namespace Imath;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( Blur );

const char *g_blurFilterName = "smoothGaussian";

size_t Blur::g_firstPlugIndex = 0;

Blur::Blur( const std::string &name )
	:   FlatImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	ResamplePtr resample = new Resample( "__resample" );

	addChild( new V2fPlug( "radius", Plug::In, V2f( 0 ), V2f( 0 ) ) );
	addChild( resample->boundingModePlug()->createCounterpart( "boundingMode", Plug::In ) );
	addChild( new BoolPlug( "expandDataWindow" ) );

	addChild( new V2fPlug( "__filterScale", Plug::Out ) );

	addChild( new AtomicBox2iPlug( "__resampledDataWindow", Plug::In, Box2i(), Plug::Default & ~Plug::Serialisable ) );
	addChild( new FloatVectorDataPlug( "__resampledChannelData", Plug::In, ImagePlug::blackTile(), Plug::Default & ~Plug::Serialisable ) );

	addChild( resample );

	resample->inPlug()->setInput( inPlug() );
	resample->filterPlug()->setValue( g_blurFilterName );
	resample->boundingModePlug()->setInput( boundingModePlug() );
	resample->filterScalePlug()->setInput( filterScalePlug() );
	resample->expandDataWindowPlug()->setValue( true );

	resampledDataWindowPlug()->setInput( resample->outPlug()->dataWindowPlug() );
	resampledChannelDataPlug()->setInput( resample->outPlug()->channelDataPlug() );

	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
}

Blur::~Blur()
{
}

Gaffer::V2fPlug *Blur::radiusPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex );
}

const Gaffer::V2fPlug *Blur::radiusPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *Blur::boundingModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *Blur::boundingModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *Blur::expandDataWindowPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *Blur::expandDataWindowPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::V2fPlug *Blur::filterScalePlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::V2fPlug *Blur::filterScalePlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 3 );
}

Gaffer::AtomicBox2iPlug *Blur::resampledDataWindowPlug()
{
	return getChild<AtomicBox2iPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::AtomicBox2iPlug *Blur::resampledDataWindowPlug() const
{
	return getChild<AtomicBox2iPlug>( g_firstPlugIndex + 4 );
}

Gaffer::FloatVectorDataPlug *Blur::resampledChannelDataPlug()
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::FloatVectorDataPlug *Blur::resampledChannelDataPlug() const
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex + 5 );
}

Resample *Blur::resample()
{
	return getChild<Resample>( g_firstPlugIndex + 6 );
}

const Resample *Blur::resample() const
{
	return getChild<Resample>( g_firstPlugIndex + 6 );
}

void Blur::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageProcessor::affects( input, outputs );

	if(
		input == expandDataWindowPlug() ||
		input == resampledDataWindowPlug()
	)
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
	}
	else if( input->parent<V2fPlug>() == radiusPlug() )
	{
		outputs.push_back( filterScalePlug()->getChild<ValuePlug>( input->getName() ) );
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if(
		input == resampledChannelDataPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void Blur::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hash( output, context, h );

	if( output->parent<ValuePlug>() == filterScalePlug() )
	{
		radiusPlug()->getChild<ValuePlug>( output->getName() )->hash( h );
	}
}

void Blur::compute( ValuePlug *output, const Context *context ) const
{
	if( output->parent<ValuePlug>() == filterScalePlug() )
	{
		const OIIO::Filter2D *filter = FilterAlgo::acquireFilter( g_blurFilterName );
		float filterSupport = filter->width();

		// We want the final support of the filter to start from exactly 2 here, so that it just barely
		// doesn't pick up adjacent pixels when radius = 0.  So we multiply by 2 divided by the
		// support width of the filter.  Note that for the smooth gaussian we are actually using, this
		// means we start with a filter that is narrower than the default we would use for resampling:
		// our smooth gaussian has a support width of 3, so we scale it down.  This would produce more
		// aliasing than is expected with a gaussian if we used it for resampling, but because we know
		// that we are just sampling straight back onto the same pixel centers, we know this isn't a
		// problem for blur.

		static_cast<FloatPlug *>( output )->setValue(
			2.0f / filterSupport * ( 1.0f + radiusPlug()->getChild<FloatPlug>( output->getName() )->getValue() )
		);
		return;
	}

	FlatImageProcessor::compute( output, context );
}

void Blur::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( radiusPlug()->getValue() != V2f( 0 ) && expandDataWindowPlug()->getValue() )
	{
		h = resampledDataWindowPlug()->hash();
	}
	else
	{
		h = inPlug()->dataWindowPlug()->hash();
	}
}

Imath::Box2i Blur::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( radiusPlug()->getValue() != V2f( 0 ) && expandDataWindowPlug()->getValue() )
	{
		return resampledDataWindowPlug()->getValue();
	}
	else
	{
		return inPlug()->dataWindowPlug()->getValue();
	}
}

void Blur::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( radiusPlug()->getValue() != V2f( 0 ) )
	{
		h = resampledChannelDataPlug()->hash();
	}
	else
	{
		h = inPlug()->channelDataPlug()->hash();
	}
}

IECore::ConstFloatVectorDataPtr Blur::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( radiusPlug()->getValue() != V2f( 0 ) )
	{
		return resampledChannelDataPlug()->getValue();
	}
	else
	{
		return inPlug()->channelDataPlug()->getValue();
	}
}
