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

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Engine implementation
//////////////////////////////////////////////////////////////////////////

struct UVWarp::Engine : public Warp::Engine
{

	Engine( const Box2i &displayWindow, const Box2i &tileBound, const Box2i &validTileBound, ConstFloatVectorDataPtr uData, ConstFloatVectorDataPtr vData, ConstFloatVectorDataPtr aData )
		:	m_displayWindow( displayWindow ),
			m_tileBound( tileBound ),
			m_uData( uData ),
			m_vData( vData ),
			m_aData( aData ),
			m_u( uData->readable() ),
			m_v( vData->readable() ),
			m_a( aData->readable() )
	{
		V2i oP;
		for( oP.y = validTileBound.min.y; oP.y < validTileBound.max.y; ++oP.y )
		{
			size_t i = index( V2i( validTileBound.min.x, oP.y ), tileBound );
			for( oP.x = validTileBound.min.x; oP.x < validTileBound.max.x; ++oP.x, ++i )
			{
				if( m_a[i] == 0.0f )
				{
					continue;
				}
				const V2f iP = uvToPixel( V2f( m_u[i], m_v[i] ) );
				m_inputWindow.extendBy( iP );
			}
		}

		m_inputWindow.min -= V2i( 1 );
		m_inputWindow.max += V2i( 1 );
	}

	virtual Imath::Box2i inputWindow( const Imath::V2i &tileOrigin ) const
	{
		assert( tileOrigin == m_tileBound.min );
		return m_inputWindow;
	}

	virtual Imath::V2f inputPixel( const Imath::V2f &outputPixel ) const
	{
		const V2i outputPixelI( (int)floorf( outputPixel.x ), (int)floorf( outputPixel.y ) );
		const size_t i = index( outputPixelI, m_tileBound );
		if( m_a[i] == 0.0f )
		{
			return black;
		}
		else
		{
			return uvToPixel( V2f( m_u[i], m_v[i] ) );
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
		Box2i m_inputWindow;

		ConstFloatVectorDataPtr m_uData;
		ConstFloatVectorDataPtr m_vData;
		ConstFloatVectorDataPtr m_aData;

		const std::vector<float> &m_u;
		const std::vector<float> &m_v;
		const std::vector<float> &m_a;

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

	outPlug()->formatPlug()->setInput( 0 );
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

bool UVWarp::inputsAreFlat() const
{
	return uvPlug()->deepStatePlug()->getValue() == ImagePlug::Flat &&
		Warp::inputsAreFlat();
}

void UVWarp::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	Warp::affects( input, outputs );

	if( input == uvPlug()->deepStatePlug() )
	{
		outputs.push_back( outPlug()->formatPlug() );
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->metadataPlug() );
		outputs.push_back( outPlug()->channelNamesPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if ( input == uvPlug()->formatPlug() )
	{
		outputs.push_back( outPlug()->formatPlug() );
	}
	else if ( input == uvPlug()->dataWindowPlug() )
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
	}
}

bool UVWarp::affectsEngine( const Gaffer::Plug *input ) const
{
	return
		Warp::affectsEngine( input ) ||
		input == inPlug()->formatPlug() ||
		input == uvPlug()->channelNamesPlug() ||
		input == uvPlug()->channelDataPlug();
}

void UVWarp::hashEngine( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Warp::hashEngine( channelName, tileOrigin, context, h );

	h.append( tileOrigin );
	uvPlug()->dataWindowPlug()->hash( h );

	ConstStringVectorDataPtr channelNames = uvPlug()->channelNamesPlug()->getValue();

	ContextPtr tmpContext = new Context( *context, Context::Borrowed );
	Context::Scope scopedContext( tmpContext.get() );

	if( channelExists( channelNames->readable(), "R" ) )
	{
		tmpContext->set<std::string>( ImagePlug::channelNameContextName, "R" );
		uvPlug()->channelDataPlug()->hash( h );
	}

	if( channelExists( channelNames->readable(), "G" ) )
	{
		tmpContext->set<std::string>( ImagePlug::channelNameContextName, "G" );
		uvPlug()->channelDataPlug()->hash( h );
	}

	if( channelExists( channelNames->readable(), "A" ) )
	{
		tmpContext->set<std::string>( ImagePlug::channelNameContextName, "A" );
		uvPlug()->channelDataPlug()->hash( h );
	}

	inPlug()->formatPlug()->hash( h );
}

const Warp::Engine *UVWarp::computeEngine( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context ) const
{
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i validTileBound = intersection( tileBound, uvPlug()->dataWindowPlug()->getValue() );

	ConstStringVectorDataPtr channelNames = uvPlug()->channelNamesPlug()->getValue();

	ContextPtr tmpContext = new Context( *context, Context::Borrowed );
	Context::Scope scopedContext( tmpContext.get() );

	ConstFloatVectorDataPtr uData = ImagePlug::blackTile();
	if( channelExists( channelNames->readable(), "R" ) )
	{
		tmpContext->set<std::string>( ImagePlug::channelNameContextName, "R" );
		uData = uvPlug()->channelDataPlug()->getValue();
	}

	ConstFloatVectorDataPtr vData = ImagePlug::blackTile();
	if( channelExists( channelNames->readable(), "G" ) )
	{
		tmpContext->set<std::string>( ImagePlug::channelNameContextName, "G" );
		vData = uvPlug()->channelDataPlug()->getValue();
	}

	ConstFloatVectorDataPtr aData = ImagePlug::whiteTile();
	if( channelExists( channelNames->readable(), "A" ) )
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
		aData
	);
}

void UVWarp::hashFlatFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = uvPlug()->formatPlug()->hash();
}

void UVWarp::hashFlatDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = uvPlug()->dataWindowPlug()->hash();
}

GafferImage::Format UVWarp::computeFlatFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return uvPlug()->formatPlug()->getValue();
}

Imath::Box2i UVWarp::computeFlatDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return uvPlug()->dataWindowPlug()->getValue();
}
