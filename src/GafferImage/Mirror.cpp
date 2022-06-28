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

#include "GafferImage/Mirror.h"

#include "GafferImage/Sampler.h"

#include "Gaffer/Context.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

Box2i mirror( const Box2i &box, bool horizontal, bool vertical, const Box2i &displayWindow )
{
	Box2i result = box;
	if( horizontal )
	{
		result.max.x = displayWindow.max.x - (box.min.x - displayWindow.min.x);
		result.min.x = displayWindow.max.x - (box.max.x - displayWindow.min.x);
	}
	if( vertical )
	{
		result.max.y = displayWindow.max.y - (box.min.y - displayWindow.min.y);
		result.min.y = displayWindow.max.y - (box.max.y - displayWindow.min.y);
	}

	return result;
}

V2i mirror( const V2i &point, bool horizontal, bool vertical, const Box2i &displayWindow )
{
	V2i result = point;
	if( horizontal )
	{
		result.x = displayWindow.max.x - 1 - (point.x - displayWindow.min.x);
	}
	if( vertical )
	{
		result.y = displayWindow.max.y - 1 - (point.y - displayWindow.min.y);
	}
	return result;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Mirror
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Mirror );

size_t Mirror::g_firstPlugIndex = 0;

Mirror::Mirror( const std::string &name )
	:	FlatImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new BoolPlug( "horizontal" ) );
	addChild( new BoolPlug( "vertical" ) );

	outPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
}

Mirror::~Mirror()
{
}

Gaffer::BoolPlug *Mirror::horizontalPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

const Gaffer::BoolPlug *Mirror::horizontalPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *Mirror::verticalPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *Mirror::verticalPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

void Mirror::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageProcessor::affects( input, outputs );

	const bool affectsTransform =
		input == inPlug()->formatPlug() ||
		input == horizontalPlug() ||
		input == verticalPlug()
	;

	if(
		affectsTransform ||
		input == inPlug()->dataWindowPlug()
	)
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
	}

	if(
		affectsTransform ||
		input == inPlug()->channelDataPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void Mirror::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const bool horizontal = horizontalPlug()->getValue();
	const bool vertical = verticalPlug()->getValue();

	if( !horizontal && !vertical )
	{
		h = inPlug()->dataWindowPlug()->hash();
		return;
	}

	FlatImageProcessor::hashDataWindow( parent, context, h );
	inPlug()->dataWindowPlug()->hash( h );
	inPlug()->formatPlug()->hash( h );
	h.append( horizontal );
	h.append( vertical );
}

Imath::Box2i Mirror::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const Box2i inDataWindow = inPlug()->dataWindowPlug()->getValue();
	if( BufferAlgo::empty( inDataWindow ) )
	{
		return inDataWindow;
	}

	const bool horizontal = horizontalPlug()->getValue();
	const bool vertical = verticalPlug()->getValue();
	if( !horizontal && !vertical )
	{
		return inDataWindow;
	}

	return mirror(
		inDataWindow,
		horizontal,
		vertical,
		inPlug()->formatPlug()->getValue().getDisplayWindow()
	);
}

void Mirror::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const bool horizontal = horizontalPlug()->getValue();
	const bool vertical = verticalPlug()->getValue();

	if( !horizontal && !vertical )
	{
		h = inPlug()->channelDataPlug()->hash();
		return;
	}

	FlatImageProcessor::hashChannelData( parent, context, h );

	const std::string &channelName = context->get<string>( ImagePlug::channelNameContextName );
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	Box2i displayWindow;
	{
		ImagePlug::GlobalScope c( context );
		displayWindow = inPlug()->formatPlug()->getValue().getDisplayWindow();
	}

	const Box2i sampleWindow = mirror(
		tileBound,
		horizontal,
		vertical,
		displayWindow
	);

	Sampler sampler( inPlug(), channelName, sampleWindow );
	sampler.hash( h );

	h.append( horizontal );
	h.append( vertical );
}

IECore::ConstFloatVectorDataPtr Mirror::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const bool horizontal = horizontalPlug()->getValue();
	const bool vertical = verticalPlug()->getValue();

	if( !horizontal && !vertical )
	{
		return inPlug()->channelDataPlug()->getValue();
	}

	Box2i displayWindow;
	{
		ImagePlug::GlobalScope c( context );
		displayWindow = inPlug()->formatPlug()->getValue().getDisplayWindow();
	}
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i sampleWindow = mirror(
		tileBound,
		horizontal,
		vertical,
		displayWindow
	);

	Sampler sampler( inPlug(), channelName, sampleWindow );

	FloatVectorDataPtr outData = new FloatVectorData;
	vector<float> &out = outData->writable();
	out.reserve( ImagePlug::tileSize() * ImagePlug::tileSize() );

	V2i pIn;
	V2i pOut;
	for( pOut.y = tileBound.min.y; pOut.y < tileBound.max.y; ++pOut.y )
	{
		pOut.x = tileBound.min.x;
		pIn = mirror( pOut, horizontal, vertical, displayWindow );
		const int xStep = horizontal ? -1 : 1;
		for( ; pOut.x < tileBound.max.x; ++pOut.x )
		{
			out.push_back( sampler.sample( pIn.x, pIn.y ) );
			pIn.x += xStep;
		}
	}

	return outData;
}
