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

#include "GafferScene/ImageToPoints.h"

#include "GafferImage/ImageAlgo.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/PointsPrimitive.h"

#include "IECore/DataAlgo.h"

#include "tbb/enumerable_thread_specific.h"

using namespace Gaffer;
using namespace GafferScene;
using namespace GafferImage;
using namespace IECore;
using namespace IECoreScene;
using namespace Imath;
using namespace std;

GAFFER_NODE_DEFINE_TYPE( ImageToPoints );

size_t ImageToPoints::g_firstPlugIndex = 0;

ImageToPoints::ImageToPoints( const std::string &name )
	:	ObjectSource( name, "points" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "image" ) );
	addChild( new StringPlug( "view", Plug::In, "default" ) );
	addChild( new StringVectorDataPlug( "position", Plug::In, new StringVectorData ) );
	addChild( new StringPlug( "primitiveVariables", Plug::In, "[RGB]" ) );
	addChild( new FloatPlug( "width", Plug::In, 1.0f ) );
	addChild( new StringPlug( "widthChannel" ) );
	addChild( new BoolPlug( "ignoreTransparent" ) );
	addChild( new FloatPlug( "alphaThreshold" ) );
}

ImageToPoints::~ImageToPoints()
{
}

GafferImage::ImagePlug *ImageToPoints::imagePlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const GafferImage::ImagePlug *ImageToPoints::imagePlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *ImageToPoints::viewPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *ImageToPoints::viewPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringVectorDataPlug *ImageToPoints::positionPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringVectorDataPlug *ImageToPoints::positionPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *ImageToPoints::primitiveVariablesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *ImageToPoints::primitiveVariablesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::FloatPlug *ImageToPoints::widthPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::FloatPlug *ImageToPoints::widthPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringPlug *ImageToPoints::widthChannelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringPlug *ImageToPoints::widthChannelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

Gaffer::BoolPlug *ImageToPoints::ignoreTransparentPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::BoolPlug *ImageToPoints::ignoreTransparentPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

Gaffer::FloatPlug *ImageToPoints::alphaThresholdPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::FloatPlug *ImageToPoints::alphaThresholdPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 7 );
}

void ImageToPoints::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );

	if(
		input == imagePlug()->formatPlug() ||
		input == imagePlug()->dataWindowPlug() ||
		input == imagePlug()->channelNamesPlug() ||
		input == imagePlug()->channelDataPlug() ||
		input == positionPlug() ||
		input == primitiveVariablesPlug() ||
		input == widthPlug() ||
		input == widthChannelPlug() ||
		input == ignoreTransparentPlug() ||
		input == alphaThresholdPlug()
	)
	{
		outputs.push_back( sourcePlug() );
	}
}

void ImageToPoints::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImagePlug::ViewScope viewScope( context );
	const std::string view = viewPlug()->getValue();
	viewScope.setViewNameChecked( &view, imagePlug()->viewNames().get() );

	const Format format = imagePlug()->formatPlug()->getValue();
	const Box2i displayWindow = format.getDisplayWindow();
	const Box2i dataWindow = imagePlug()->dataWindowPlug()->getValue();

	h.append( displayWindow );

	bool mappingProvidesP = false;
	vector<ChannelMapping> mappings = channelMappings();
	for( const auto &mapping : mappings )
	{
		h.append( mapping.name );
		for( const auto &destination : mapping.destinations )
		{
			h.append( destination.name );
			h.append( destination.type );
			h.append( destination.offset );
			mappingProvidesP = mappingProvidesP || destination.name == "P";
		}
	}

	if( !mappingProvidesP )
	{
		h.append( format.getPixelAspect() );
	}

	widthPlug()->hash( h );
	ignoreTransparentPlug()->hash( h );

	tbb::enumerable_thread_specific<IECore::MurmurHash> threadLocalHash;
	ImageAlgo::parallelProcessTiles(
		imagePlug(),
		[&] ( const ImagePlug *image, const V2i &tileOrigin ) {

			const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
			const Box2i validTileBound = BufferAlgo::intersection(
				BufferAlgo::intersection( tileBound, dataWindow ), displayWindow
			);

			MurmurHash tileHash;
			tileHash.append( validTileBound );
			for( const auto &mapping : mappings )
			{
				tileHash.append( image->channelDataHash( mapping.name, tileOrigin ) );
			}

			MurmurHash &hash = threadLocalHash.local();
			hash = MurmurHash( hash.h1() + tileHash.h1(), hash.h2() + tileHash.h2() );
		},
		BufferAlgo::intersection( displayWindow, dataWindow )
	);

	const MurmurHash tilesHash = threadLocalHash.combine(
		[] ( const MurmurHash &a, const MurmurHash &b ) {
			// See SceneAlgo's ThreadablePathHashAccumulator for further discussion of
			// this "sum of hashes" strategy for deterministic parallel hashing.
			return MurmurHash( a.h1() + b.h1(), a.h2() + b.h2() );
		}
	);
	h.append( tilesHash );

	alphaThresholdPlug()->hash( h );
}

