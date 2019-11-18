//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2015, Nvizible Ltd. All rights reserved.
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

#include "GafferImage/Crop.h"

#include "GafferImage/BufferAlgo.h"
#include "GafferImage/FormatPlug.h"
#include "GafferImage/Offset.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Crop );

size_t Crop::g_firstPlugIndex = 0;

Crop::Crop( const std::string &name )
	:   ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "areaSource", Gaffer::Plug::In, Crop::Area, Crop::Area, Crop::Format ) );
	addChild( new Box2iPlug( "area" ) );
	addChild( new FormatPlug( "format" ) );
	addChild( new BoolPlug( "formatCenter" ) );
	addChild( new BoolPlug( "affectDataWindow", Gaffer::Plug::In, true ) );
	addChild( new BoolPlug( "affectDisplayWindow", Gaffer::Plug::In, true ) );
	addChild( new BoolPlug( "resetOrigin", Gaffer::Plug::In, true ) );

	addChild( new AtomicBox2iPlug( "__cropWindow", Gaffer::Plug::Out ) );
	addChild( new AtomicBox2iPlug( "__cropDataWindow", Gaffer::Plug::Out ) );
	addChild( new V2iPlug( "__offset", Gaffer::Plug::Out ) );

	OffsetPtr offset = new Offset( "__offset" );
	addChild( offset );
	offset->inPlug()->setInput( inPlug() );
	offset->inPlug()->dataWindowPlug()->setInput( cropDataWindowPlug() );
	offset->enabledPlug()->setInput( enabledPlug() );
	offset->offsetPlug()->setInput( offsetPlug() );
	outPlug()->dataWindowPlug()->setInput( offset->outPlug()->dataWindowPlug() );
	outPlug()->channelDataPlug()->setInput( offset->outPlug()->channelDataPlug() );

	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
}

Crop::~Crop()
{
}

Gaffer::IntPlug *Crop::areaSourcePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Crop::areaSourcePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::Box2iPlug *Crop::areaPlug()
{
	return getChild<Box2iPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::Box2iPlug *Crop::areaPlug() const
{
	return getChild<Box2iPlug>( g_firstPlugIndex + 1 );
}

GafferImage::FormatPlug *Crop::formatPlug()
{
	return getChild<FormatPlug>( g_firstPlugIndex + 2 );
}

const GafferImage::FormatPlug *Crop::formatPlug() const
{
	return getChild<FormatPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *Crop::formatCenterPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *Crop::formatCenterPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

Gaffer::BoolPlug *Crop::affectDataWindowPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::BoolPlug *Crop::affectDataWindowPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

Gaffer::BoolPlug *Crop::affectDisplayWindowPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::BoolPlug *Crop::affectDisplayWindowPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 5 );
}

Gaffer::BoolPlug *Crop::resetOriginPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::BoolPlug *Crop::resetOriginPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

Gaffer::AtomicBox2iPlug *Crop::cropWindowPlug()
{
	return getChild<AtomicBox2iPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::AtomicBox2iPlug *Crop::cropWindowPlug() const
{
	return getChild<AtomicBox2iPlug>( g_firstPlugIndex + 7 );
}

Gaffer::AtomicBox2iPlug *Crop::cropDataWindowPlug()
{
	return getChild<AtomicBox2iPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::AtomicBox2iPlug *Crop::cropDataWindowPlug() const
{
	return getChild<AtomicBox2iPlug>( g_firstPlugIndex + 8 );
}

Gaffer::V2iPlug *Crop::offsetPlug()
{
	return getChild<V2iPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::V2iPlug *Crop::offsetPlug() const
{
	return getChild<V2iPlug>( g_firstPlugIndex + 9 );
}

void Crop::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if(
		input == areaSourcePlug() ||
		areaPlug()->isAncestorOf( input ) ||
		formatPlug()->isAncestorOf( input ) ||
		input == formatCenterPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == inPlug()->formatPlug()
	)
	{
		outputs.push_back( cropWindowPlug() );
	}

	if(
		input == cropWindowPlug() ||
		input == affectDisplayWindowPlug() ||
		offsetPlug()->isAncestorOf( input ) ||
		input == inPlug()->formatPlug()
	)
	{
		outputs.push_back( outPlug()->formatPlug() );
	}

	if(
		input == cropWindowPlug() ||
		input == affectDataWindowPlug() ||
		offsetPlug()->isAncestorOf( input ) ||
		input == inPlug()->dataWindowPlug() ||
		input == enabledPlug()
	)
	{
		outputs.push_back( cropDataWindowPlug() );
	}

	if(
		input == affectDisplayWindowPlug() ||
		input == areaSourcePlug() ||
		input == formatCenterPlug() ||
		input == resetOriginPlug() ||
		input == cropWindowPlug()
	)
	{
		outputs.push_back( offsetPlug()->getChild( 0 ) );
		outputs.push_back( offsetPlug()->getChild( 1 ) );
	}

}

void Crop::hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if ( ! affectDisplayWindowPlug()->getValue() )
	{
		// No-op because we are not applying this
		// crop to the display window
		h = inPlug()->formatPlug()->hash();
		return;
	}

	ImageProcessor::hashFormat( parent, context, h );

	inPlug()->formatPlug()->hash( h );
	cropWindowPlug()->hash( h );
	offsetPlug()->hash( h );
}

GafferImage::Format Crop::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if ( ! affectDisplayWindowPlug()->getValue() )
	{
		// No-op because we are not applying this
		// crop to the display window
		return inPlug()->formatPlug()->getValue();
	}

	Imath::Box2i displayWindow = cropWindowPlug()->getValue();
	const Imath::V2i offset = offsetPlug()->getValue();

	displayWindow.max += offset;
	displayWindow.min += offset;

	return GafferImage::Format( displayWindow, inPlug()->formatPlug()->getValue().getPixelAspect() );
}

