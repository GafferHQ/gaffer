//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERIMAGE_IMAGEALGO_INL
#define GAFFERIMAGE_IMAGEALGO_INL

#include "GafferImage/BufferAlgo.h"
#include "GafferImage/ImagePlug.h"

#include "Gaffer/Context.h"

#include "boost/tuple/tuple.hpp"

#include "tbb/tbb.h"

namespace GafferImage
{

namespace ImageAlgo
{

namespace Detail
{

inline Imath::Box2i tileRangeFromDataWindow( const Imath::Box2i &dataWindow )
{
    return Imath::Box2i(
        ImagePlug::tileOrigin( dataWindow.min ) / ImagePlug::tileSize(),
        ImagePlug::tileOrigin( dataWindow.max - Imath::V2i( 1 ) ) / ImagePlug::tileSize() + Imath::V2i( 1 )
    );
}

class TileInputFilter
{
	public:
		TileInputFilter( const Imath::Box2i &dataWindow, TileOrder tileOrder )
			:	m_dataWindow( dataWindow ), m_numTileIndices( numTileIndices( dataWindow ) ),
				m_tileOrder( tileOrder ), m_index( 0 )
		{}

		Imath::V2i operator()( tbb::flow_control &fc ) const
		{
			if( m_index == m_numTileIndices )
			{
				fc.stop();
				return Imath::V2i();
			}

			int i = m_tileOrder == BottomToTop ? m_numTileIndices - 1 - m_index : m_index;
			Imath::V2i result = tileOriginFromIndex( i, m_dataWindow );
			m_index++;
			return result;
		}

	private:

		const Imath::Box2i &m_dataWindow;
		const int m_numTileIndices;
		const TileOrder m_tileOrder;
		// I don't understand why the previous m_it didn't need to be declared mutable, since
		// it is altered in "operator( ... ) const"
		mutable int m_index;
};

} // namespace Detail

} // namespace ImageAlgo

} // namespace GafferImage

//////////////////////////////////////////////////////////////////////////
// Channel name utilities
//////////////////////////////////////////////////////////////////////////

