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

#include "GafferImage/ImageStats.h"

#include "GafferImage/FormatPlug.h"
#include "GafferImage/ImageAlgo.h"
#include "GafferImage/Sampler.h"

#include "Gaffer/BoxPlug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/TypedPlug.h"

using namespace std;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

int colorIndex( const ValuePlug *plug )
{
	const Color4fPlug *colorPlug = plug->parent<Color4fPlug>();
	assert( colorPlug );
	for( size_t i = 0; i < 4; ++i )
	{
		if( plug == colorPlug->getChild( i ) )
		{
			return i;
		}
	}
	assert( false );
	return 0;
}

std::string channelName( const ValuePlug *outChannelPlug, const vector<string> &selectChannels, const vector<string> &channelNames )
{
	int index = colorIndex( outChannelPlug );
	if( selectChannels.size() <= (size_t)index )
	{
		return "";
	}

	if( find( channelNames.begin(), channelNames.end(), selectChannels[index] ) != channelNames.end() )
	{
		return selectChannels[index];
	}

	return "";
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ImageStats
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( ImageStats );

size_t ImageStats::g_firstPlugIndex = 0;

ImageStats::ImageStats( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "in", Gaffer::Plug::In ) );

	addChild( new StringPlug( "view", Plug::In, "" ) );

	IECore::StringVectorDataPtr defaultChannelsData = new IECore::StringVectorData;
	vector<string> &defaultChannels = defaultChannelsData->writable();
	defaultChannels.push_back( "R" );
	defaultChannels.push_back( "G" );
	defaultChannels.push_back( "B" );
	defaultChannels.push_back( "A" );
	addChild( new StringVectorDataPlug( "channels", Plug::In, defaultChannelsData ) );

	addChild( new IntPlug( "areaSource", Gaffer::Plug::In, ImageStats::Area, ImageStats::Area, ImageStats::DisplayWindow ) );
	addChild( new Box2iPlug( "area", Gaffer::Plug::In ) );
	addChild( new Color4fPlug(
		"average", Gaffer::Plug::Out, Imath::Color4f( 0, 0, 0, 1 ),
		Imath::Color4f( -std::numeric_limits<float>::infinity() ), Imath::Color4f( std::numeric_limits<float>::infinity() )
	) );
	addChild(
		new Color4fPlug( "min", Gaffer::Plug::Out, Imath::Color4f( 0, 0, 0, 1 ),
		Imath::Color4f( -std::numeric_limits<float>::infinity() ), Imath::Color4f( std::numeric_limits<float>::infinity() )
	) );
	addChild(
		new Color4fPlug( "max", Gaffer::Plug::Out, Imath::Color4f( 0, 0, 0, 1 ),
		Imath::Color4f( -std::numeric_limits<float>::infinity() ), Imath::Color4f( std::numeric_limits<float>::infinity() )
	) );

	addChild( new ObjectPlug( "__tileStats", Gaffer::Plug::Out, new IECore::V3dData() ) );
	addChild( new ObjectPlug( "__allStats", Gaffer::Plug::Out, new IECore::V3dData() ) );

	addChild( new ImagePlug( "__flattenedIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	DeepStatePtr deepStateNode = new DeepState( "__deepState" );
	addChild( deepStateNode );

	deepStateNode->inPlug()->setInput( inPlug() );
	deepStateNode->deepStatePlug()->setValue( int( DeepState::TargetState::Flat ) );
	flattenedInPlug()->setInput( deepStateNode->outPlug() );
}

ImageStats::~ImageStats()
{
}

ImagePlug *ImageStats::inPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const ImagePlug *ImageStats::inPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *ImageStats::viewPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *ImageStats::viewPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringVectorDataPlug *ImageStats::channelsPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringVectorDataPlug *ImageStats::channelsPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 2 );
}

IntPlug *ImageStats::areaSourcePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

const IntPlug *ImageStats::areaSourcePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

Box2iPlug *ImageStats::areaPlug()
{
	return getChild<Box2iPlug>( g_firstPlugIndex + 4 );
}

const Box2iPlug *ImageStats::areaPlug() const
{
	return getChild<Box2iPlug>( g_firstPlugIndex + 4 );
}

Color4fPlug *ImageStats::averagePlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 5 );
}

const Color4fPlug *ImageStats::averagePlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 5 );
}

Color4fPlug *ImageStats::minPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 6 );
}

const Color4fPlug *ImageStats::minPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 6 );
}

Color4fPlug *ImageStats::maxPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 7 );
}

const Color4fPlug *ImageStats::maxPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 7 );
}

ObjectPlug *ImageStats::tileStatsPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 8 );
}

const ObjectPlug *ImageStats::tileStatsPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 8 );
}

ObjectPlug *ImageStats::allStatsPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 9 );
}

const ObjectPlug *ImageStats::allStatsPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 9 );
}


ImagePlug *ImageStats::flattenedInPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 10 );
}

const ImagePlug *ImageStats::flattenedInPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 10 );
}