void Crop::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );

	if ( output == cropWindowPlug() )
	{
		int areaSource = areaSourcePlug()->getValue();

		switch ( areaSource )
		{
			case Crop::DataWindow:
			{
				inPlug()->dataWindowPlug()->hash( h );
				break;
			}
			case Crop::DisplayWindow:
			{
				inPlug()->formatPlug()->hash( h );
				break;
			}
			case Crop::Format:
			{
				formatPlug()->hash( h );
				if( formatCenterPlug()->getValue() )
				{
					inPlug()->formatPlug()->hash( h );
				}
				break;
			}
			default:
			{
				areaPlug()->hash( h );
				break;
			}
		}
	}
	else if ( output == cropDataWindowPlug() )
	{
		if( !enabledPlug()->getValue() )
		{
			h = inPlug()->dataWindowPlug()->hash();
			return;
		}
		inPlug()->dataWindowPlug()->hash( h );
		cropWindowPlug()->hash( h );
		affectDataWindowPlug()->hash( h );
	}
	else if( output->parent<Plug>() == offsetPlug() )
	{
		ImagePlug::GlobalScope c( context );
		affectDisplayWindowPlug()->hash( h );
		resetOriginPlug()->hash( h );
		cropWindowPlug()->hash( h );
		if( areaSourcePlug()->getValue() == Crop::Format && formatCenterPlug()->getValue() )
		{
			inPlug()->formatPlug()->hash( h );
		}
	}
}

void Crop::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if ( output == cropWindowPlug() )
	{
		int areaSource = areaSourcePlug()->getValue();
		Imath::Box2i cropWindow;

		switch ( areaSource )
		{
			case Crop::DataWindow:
			{
				cropWindow = inPlug()->dataWindowPlug()->getValue();
				break;
			}
			case Crop::DisplayWindow:
			{
				cropWindow = inPlug()->formatPlug()->getValue().getDisplayWindow();
				break;
			}
			case Crop::Format:
			{
				cropWindow = formatPlug()->getValue().getDisplayWindow();
				if( formatCenterPlug()->getValue() )
				{
					const Imath::Box2i displayWindow = inPlug()->formatPlug()->getValue().getDisplayWindow();
					Imath::V2i centerOffset( cropWindow.center() - displayWindow.center() );

					cropWindow.min -= centerOffset;
					cropWindow.max -= centerOffset;
				}
				break;
			}
			default:
			{
				cropWindow = areaPlug()->getValue();
				break;
			}
		}

		static_cast<Gaffer::AtomicBox2iPlug *>( output )->setValue( cropWindow );
	}
	else if ( output == cropDataWindowPlug() )
	{
		Box2i result = inPlug()->dataWindowPlug()->getValue();

		if( enabledPlug()->getValue() )
		{
			const Box2i cropWindow = cropWindowPlug()->getValue();
			if( affectDataWindowPlug()->getValue() )
			{
				result = BufferAlgo::intersection( result, cropWindow );
			}
		}

		static_cast<Gaffer::AtomicBox2iPlug *>( output )->setValue( result );
	}
	else if( output->parent<Plug>() == offsetPlug() )
	{
		ImagePlug::GlobalScope c( context );
		V2i offset( 0 );
		if( affectDisplayWindowPlug()->getValue() )
		{
			if( resetOriginPlug()->getValue() )
			{
				offset -= cropWindowPlug()->getValue().min;
			}
			else if( areaSourcePlug()->getValue() == Crop::Format && formatCenterPlug()->getValue() )
			{
				offset -= cropWindowPlug()->getValue().min - formatPlug()->getValue().getDisplayWindow().min;
			}
		}
		static_cast<IntPlug *>( output )->setValue(
			output == offsetPlug()->getChild( 0 ) ? offset[0] : offset[1]
		);
	}
	else
	{
		ImageProcessor::compute( output, context );
	}
}
