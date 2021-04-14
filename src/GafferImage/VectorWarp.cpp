//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/VectorWarp.h"

#include "GafferImage/FilterAlgo.h"
#include "GafferImage/ImageAlgo.h"

#include "Gaffer/Context.h"

#include "OpenEXR/ImathFun.h"

#include <cmath>

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Engine implementation
//////////////////////////////////////////////////////////////////////////

struct VectorWarp::Engine : public Warp::Engine
{

	Engine( const Box2i &displayWindow, const Box2i &tileBound, const Box2i &validTileBound, ConstFloatVectorDataPtr xData, ConstFloatVectorDataPtr yData, ConstFloatVectorDataPtr aData, VectorMode vectorMode, VectorUnits vectorUnits )
		:	m_displayWindow( displayWindow ),
			m_tileBound( tileBound ),
			m_xData( xData ),
			m_yData( yData ),
			m_aData( aData ),
			m_x( xData->readable() ),
			m_y( yData->readable() ),
			m_a( aData->readable() ),
			m_vectorMode( vectorMode ),
			m_vectorUnits( vectorUnits )
	{
	}

	Imath::V2f inputPixel( const Imath::V2f &outputPixel ) const override
	{
		const V2i outputPixelI( (int)floorf( outputPixel.x ), (int)floorf( outputPixel.y ) );
		const size_t i = BufferAlgo::index( outputPixelI, m_tileBound );
		if( m_a[i] == 0.0f )
		{
			return black;
		}
		else
		{
			V2f result = m_vectorMode == Relative ? outputPixel : V2f( 0.0f );

			result += m_vectorUnits == Screen ?
				screenToPixel( V2f( m_x[i], m_y[i] ) ) :
				V2f( m_x[i], m_y[i] );

			if( !std::isfinite( result[0] ) || !std::isfinite( result[1] ) )
			{
				return black;
			}

			return result;
		}
	}

	private :

		inline V2f screenToPixel( const V2f &vector ) const
		{
			return V2f(
				lerp<float>( m_displayWindow.min.x, m_displayWindow.max.x, vector.x ),
				lerp<float>( m_displayWindow.min.y, m_displayWindow.max.y, vector.y )
			);
		}

		const Box2i m_displayWindow;
		const Box2i m_tileBound;

		ConstFloatVectorDataPtr m_xData;
		ConstFloatVectorDataPtr m_yData;
		ConstFloatVectorDataPtr m_aData;

		const std::vector<float> &m_x;
		const std::vector<float> &m_y;
		const std::vector<float> &m_a;

		const VectorMode m_vectorMode;
		const VectorUnits m_vectorUnits;

};

//////////////////////////////////////////////////////////////////////////
// VectorWarp implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( VectorWarp );

size_t VectorWarp::g_firstPlugIndex = 0;

VectorWarp::VectorWarp( const std::string &name )
	:	Warp( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "vector" ) );
	addChild( new IntPlug( "vectorMode", Gaffer::Plug::In, (int)Absolute, (int)Relative, (int)Absolute ) );
	addChild( new IntPlug( "vectorUnits", Gaffer::Plug::In, (int)Screen, (int)Pixels, (int)Screen ) );

	outPlug()->formatPlug()->setInput( vectorPlug()->formatPlug() );
	outPlug()->dataWindowPlug()->setInput( vectorPlug()->dataWindowPlug() );
}

VectorWarp::~VectorWarp()
{
}

ImagePlug *VectorWarp::vectorPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const ImagePlug *VectorWarp::vectorPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

IntPlug *VectorWarp::vectorModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const IntPlug *VectorWarp::vectorModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

IntPlug *VectorWarp::vectorUnitsPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const IntPlug *VectorWarp::vectorUnitsPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

void VectorWarp::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	Warp::affects( input, outputs );

	if( input == vectorPlug()->deepPlug() )
	{
		outputs.push_back( outPlug()->deepPlug() );
	}
}

bool VectorWarp::affectsEngine( const Gaffer::Plug *input ) const
{
	return
		Warp::affectsEngine( input ) ||
		input == inPlug()->formatPlug() ||
		input == vectorPlug()->channelNamesPlug() ||
		input == vectorPlug()->channelDataPlug() ||
		input == vectorModePlug() ||
		input == vectorUnitsPlug();
}

