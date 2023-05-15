//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "boost/python.hpp"
#include "fmt/format.h"

#include "GafferImageTest/ContextSanitiser.h"

#include "GafferTest/ContextTest.h"

#include "GafferImage/ImageAlgo.h"
#include "GafferImage/ImagePlug.h"
#include "GafferImage/Format.h"
#include "GafferImage/Sampler.h"

#include "Gaffer/Node.h"

#include "IECorePython/RefCountedBinding.h"
#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferImage;
using namespace GafferImageTest;

namespace
{

struct TilesEvaluateFunctor
{
	bool operator()( const GafferImage::ImagePlug *imagePlug, const std::string &channelName, const Imath::V2i &tileOrigin )
	{
		imagePlug->channelDataPlug()->getValue();
		return true;
	}
};

void processTiles( const GafferImage::ImagePlug *imagePlug )
{
	TilesEvaluateFunctor f;

	IECore::ConstStringVectorDataPtr viewNames = imagePlug->viewNames();
	ImagePlug::ViewScope viewScope( Context::current() );

	for( const std::string &viewName : viewNames->readable() )
	{
		viewScope.setViewName( &viewName );
		ImageAlgo::parallelProcessTiles(
			imagePlug, imagePlug->channelNamesPlug()->getValue()->readable(),
			f,
			imagePlug->dataWindowPlug()->getValue(),
			ImageAlgo::TopToBottom
		);
	}
}

void processTilesOnDirty( const Gaffer::Plug *dirtiedPlug, ConstImagePlugPtr image )
{
	if( dirtiedPlug == image.get() )
	{
		processTiles( image.get() );
	}
}

void processTilesWrapper( GafferImage::ImagePlug *imagePlug )
{
	IECorePython::ScopedGILRelease gilRelease;
	processTiles( imagePlug );
}

Signals::Connection connectProcessTilesToPlugDirtiedSignal( GafferImage::ConstImagePlugPtr image )
{
	const Node *node = image->node();
	if( !node )
	{
		throw IECore::Exception( "Plug does not belong to a node." );
	}

	return const_cast<Node *>( node )->plugDirtiedSignal().connect( boost::bind( &processTilesOnDirty, ::_1, image ) );
}

void testEditableScopeForFormat()
{
	GafferTest::testEditableScopeTyped<FormatData>(
		Format( Imath::Box2i( Imath::V2i( 1, 2 ), Imath::V2i( 1, 2 ) ), 1 ),
		Format( Imath::Box2i( Imath::V2i( 3, 5 ), Imath::V2i( 1920, 1080 ) ), 1.6 )
	);
}

void validateVisitPixels( GafferImage::Sampler &sampler, const Imath::Box2i &region )
{
	int i = 0;
	int sizeX = region.size().x;
	sampler.visitPixels( region,
		[&region, &sampler, &i, sizeX ] ( float value, int x, int y )
		{
			int expectedX = ( i % sizeX ) + region.min.x;
			int expectedY = ( i / sizeX ) + region.min.y;
			if( x != expectedX || y != expectedY )
			{
				throw IECore::Exception( fmt::format (
					"visitPixels passed incorrect coordinate - expected {},{}, received {},{}",
					expectedX, expectedY, x, y
				) );
			}

			float expectedValue = sampler.sample( x, y );
			if( value != expectedValue )
			{
				throw IECore::Exception( fmt::format(
					"visitPixels passed incorrect value for pixel {},{} - expected {} received {}",
					x, y, expectedValue, value
				) );
			}
			i++;
		}
	);
	if( i != region.size().x * region.size().y )
	{
		throw IECore::Exception( fmt::format(
			"visitPixels processed wrong number of pixels: visited {} in region of size {},{}",
			i, region.size().x, region.size().y
		) );
	}
}

} // namespace

BOOST_PYTHON_MODULE( _GafferImageTest )
{
	IECorePython::RefCountedClass<ContextSanitiser, Gaffer::Monitor>( "ContextSanitiser" )
		.def( init<>() )
	;

	def( "processTiles", &processTilesWrapper );
	def( "connectProcessTilesToPlugDirtiedSignal", &connectProcessTilesToPlugDirtiedSignal );
	def( "testEditableScopeForFormat", &testEditableScopeForFormat );
	def( "validateVisitPixels", &validateVisitPixels );
}
