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

#include "OpenEXR/ImathFun.h"

#include "Gaffer/Context.h"

#include "GafferImage/ImageAlgo.h"
#include "GafferImage/UVWarp.h"
#include "GafferImage/FilterAlgo.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Engine implementation
//////////////////////////////////////////////////////////////////////////

struct UVWarp::Engine : public Warp::Engine
{

	Engine( const Box2i &displayWindow, const Box2i &tileBound, const Box2i &validTileBound, ConstFloatVectorDataPtr uData, ConstFloatVectorDataPtr vData, ConstFloatVectorDataPtr aData, VectorMode vectorMode, VectorUnits vectorUnits )
		:	m_displayWindow( displayWindow ),
			m_tileBound( tileBound ),
			m_uData( uData ),
			m_vData( vData ),
			m_aData( aData ),
			m_u( uData->readable() ),
			m_v( vData->readable() ),
			m_a( aData->readable() ),
			m_vectorMode( vectorMode ),
			m_vectorUnits( vectorUnits )
	{
	}

	virtual Imath::V2f inputPixel( const Imath::V2f &outputPixel ) const
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
				uvToPixel( V2f( m_u[i], m_v[i] ) ) :
				V2f( m_u[i], m_v[i] );
				
			return result;
		}
	}

	private :

		inline V2f uvToPixel( const V2f &uv ) const
		{
			return V2f(
				lerp<float>( m_displayWindow.min.x, m_displayWindow.max.x, uv.x ),
				lerp<float>( m_displayWindow.min.y, m_displayWindow.max.y, uv.y )
			);
		}

		const Box2i m_displayWindow;
		const Box2i m_tileBound;

		ConstFloatVectorDataPtr m_uData;
		ConstFloatVectorDataPtr m_vData;
		ConstFloatVectorDataPtr m_aData;

		const std::vector<float> &m_u;
		const std::vector<float> &m_v;
		const std::vector<float> &m_a;

		const VectorMode m_vectorMode;
		const VectorUnits m_vectorUnits;

};

//////////////////////////////////////////////////////////////////////////
// UVWarp implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( UVWarp );

size_t UVWarp::g_firstPlugIndex = 0;

UVWarp::UVWarp( const std::string &name )
	:	Warp( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "uv" ) );
	addChild( new IntPlug( "vectorMode", Gaffer::Plug::In, (int)Absolute, (int)Relative, (int)Absolute ) );
	addChild( new IntPlug( "vectorUnits", Gaffer::Plug::In, (int)Screen, (int)Pixels, (int)Screen ) );

	outPlug()->formatPlug()->setInput( uvPlug()->formatPlug() );
	outPlug()->dataWindowPlug()->setInput( uvPlug()->dataWindowPlug() );
}

UVWarp::~UVWarp()
{
}

ImagePlug *UVWarp::uvPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const ImagePlug *UVWarp::uvPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

IntPlug *UVWarp::vectorModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const IntPlug *UVWarp::vectorModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

IntPlug *UVWarp::vectorUnitsPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const IntPlug *UVWarp::vectorUnitsPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

bool UVWarp::affectsEngine( const Gaffer::Plug *input ) const
{
	return
		Warp::affectsEngine( input ) ||
		input == inPlug()->formatPlug() ||
		input == uvPlug()->channelNamesPlug() ||
		input == uvPlug()->channelDataPlug() ||
		input == vectorModePlug() ||
		input == vectorUnitsPlug();
}

void UVWarp::hashEngine( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Warp::hashEngine( channelName, tileOrigin, context, h );

	h.append( tileOrigin );
	uvPlug()->dataWindowPlug()->hash( h );

	ConstStringVectorDataPtr channelNames = uvPlug()->channelNamesPlug()->getValue();

	ContextPtr tmpContext = new Context( *context, Context::Borrowed );
	Context::Scope scopedContext( tmpContext.get() );

	if( ImageAlgo::channelExists( channelNames->readable(), "R" ) )
	{
		tmpContext->set<std::string>( ImagePlug::channelNameContextName, "R" );
		uvPlug()->channelDataPlug()->hash( h );
	}

	if( ImageAlgo::channelExists( channelNames->readable(), "G" ) )
	{
		tmpContext->set<std::string>( ImagePlug::channelNameContextName, "G" );
		uvPlug()->channelDataPlug()->hash( h );
	}

	if( ImageAlgo::channelExists( channelNames->readable(), "A" ) )
	{
		tmpContext->set<std::string>( ImagePlug::channelNameContextName, "A" );
		uvPlug()->channelDataPlug()->hash( h );
	}

	inPlug()->formatPlug()->hash( h );

	vectorModePlug()->hash( h );
	vectorUnitsPlug()->hash( h );
}

const Warp::Engine *UVWarp::computeEngine( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context ) const
{
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i validTileBound = BufferAlgo::intersection( tileBound, uvPlug()->dataWindowPlug()->getValue() );

	ConstStringVectorDataPtr channelNames = uvPlug()->channelNamesPlug()->getValue();

	ContextPtr tmpContext = new Context( *context, Context::Borrowed );
	Context::Scope scopedContext( tmpContext.get() );

	ConstFloatVectorDataPtr uData = ImagePlug::blackTile();
	if( ImageAlgo::channelExists( channelNames->readable(), "R" ) )
	{
		tmpContext->set<std::string>( ImagePlug::channelNameContextName, "R" );
		uData = uvPlug()->channelDataPlug()->getValue();
	}

	ConstFloatVectorDataPtr vData = ImagePlug::blackTile();
	if( ImageAlgo::channelExists( channelNames->readable(), "G" ) )
	{
		tmpContext->set<std::string>( ImagePlug::channelNameContextName, "G" );
		vData = uvPlug()->channelDataPlug()->getValue();
	}

	ConstFloatVectorDataPtr aData = ImagePlug::whiteTile();
	if( ImageAlgo::channelExists( channelNames->readable(), "A" ) )
	{
		tmpContext->set<std::string>( ImagePlug::channelNameContextName, "A" );
		aData = uvPlug()->channelDataPlug()->getValue();
	}

	return new Engine(
		inPlug()->formatPlug()->getValue().getDisplayWindow(),
		tileBound,
		validTileBound,
		uData,
		vData,
		aData,
		(VectorMode)vectorModePlug()->getValue(),
		(VectorUnits)vectorUnitsPlug()->getValue()
	);
}
