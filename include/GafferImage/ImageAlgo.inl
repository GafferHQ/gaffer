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
void parallelProcessTiles( const ImagePlug *imagePlug, ThreadableFunctor &functor, const Imath::Box2i &window, TileOrder tileOrder )
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
	const Gaffer::Context *context = Gaffer::Context::current();

	parallel_pipeline( tbb::task_scheduler_init::default_num_threads(),

		tbb::make_filter<void, Imath::V2i>(
			tbb::filter::serial,
			Detail::TileInputFilter<Detail::TileInputIterator>( tileIterator )
		) &

		tbb::make_filter<Imath::V2i, void>(

			tbb::filter::parallel,

			[ imagePlug, &functor, context ] ( const Imath::V2i &tileOrigin ) {

				ImagePlug::ChannelDataScope channelDataScope( context );
				channelDataScope.setTileOrigin( tileOrigin );
				functor( imagePlug, tileOrigin );

			}

		)

	);
}

template <class ThreadableFunctor>
void parallelProcessTiles( const ImagePlug *imagePlug, const std::vector<std::string> &channelNames, ThreadableFunctor &functor, const Imath::Box2i &window, TileOrder tileOrder )
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
	const Gaffer::Context *context = Gaffer::Context::current();

	parallel_pipeline(

		tbb::task_scheduler_init::default_num_threads(),

		tbb::make_filter<void, Detail::OriginAndName> (
			tbb::filter::serial_in_order,
			Detail::TileInputFilter<Detail::TileChannelInputIterator>( tileIterator )
		) &

		tbb::make_filter<Detail::OriginAndName, void>(

			tbb::filter::parallel,

			[ imagePlug, &functor, context ] ( const Detail::OriginAndName &input ) {

				ImagePlug::ChannelDataScope channelDataScope( context );
				channelDataScope.setTileOrigin( input.origin );
				channelDataScope.setChannelName( input.name );
				functor( imagePlug, input.name, input.origin );

			}

		)

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

	typedef typename std::result_of<TileFunctor( const ImagePlug *, const Imath::V2i & )>::type TileFunctorResult;
	typedef std::pair<Imath::V2i, TileFunctorResult> TileFilterResult;

	Detail::TileInputIterator tileIterator( processWindow, tileOrder );
	const Gaffer::Context *context = Gaffer::Context::current();

	parallel_pipeline( tbb::task_scheduler_init::default_num_threads(),

		tbb::make_filter<void, Imath::V2i>(
			tbb::filter::serial,
			Detail::TileInputFilter<Detail::TileInputIterator>( tileIterator )
		) &

		tbb::make_filter<Imath::V2i, TileFilterResult>(

			tbb::filter::parallel,

			[ imagePlug, &tileFunctor, context ] ( const Imath::V2i &tileOrigin ) {

				ImagePlug::ChannelDataScope channelDataScope( context );
				channelDataScope.setTileOrigin( tileOrigin );

				return TileFilterResult(
					tileOrigin, tileFunctor( imagePlug, tileOrigin )
				);
			}

		) &

		tbb::make_filter<TileFilterResult, void>(

			tileOrder == Unordered ? tbb::filter::serial_out_of_order : tbb::filter::serial_in_order,

			[ imagePlug, &gatherFunctor, context ] ( const TileFilterResult &input ) {

				ImagePlug::ChannelDataScope channelDataScope( context );
				channelDataScope.setTileOrigin( input.first );

				gatherFunctor( imagePlug, input.first, input.second );

			}

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

	typedef typename std::result_of<TileFunctor( const ImagePlug *, const std::string &, const Imath::V2i & )>::type TileFunctorResult;
	typedef std::pair<Detail::OriginAndName, TileFunctorResult> TileFilterResult;

	Detail::TileChannelInputIterator tileIterator( processWindow, channelNames, tileOrder );
	const Gaffer::Context *context = Gaffer::Context::current();

	parallel_pipeline(

		tbb::task_scheduler_init::default_num_threads(),

		tbb::make_filter<void, Detail::OriginAndName> (
			tbb::filter::serial_in_order,
			Detail::TileInputFilter<Detail::TileChannelInputIterator>( tileIterator )
		) &

		tbb::make_filter<Detail::OriginAndName, TileFilterResult>(

			tbb::filter::parallel,

			[ imagePlug, &tileFunctor, context ] ( const Detail::OriginAndName &input ) {

				ImagePlug::ChannelDataScope channelDataScope( context );
				channelDataScope.setTileOrigin( input.origin );
				channelDataScope.setChannelName( input.name );

				return TileFilterResult(
					input,
					tileFunctor( imagePlug, input.name, input.origin )
				);
			}

		) &

		tbb::make_filter<TileFilterResult, void>(

			tileOrder == Unordered ? tbb::filter::serial_out_of_order : tbb::filter::serial_in_order,

			[ imagePlug, &gatherFunctor, context ] ( const TileFilterResult &input ) {

				ImagePlug::ChannelDataScope channelDataScope( context );
				channelDataScope.setTileOrigin( input.first.origin );
				channelDataScope.setChannelName( input.first.name );

				gatherFunctor( imagePlug, input.first.name, input.first.origin, input.second );
			}

		)

	);
}

} // namespace ImageAlgo

} // namespace GafferImage

#endif // GAFFERIMAGE_IMAGEALGO_INL
