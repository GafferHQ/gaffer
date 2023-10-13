//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/ImageScatter.h"

#include "GafferImage/ImageAlgo.h"
#include "GafferImage/Sampler.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/PointsPrimitive.h"

#include "IECore/PointDistribution.h"

#include "tbb/parallel_for.h"

using namespace Gaffer;
using namespace GafferScene;
using namespace GafferImage;
using namespace IECore;
using namespace IECoreScene;
using namespace Imath;
using namespace std;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

void sampleChannel( const ImagePlug *image, const Box2i &displayWindow, const string &channelName, const vector<V3f> &positions, const IECore::Canceller *canceller, float *outData, int stride, float multiplier = 1.0f )
{
	Sampler sampler( image, channelName, displayWindow, Sampler::Clamp );
	sampler.populate(); // Multithread the population of image tiles

	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );
	tbb::parallel_for( tbb::blocked_range<size_t>( 0, positions.size() ),
		[&] ( const tbb::blocked_range<size_t> &range ) {
			IECore::Canceller::check( canceller );
			for( size_t i = range.begin(); i < range.end(); ++i )
			{
				outData[i*stride] = sampler.sample( positions[i].x, positions[i].y ) * multiplier;
			}
		},
		taskGroupContext
	);
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ImageScatter
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( ImageScatter );

size_t ImageScatter::g_firstPlugIndex = 0;

ImageScatter::ImageScatter( const std::string &name )
	:	ObjectSource( name, "points" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "image" ) );
	addChild( new StringPlug( "view", Plug::In, "default" ) );
	addChild( new FloatPlug( "density", Plug::In, 0.5f, 0.0f ) );
	addChild( new StringPlug( "densityChannel", Plug::In, "R" ) );
	addChild( new StringPlug( "primitiveVariables" ) );
	addChild( new FloatPlug( "width", Plug::In, 1.0f ) );
	addChild( new StringPlug( "widthChannel" ) );
}

ImageScatter::~ImageScatter()
{
}

GafferImage::ImagePlug *ImageScatter::imagePlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const GafferImage::ImagePlug *ImageScatter::imagePlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *ImageScatter::viewPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *ImageScatter::viewPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::FloatPlug *ImageScatter::densityPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::FloatPlug *ImageScatter::densityPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *ImageScatter::densityChannelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *ImageScatter::densityChannelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *ImageScatter::primitiveVariablesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *ImageScatter::primitiveVariablesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::FloatPlug *ImageScatter::widthPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::FloatPlug *ImageScatter::widthPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 5 );
}

Gaffer::StringPlug *ImageScatter::widthChannelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::StringPlug *ImageScatter::widthChannelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

void ImageScatter::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );

	if(
		input == viewPlug() ||
		input == imagePlug()->viewNamesPlug() ||
		input == imagePlug()->channelNamesPlug() ||
		input == densityChannelPlug() ||
		input == widthChannelPlug() ||
		input == imagePlug()->formatPlug() ||
		input == imagePlug()->dataWindowPlug() ||
		input == imagePlug()->channelDataPlug() ||
		input == densityPlug() ||
		input == widthPlug() ||
		input == primitiveVariablesPlug()
	)
	{
		outputs.push_back( sourcePlug() );
	}
}

void ImageScatter::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImagePlug::ViewScope viewScope( context );
	const std::string view = viewPlug()->getValue();
	viewScope.setViewNameChecked( &view, imagePlug()->viewNames().get() );

	ConstStringVectorDataPtr channelNamesData = imagePlug()->channelNamesPlug()->getValue();
	const string densityChannel = densityChannelPlug()->getValue();
	if( !ImageAlgo::channelExists( channelNamesData->readable(), densityChannel ) )
	{
		throw IECore::Exception( fmt::format( "Density channel \"{}\" does not exist", densityChannel ) );
	}

	const string widthChannel = widthChannelPlug()->getValue();
	if( widthChannel.size() && !ImageAlgo::channelExists( channelNamesData->readable(), widthChannel ) )
	{
		throw IECore::Exception( fmt::format( "Width channel \"{}\" does not exist", widthChannel ) );
	}

	const Format format = imagePlug()->formatPlug()->getValue();
	const Box2i &displayWindow = format.getDisplayWindow();
	Sampler densitySampler( imagePlug(), densityChannel, displayWindow, Sampler::Clamp );

	h.append( displayWindow );
	h.append( format.getPixelAspect() );
	densitySampler.hash( h );
	densityPlug()->hash( h );

	widthPlug()->hash( h );
	h.append( widthChannel );

	const std::string primitiveVariablesMatchPattern = primitiveVariablesPlug()->getValue();
	for( const auto &channelName : channelNamesData->readable() )
	{
		if( channelName == widthChannel || StringAlgo::matchMultiple( channelName, primitiveVariablesMatchPattern ) )
		{
			h.append( channelName );
			Sampler sampler( imagePlug(), channelName, displayWindow, Sampler::Clamp );
			sampler.hash( h );
		}
	}
}