namespace GafferImage
{

namespace ImageAlgo
{

inline std::string layerName( const std::string &channelName )
{
	const size_t p = channelName.find_last_of( '.' );
	if( p == std::string::npos )
	{
		return "";
	}
	else
	{
		return channelName.substr( 0, p );
	}
}

inline std::string baseName( const std::string &channelName )
{
	const size_t p = channelName.find_last_of( '.' );
	if( p == std::string::npos )
	{
		return channelName;
	}
	else
	{
		return channelName.substr( p + 1 );
	}
}

inline std::string channelName( const std::string &layerName, const std::string &baseName )
{
	if( layerName.empty() )
	{
		return baseName;
	}

	return layerName + "." + baseName;
}

inline int colorIndex( const std::string &channelName )
{
	const size_t p = channelName.find_last_of( '.' );

	char baseName;
	if( p == std::string::npos )
	{
		if( channelName.size() != 1 )
		{
			return -1;
		}
		baseName = channelName[0];
	}
	else
	{
		if( p != channelName.size() - 2 )
		{
			return -1;
		}
		baseName = *channelName.rbegin();
	}

	switch( baseName )
	{
		case 'R' :
			return 0;
		case 'G' :
			return 1;
		case 'B' :
			return 2;
		case 'A' :
			return 3;
		default :
			return -1;
	}
}

inline bool channelExists( const ImagePlug *image, const std::string &channelName )
{
	IECore::ConstStringVectorDataPtr channelNamesData = image->channelNamesPlug()->getValue();
	const std::vector<std::string> &channelNames = channelNamesData->readable();

	return channelExists( channelNames, channelName );
}

inline bool channelExists( const std::vector<std::string> &channelNames, const std::string &channelName )
{
	return std::find( channelNames.begin(), channelNames.end(), channelName ) != channelNames.end();
}

//////////////////////////////////////////////////////////////////////////
// Helpers for indexing tiles with an unwrapped integer index
//////////////////////////////////////////////////////////////////////////

inline int numTileIndices( const Imath::Box2i &dataWindow )
{
	const Imath::V2i tileRangeSize = Detail::tileRangeFromDataWindow( dataWindow ).size();
	return tileRangeSize.x * tileRangeSize.y;
}

inline int tileIndexFromOrigin( const Imath::V2i &tileOrigin, const Imath::Box2i &dataWindow )
{
	const Imath::Box2i tileRange = Detail::tileRangeFromDataWindow( dataWindow );
	Imath::V2i index2D = tileOrigin / ImagePlug::tileSize();
	return ( tileRange.max.y - 1 - index2D.y ) * tileRange.size().x + ( index2D.x - tileRange.min.x );
}

inline Imath::V2i tileOriginFromIndex( int index, const Imath::Box2i &dataWindow )
{
	const Imath::Box2i tileRange = Detail::tileRangeFromDataWindow( dataWindow );
	return Imath::V2i(
		(( index % tileRange.size().x ) + tileRange.min.x) * ImagePlug::tileSize(),
		( tileRange.max.y - 1 - ( index / tileRange.size().x ) ) * ImagePlug::tileSize()
	);
}

//////////////////////////////////////////////////////////////////////////
// Parallel processing functions
//////////////////////////////////////////////////////////////////////////


template <class TileFunctor>
void parallelProcessTiles( const ImagePlug *imagePlug, TileFunctor &&functor, const Imath::Box2i &window, TileOrder tileOrder )
{
	Imath::Box2i processWindow = window;
	if( BufferAlgo::empty( processWindow ) )
	{
		processWindow = imagePlug->dataWindowPlug()->getValue();
		if( BufferAlgo::empty( processWindow ) )
		{
			return;
		}
	}

	const Gaffer::ThreadState &threadState = Gaffer::ThreadState::current();

	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );
	parallel_pipeline( tbb::task_scheduler_init::default_num_threads(),

		tbb::make_filter<void, Imath::V2i>(
			tbb::filter::serial,
			Detail::TileInputFilter( processWindow, tileOrder )
		) &

		tbb::make_filter<Imath::V2i, void>(

			tbb::filter::parallel,

			[ imagePlug, &functor, &threadState ] ( const Imath::V2i &tileOrigin ) {

				ImagePlug::ChannelDataScope channelDataScope( threadState );
				channelDataScope.setTileOrigin( tileOrigin );
				functor( imagePlug, tileOrigin );

			}

		),

		// Prevents outer tasks silently cancelling our tasks
		taskGroupContext

	);
}

template <class TileFunctor>
void parallelProcessTiles( const ImagePlug *imagePlug, const std::vector<std::string> &channelNames, TileFunctor &&functor, const Imath::Box2i &window, TileOrder tileOrder )
{

	// In theory, we could run in parallel over all tiles and channels at the same time.  However,
	// hitting all channels of a tile at once can lead to some terrible bottlenecks whenever all channels
	// depend on the same channel ( For example, an Unpremultiply requiring A ).  This could result in
	// multiple threads needing to compute the same tile channel at the same time, which currently can
	// resulting in duplicate computes or spinlocking.
	//
	// By accessing one channel first on a single thread, we make sure that any shared data is loaded first,
	// before we access any remaining channels in parallel

	if( channelNames.size() == 0 )
	{
		return;
	}

	auto f = [&channelNames, &functor] ( const ImagePlug *imagePlug, const Imath::V2i &tileOrigin )
	{
		const Gaffer::ThreadState &threadState = Gaffer::ThreadState::current();
		{
			ImagePlug::ChannelDataScope channelDataScope( threadState );
			channelDataScope.setChannelName( channelNames[0] );
			functor( imagePlug, channelNames[0], tileOrigin );
		}

		tbb::parallel_for_each(
			channelNames.begin() + 1, channelNames.end(),
			[&threadState, &functor, imagePlug, tileOrigin]( const std::string &channelName )
			{
				ImagePlug::ChannelDataScope channelDataScope( threadState );
				channelDataScope.setChannelName( channelName );
				functor( imagePlug, channelName, tileOrigin );
			}
		);
	};

	parallelProcessTiles( imagePlug, f, window, tileOrder );
}

template <class TileFunctor, class GatherFunctor>
void parallelGatherTiles( const ImagePlug *imagePlug, const TileFunctor &tileFunctor, GatherFunctor &&gatherFunctor, const Imath::Box2i &window, TileOrder tileOrder )
{
	Imath::Box2i processWindow = window;
	if( BufferAlgo::empty( processWindow ) )
	{
		processWindow = imagePlug->dataWindowPlug()->getValue();
		if( BufferAlgo::empty( processWindow ) )
		{
			return;
		}
	}

	typedef typename std::result_of<TileFunctor( const ImagePlug *, const Imath::V2i & )>::type TileFunctorResult;
	typedef std::pair<Imath::V2i, TileFunctorResult> TileFilterResult;

	const Gaffer::ThreadState &threadState = Gaffer::ThreadState::current();

	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );
	parallel_pipeline( tbb::task_scheduler_init::default_num_threads(),

		tbb::make_filter<void, Imath::V2i>(
			tbb::filter::serial,
			Detail::TileInputFilter( processWindow, tileOrder )
		) &

		tbb::make_filter<Imath::V2i, TileFilterResult>(

			tbb::filter::parallel,

			[ imagePlug, &tileFunctor, &threadState ] ( const Imath::V2i &tileOrigin ) {

				ImagePlug::ChannelDataScope channelDataScope( threadState );
				channelDataScope.setTileOrigin( tileOrigin );

				return TileFilterResult(
					tileOrigin, tileFunctor( imagePlug, tileOrigin )
				);
			}

		) &

		tbb::make_filter<TileFilterResult, void>(

			tileOrder == Unordered ? tbb::filter::serial_out_of_order : tbb::filter::serial_in_order,

			[ imagePlug, &gatherFunctor, &threadState ] ( const TileFilterResult &input ) {

				ImagePlug::ChannelDataScope channelDataScope( threadState );
				channelDataScope.setTileOrigin( input.first );

				gatherFunctor( imagePlug, input.first, input.second );

			}

		),

		// Prevents outer tasks silently cancelling our tasks
		taskGroupContext

	);
}