IECore::ConstObjectPtr ImageToPoints::computeSource( const Context *context ) const
{
	ImagePlug::ViewScope viewScope( context );
	const std::string view = viewPlug()->getValue();
	viewScope.setViewNameChecked( &view, imagePlug()->viewNames().get() );

	const Format format = imagePlug()->formatPlug()->getValue();
	const Box2i displayWindow = format.getDisplayWindow();
	const Box2i dataWindow = imagePlug()->dataWindowPlug()->getValue();
	size_t numPixels = displayWindow.size().x * displayWindow.size().y;

	// Make a PointsPrimitive with all the primitive variables specified
	// by our channel mappings.

	PointsPrimitivePtr pointsPrimitive = new PointsPrimitive( numPixels );

	vector<ChannelMapping> mappings = channelMappings();
	for( auto &mapping : mappings )
	{
		for( auto &destination : mapping.destinations )
		{
			PrimitiveVariable &pv = pointsPrimitive->variables[destination.name];
			pv.interpolation = PrimitiveVariable::Vertex;
			if( destination.type == Color3fVectorData::staticTypeId() )
			{
				if( !pv.data )
				{
					pv.data = new Color3fVectorData( vector<Color3f>( numPixels, Imath::Color3f( 0 ) ) );
				}
				destination.data = static_cast<Color3fVectorData *>( pv.data.get() )->baseWritable();
			}
			else if( destination.type == V3fVectorData::staticTypeId() )
			{
				if( !pv.data )
				{
					pv.data = new V3fVectorData( vector<V3f>( numPixels, Imath::V3f( 0 ) ) );
				}
				destination.data = static_cast<V3fVectorData *>( pv.data.get() )->baseWritable();
			}
			else
			{
				assert( destination.type == FloatVectorData::staticTypeId() );
				assert( !pv.data );
				FloatVectorDataPtr data = new FloatVectorData( vector<float>( numPixels, 0 ) );
				pv.data = data;
				destination.data = data->baseWritable();
			}
		}
	}

	// Add on our own "P" if it is not mapped from a channel.

	if( !pointsPrimitive->variableData<V3fVectorData>( "P" ) )
	{
		V3fVectorDataPtr pData = new V3fVectorData( vector<V3f>( numPixels, V3f( 0 ) ) );
		pointsPrimitive->variables["P"] = PrimitiveVariable( PrimitiveVariable::Vertex, pData );
		auto it = pData->writable().begin();
		const float pixelAspect = format.getPixelAspect();
		for( int y = displayWindow.min.y; y < displayWindow.max.y; ++y )
		{
			for( int x = displayWindow.min.x; x < displayWindow.max.x; ++x )
			{
				*it++ = V3f( ( x + 0.5 ) * pixelAspect, y + 0.5, 0.0 );
			}
		}
	}

	// Add width if it is not mapped from a channel.

	const float width = widthPlug()->getValue();
	if( !pointsPrimitive->variableData<FloatVectorData>( "width" ) )
	{
		pointsPrimitive->variables["width"] = PrimitiveVariable( PrimitiveVariable::Constant, new FloatData( width ) );
	}

	// Compute image tiles in parallel, shuffling the data into the primitive variables
	// via our mapping. Although we may visit tiles in any order, the ordering of points
	// in the primitive variables is stable, based on the scanline order of the image.

	ImageAlgo::parallelProcessTiles(
		imagePlug(),
		[&] ( const ImagePlug *image, const V2i &tileOrigin ) {

			const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
			const Box2i validTileBound = BufferAlgo::intersection(
				BufferAlgo::intersection( tileBound, dataWindow ), displayWindow
			);

			for( const auto &mapping : mappings )
			{
				ConstFloatVectorDataPtr channelData = image->channelData( mapping.name, tileOrigin );
				const vector<float> &data = channelData->readable();

				for( const auto &destination : mapping.destinations )
				{
					const bool isWidth = destination.name == "width";
					const size_t stride = destination.type == FloatVectorData::staticTypeId() ? 1 : 3;
					for( int y = validTileBound.min.y; y < validTileBound.max.y; ++y )
					{
						size_t inIndex = BufferAlgo::index( V2i( validTileBound.min.x, y ), tileBound );
						size_t outIndex = BufferAlgo::index( V2i( validTileBound.min.x, y ), displayWindow ) * stride + destination.offset;
						if( !isWidth )
						{
							for( int x = validTileBound.min.x; x < validTileBound.max.x; ++x )
							{
								destination.data[outIndex] = data[inIndex++];
								outIndex += stride;
							}
						}
						else
						{
							// As above, but with multiplier
							for( int x = validTileBound.min.x; x < validTileBound.max.x; ++x )
							{
								destination.data[outIndex] = data[inIndex++] * width;
								outIndex += stride;
							}
						}
					}
				}
			}
		},
		BufferAlgo::intersection( displayWindow, dataWindow )
	);

	// Strip out points below the alpha threshold in a final serial step.
	// We can't easily do this in the step above because we don't know the
	// point count or order until after we've visited all tiles.

	if( ConstFloatVectorDataPtr alphaData = pointsPrimitive->variableData<FloatVectorData>( "__imageToPointsAlpha__" ) )
	{
		const vector<float> &alphaBuffer = alphaData->readable();
		pointsPrimitive->variables.erase( "__imageToPointsAlpha__" );
		const float alphaThreshold = alphaThresholdPlug()->getValue();
		for( auto &[name, variable] : pointsPrimitive->variables )
		{
			IECore::dispatch(
				variable.data.get(),
				[&] ( auto *typedData ) {
					using DataType = typename std::remove_pointer_t<decltype( typedData )>;
					if constexpr ( TypeTraits::IsVectorTypedData<DataType>::value )
					{
						auto &typedVector = typedData->writable();
						size_t newIndex = 0;
						for( size_t oldIndex = 0; oldIndex < typedVector.size(); ++oldIndex )
						{
							if( alphaBuffer[oldIndex] > alphaThreshold )
							{
								if( newIndex != oldIndex )
								{
									typedVector[newIndex] = std::move( typedVector[oldIndex] );
								}
								++newIndex;
							}
						}
						typedVector.resize( newIndex );
						typedVector.shrink_to_fit();
					}
				}
			);
		}

		pointsPrimitive->setNumPoints(
			pointsPrimitive->variableData<V3fVectorData>( "P" )->readable().size()
		);
	}

	return pointsPrimitive;
}

