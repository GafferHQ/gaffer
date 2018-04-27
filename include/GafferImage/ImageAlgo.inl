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

template <class ThreadableFunctor>
class ProcessTiles
{
	public:
		ProcessTiles(
			ThreadableFunctor &functor,
			const ImagePlug* imagePlug,
			const Imath::V2i &tilesOrigin,
			const Gaffer::Context *context
		) :
			m_functor( functor ),
			m_imagePlug( imagePlug ),
			m_tilesOrigin( tilesOrigin ),
			m_parentContext( context )
		{}

		ProcessTiles(
			ThreadableFunctor &functor,
			const ImagePlug* imagePlug,
			const std::vector<std::string> &channelNames,
			const Imath::V2i &tilesOrigin,
			const Gaffer::Context *context
		) :
			m_functor( functor ),
			m_imagePlug( imagePlug ),
			m_channelNames( channelNames ),
			m_tilesOrigin( tilesOrigin ),
			m_parentContext( context )
		{}

		void operator()( const tbb::blocked_range2d<size_t>& r ) const
		{
			ImagePlug::ChannelDataScope channelDataScope( m_parentContext );

			Imath::V2i tileId;
			Imath::V2i tileIdMax( r.rows().end(), r.cols().end() );

			for( tileId.x = r.rows().begin(); tileId.x < tileIdMax.x; ++tileId.x )
			{
				for( tileId.y = r.cols().begin(); tileId.y < tileIdMax.y; ++tileId.y )
				{
					Imath::V2i tileOrigin = m_tilesOrigin + ( tileId * ImagePlug::tileSize() );
					channelDataScope.setTileOrigin( tileOrigin );

					m_functor( m_imagePlug, tileOrigin );
				}
			}
		}

		void operator()( const tbb::blocked_range3d<size_t>& r ) const
		{
			ImagePlug::ChannelDataScope channelDataScope( m_parentContext );

			Imath::V2i tileId;
			Imath::V2i tileIdMax( r.rows().end(), r.cols().end() );

			for( tileId.x = r.rows().begin(); tileId.x < tileIdMax.x; ++tileId.x )
			{
				for( tileId.y = r.cols().begin(); tileId.y < tileIdMax.y; ++tileId.y )
				{
					Imath::V2i tileOrigin = m_tilesOrigin + ( tileId * ImagePlug::tileSize() );
					channelDataScope.setTileOrigin( tileOrigin );

					for( size_t channelIndex = r.pages().begin(); channelIndex < r.pages().end(); ++channelIndex )
					{
						channelDataScope.setChannelName( m_channelNames[channelIndex] );

						m_functor( m_imagePlug, m_channelNames[channelIndex], tileOrigin );
					}
				}
			}
		}

	private:
		ThreadableFunctor &m_functor;
		const ImagePlug *m_imagePlug;
		const std::vector<std::string> m_channelNames; // Don't declare as a reference, as it may not be set in the constructor
		const Imath::V2i &m_tilesOrigin;
		const Gaffer::Context *m_parentContext;
};

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

class TileChannelInputIterator : public boost::iterator_facade<TileChannelInputIterator, const OriginAndName, boost::forward_traversal_tag>
{

	public :

		TileChannelInputIterator(
			const Imath::Box2i &window,
			const std::vector<std::string> &channelNames,
			const TileOrder tileOrder
		) :
			m_originIt( window, tileOrder ),
			m_channelNames( channelNames ),
			m_channelIt( m_channelNames.begin() )
		{
			m_value.origin = *m_originIt;
			m_value.name = *m_channelIt;
		}

		bool done() const
		{
			return m_originIt.done();
		}

	private :

		friend class boost::iterator_core_access;

		void increment()
		{
			if( ++m_channelIt == m_channelNames.end() )
			{
				m_channelIt = m_channelNames.begin();
				++m_originIt;
				if( !m_originIt.done() )
				{
					m_value.origin = *m_originIt;
				}
			}
			m_value.name = *m_channelIt;
		}

		const OriginAndName &dereference() const
		{
			return m_value;
		}

		TileInputIterator m_originIt;

		const std::vector<std::string> m_channelNames;
		std::vector<std::string>::const_iterator m_channelIt;

		OriginAndName m_value;

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

template<class TileFunctor>
class TileFunctorFilter
{
	public:
		TileFunctorFilter(
			TileFunctor &functor,
			const ImagePlug *imagePlug,
			const Gaffer::Context *context
		) :
			m_functor( functor ),
			m_imagePlug( imagePlug ),
			m_parentContext( context )
		{}

		boost::tuple<Imath::V2i, typename TileFunctor::Result> operator()( const Imath::V2i &tileOrigin ) const
		{
			ImagePlug::ChannelDataScope channelDataScope( m_parentContext );
			channelDataScope.setTileOrigin( tileOrigin );

			typename TileFunctor::Result result = m_functor( m_imagePlug, tileOrigin );

			return boost::tuple<Imath::V2i, typename TileFunctor::Result>( tileOrigin, result );
		}

		boost::tuple<OriginAndName, typename TileFunctor::Result> operator()( OriginAndName &it ) const
		{
			ImagePlug::ChannelDataScope channelDataScope( m_parentContext );
			channelDataScope.setTileOrigin( it.origin );
			channelDataScope.setChannelName( it.name );

			typename TileFunctor::Result result = m_functor( m_imagePlug, it.name, it.origin );

			return boost::tuple<OriginAndName, typename TileFunctor::Result>( it, result );
		}