IECore::ConstObjectPtr ImageScatter::computeSource( const Context *context ) const
{
	// Validate input image.

	ImagePlug::ViewScope viewScope( context );
	const std::string view = viewPlug()->getValue();
	viewScope.setViewNameChecked( &view, imagePlug()->viewNames().get() );

	ConstStringVectorDataPtr channelNamesData = imagePlug()->channelNamesPlug()->getValue();
	const string densityChannel = densityChannelPlug()->getValue();
	if( !ImageAlgo::channelExists( channelNamesData->readable(), densityChannel ) )
	{
		throw IECore::Exception( fmt::format( "Density channel \"{}\" does not exist", densityChannel ) );
	}

	const string widthChannel = widthChannelPlug()->getValue();
	if( widthChannel.size() && !ImageAlgo::channelExists( channelNamesData->readable(), widthChannel ) )
	{
		throw IECore::Exception( fmt::format( "Density channel \"{}\" does not exist", widthChannel ) );
	}

	const Format format = imagePlug()->formatPlug()->getValue();
	const Box2i &displayWindow = format.getDisplayWindow();
	const float pixelAspect = format.getPixelAspect();
	const Box2f outputArea = Box2f(
		V2f( displayWindow.min.x * pixelAspect, displayWindow.min.y ),
		V2f( displayWindow.max.x * pixelAspect, displayWindow.max.y )
	);

	// Generate positions using a PointDistribution reading from a Sampler for
	// the density channel.

	Sampler densitySampler( imagePlug(), densityChannel, displayWindow, Sampler::Clamp );
	densitySampler.populate(); // Multithread the population of image tiles

	// Point distribution is designed for samping within a unit square, so we
	// offset and scale to fit that to our input image.
	const float scale = std::max( outputArea.size().x, outputArea.size().y );
	const V2i offset = displayWindow.min;

	auto densityFunction = [&] ( const V2f &p ) {
		IECore::Canceller::check( context->canceller() );
		return densitySampler.sample( offset.x + p.x * scale / pixelAspect, offset.y + p.y * scale );
	};

	V3fVectorDataPtr positionsData = new V3fVectorData;
	positionsData->setInterpretation( IECore::GeometricData::Point );
	vector<V3f> &positions = positionsData->writable();
	auto emitter = [&] ( const V2f &p ) {
		positions.push_back( V3f( offset.x + p.x * scale, offset.y + p.y * scale, 0.0f ) );
	};

	/// \todo It would be nice to multithread this, but it could also be pretty
	/// handy that the order of the points we're outputting matches the
	/// progressive order in which they are generated.
	PointDistribution::defaultInstance()(
		Box2f( V2f( 0 ), V2f( outputArea.size() ) / scale ),
		// Scale density to be in points per pixel
		densityPlug()->getValue() * scale * scale,
		densityFunction,
		emitter
	);

	// Make a PointsPrimitive from the positions

	PointsPrimitivePtr result = new PointsPrimitive( positionsData );

	// Add on primitive variables.

	const float width = widthPlug()->getValue();
	if( widthChannel.empty() )
	{
		result->variables["width"] = PrimitiveVariable( PrimitiveVariable::Interpolation::Constant, new FloatData( width ) );
	}

	const std::string primitiveVariablesMatchPattern = primitiveVariablesPlug()->getValue();
	for( const auto &channelName : channelNamesData->readable() )
	{
		if( StringAlgo::matchMultiple( channelName, primitiveVariablesMatchPattern ) )
		{
			const int colorIndex = ImageAlgo::colorIndex( channelName );
			if( colorIndex >= 0 && colorIndex <= 2 )
			{
				// Map R, G and B to the components of colour primitive variables.
				// This is the same behaviour as ImageToPoints.
				string name = ImageAlgo::layerName( channelName );
				name = name == "" ? "Cs" : name;
				Color3fVectorDataPtr colorData = result->variableData<Color3fVectorData>( name );
				if( !colorData )
				{
					colorData = new Color3fVectorData;
					colorData->writable().resize( positions.size() );
					result->variables[name] = PrimitiveVariable( PrimitiveVariable::Vertex, colorData );
				}
				sampleChannel( imagePlug(), displayWindow, channelName, positions, context->canceller(), colorData->baseWritable() + colorIndex, 3 );
			}
			else
			{
				// Map everything else to individual float primitive variables.
				const string name = channelName == widthChannel ? "width" : channelName;
				FloatVectorDataPtr floatData = new FloatVectorData;
				floatData->writable().resize( positions.size() );
				result->variables[name] = PrimitiveVariable( PrimitiveVariable::Vertex, floatData );
				sampleChannel( imagePlug(), displayWindow, channelName, positions, context->canceller(), floatData->writable().data(), 1 );
			}
		}

		if( channelName == widthChannel )
		{
			FloatVectorDataPtr widthData = new FloatVectorData;
			widthData->writable().resize( positions.size() );
			result->variables["width"] = PrimitiveVariable( PrimitiveVariable::Vertex, widthData );
			sampleChannel( imagePlug(), displayWindow, channelName, positions, context->canceller(), widthData->writable().data(), 1, width );
		}
	}

	return result;
}

Gaffer::ValuePlug::CachePolicy ImageScatter::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == sourcePlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return ObjectSource::computeCachePolicy( output );
}