std::vector<ImageToPoints::ChannelMapping> ImageToPoints::channelMappings() const
{
	vector<ChannelMapping> result;

	const string primitiveVariables = primitiveVariablesPlug()->getValue();
	ConstStringVectorDataPtr positionChannelsData = positionPlug()->getValue();
	const vector<string> &positionChannels = positionChannelsData->readable();
	const string widthChannel = widthChannelPlug()->getValue();
	const bool ignoreTransparent = ignoreTransparentPlug()->getValue();

	unsigned int numPositionMappings = 0;
	bool haveWidthMapping = false;
	bool haveAlphaMapping = false;
	ConstStringVectorDataPtr channelNamesData = imagePlug()->channelNamesPlug()->getValue();
	for( const auto &channelName : channelNamesData->readable() )
	{
		ChannelMapping mapping = { channelName, {} };

		// Position

		auto positionIt = find( positionChannels.begin(), positionChannels.end(), channelName );
		if( positionIt != positionChannels.end() && positionIt - positionChannels.begin() < 3 )
		{
			mapping.destinations.push_back( {
				"P",
				V3fVectorData::staticTypeId(),
				static_cast<size_t>( positionIt - positionChannels.begin() )
			} );
			numPositionMappings++;
		}

		// Custom primitive variables

		if( StringAlgo::matchMultiple( channelName, primitiveVariables ) )
		{
			const int colorIndex = ImageAlgo::colorIndex( channelName );
			if( colorIndex >= 0 && colorIndex <= 2 )
			{
				// Map R, G and B to the components of colour primitive variables.
				const string layerName = ImageAlgo::layerName( channelName );
				mapping.destinations.push_back( {
					layerName == "" ? "Cs" : layerName,
					Color3fVectorData::staticTypeId(),
					(size_t)colorIndex
				} );
			}
			else
			{
				// Map everything else to individual float primitive variables.
				mapping.destinations.push_back( {
					channelName,
					FloatVectorData::staticTypeId(),
					0
				} );
			}
		}

		// Width

		if( channelName == widthChannel )
		{
			mapping.destinations.push_back( {
				"width",
				FloatVectorData::staticTypeId(),
				0
			} );
			haveWidthMapping = true;
		}

		// Alpha for skipping transparent pixels

		if( channelName == "A" && ignoreTransparent )
		{
			mapping.destinations.push_back( {
				"__imageToPointsAlpha__",
				FloatVectorData::staticTypeId(),
				0
			} );
			haveAlphaMapping = true;
		}

		if( mapping.destinations.size() )
		{
			result.push_back( mapping );
		}
	}

	if( numPositionMappings < 3 && positionChannels.size() > numPositionMappings )
	{
		throw IECore::Exception( "Position channels are missing from the input image" );
	}

	if( !widthChannel.empty() and !haveWidthMapping )
	{
		throw IECore::Exception( "Width channels is missing from the input image" );
	}

	if( ignoreTransparent && !haveAlphaMapping )
	{
		throw IECore::Exception( "Alpha channel is missing from the input image" );
	}

	return result;
}