	private:
		TileFunctor &m_functor;
		const ImagePlug *m_imagePlug;
		const Gaffer::Context *m_parentContext;
};

template<class GatherFunctor, class TileFunctor>
class GatherFunctorFilter
{
	public:
		GatherFunctorFilter(
			GatherFunctor &functor,
			const ImagePlug *imagePlug,
			const Gaffer::Context *context
		) :
			m_functor( functor ),
			m_imagePlug( imagePlug ),
			m_parentContext( context )
		{}

		void operator()( boost::tuple<Imath::V2i, typename TileFunctor::Result> &it ) const
		{
			ImagePlug::ChannelDataScope channelDataScope( m_parentContext );
			channelDataScope.setTileOrigin( boost::get<0>( it ) );

			m_functor( m_imagePlug, boost::get<0>( it ), boost::get<1>( it ) );
		}

		void operator()( boost::tuple<OriginAndName, typename TileFunctor::Result> &it ) const
		{
			ImagePlug::ChannelDataScope channelDataScope( m_parentContext );
			channelDataScope.setTileOrigin( boost::get<0>( it ).origin );
			channelDataScope.setChannelName( boost::get<0>( it ).name );

			m_functor( m_imagePlug, boost::get<0>( it ).name, boost::get<0>( it ).origin, boost::get<1>( it ) );
		}

	private:
		GatherFunctor &m_functor;
		const ImagePlug *m_imagePlug;
		const Gaffer::Context *m_parentContext;
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

template <class ThreadableFunctor>
void parallelProcessTiles( const ImagePlug *imagePlug, ThreadableFunctor &functor, const Imath::Box2i &window )
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

	const Imath::V2i tilesOrigin = ImagePlug::tileOrigin( processWindow.min );
	const Imath::V2i numTiles = ( ( ImagePlug::tileOrigin( processWindow.max - Imath::V2i( 1 ) ) - tilesOrigin ) / ImagePlug::tileSize() ) + Imath::V2i( 1 );

	parallel_for(
		tbb::blocked_range2d<size_t>( 0, numTiles.x, 1, 0, numTiles.y, 1 ),
		Detail::ProcessTiles<ThreadableFunctor>( functor, imagePlug, tilesOrigin, Gaffer::Context::current() )
	);
}

template <class ThreadableFunctor>
void parallelProcessTiles( const ImagePlug *imagePlug, const std::vector<std::string> &channelNames, ThreadableFunctor &functor, const Imath::Box2i &window )
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

	const Imath::V2i tilesOrigin = ImagePlug::tileOrigin( processWindow.min );
	Imath::V2i numTiles = ( ( ImagePlug::tileOrigin( processWindow.max - Imath::V2i( 1 ) ) - tilesOrigin ) / ImagePlug::tileSize() ) + Imath::V2i( 1 );

	parallel_for(
		tbb::blocked_range3d<size_t>( 0, channelNames.size(), 1, 0, numTiles.x, 1, 0, numTiles.y, 1 ),
		Detail::ProcessTiles<ThreadableFunctor>( functor, imagePlug, channelNames, tilesOrigin, Gaffer::Context::current() )
	);
}

template <class TileFunctor, class GatherFunctor>
void parallelGatherTiles( const ImagePlug *imagePlug, TileFunctor &tileFunctor, GatherFunctor &gatherFunctor, const Imath::Box2i &window, TileOrder tileOrder )
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

	Detail::TileInputIterator tileIterator( processWindow, tileOrder );

	parallel_pipeline( tbb::task_scheduler_init::default_num_threads(),
		tbb::make_filter<void, Imath::V2i>(
			tbb::filter::serial,
			Detail::TileInputFilter<Detail::TileInputIterator>( tileIterator )
		) &
		tbb::make_filter<Imath::V2i, boost::tuple<Imath::V2i, typename TileFunctor::Result>>(
			tbb::filter::parallel,
			Detail::TileFunctorFilter<TileFunctor>( tileFunctor, imagePlug, Gaffer::Context::current() )
		) &
		tbb::make_filter<boost::tuple<Imath::V2i, typename TileFunctor::Result>, void>(
			tileOrder == Unordered ? tbb::filter::serial_out_of_order : tbb::filter::serial_in_order,
			Detail::GatherFunctorFilter<GatherFunctor, TileFunctor>( gatherFunctor, imagePlug, Gaffer::Context::current() )
		)
	);
}

template <class TileFunctor, class GatherFunctor>
void parallelGatherTiles( const ImagePlug *imagePlug, const std::vector<std::string> &channelNames, TileFunctor &tileFunctor, GatherFunctor &gatherFunctor, const Imath::Box2i &window, TileOrder tileOrder )
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

	Detail::TileChannelInputIterator tileIterator( processWindow, channelNames, tileOrder );

	parallel_pipeline(
		tbb::task_scheduler_init::default_num_threads(),
		tbb::make_filter<void, Detail::OriginAndName> (
			tbb::filter::serial_in_order,
			Detail::TileInputFilter<Detail::TileChannelInputIterator>( tileIterator )
		) &
		tbb::make_filter<Detail::OriginAndName, boost::tuple<Detail::OriginAndName, typename TileFunctor::Result>>(
			tbb::filter::parallel,
			Detail::TileFunctorFilter<TileFunctor>( tileFunctor, imagePlug, Gaffer::Context::current() )
		) &
		tbb::make_filter<boost::tuple<Detail::OriginAndName, typename TileFunctor::Result>, void>(
			tileOrder == Unordered ? tbb::filter::serial_out_of_order : tbb::filter::serial_in_order,
			Detail::GatherFunctorFilter<GatherFunctor, TileFunctor>( gatherFunctor, imagePlug, Gaffer::Context::current() )
		)
	);
}

} // namespace ImageAlgo

} // namespace GafferImage

#endif // GAFFERIMAGE_IMAGEALGO_INL
