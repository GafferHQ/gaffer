//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/StringPlug.h"

#include "GafferImage/Resize.h"
#include "GafferImage/Sampler.h"
#include "GafferImage/Resample.h"

using namespace Imath;
using namespace Gaffer;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( Resize );

size_t Resize::g_firstPlugIndex = 0;

Resize::Resize( const std::string &name )
	:   ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new FormatPlug( "format" ) );
	addChild( new IntPlug( "fitMode", Plug::In, Horizontal, Horizontal, Distort ) );
	addChild( new StringPlug( "filter" ) );
	addChild( new AtomicBox2fPlug( "__dataWindow", Plug::Out ) );

	// We don't really do much work ourselves - we just
	// defer to an internal Resample node to do the hard
	// work of filtering everything into the right place.

	ResamplePtr resample = new Resample( "__resample" );
	addChild( resample );

	resample->inPlug()->setInput( inPlug() );
	resample->filterPlug()->setInput( filterPlug() );
	resample->dataWindowPlug()->setInput( dataWindowPlug() );
	resample->boundingModePlug()->setValue( Sampler::Clamp );

	outPlug()->dataWindowPlug()->setInput( resample->outPlug()->dataWindowPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );

}

Resize::~Resize()
{
}

GafferImage::FormatPlug *Resize::formatPlug()
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

const GafferImage::FormatPlug *Resize::formatPlug() const
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *Resize::fitModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *Resize::fitModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *Resize::filterPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *Resize::filterPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::AtomicBox2fPlug *Resize::dataWindowPlug()
{
	return getChild<AtomicBox2fPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::AtomicBox2fPlug *Resize::dataWindowPlug() const
{
	return getChild<AtomicBox2fPlug>( g_firstPlugIndex + 3 );
}

Resample *Resize::resample()
{
	return getChild<Resample>( g_firstPlugIndex + 4 );
}

const Resample *Resize::resample() const
{
	return getChild<Resample>( g_firstPlugIndex + 4 );
}

void Resize::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( formatPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->formatPlug() );
		outputs.push_back( dataWindowPlug() );
	}
	else if(
		input == inPlug()->formatPlug() ||
		input == fitModePlug() ||
		input == inPlug()->dataWindowPlug()
	)
	{
		outputs.push_back( dataWindowPlug() );
	}
	else if(
		input == inPlug()->channelDataPlug() ||
		input == filterPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void Resize::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );

	if( output == dataWindowPlug() )
	{
		formatPlug()->hash( h );
		fitModePlug()->hash( h );
		inPlug()->formatPlug()->hash( h );
		inPlug()->dataWindowPlug()->hash( h );
	}
}

void Resize::compute( ValuePlug *output, const Context *context ) const
{
	if( output == dataWindowPlug() )
	{
		const Format inFormat = inPlug()->formatPlug()->getValue();
		const Format outFormat = formatPlug()->getValue();

		const V2f inSize( inFormat.width(), inFormat.height() );
		const V2f outSize( outFormat.width(), outFormat.height() );
		const V2f formatScale = outSize / inSize;

		V2f dataWindowScale( 1 );
		switch( (FitMode)fitModePlug()->getValue() )
		{
			case Horizontal :
				dataWindowScale = V2f( formatScale.x );
				break;
			case Vertical :
				dataWindowScale = V2f( formatScale.y );
				break;
			case Fit :
				dataWindowScale = V2f( std::min( formatScale.x, formatScale.y ) );
				break;
			case Fill :
				dataWindowScale = V2f( std::max( formatScale.x, formatScale.y ) );
				break;
			case Distort :
			default :
				dataWindowScale = formatScale;
				break;
		}

		const V2f dataWindowOffset = ( outSize - ( inSize * dataWindowScale ) ) / 2.0f;
		const Box2i inDataWindow = inPlug()->dataWindowPlug()->getValue();
		Box2f outDataWindow(
			V2f( inDataWindow.min ) * dataWindowScale + dataWindowOffset,
			V2f( inDataWindow.max ) * dataWindowScale + dataWindowOffset
		);

		// It's important that we use floating point data windows in the Resample node
		// so we can accurately represent scaling which produces border pixels without full
		// coverage. In this case, the Resample outputs an integer data window expanded to
		// cover the floating point one fully, and samples the edges appropriately. But
		// floating point error can mean that our data window is a tiny bit above or below the
		// exact integer values the user expects, so we must detect this case and adjust
		// accordingly.
		const float eps = 1e-4;
		if( ceilf( outDataWindow.min.x ) - outDataWindow.min.x < eps )
		{
			outDataWindow.min.x = ceilf( outDataWindow.min.x );
		}
		if( outDataWindow.max.x - floorf( outDataWindow.max.x ) < eps )
		{
			outDataWindow.max.x = floorf( outDataWindow.max.x );
		}
		if( ceilf( outDataWindow.min.y ) - outDataWindow.min.y < eps )
		{
			outDataWindow.min.y = ceilf( outDataWindow.min.y );
		}
		if( outDataWindow.max.y - floorf( outDataWindow.max.y ) < eps )
		{
			outDataWindow.max.y = floorf( outDataWindow.max.y );
		}

		static_cast<AtomicBox2fPlug *>( output )->setValue( outDataWindow );
	}

	ImageProcessor::compute( output, context );
}

void Resize::hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = formatPlug()->hash();
}

GafferImage::Format Resize::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue();
}

void Resize::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( formatPlug()->getValue() == inPlug()->formatPlug()->getValue() )
	{
		h = inPlug()->channelDataPlug()->hash();
	}
	else
	{
		h = resample()->outPlug()->channelDataPlug()->hash();
	}
}

IECore::ConstFloatVectorDataPtr Resize::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( formatPlug()->getValue() == inPlug()->formatPlug()->getValue() )
	{
		return inPlug()->channelDataPlug()->getValue();
	}
	else
	{
		return resample()->outPlug()->channelDataPlug()->getValue();
	}
}