void ImageStats::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == viewPlug() ||
		input == flattenedInPlug()->viewNamesPlug() ||
		input == flattenedInPlug()->dataWindowPlug() ||
		input == flattenedInPlug()->formatPlug() ||
		input == flattenedInPlug()->channelDataPlug() ||
		input == areaSourcePlug() ||
		areaPlug()->isAncestorOf( input )
	)
	{
		outputs.push_back( tileStatsPlug() );
	}

	if(
		input == viewPlug() ||
		input == flattenedInPlug()->viewNamesPlug() ||
		input == tileStatsPlug() ||
		input == flattenedInPlug()->dataWindowPlug() ||
		input == flattenedInPlug()->formatPlug() ||
		input == areaSourcePlug() ||
		areaPlug()->isAncestorOf( input )
	)
	{
		outputs.push_back( allStatsPlug() );
	}

	if(
		input == viewPlug() ||
		input == flattenedInPlug()->viewNamesPlug() ||
		input == allStatsPlug() ||
		input == flattenedInPlug()->channelNamesPlug() ||
		input == channelsPlug()
	)
	{
		for( unsigned int i = 0; i < 4; ++i )
		{
			outputs.push_back( minPlug()->getChild(i) );
			outputs.push_back( averagePlug()->getChild(i) );
			outputs.push_back( maxPlug()->getChild(i) );
		}
	}
}

void ImageStats::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h);

	ImagePlug::ViewScope viewScope( context );

	std::string view = viewPlug()->getValue();
	if( !view.size() )
	{
		view = context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName );
	}
	viewScope.setViewNameChecked( &view, inPlug()->viewNames().get() );

	const Plug *parent = output->parent<Plug>();
	if( parent == minPlug() || parent == maxPlug() || parent == averagePlug() )
	{
		IECore::ConstStringVectorDataPtr channelsData = channelsPlug()->getValue();
		IECore::ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
		const std::string channelName = ::channelName( output, channelsData->readable(), channelNamesData->readable() );
		if( channelName.empty() )
		{
			h.append( 0.0f );
			return;
		}

		int statIndex = ( parent == averagePlug() ) ? 2 : ( parent == maxPlug() );
		h.append( statIndex );

		ImagePlug::ChannelDataScope s( context );
		s.setChannelName( &channelName );
		allStatsPlug()->hash( h );
		return;
	}

	Imath::Box2i boundsIntersection;
	bool beyondDataWindow;
	double areaMult;

	{
		ImagePlug::GlobalScope s( viewScope.context() );
		int areaSource = areaSourcePlug()->getValue();
		Imath::Box2i area;
		switch ( areaSource )
		{
			case ImageStats::DataWindow:
			{
				area = inPlug()->dataWindowPlug()->getValue();
				break;
			}
			case ImageStats::DisplayWindow:
			{
				area = inPlug()->formatPlug()->getValue().getDisplayWindow();
				break;
			}
			default:
			{
				area = areaPlug()->getValue();
				break;
			}
		}
		const Imath::Box2i dataWindow = flattenedInPlug()->dataWindowPlug()->getValue();
		boundsIntersection = BufferAlgo::intersection( area, dataWindow );
		beyondDataWindow = boundsIntersection != area;
		areaMult = double(area.size().x) * area.size().y;
	}

	if( output == tileStatsPlug() )
	{
		Imath::V2i tileOrigin = context->get<Imath::V2i>( ImagePlug::tileOriginContextName );
		const Imath::Box2i tileBound = BufferAlgo::intersection(
			Imath::Box2i( boundsIntersection.min - tileOrigin, boundsIntersection.max - tileOrigin ),
			Imath::Box2i( Imath::V2i( 0 ), Imath::V2i( ImagePlug::tileSize() ) )
		);
		// Work around strange Box2i hashing behaviour in GCC 11, though it would be
		// preferable to fix this in MurmurHash.
		h.append( tileBound.min );
		h.append( tileBound.max );
		flattenedInPlug()->channelDataPlug()->hash( h );
	}
	else if( output == allStatsPlug() )
	{
		if( BufferAlgo::empty( boundsIntersection ) )
		{
			h.append( 0.0f );
			return;
		}

		h.append( beyondDataWindow );

		// We traverse in TopToBottom order because otherwise the hash could change just based on
		// the order in which hashes are combined
		ImageAlgo::parallelGatherTiles(
			flattenedInPlug(),
			// Tile
			[this] ( const ImagePlug *imageP, const Imath::V2i &tileOrigin )
			{
				return tileStatsPlug()->hash();
			},
			// Gather
			[ &h ] ( const ImagePlug *imageP, const Imath::V2i &tileOrigin, const IECore::MurmurHash &tileHash )
			{
				h.append( tileHash );
			},
			boundsIntersection,
			ImageAlgo::TopToBottom
		);
		h.append( areaMult );
	}
}

