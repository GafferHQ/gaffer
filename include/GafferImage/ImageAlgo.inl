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

#pragma once

#include "GafferImage/BufferAlgo.h"
#include "GafferImage/ImagePlug.h"

#include "Gaffer/Context.h"

#include "boost/tuple/tuple.hpp"

#include "tbb/pipeline.h"
#include "tbb/task_scheduler_init.h"

namespace GafferImage
{

namespace ImageAlgo
{

namespace Detail
{

class TileInputIterator : public boost::iterator_facade<TileInputIterator, const Imath::V2i, boost::forward_traversal_tag>
{

	public :

		TileInputIterator(
			const Imath::Box2i &window,
			const TileOrder tileOrder
		) :
			m_range( ImagePlug::tileOrigin( window.min ), ImagePlug::tileOrigin( window.max - Imath::V2i( 1 ) ) ),
			m_tileOrder( tileOrder )
		{
			switch( m_tileOrder )
			{
				case Unordered :
				case TopToBottom :
					m_tileOrigin = Imath::V2i( m_range.min.x, m_range.max.y );
					break;
				case BottomToTop :
					m_tileOrigin = ImagePlug::tileOrigin( m_range.min );
					break;
			}
		}

		bool done() const
		{
			return !m_range.intersects( m_tileOrigin );
		}

	private :

		friend class boost::iterator_core_access;

		void increment()
		{
			m_tileOrigin.x += ImagePlug::tileSize();
			if( m_tileOrigin.x > m_range.max.x )
			{
				m_tileOrigin.x = m_range.min.x;
				switch( m_tileOrder )
				{
					case Unordered :
					case TopToBottom :
						m_tileOrigin.y -= ImagePlug::tileSize();
						break;
					case BottomToTop :
						m_tileOrigin.y += ImagePlug::tileSize();
				}
			}
		}

		const Imath::V2i &dereference() const
		{
			return m_tileOrigin;
		}

		const Imath::Box2i m_range;
		const ImageAlgo::TileOrder m_tileOrder;
		Imath::V2i m_tileOrigin;

};

struct OriginAndName
{
	Imath::V2i origin;
	std::string name;
};

template <class Iterator>
class TileInputFilter
{
	public:
		TileInputFilter( Iterator &it )
			:	m_it( it )
		{}

		typename Iterator::value_type operator()( tbb::flow_control &fc ) const
		{
			if( m_it.done() )
			{
				fc.stop();
				return typename Iterator::value_type();
			}

			typename Iterator::value_type result = *m_it;
			++m_it;
			return result;
		}

	private:

		Iterator &m_it;

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

template <class TileFunctor>
void parallelProcessTiles( const ImagePlug *imagePlug, TileFunctor &&functor, const Imath::Box2i &window, TileOrder tileOrder )
{
	Imath::Box2i processWindow = window;
	if( processWindow == Imath::Box2i() )
	{
		processWindow = imagePlug->dataWindowPlug()->getValue();
	}

	if( BufferAlgo::empty( processWindow ) )
	{
		return;
	}

	Detail::TileInputIterator tileIterator( processWindow, tileOrder );
	const Gaffer::ThreadState &threadState = Gaffer::ThreadState::current();

	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );
	parallel_pipeline( tbb::task_scheduler_init::default_num_threads(),

		tbb::make_filter<void, Imath::V2i>(
			tbb::filter::serial,
			Detail::TileInputFilter<Detail::TileInputIterator>( tileIterator )
		) &

		tbb::make_filter<Imath::V2i, void>(

			tbb::filter::parallel,

			[ imagePlug, &functor, &threadState ] ( const Imath::V2i &tileOrigin ) {

				ImagePlug::ChannelDataScope channelDataScope( threadState );
				channelDataScope.setTileOrigin( &tileOrigin );
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
	// In theory, we could access one channel, then run the rest in parallel, but the overhead of a
	// parallel_for with a small number of items is significant when the upstream network is fast.
	//
	// The simplest option is just to process the channels within a tile serially

	if( channelNames.size() == 0 )
	{
		return;
	}

	auto f = [&channelNames, &functor] ( const ImagePlug *imagePlug, const Imath::V2i &tileOrigin )
	{
		ImagePlug::ChannelDataScope channelDataScope( Gaffer::Context::current() );

		for( const std::string &c : channelNames )
		{
			channelDataScope.setChannelName( &c );
			functor( imagePlug, c, tileOrigin );
		}
	};

	parallelProcessTiles( imagePlug, f, window, tileOrder );
}

template <class TileFunctor, class GatherFunctor>
void parallelGatherTiles( const ImagePlug *imagePlug, const TileFunctor &tileFunctor, GatherFunctor &&gatherFunctor, const Imath::Box2i &window, TileOrder tileOrder )
{
	Imath::Box2i processWindow = window;
	if( processWindow == Imath::Box2i() )
	{
		processWindow = imagePlug->dataWindowPlug()->getValue();
	}

	if( BufferAlgo::empty( processWindow ) )
	{
		return;
	}

	using TileFunctorResult = std::invoke_result_t<TileFunctor, const ImagePlug *, const Imath::V2i &>;
	using TileFilterResult = std::pair<Imath::V2i, TileFunctorResult>;

	Detail::TileInputIterator tileIterator( processWindow, tileOrder );
	const Gaffer::ThreadState &threadState = Gaffer::ThreadState::current();

	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );
	parallel_pipeline( tbb::task_scheduler_init::default_num_threads(),

		tbb::make_filter<void, Imath::V2i>(
			tbb::filter::serial,
			Detail::TileInputFilter<Detail::TileInputIterator>( tileIterator )
		) &

		tbb::make_filter<Imath::V2i, TileFilterResult>(

			tbb::filter::parallel,

			[ imagePlug, &tileFunctor, &threadState ] ( const Imath::V2i &tileOrigin ) {

				ImagePlug::ChannelDataScope channelDataScope( threadState );
				channelDataScope.setTileOrigin( &tileOrigin );

				return TileFilterResult(
					tileOrigin, tileFunctor( imagePlug, tileOrigin )
				);
			}

		) &

		tbb::make_filter<TileFilterResult, void>(

			tileOrder == Unordered ? tbb::filter::serial_out_of_order : tbb::filter::serial_in_order,

			[ imagePlug, &gatherFunctor, &threadState ] ( const TileFilterResult &input ) {

				ImagePlug::ChannelDataScope channelDataScope( threadState );
				channelDataScope.setTileOrigin( &input.first );

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
	using TileFunctorResult = std::invoke_result_t<TileFunctor, const ImagePlug *, const std::string &, const Imath::V2i &>;
	using WholeTileResult = std::vector<TileFunctorResult>;

	if( channelNames.size() == 0 )
	{
		return;
	}

	auto f = [&channelNames, &tileFunctor] ( const ImagePlug *imagePlug, const Imath::V2i &tileOrigin )
	{
		WholeTileResult result;
		result.resize( channelNames.size() );

		ImagePlug::ChannelDataScope channelDataScope( Gaffer::Context::current() );
		for( unsigned int i = 0; i < channelNames.size(); i++ )
		{
			channelDataScope.setChannelName( &channelNames[i] );
			result[i] = tileFunctor( imagePlug, channelNames[i], tileOrigin );
		}

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