template <class TileFunctor, class GatherFunctor>
void parallelGatherTiles( const ImagePlug *imagePlug, const std::vector<std::string> &channelNames, const TileFunctor &tileFunctor, GatherFunctor &&gatherFunctor, const Imath::Box2i &window, TileOrder tileOrder )
{
	typedef typename std::result_of<TileFunctor( const ImagePlug *, const std::string &, const Imath::V2i & )>::type TileFunctorResult;
	typedef std::vector< TileFunctorResult > WholeTileResult;

	if( channelNames.size() == 0 )
	{
		return;
	}

	auto f = [&channelNames, &tileFunctor] ( const ImagePlug *imagePlug, const Imath::V2i &tileOrigin )
	{
		WholeTileResult result;
		result.resize( channelNames.size() );

		const Gaffer::ThreadState &threadState = Gaffer::ThreadState::current();
		{
			ImagePlug::ChannelDataScope channelDataScope( threadState );
			channelDataScope.setChannelName( channelNames[0] );
			result[0] = tileFunctor( imagePlug, channelNames[0], tileOrigin );
		}

		tbb::parallel_for(
			(size_t)1, channelNames.size(),
			[&result, threadState, tileFunctor, channelNames, imagePlug, tileOrigin]( int i )
			{
				ImagePlug::ChannelDataScope channelDataScope( threadState );
				channelDataScope.setChannelName( channelNames[i] );
				result[i] = tileFunctor( imagePlug, channelNames[i], tileOrigin );
			}
		);

		return result;
	};

	auto g = [&channelNames, &gatherFunctor] ( const ImagePlug *imagePlug, const Imath::V2i &tileOrigin, const WholeTileResult &tileData )
	{
		for( unsigned int i = 0; i < tileData.size(); i++ )
		{
			gatherFunctor( imagePlug, channelNames[i], tileOrigin, tileData[i] );
		}
	};

	parallelGatherTiles( imagePlug, f, g, window, tileOrder );
}

} // namespace ImageAlgo

} // namespace GafferImage

#endif // GAFFERIMAGE_IMAGEALGO_INL
