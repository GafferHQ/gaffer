//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2013, Luke Goddard. All rights reserved.
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

#include "boost/bind.hpp"

#include "GafferImage/Crop.h"
#include "GafferImage/Sampler.h"

using namespace Gaffer;
using namespace IECore;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( Crop );

size_t Crop::g_firstPlugIndex = 0;

Crop::Crop( const std::string &name )
	:   ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "areaSource", Gaffer::Plug::In, Crop::DisplayWindow ) );
	addChild( new Box2iPlug( "area" ) );
	addChild( new BoolPlug( "affectDataWindow", Gaffer::Plug::In, true ) );
	addChild( new BoolPlug( "affectDisplayWindow", Gaffer::Plug::In, false ) );

	addChild( new AtomicBox2iPlug( "__cropWindow", Gaffer::Plug::Out ) );

	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
	outPlug()->channelDataPlug()->setInput( inPlug()->channelDataPlug() );
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
	return getChild<Box2iPlug>( g_firstPlugIndex+1 );
}

const Gaffer::Box2iPlug *Crop::areaPlug() const
{
	return getChild<Box2iPlug>( g_firstPlugIndex+1 );
}

Gaffer::BoolPlug *Crop::affectDataWindowPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex+2 );
}

const Gaffer::BoolPlug *Crop::affectDataWindowPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex+2 );
}

Gaffer::BoolPlug *Crop::affectDisplayWindowPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex+3 );
}

const Gaffer::BoolPlug *Crop::affectDisplayWindowPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex+3 );
}

Gaffer::AtomicBox2iPlug *Crop::cropWindowPlug()
{
	return getChild<AtomicBox2iPlug>( g_firstPlugIndex+4 );
}

const Gaffer::AtomicBox2iPlug *Crop::cropWindowPlug() const
{
	return getChild<AtomicBox2iPlug>( g_firstPlugIndex+4 );
}

void Crop::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if ( areaPlug()->isAncestorOf( input ) ||
	     input == areaSourcePlug() )
	{
		outputs.push_back( cropWindowPlug() );
	}
	else if ( input == cropWindowPlug() ||
	          input == affectDataWindowPlug() ||
	          input == affectDisplayWindowPlug() ||
	          input == inPlug()->dataWindowPlug() )
	{
		outputs.push_back( outPlug()->formatPlug() );
		outputs.push_back( outPlug()->dataWindowPlug() );
	}
}

void Crop::hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	bool affectDisplayWindow = affectDisplayWindowPlug()->getValue();

	if ( ! affectDisplayWindow )
	{
		// No-op because we are not applying this
		// crop to the display window
		h = inPlug()->formatPlug()->hash();
		return;
	}

	Format inFormat = inPlug()->formatPlug()->getValue();

	Imath::Box2i cropWindow = cropWindowPlug()->getValue();

	Format newFormat( cropWindow, inFormat.getPixelAspect() );

	if ( inFormat == newFormat )
	{
		// No-op because the resulting format will
		// be identical to the input format
		h = inPlug()->formatPlug()->hash();
		return;
	}

	ImageProcessor::hashFormat( parent, context, h );

	cropWindowPlug()->hash( h );
}

GafferImage::Format Crop::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	bool affectDisplayWindow = affectDisplayWindowPlug()->getValue();

	if ( ! affectDisplayWindow )
	{
		// No-op because we are not applying this
		// crop to the display window
		return inPlug()->formatPlug()->getValue();
	}

	Format inFormat = inPlug()->formatPlug()->getValue();

	Imath::Box2i cropWindow = cropWindowPlug()->getValue();

	return Format( cropWindow, inFormat.getPixelAspect() );
}


void Crop::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	bool affectDataWindow = affectDataWindowPlug()->getValue();

	if ( ! affectDataWindow )
	{
		// No-op because we are not applying this
		// crop to the data window
		h = inPlug()->dataWindowPlug()->hash();
		return;
	}

	Imath::Box2i cropWindow = cropWindowPlug()->getValue();
	Imath::Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();

	if ( dataWindow.min.x >= cropWindow.min.x &&
		 dataWindow.min.y >= cropWindow.min.y &&
		 dataWindow.max.x <= cropWindow.max.x &&
		 dataWindow.max.y <= cropWindow.max.y )
	{
		// No-op because the data window is wholly
		// contained inside the specified area
		h = inPlug()->dataWindowPlug()->hash();
		return;
	}

	ImageProcessor::hashDataWindow( parent, context, h );

	cropWindowPlug()->hash( h );
}

Imath::Box2i Crop::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	bool affectDataWindow = affectDataWindowPlug()->getValue();

	if ( ! affectDataWindow )
	{
		// No-op because we are not applying this
		// crop to the data window
		return inPlug()->dataWindowPlug()->getValue();
	}

	Imath::Box2i cropWindow = cropWindowPlug()->getValue();
	Imath::Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();

	return Imath::Box2i( Imath::V2i( std::max( dataWindow.min.x, cropWindow.min.x ),
									 std::max( dataWindow.min.y, cropWindow.min.y ) ),
						 Imath::V2i( std::min( dataWindow.max.x, cropWindow.max.x ),
									 std::min( dataWindow.max.y, cropWindow.max.y ) ) );
}

void Crop::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if ( output == cropWindowPlug() )
	{
		int areaSource = areaSourcePlug()->getValue();

		switch ( areaSource )
		{
			case DataWindow:
			{
				inPlug()->dataWindowPlug()->hash( h );
				break;
			}
			case DisplayWindow:
			{
				inPlug()->formatPlug()->hash( h );
				break;
			}
			default:
			{
				areaPlug()->hash( h );
				break;
			}
		}
	}
	else
	{
		ImageProcessor::hash( output, context, h );
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
			case DataWindow:
			{
				cropWindow = inPlug()->dataWindowPlug()->getValue();
				break;
			}
			case DisplayWindow:
			{
				cropWindow = inPlug()->formatPlug()->getValue().getDisplayWindow();
				break;
			}
			default:
			{
				cropWindow = areaPlug()->getValue();
				// Because we are treating the areaPlug as exclusive, but the
				// cropWindow is inclusive, need to subtract 1 from the max
				// values.
				cropWindow.max -= Imath::V2i( 1 );
				break;
			}
		}

		static_cast<Gaffer::AtomicBox2iPlug *>( output )->setValue( cropWindow );
	}
	else
	{
		ImageProcessor::compute( output, context );
	}
}