void ImageStats::compute( ValuePlug *output, const Context *context ) const
{
	ImagePlug::ViewScope viewScope( context );

	std::string view = viewPlug()->getValue();
	if( !view.size() )
	{
		view = context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName );
	}
	viewScope.setViewNameChecked( &view, inPlug()->viewNames().get() );

	const Plug *parent = output->parent<Plug>();
	if(
		parent == minPlug() ||
		parent == maxPlug() ||
		parent == averagePlug()
	)
	{
		IECore::ConstStringVectorDataPtr channelsData = channelsPlug()->getValue();
		IECore::ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
		const std::string channelName = ::channelName( output, channelsData->readable(), channelNamesData->readable() );
		if( channelName.empty() )
		{
			static_cast<FloatPlug *>( output )->setValue( 0.0f );
			return;
		}

		int statIndex = ( parent == averagePlug() ) ? 2 : ( parent == maxPlug() );

		ImagePlug::ChannelDataScope s( context );
		s.setChannelName( &channelName );
		Imath::V3d stats = boost::static_pointer_cast<const IECore::V3dData>( allStatsPlug()->getValue() )->readable();
		static_cast<FloatPlug *>( output )->setValue( stats[ statIndex ] );
		return;
	}

	Imath::Box2i boundsIntersection;
	bool beyondDataWindow;
	double areaMult;

	{
		ImagePlug::GlobalScope s( viewScope.context() );
		int areaSource = areaSourcePlug()->getValue();
		Imath::Box2i area;
		switch ( areaSource )
		{
			case ImageStats::DataWindow:
			{
				area = inPlug()->dataWindowPlug()->getValue();
				break;
			}
			case ImageStats::DisplayWindow:
			{
				area = inPlug()->formatPlug()->getValue().getDisplayWindow();
				break;
			}
			default:
			{
				area = areaPlug()->getValue();
				break;
			}
		}
		const Imath::Box2i dataWindow = flattenedInPlug()->dataWindowPlug()->getValue();
		boundsIntersection = BufferAlgo::intersection( area, dataWindow );
		beyondDataWindow = boundsIntersection != area;
		areaMult = double(area.size().x) * area.size().y;
	}

	if( output == tileStatsPlug() )
	{
		Imath::V2i tileOrigin = context->get<Imath::V2i>( ImagePlug::tileOriginContextName );
		const Imath::Box2i tileBound = BufferAlgo::intersection(
			Imath::Box2i( boundsIntersection.min - tileOrigin, boundsIntersection.max - tileOrigin ),
			Imath::Box2i( Imath::V2i( 0 ), Imath::V2i( ImagePlug::tileSize() ) )
		);

		IECore::ConstFloatVectorDataPtr channelData = flattenedInPlug()->channelDataPlug()->getValue();

		float min = std::numeric_limits<float>::infinity();
		float max = -std::numeric_limits<float>::infinity();
		double sum = 0.;

		const std::vector<float> &channel = channelData->readable();
		for( int y = tileBound.min.y; y < tileBound.max.y; ++y )
		{
			for( int x = tileBound.min.x; x < tileBound.max.x; ++x )
			{
				float v = channel[ x + y * ImagePlug::tileSize() ];
				min = std::min( v, min );
				max = std::max( v, max );
				sum += v;
			}
		}

		static_cast<ObjectPlug *>( output )->setValue( new IECore::V3dData( Imath::V3d( min, max, sum ) ) );
	}
	else if( output == allStatsPlug() )
	{
		if( BufferAlgo::empty( boundsIntersection ) )
		{
			static_cast<ObjectPlug *>( output )->setValue( new IECore::V3dData( Imath::V3d( 0 ) ) );
			return;
		}
		float min = std::numeric_limits<float>::infinity();
		float max = -std::numeric_limits<float>::infinity();
		double sum = 0.;

		if( beyondDataWindow )
		{
			min = 0.;
			max = 0.;
		}

		// We traverse in TopToBottom order because floating point precision means that changing
		// the order to sum in could produce slightly non-deterministic results
		ImageAlgo::parallelGatherTiles(
			flattenedInPlug(),
			// Tile
			[this] ( const ImagePlug *imageP, const Imath::V2i &tileOrigin ) -> Imath::V3d
			{
				return boost::static_pointer_cast<const IECore::V3dData>( tileStatsPlug()->getValue() )->readable();
			},
			// Gather
			[ &min, &max, &sum ] ( const ImagePlug *imageP, const Imath::V2i &tileOrigin, const Imath::V3d &v )
			{
				min = std::min( float(v[0]), min );
				max = std::max( float(v[1]), max );
				sum += v[2];
			},
			boundsIntersection,
			ImageAlgo::TopToBottom
		);
		float average = sum / areaMult;
		static_cast<ObjectPlug *>( output )->setValue( new IECore::V3dData( Imath::V3d( min, max, average ) ) );
	}
}

ValuePlug::CachePolicy ImageStats::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == allStatsPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}

	return ComputeNode::computeCachePolicy( output );
}

ValuePlug::CachePolicy ImageStats::hashCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == allStatsPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}

	return ComputeNode::hashCachePolicy( output );
}
