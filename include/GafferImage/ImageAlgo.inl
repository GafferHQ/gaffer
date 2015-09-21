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

#include "tbb/tbb.h"
#include "boost/tuple/tuple.hpp"

#include "Gaffer/Context.h"
#include "GafferImage/ImagePlug.h"
#include "GafferImage/BufferAlgo.h"

namespace GafferImage
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
			Gaffer::ContextPtr context = new Gaffer::Context( *m_parentContext, Gaffer::Context::Borrowed );
			Gaffer::Context::Scope scope( context.get() );

			Imath::V2i tileId;
			Imath::V2i tileIdMax( r.rows().end(), r.cols().end() );

			for( tileId.x = r.rows().begin(); tileId.x < tileIdMax.x; ++tileId.x )
			{
				for( tileId.y = r.cols().begin(); tileId.y < tileIdMax.y; ++tileId.y )
				{
					Imath::V2i tileOrigin = m_tilesOrigin + ( tileId * ImagePlug::tileSize() );
					context->set( ImagePlug::tileOriginContextName, tileOrigin );

					m_functor( m_imagePlug, tileOrigin );
				}
			}
		}

		void operator()( const tbb::blocked_range3d<size_t>& r ) const
		{
			Gaffer::ContextPtr context = new Gaffer::Context( *m_parentContext, Gaffer::Context::Borrowed );
			Gaffer::Context::Scope scope( context.get() );

			Imath::V2i tileId;
			Imath::V2i tileIdMax( r.rows().end(), r.cols().end() );

			for( tileId.x = r.rows().begin(); tileId.x < tileIdMax.x; ++tileId.x )
			{
				for( tileId.y = r.cols().begin(); tileId.y < tileIdMax.y; ++tileId.y )
				{
					Imath::V2i tileOrigin = m_tilesOrigin + ( tileId * ImagePlug::tileSize() );
					context->set( ImagePlug::tileOriginContextName, tileOrigin );

					for( size_t channelIndex = r.pages().begin(); channelIndex < r.pages().end(); ++channelIndex )
					{
						context->set( ImagePlug::channelNameContextName, m_channelNames[channelIndex] );

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

class TileInputIterator
{
	public:
		typedef boost::tuple<Imath::V2i> Result;

		TileInputIterator(
				const Imath::V2i &numTiles,
				const TileOrder tileOrder
			) :
				m_numTiles( numTiles ),
				m_tileOrder( tileOrder ),
				nextTileId( Imath::V2i( 0 ) )
		{
			if( m_tileOrder == TopToBottom )
			{
				nextTileId.y = m_numTiles.y - 1;
			}
		}

		bool finished()
		{
			if( m_tileOrder == TopToBottom )
			{
				return nextTileId.y < 0;
			}
			else
			{
				return nextTileId.y >= m_numTiles.y;
			}
		}

		Result next()
		{
			Imath::V2i returnTileId( nextTileId );

			++nextTileId.x;
			if( nextTileId.x >= m_numTiles.x )
			{
				nextTileId.x = 0;
				if( m_tileOrder == TopToBottom )
				{
					--nextTileId.y;
				}
				else
				{
					++nextTileId.y;
				}
			}

			return Result( returnTileId );
		}

	private:
		const Imath::V2i &m_numTiles;
		const TileOrder m_tileOrder;
		Imath::V2i nextTileId;
};

class TileChannelInputIterator
{
	public:
		typedef boost::tuple<size_t, Imath::V2i> Result;

		TileChannelInputIterator(
				const std::vector<std::string> &channelNames,
				const Imath::V2i &numTiles,
				const TileOrder tileOrder
			) :
				m_channelNames( channelNames ),
				m_numTiles( numTiles ),
				m_tileOrder( tileOrder ),
				nextTileId( Imath::V2i( 0 ) ),
				nextChannelIndex( 0 )
		{
			if( m_tileOrder == TopToBottom )
			{
				nextTileId.y = m_numTiles.y - 1;
			}
		}

		bool finished()
		{
			if( m_tileOrder == TopToBottom )
			{
				return nextTileId.y < 0;
			}
			else
			{
				return nextTileId.y >= m_numTiles.y;
			}
		}

		Result next()
		{
			Imath::V2i returnTileId( nextTileId );
			size_t returnChannelIndex( nextChannelIndex );

			++nextChannelIndex;
			if( nextChannelIndex >= m_channelNames.size() )
			{
				nextChannelIndex = 0;

				++nextTileId.x;
				if( nextTileId.x >= m_numTiles.x )
				{
					nextTileId.x = 0;
					if( m_tileOrder == TopToBottom )
					{
						--nextTileId.y;
					}
					else
					{
						++nextTileId.y;
					}
				}
			}

			return Result( returnChannelIndex, returnTileId );
		}

	private:
		const std::vector<std::string> &m_channelNames;
		const Imath::V2i &m_numTiles;
		const TileOrder m_tileOrder;
		Imath::V2i nextTileId;
		size_t nextChannelIndex;

};

template <class InputIterator>
class TileInputFilter
{
	public:
		TileInputFilter( InputIterator &it ) :
				m_it( it )
		{}

		typename InputIterator::Result operator()( tbb::flow_control &fc ) const
		{
			if( m_it.finished() )
			{
				fc.stop();
			}

			return m_it.next();
		}

	private:
		InputIterator &m_it;
};

template<class TileFunctor>
class TileFunctorFilter
{
	public:
		TileFunctorFilter(
				TileFunctor &functor,
				const ImagePlug *imagePlug,
				const Imath::V2i &tilesOrigin,
				const Gaffer::Context *context
			) :
				m_functor( functor ),
				m_imagePlug( imagePlug ),
				m_tilesOrigin( tilesOrigin ),
				m_parentContext( context )
		{}

		TileFunctorFilter(
				TileFunctor &functor,
				const ImagePlug *imagePlug,
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

		boost::tuple<size_t, Imath::V2i, typename TileFunctor::Result> operator()( boost::tuple<size_t, Imath::V2i> &it ) const
		{
			Gaffer::ContextPtr context = new Gaffer::Context( *m_parentContext, Gaffer::Context::Borrowed );
			Gaffer::Context::Scope scope( context.get() );

			const Imath::V2i tileOrigin = m_tilesOrigin + ( boost::get<1>( it ) * ImagePlug::tileSize() );
			context->set( ImagePlug::tileOriginContextName, tileOrigin );
			context->set( ImagePlug::channelNameContextName, m_channelNames[boost::get<0>( it )] );

			typename TileFunctor::Result result = m_functor( m_imagePlug, m_channelNames[boost::get<0>( it )], tileOrigin );

			return boost::tuple<size_t, Imath::V2i, typename TileFunctor::Result>( boost::get<0>( it ), boost::get<1>( it ), result );
		}

		boost::tuple<Imath::V2i, typename TileFunctor::Result> operator()( boost::tuple<Imath::V2i> &it ) const
		{
			Gaffer::ContextPtr context = new Gaffer::Context( *m_parentContext, Gaffer::Context::Borrowed );
			Gaffer::Context::Scope scope( context.get() );

			const Imath::V2i tileOrigin = m_tilesOrigin + ( boost::get<0>( it ) * ImagePlug::tileSize() );
			context->set( ImagePlug::tileOriginContextName, tileOrigin );

			typename TileFunctor::Result result = m_functor( m_imagePlug, tileOrigin );

			return boost::tuple<Imath::V2i, typename TileFunctor::Result>( boost::get<0>( it ), result );
		}

	private:
		TileFunctor &m_functor;
		const ImagePlug *m_imagePlug;
		const std::vector<std::string> m_channelNames; // Don't declare as a reference, as it may not be set in the constructor
		const Imath::V2i &m_tilesOrigin;
		const Gaffer::Context *m_parentContext;
};

template<class GatherFunctor, class TileFunctor>
class GatherFunctorFilter
{
	public:
		GatherFunctorFilter(
				GatherFunctor &functor,
				const ImagePlug *imagePlug,
				const Imath::V2i &tilesOrigin,
				const Gaffer::Context *context
			) :
				m_functor( functor ),
				m_imagePlug( imagePlug ),
				m_tilesOrigin( tilesOrigin ),
				m_parentContext( context )
		{}

		GatherFunctorFilter(
				GatherFunctor &functor,
				const ImagePlug *imagePlug,
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

		void operator()( boost::tuple<size_t, Imath::V2i, typename TileFunctor::Result> &it ) const
		{
			Gaffer::ContextPtr context = new Gaffer::Context( *m_parentContext, Gaffer::Context::Borrowed );
			Gaffer::Context::Scope scope( context.get() );

			const Imath::V2i tileOrigin = m_tilesOrigin + ( boost::get<1>( it ) * ImagePlug::tileSize() );
			context->set( ImagePlug::tileOriginContextName, tileOrigin );
			context->set( ImagePlug::channelNameContextName, m_channelNames[boost::get<0>( it )] );

			m_functor( m_imagePlug, m_channelNames[boost::get<0>( it )], tileOrigin, boost::get<2>( it ) );
		}

		void operator()( boost::tuple<Imath::V2i, typename TileFunctor::Result> &it ) const
		{
			Gaffer::ContextPtr context = new Gaffer::Context( *m_parentContext, Gaffer::Context::Borrowed );
			Gaffer::Context::Scope scope( context.get() );

			const Imath::V2i tileOrigin = m_tilesOrigin + ( boost::get<0>( it ) * ImagePlug::tileSize() );
			context->set( ImagePlug::tileOriginContextName, tileOrigin );

			m_functor( m_imagePlug, tileOrigin, boost::get<1>( it ) );
		}

	private:
		GatherFunctor &m_functor;
		const ImagePlug *m_imagePlug;
		const std::vector<std::string> m_channelNames; // Don't declare as a reference, as it may not be set in the constructor
		const Imath::V2i m_tilesOrigin;
		const Gaffer::Context *m_parentContext;
};

};

//////////////////////////////////////////////////////////////////////////
// Channel name utilities
//////////////////////////////////////////////////////////////////////////

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
	if( empty( processWindow ) )
	{
		processWindow = imagePlug->dataWindowPlug()->getValue();
		if( empty( processWindow ) )
		{
			return;
		}
	}

	const Imath::V2i tilesOrigin = ImagePlug::tileOrigin( processWindow.min );
	const Imath::V2i numTiles = ( ImagePlug::tileOrigin( processWindow.max - Imath::V2i( 1 ) ) - tilesOrigin ) / ImagePlug::tileSize();

	parallel_for( tbb::blocked_range2d<size_t>( 0, numTiles.x, 1, 0, numTiles.y, 1 ),
			  GafferImage::Detail::ProcessTiles<ThreadableFunctor>( functor, imagePlug, tilesOrigin, Gaffer::Context::current() ) );
}

template <class ThreadableFunctor>
void parallelProcessTiles( const ImagePlug *imagePlug, const std::vector<std::string> &channelNames, ThreadableFunctor &functor, const Imath::Box2i &window )
{
	Imath::Box2i processWindow = window;
	if( empty( processWindow ) )
	{
		processWindow = imagePlug->dataWindowPlug()->getValue();
		if( empty( processWindow ) )
		{
			return;
		}
	}

	const Imath::V2i tilesOrigin = ImagePlug::tileOrigin( processWindow.min );
	Imath::V2i numTiles = ( ( ImagePlug::tileOrigin( processWindow.max - Imath::V2i( 1 ) ) - tilesOrigin ) / ImagePlug::tileSize() ) + Imath::V2i( 1 );

	parallel_for( tbb::blocked_range3d<size_t>( 0, channelNames.size(), 1, 0, numTiles.x, 1, 0, numTiles.y, 1 ),
			  GafferImage::Detail::ProcessTiles<ThreadableFunctor>( functor, imagePlug, channelNames, tilesOrigin, Gaffer::Context::current() ) );
}

template <class TileFunctor, class GatherFunctor>
void parallelGatherTiles( const ImagePlug *imagePlug, TileFunctor &tileFunctor, GatherFunctor &gatherFunctor, const Imath::Box2i &window, TileOrder tileOrder )
{
	Imath::Box2i processWindow = window;
	if( empty( processWindow ) )
	{
		processWindow = imagePlug->dataWindowPlug()->getValue();
		if( empty( processWindow ) )
		{
			return;
		}
	}

	const Imath::V2i tilesOrigin = ImagePlug::tileOrigin( processWindow.min );
	const Imath::V2i numTiles = ( ImagePlug::tileOrigin( processWindow.max - Imath::V2i( 1 ) ) - tilesOrigin ) / ImagePlug::tileSize();

	GafferImage::Detail::TileInputIterator inputIterator( numTiles, tileOrder );

	parallel_pipeline( tbb::task_scheduler_init::default_num_threads(),
		tbb::make_filter<void, boost::tuple<Imath::V2i> >(
			tbb::filter::serial,
			GafferImage::Detail::TileInputFilter<GafferImage::Detail::TileInputIterator>( inputIterator )
		) &
		tbb::make_filter<boost::tuple<Imath::V2i>, boost::tuple<Imath::V2i, typename TileFunctor::Result> >(
			tbb::filter::parallel,
			GafferImage::Detail::TileFunctorFilter<TileFunctor>( tileFunctor, imagePlug, tilesOrigin, Gaffer::Context::current() )
		) &
		tbb::make_filter<boost::tuple<Imath::V2i, typename TileFunctor::Result>, void>(
			tileOrder == Unordered ? tbb::filter::serial_out_of_order : tbb::filter::serial_in_order,
			GafferImage::Detail::GatherFunctorFilter<GatherFunctor, TileFunctor>( gatherFunctor, imagePlug, tilesOrigin, Gaffer::Context::current() )
		)
	);
}

template <class TileFunctor, class GatherFunctor>
void parallelGatherTiles( const ImagePlug *imagePlug, const std::vector<std::string> &channelNames, TileFunctor &tileFunctor, GatherFunctor &gatherFunctor, const Imath::Box2i &window, TileOrder tileOrder )
{
	Imath::Box2i processWindow = window;
	if( empty( processWindow ) )
	{
		processWindow = imagePlug->dataWindowPlug()->getValue();
		if( empty( processWindow ) )
		{
			return;
		}
	}

	const Imath::V2i tilesOrigin = ImagePlug::tileOrigin( processWindow.min );
	const Imath::V2i numTiles = ( ImagePlug::tileOrigin( processWindow.max - Imath::V2i( 1 ) ) - tilesOrigin ) / ImagePlug::tileSize() + Imath::V2i( 1 );

	GafferImage::Detail::TileChannelInputIterator inputIterator( channelNames, numTiles, tileOrder );

	parallel_pipeline( tbb::task_scheduler_init::default_num_threads(),
		tbb::make_filter<void, boost::tuple<size_t, Imath::V2i> >(
			tbb::filter::serial_in_order,
			GafferImage::Detail::TileInputFilter<GafferImage::Detail::TileChannelInputIterator>( inputIterator )
		) &
		tbb::make_filter<boost::tuple<size_t, Imath::V2i>, boost::tuple<size_t, Imath::V2i, typename TileFunctor::Result> >(
			tbb::filter::parallel,
			GafferImage::Detail::TileFunctorFilter<TileFunctor>( tileFunctor, imagePlug, channelNames, tilesOrigin, Gaffer::Context::current() )
		) &
		tbb::make_filter<boost::tuple<size_t, Imath::V2i, typename TileFunctor::Result>, void>(
			tileOrder == Unordered ? tbb::filter::serial_out_of_order : tbb::filter::serial_in_order,
			GafferImage::Detail::GatherFunctorFilter<GatherFunctor, TileFunctor>( gatherFunctor, imagePlug, channelNames, tilesOrigin, Gaffer::Context::current() )
		)
	);
}

inline int sampleCount( const std::vector<int>::const_iterator &sampleOffset, const std::vector<int>::const_iterator &sampleOffsetBegin )
{
	if( sampleOffset == sampleOffsetBegin )
	{
		return (*sampleOffset);
	}
	else
	{
		return (*sampleOffset) - (*(sampleOffset-1));
	}
}

inline int sampleCount( const std::vector<int> &sampleOffsets, const Imath::V2i &tilePos )
{
	return sampleCount( sampleOffsets.begin() + tileIndex( tilePos ), sampleOffsets.begin() );
}

template<class T>
inline typename SampleRange<T>::Type sampleRange( std::vector<T> &channelData, const std::vector<int>::const_iterator &sampleOffset, const std::vector<int>::const_iterator &sampleOffsetBegin )
{
	if( sampleOffset == sampleOffsetBegin )
	{
		return boost::make_iterator_range(channelData.begin(), channelData.begin() + (*sampleOffset));
	}
	else
	{
		return boost::make_iterator_range(channelData.begin() + (*(sampleOffset-1)), channelData.begin() + (*sampleOffset));
	}
}

template<class T>
inline typename SampleRange<T>::Type sampleRange( std::vector<T> &channelData, const std::vector<int> &sampleOffsets, const Imath::V2i &tilePos )
{
	return sampleRange( channelData, sampleOffsets.begin() + tileIndex( tilePos ), sampleOffsets.begin() );
}

template<class T>
inline typename ConstSampleRange<T>::Type sampleRange( const std::vector<T> &channelData, const std::vector<int>::const_iterator &sampleOffset, const std::vector<int>::const_iterator &sampleOffsetBegin )
{
	if( sampleOffset == sampleOffsetBegin )
	{
		return boost::make_iterator_range(channelData.begin(), channelData.begin() + (*sampleOffset));
	}
	else
	{
		return boost::make_iterator_range(channelData.begin() + (*(sampleOffset-1)), channelData.begin() + (*sampleOffset));
	}
}

template<class T>
inline typename ConstSampleRange<T>::Type sampleRange( const std::vector<T> &channelData, const std::vector<int> &sampleOffsets, const Imath::V2i &tilePos )
{
	return sampleRange( channelData, sampleOffsets.begin() + tileIndex( tilePos ), sampleOffsets.begin() );
}

inline std::string channelAlpha( const std::string &channelName, const std::vector<std::string> &channelNames )
{
	std::vector<std::string> layers;
	std::string layerName, baseName, alphaName;

	std::size_t layerSplit = channelName.find_last_of( "." );

	std::string chan;

	if( layerSplit == std::string::npos )
	{
		baseName = channelName;
	}
	else
	{
		baseName = channelName.substr( layerSplit+1 );

		while( layerSplit != std::string::npos )
		{
			layers.push_back( channelName.substr( 0, layerSplit ) );
			layerSplit = channelName.find_last_of( ".", layerSplit );
		}
	}

	// These base channels do not have associated alpha channels.
	if( baseName == "A" ||
		baseName == "AR" ||
		baseName == "AG" ||
		baseName == "AB" ||
		baseName == "Z" ||
		baseName == "ZBack" )
	{
		return "";
	}
	else if( baseName == "R" )
	{
		alphaName = "AR";
	}
	else if( baseName == "G" )
	{
		alphaName = "AG";
	}
	else if( baseName == "B" )
	{
		alphaName = "AB";
	}

	for( std::vector<std::string>::iterator layerIt = layers.begin(); layerIt != layers.end(); ++layerIt )
	{
		if( ! alphaName.empty() )
		{
			chan = (*layerIt) + "." + alphaName;
			if( std::find( channelNames.begin(), channelNames.end(), chan ) != channelNames.end() )
			{
				return chan;
			}
		}

		chan = (*layerIt) + ".A";
		if( std::find( channelNames.begin(), channelNames.end(), chan ) != channelNames.end() )
		{
			return chan;
		}
	}

	if( ! alphaName.empty() )
	{
		chan = alphaName;
		if( std::find( channelNames.begin(), channelNames.end(), chan ) != channelNames.end() )
		{
			return chan;
		}
	}

	chan = "A";
	if( std::find( channelNames.begin(), channelNames.end(), chan ) != channelNames.end() )
	{
		return chan;
	}

	return "";
}

inline int tileIndex( const Imath::V2i &tilePos )
{
	return tilePos.x + ( tilePos.y * ImagePlug::tileSize() );
}

} // namespace GafferImage

#endif // GAFFERIMAGE_IMAGEALGO_INL