void VectorWarp::hashEngine( const Imath::V2i &tileOrigin, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Warp::hashEngine( tileOrigin, context, h );

	h.append( tileOrigin );

	ConstStringVectorDataPtr channelNames;

	{
		ImagePlug::GlobalScope c( context );
		channelNames = vectorPlug()->channelNamesPlug()->getValue();
		vectorPlug()->dataWindowPlug()->hash( h );
		inPlug()->formatPlug()->hash( h );
	}


	ImagePlug::ChannelDataScope channelDataScope( context );

	if( ImageAlgo::channelExists( channelNames->readable(), ImageAlgo::channelNameR ) )
	{
		channelDataScope.setChannelName( &ImageAlgo::channelNameR );
		vectorPlug()->channelDataPlug()->hash( h );
	}

	if( ImageAlgo::channelExists( channelNames->readable(), ImageAlgo::channelNameG ) )
	{
		channelDataScope.setChannelName( &ImageAlgo::channelNameG );
		vectorPlug()->channelDataPlug()->hash( h );
	}

	if( ImageAlgo::channelExists( channelNames->readable(), ImageAlgo::channelNameA ) )
	{
		channelDataScope.setChannelName( &ImageAlgo::channelNameA );
		vectorPlug()->channelDataPlug()->hash( h );
	}

	vectorModePlug()->hash( h );
	vectorUnitsPlug()->hash( h );
}

const Warp::Engine *VectorWarp::computeEngine( const Imath::V2i &tileOrigin, const Gaffer::Context *context ) const
{
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );


	Box2i validTileBound;
	ConstStringVectorDataPtr channelNames;
	Box2i displayWindow;

	{
		ImagePlug::GlobalScope c( context );
		validTileBound = BufferAlgo::intersection( tileBound, vectorPlug()->dataWindowPlug()->getValue() );
		channelNames = vectorPlug()->channelNamesPlug()->getValue();
		displayWindow = inPlug()->formatPlug()->getValue().getDisplayWindow();
	}

	ImagePlug::ChannelDataScope channelDataScope( context );

	ConstFloatVectorDataPtr xData = ImagePlug::blackTile();
	if( ImageAlgo::channelExists( channelNames->readable(), ImageAlgo::channelNameR ) )
	{
		channelDataScope.setChannelName( &ImageAlgo::channelNameR );
		xData = vectorPlug()->channelDataPlug()->getValue();
	}

	ConstFloatVectorDataPtr yData = ImagePlug::blackTile();
	if( ImageAlgo::channelExists( channelNames->readable(), ImageAlgo::channelNameG ) )
	{
		channelDataScope.setChannelName( &ImageAlgo::channelNameG );
		yData = vectorPlug()->channelDataPlug()->getValue();
	}

	ConstFloatVectorDataPtr aData = ImagePlug::whiteTile();
	if( ImageAlgo::channelExists( channelNames->readable(), ImageAlgo::channelNameA ) )
	{
		channelDataScope.setChannelName( &ImageAlgo::channelNameA );
		aData = vectorPlug()->channelDataPlug()->getValue();
	}

	if( xData->readable().size() != (unsigned int)ImagePlug::tilePixels() ||
		yData->readable().size() != (unsigned int)ImagePlug::tilePixels() ||
		aData->readable().size() != (unsigned int)ImagePlug::tilePixels() )
	{
		throw IECore::Exception( "VectorWarp::computeEngine : Bad channel data size on vector plug.  Maybe it's deep?" );
	}

	return new Engine(
		displayWindow,
		tileBound,
		validTileBound,
		xData,
		yData,
		aData,
		(VectorMode)vectorModePlug()->getValue(),
		(VectorUnits)vectorUnitsPlug()->getValue()
	);
}

void VectorWarp::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashDeep( parent, context, h );
	h.append( vectorPlug()->deepPlug()->hash() );
}

bool VectorWarp::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( vectorPlug()->deepPlug()->getValue() )
	{
		throw IECore::Exception( "Deep data not supported in input \"vector\"" );
	}
	return false;
}
