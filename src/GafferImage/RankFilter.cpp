//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
//      * Neither the name of Image Engine Design nor the names of
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

#include "GafferImage/RankFilter.h"

#include "GafferImage/Sampler.h"

#include "Gaffer/Context.h"

#include <algorithm>
#include <climits>
#include <boost/heap/d_ary_heap.hpp>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( RankFilter );

size_t RankFilter::g_firstPlugIndex = 0;

RankFilter::RankFilter( const std::string &name, Mode mode )
	: FlatImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new V2iPlug( "radius", Plug::In, V2i( 0 ), V2i( 0 ) ) );
	addChild( new IntPlug( "boundingMode", Plug::In, Sampler::Black, Sampler::Black, Sampler::Clamp ) );
	addChild( new BoolPlug( "expandDataWindow" ) );
	addChild( new StringPlug( "masterChannel" ) );
	addChild( new V2iVectorDataPlug( "__pixelOffsets", Plug::Out, new V2iVectorData ) );

	outPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
	m_mode = mode;
}

RankFilter::~RankFilter()
{
}

Gaffer::V2iPlug *RankFilter::radiusPlug()
{
	return getChild<V2iPlug>( g_firstPlugIndex );
}

const Gaffer::V2iPlug *RankFilter::radiusPlug() const
{
	return getChild<V2iPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *RankFilter::boundingModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *RankFilter::boundingModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *RankFilter::expandDataWindowPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *RankFilter::expandDataWindowPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *RankFilter::masterChannelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *RankFilter::masterChannelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::V2iVectorDataPlug *RankFilter::pixelOffsetsPlug()
{
	return getChild<V2iVectorDataPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::V2iVectorDataPlug *RankFilter::pixelOffsetsPlug() const
{
	return getChild<V2iVectorDataPlug>( g_firstPlugIndex + 4 );
}


void RankFilter::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageProcessor::affects( input, outputs );

	if(
		input == expandDataWindowPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input->parent<V2iPlug>() == radiusPlug()
	)
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
	}

	if(
		input == inPlug()->channelDataPlug() ||
		input->parent<V2iPlug>() == radiusPlug() ||
		input == boundingModePlug() ||
		input == masterChannelPlug()
	)
	{
		outputs.push_back( pixelOffsetsPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void RankFilter::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const V2i radius = radiusPlug()->getValue();
	if( radius == V2i( 0 ) || !expandDataWindowPlug()->getValue() )
	{
		h = inPlug()->dataWindowPlug()->hash();
		return;
	}

	FlatImageProcessor::hashDataWindow( parent, context, h );
	h.append( radius );
}

Imath::Box2i RankFilter::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const V2i radius = radiusPlug()->getValue();
	if( radius == V2i( 0 ) || !expandDataWindowPlug()->getValue() )
	{
		return inPlug()->dataWindowPlug()->getValue();
	}

	Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();
	if( !BufferAlgo::empty( dataWindow ) )
	{
		dataWindow.min -= radius;
		dataWindow.max += radius;
	}
	return dataWindow;
}

namespace
{

const float infinity = std::numeric_limits<float>::infinity();


// The core of our implementation of RankFilter is these Buffer classes.
// Each buffer holds data for each row with within a filter support, allowing us to compute some
// metric for all the rows. The rows are independent, and their order does not matter, which means
// that the buffer can be treated as a circular - to advance to a pixel below the current one,
// just take the y value of the next row, modulo it by the filter size, and replace the buffer
// entry for that rowIndex.
//
// There is also an extra function rowContainsResult which allows testing whether a particular row
// may contain the given result value - this is used just for driver channel mode, where we need to
// find a pixel index that corresponds to the result.


// To compute the maximum of all pixels, we only need to hold the maximum value for each row
class RankMaxBuffer
{
public:
	inline RankMaxBuffer( const V2i &size ) : m_values( size.y )
	{
	}

	inline void sampleRow( int rowIndex, Sampler &sampler, const Box2i &rowBound )
	{
		// Store the maximum value of the given row
		float r = -infinity;
		sampler.visitPixels( rowBound,
			[&r] ( float v, int x, int y )
			{
				r = std::max( r, v );
			}
		);
		m_values[rowIndex] = r;
	}

	inline float currentResult()
	{
		// Return maximum value of all rows
		float result = m_values[0];
		for( int i = 1; i < (int)m_values.size(); i++ )
		{
			result = std::max( result, m_values[i] );
		}
		return result;
	}

	inline bool rowContainsResult( int rowIndex, float result )
	{
		// The given row can only contain the given result if the result is the maximum value of the row
		return m_values[rowIndex] == result;
	}

private:
	std::vector<float> m_values;
};

// To compute the minimum of all pixels, we only need to hold the minimum value for each row
class RankMinBuffer
{
public:
	inline RankMinBuffer( const V2i &size ) : m_values( size.y )
	{
	}

	inline void sampleRow( int rowIndex, Sampler &sampler, const Box2i &rowBound )
	{
		// Store the minimum value of the given row
		float r = infinity;
		sampler.visitPixels( rowBound,
			[&r] ( float v, int x, int y )
			{
				r = std::min( r, v );
			}
		);
		m_values[rowIndex] = r;
	}

	inline float currentResult()
	{
		// Return minimum value of all rows
		float result = m_values[0];
		for( int i = 1; i < (int)m_values.size(); i++ )
		{
			result = std::min( result, m_values[i] );
		}
		return result;
	}

	inline bool rowContainsResult( int rowIndex, float result )
	{
		// The given row can only contain the given result if the result is the minimum value of the row
		return m_values[rowIndex] == result;
	}

private:
	std::vector<float> m_values;
};

// Min and max were easy, but here's where things get interesting.
//
// We can compute the median for the region by storing the pixels for each row, sorted within the row,
// and an integer index we call the "split" for each row.
//
// The split is used to divide each row into a lower and upper section: m_splits[i] is the
// number of elements in the lower set, the remaining elements are in the upper set. Since
// Since the elements in the row are stored sorted, for each row the first m_splits[i] elements are
// all <= all the remaining elements.
//
// We can then think about two conceptual sets - the lower set is the set of all elements in the
// first section for all rows and the upper set is the set of all elements in second section for all
// rows. By choosing appropriate values for m_splits, we can maintain our main important invariant
// that all elements in the lower set are <= all elements in the upper set.
//
// We refer to the lowest element in the upper set as the split value.
//
// If we then adjust m_splits so that the number of elements in the lower set is one less than the
// number of elements in the upper set, then the the split value is the median.
//
// In order to control the number of elements in the lower set, we need to be able to add elements
// while preserving the comparison invariant between the upper and lower sets. To do this, we need to
// take the lowest element from the upper set, which we can do by finding which row has the lowest
// value above the split, and increasing that split. This can be implemented fairly efficiently with
// any sort of priority queue / heap.
//
// Performing N^2/2 heap push/pops would give us an average O( N^2 log N ) runtime however ( in the
// diameter of the filter ), and we want O( N log N ). To achieve this, the key is to not recompute
// the splits from scratch for each pixel. If we keep the splits from the previous pixel, and just
// update one row, then the median position only shifts by a maximum of N ( and it's usually going to
// be much less ).
//
// This requires us in sampleRow to recompute m_splits[i] to match the current m_splitValue ( preserving the
// invariant that the upper set is greater than the lower set ). It also requires us to be able to move
// elements either from the upper set to the lower set, or vice-versa ( the new row could have more or less
// elements below the current cutoff, and we need to adjust the cutoff to bring the number of elements in the
// two sets back to equality ). This is done with two heaps, one for shifting the lowest element of the upper
// set, and one for shifting the greatest element of the lower set.
//
// boost::d_ary_heap keeps handles to each element which are updated when they are moved. This allows
// us to update the heap instead of rebuilding it. ( If we implemented our own heap, we should be able
// to do the same thing by iterating through every element of the heap and updating based on the row
// stored in each element, but boost::d_ary_heap doesn't seem to allow this. ) A particularly big win
// for updating the heap instead of rebuilding it from scratch is that if an image is locally
// approximately linear, it is likely that the current pixel will require the median to move in the same
// direction as the previous one, in which case the majority of the heap structure will still be valid -
// the update for most rows will just be a check that everything is still valid, with only the newly updated
// row requiring a rebalance. There may be a small optimization here where we track that the heap is still
// valid, and only the new row needs to be updated, but I suspect calling update on each element even though
// it doesn't need to move is pretty cheap.
//
// The result of all this is an extremely efficient algorithm. The definite majority of cost is just in
// sorting each row. It seems very likely that this approach is competitive with the best of median sorts
// in the literature - I should probably document it a bit more cleanly and publish that somewhere. If we
// really wanted to compete with bleeding edge, the next step would probably be to switch the sort of
// individual rows from std::sort to a bleeding edge sorting algorithm ( like sorting networks for small sizes ).

class RankMedianBuffer
{
public:
	inline RankMedianBuffer( const V2i &size ) :
		m_size( size ), m_sortedRows( size.x * size.y ), m_splits( size.y ), m_splitValue( 0 )
	{
		// We need to initialize the storage for everything
		m_minHeap.reserve( size.y );
		m_minHeapHandles.reserve( size.y );
		m_maxHeap.reserve( size.y );
		m_maxHeapHandles.reserve( size.y );

		// And the heaps need to have an entry added for each row ( the priority values are not meaningful,
		// they will all be updated before we use the heaps ).
		for( int i = 0; i < size.y; i++ )
		{
			m_minHeapHandles.push_back( m_minHeap.push( std::make_pair( 0.0f, i ) ) );
			m_maxHeapHandles.push_back( m_maxHeap.push( std::make_pair( 0.0f, i ) ) );
		}
	}

	inline void sampleRow( int rowIndex, Sampler &sampler, const Box2i &rowBound )
	{
		// Find the chunk of pixels in m_sortedRows corresponding to this row
		float *currentRow = &m_sortedRows[ m_size.x * rowIndex ];

		// Grab the row of pixels into the buffer
		float *writePos = currentRow;
		sampler.visitPixels( rowBound,
			[&writePos] ( float v, int x, int y )
			{
				if( std::isnan( v ) )
				{
					v = -infinity;
				}
				*writePos = v;
				writePos++;
			}
		);

		// Sort the new row
		//
		// If we wanted to make this competitive with bleeding edge median filters, we would probably
		// need a faster sort here. Sorting networks could work for small sizes ... I'm also curious how
		// djbsort would perform.
		std::sort( currentRow, currentRow + m_size.x );

		// Update m_splits for this row to preserve the invariant - it needs to be set so that
		// currentRow[i] < m_splitValue if and only if i < m_splits[i]
		//
		// This means that the comparison invariant is preserved, but the number of elements in the
		// lower set may now be wrong - this will be rebalanced when currentResult() is called.
		//
		// I kind of wonder whether a linear search might be faster for small sizes - it's super easy for
		// the branch predictor. But lower_bound makes sense for large sizes.
		m_splits[rowIndex] = std::lower_bound( currentRow, &currentRow[m_size.x], m_splitValue ) - currentRow;
	}

	inline float currentResult()
	{
		// Count how many elements are in the lower set
		int count = 0;
		for( const int c : m_splits )
		{
			count += c;
		}

		// How many element should be in the lower set
		// ( We current always use odd sizes, so don't need to worry about the middle landing between two
		// elements )
		int targetCount = ( m_size.x * m_size.y ) / 2;

		// Decide whether we need to move the splits higher or lower
		if( count <= targetCount )
		{
			// We need more elements in the lower set, so we need to shift the splits higher,
			// so get the min heap up to date. Each entry gets a priority based on the next element
			// that could be included in the lower set.
			for( int i = 0; i < m_size.y; i++ )
			{
				m_minHeap.update( m_minHeapHandles[i], std::make_pair( m_splits[i] < m_size.x ? m_sortedRows[ i * m_size.x + m_splits[i] ] : infinity, i ) );
			}

			// For each element that needs to be added, we need to increment one of the splits
			for( int i = 0; i < targetCount - count; i++ )
			{
				// Necessary only to avoid running past the end of the sortedRow in the situation where the source
				// data includes inf values
				if( m_minHeap.top().first == infinity )
				{
					break;
				}

				// Find the lowest value of m_sortedRows[ m_splits[i] ] for any i.
				// This is the row where we can increase the split while preserving the invariant.
				int row = m_minHeap.top().second;

				int newSplit = m_splits[ row ] + 1;
				m_splits[ row ] = newSplit;

				assert( newSplit <= m_size.x );

				// Update the entry for the row that we incremented, with a priority based on the new next element
				m_minHeap.update( m_minHeapHandles[row], std::make_pair( newSplit < m_size.x ? m_sortedRows[ row * m_size.x + newSplit ] : infinity, row ) );
			}

			// Once we've set all the splits correctly, the split value is the next element that
			// could be added.
			m_splitValue = m_minHeap.top().first;
		}
		else
		{
			// We need less elements in the lower set, so we need to shift the splits lower,
			// so get the max heap up to date. Each entry gets a priority based on the next element
			// that could be removed from the lower set.
			for( int i = 0; i < m_size.y; i++ )
			{
				m_maxHeap.update( m_maxHeapHandles[i], std::make_pair( m_splits[i] > 0 ? m_sortedRows[ i * m_size.x + m_splits[i] -1 ] : -infinity, i ) );
			}

			// For each element that needs to be removed, we need to decrement one of the splits
			for( int i = 0; i < count - targetCount; i++ )
			{
				// Find the highest value of m_sortedRows[ m_splits[i - 1] ] for any i.
				// This is the row where we can decrease the split while preserving the invariant.
				const HeapEntry &root = m_maxHeap.top();
				m_splitValue = root.first;
				int row = root.second;

				// Necessary only to avoid running past the end of the data in the situation where the source
				// data includes -inf values
				if( m_splitValue == -infinity )
				{
					break;
				}

				int newSplit = m_splits[ row ] - 1;
				m_splits[ row ] = newSplit;

				assert( newSplit >= 0 );

				// Update the entry for the row that we decremented, with a priority based on the new next element
				m_maxHeap.update( m_maxHeapHandles[ row ], std::make_pair( newSplit > 0 ? m_sortedRows[ row * m_size.x + newSplit - 1] : -infinity, row ) );
			}

			// Once we've set all the splits correctly, the split is the last element that
			// we removed
		}

		// Since the number of elements in the lower set is now correct, the split value is the median.
		return m_splitValue;
	}

	inline bool rowContainsResult( int rowIndex, float result )
	{
		// Maybe it would be clearer if this function didn't take the result value in, and just
		// used m_splitValue? But for RankMaxBuffer, it was easy to take the result ... it's
		// only an internal interface anyway.
		assert( result == m_splitValue );

		// Everything before the split is <= to the split value - if the last element before the split
		// isn't equal, then everything before must be less, and the result value doesn't occur in
		// the lower section
		if( m_splits[rowIndex] > 0 && m_sortedRows[ m_size.x * rowIndex + m_splits[rowIndex] - 1 ] == result )
		{
			return true;
		}

		// Everything after the split is >= to the split value - if the first element after the split
		// isn't equal, then everything after must be greater, and the result value doesn't occur in
		// the upper section
		if( m_splits[rowIndex] < m_size.x && m_sortedRows[ m_size.x * rowIndex + m_splits[rowIndex] ] == result )
		{
			return true;
		}

		// If the split value isn't in the upper or lower section of this row, then it's not in this row
		return false;
	}

private:

	// Size of the filter, x is the size of each row, y is the number of rows
	V2i m_size;

	// The pixel values for each row, sorted within each row.
	// Row i is stored in elements [ i * size.x ... ( i + 1 ) * size.x - 1 ]
	std::vector<float> m_sortedRows;

	// The split for each row specifies how many elements in each row are part of the lower set
	std::vector<int> m_splits;

	// The value of the lowest element in the upper set
	float m_splitValue;

	// Each entry in the heap stores a priority value for when it should be chosen, and an integer for the row
	// it points to
	using HeapEntry = std::pair<float, int>;

	// The min heap is used when we need to increase the number of elements in the lower set, increasing
	// m_splits by choosing the row with the lowest value not yet included in the lower set.
	struct MinCompare
	{
		bool operator()(const HeapEntry &a, const HeapEntry &b) const
		{
			return a.first > b.first;
		}
	};
	using MinHeap = boost::heap::d_ary_heap< HeapEntry, boost::heap::arity<2>, boost::heap::mutable_<true>, boost::heap::compare<MinCompare> >;
	MinHeap m_minHeap;

	// The max heap is used when we need to decrease the number of elements in the lower set, decreasing
	// m_splits by choosing the row with the highest value currently in the lower set.
	struct MaxCompare
	{
		bool operator()(const HeapEntry &a, const HeapEntry &b) const
		{
			return a.first < b.first;
		}
	};
	using MaxHeap = boost::heap::d_ary_heap< HeapEntry, boost::heap::arity<2>, boost::heap::mutable_<true>, boost::heap::compare<MaxCompare> >;
	MaxHeap m_maxHeap;

	// We store the handle for each every element in the heaps, in order matching the rows. This allows us to
	// update the entry with a new value from the row.
	std::vector< MinHeap::handle_type > m_minHeapHandles;
	std::vector< MaxHeap::handle_type > m_maxHeapHandles;
};

inline int positiveModulo( int a, int d )
{
	return ( ( a % d ) + d ) % d;
}

// Fill in an accumulator buffer of the appropriate type, and then step it through each pixel, outputting
// the result for each pixel in the tile.
template< class Buffer >
void processTile( Sampler &sampler, const V2i &radius, const Box2i &tileBound, vector<float> &result, const Canceller *canceller )
{
	V2i s = 2 * radius + V2i( 1 );
	Buffer buffer( s );
	V2i p;
	for( p.x = tileBound.min.x; p.x < tileBound.max.x; ++p.x )
	{
		p.y = tileBound.min.y;

		// For the set of pixels to include in each row of the buffer, we need a bound.
		// Initialize this to the first row within the support of the first pixel in this column
		Imath::Box2i rowBound( p + V2i( -radius ), p + V2i( radius.x + 1, -radius.y + 1 ) );

		// Step through all but one row of the support of the first pixel, calling sampleRow on the buffer
		// so that every slot of the buffer is occupied with data for this pixel ( except for one row
		// that will be filled on the first iteration of the for loop below.
		while( rowBound.min.y < tileBound.min.y + radius.y )
		{
			buffer.sampleRow( positiveModulo( rowBound.min.y, s.y ), sampler, rowBound );
			rowBound.min.y++;
			rowBound.max.y++;
		}

		for( p.y = tileBound.min.y; p.y < tileBound.max.y; ++p.y )
		{
			IECore::Canceller::check( canceller );

			// Replace one row of the buffer with the next row
			buffer.sampleRow( positiveModulo( rowBound.min.y, s.y ), sampler, rowBound );

			// We now have a buffer with all the row data for this pixel, we can get the result for this pixel
			result[ ImagePlug::pixelIndex( p, tileBound.min ) ] = buffer.currentResult();

			// Step to the next row
			rowBound.min.y++;
			rowBound.max.y++;
		}
	}
}

template< class Buffer >
void processTileIndices( Sampler &sampler, const V2i &radius, const Box2i &tileBound, vector<V2i> &result, const Canceller *canceller )
{
	V2i s = 2 * radius + V2i( 1 );
	Buffer buffer( s );
	V2i p;
	for( p.x = tileBound.min.x; p.x < tileBound.max.x; ++p.x )
	{
		p.y = tileBound.min.y;
		Imath::Box2i rowBound( p + V2i( -radius ), p + V2i( radius.x + 1, -radius.y + 1 ) );

		// Initialize buffer to start this column
		while( rowBound.min.y < tileBound.min.y + radius.y )
		{
			buffer.sampleRow( positiveModulo( rowBound.min.y, s.y ), sampler, rowBound );
			rowBound.min.y++;
			rowBound.max.y++;
		}

		// Scanning the image to find where the value occurred
		for( p.y = tileBound.min.y; p.y < tileBound.max.y; ++p.y )
		{
			IECore::Canceller::check( canceller );

			// Find the result for this pixel, same as in processTile() above
			buffer.sampleRow( positiveModulo( rowBound.min.y, s.y ), sampler, rowBound );
			float resultValue = buffer.currentResult();

			Imath::Box2i rescanBound( p + V2i( -radius ), p + V2i( radius.x + 1, -radius.y + 1 ) );

			// Now we rescan the image to find where the rank occured
			// In case there are multiple instances of an identical value,
			// we take whichever one is closest to the center.
			//
			// Note that this may be incredibly inefficient compared to finding the result of an Erode or Dilate
			// ( or even Median with the new optimizations ), especially in a blank region of the image where
			// many pixels match the result.
			//
			// This could be fixed with the following optimizations:
			// * limit the extents to search based on the closest match found so far
			// * start with the center row and search outwards so that the closest is hopefully found quickly
			// * remember the location for the previous pixel - if the result for this pixel is the same
			//   as the previous, and the previous location is within range, we can start with that, and only
			//   need check one new row.

			V2i r( INT_MAX, INT_MAX );
			uint32_t closestMatch = UINT_MAX;

			if(
				( std::is_same_v< Buffer, RankMinBuffer > && resultValue == infinity ) ||
				( std::is_same_v< Buffer, RankMaxBuffer > && resultValue == -infinity )
			)
			{
				// If all pixels are the worst possible match, we can just use the current pixel
				r = V2i( 0 );
			}
			else
			{
				for( int i = 0; i < s.y; i++ )
				{
					if( buffer.rowContainsResult( positiveModulo( rescanBound.min.y, s.y ), resultValue ) )
					{
						sampler.visitPixels( rescanBound,
							[p, resultValue, &r, &closestMatch] ( float v, int x, int y )
							{
								if(
									v == resultValue || ( resultValue == -infinity && std::isnan( v ) )
								)
								{
									uint32_t absX = abs( x - p.x );
									uint32_t absY = abs( y - p.y );
									uint32_t distance = ( max( absX, absY ) << 16 ) + absX + absY;
									if( distance < closestMatch )
									{
										closestMatch = distance;

										// Store the offset to the rank pixel
										r = V2i( x - p.x, y - p.y );
									}
								}
							}
						);
					}
					rescanBound.min.y++;
					rescanBound.max.y++;
				}
			}

			// One of the pixels must match the rank
			assert( r != V2i( INT_MAX, INT_MAX ) );

			result[ ImagePlug::pixelIndex( p, tileBound.min ) ] = r;
			rowBound.min.y++;
			rowBound.max.y++;
		}
	}
}

} // namespace

void RankFilter::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hash( output, context, h );
	if( output == pixelOffsetsPlug() )
	{
		const V2i radius = radiusPlug()->getValue();
		const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
		const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
		const Box2i inputBound( tileBound.min - radius, tileBound.max + radius );

		Sampler sampler(
			inPlug(),
			// This plug should only be evaluated with channel name already set to the driver channel
			context->get<std::string>( ImagePlug::channelNameContextName ),
			inputBound,
			(Sampler::BoundingMode)boundingModePlug()->getValue()
		);
		sampler.hash( h );
		h.append( radius );
		h.append( tileOrigin );
	}
}

void RankFilter::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == pixelOffsetsPlug() )
	{
		const V2i radius = radiusPlug()->getValue();

		V2iVectorDataPtr resultData = new V2iVectorData;
		vector<V2i> &result = resultData->writable();
		result.resize( ImagePlug::tileSize() * ImagePlug::tileSize(), Imath::V2i( 0 ) );
		if( radius == V2i( 0 ) )
		{
			static_cast<V2iVectorDataPlug *>( output )->setValue( resultData );
			return;
		}

		const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
		const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
		const Box2i inputBound( tileBound.min - radius, tileBound.max + radius );

		Sampler sampler(
			inPlug(),
			// This plug should only be evaluated with channel name already set to the driver channel
			context->get<std::string>( ImagePlug::channelNameContextName ),
			inputBound,
			(Sampler::BoundingMode)boundingModePlug()->getValue()
		);

		switch( m_mode )
		{
			case MedianRank:
				processTileIndices<RankMedianBuffer>( sampler, radius, tileBound, result, context->canceller() );
				break;
			case ErodeRank:
				processTileIndices<RankMinBuffer>( sampler, radius, tileBound, result, context->canceller() );
				break;
			case DilateRank:
				processTileIndices<RankMaxBuffer>( sampler, radius, tileBound, result, context->canceller() );
				break;
		}

		static_cast<V2iVectorDataPlug *>( output )->setValue( resultData );
		return;
	}
	else
	{
		FlatImageProcessor::compute( output, context );
	}
}


void RankFilter::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const V2i radius = radiusPlug()->getValue();
	if( radius == V2i( 0 ) )
	{
		h = inPlug()->channelDataPlug()->hash();
		return;
	}

	FlatImageProcessor::hashChannelData( parent, context, h );

	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i inputBound( tileBound.min - radius, tileBound.max + radius );

	Sampler sampler(
		inPlug(),
		context->get<std::string>( ImagePlug::channelNameContextName ),
		inputBound,
		(Sampler::BoundingMode)boundingModePlug()->getValue()
	);
	sampler.hash( h );
	h.append( radius );
	h.append( tileOrigin );

	const std::string &masterChannel = masterChannelPlug()->getValue();
	if( masterChannel != "" )
	{
		ImagePlug::ChannelDataScope pixelOffsetsScope( context );
		pixelOffsetsScope.setChannelName( &masterChannel );

		pixelOffsetsPlug()->hash( h );
	}

}

IECore::ConstFloatVectorDataPtr RankFilter::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const V2i radius = radiusPlug()->getValue();
	if( radius == V2i( 0 ) )
	{
		return inPlug()->channelDataPlug()->getValue();
	}

	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i inputBound( tileBound.min - radius, tileBound.max + radius );

	Sampler sampler(
		inPlug(),
		channelName,
		inputBound,
		(Sampler::BoundingMode)boundingModePlug()->getValue()
	);

	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();
	result.reserve( ImagePlug::tileSize() * ImagePlug::tileSize() );

	const std::string &masterChannel = masterChannelPlug()->getValue();
	if( masterChannel != "" )
	{
		ConstV2iVectorDataPtr pixelOffsets;
		{
			ImagePlug::ChannelDataScope pixelOffsetsScope( context );
			pixelOffsetsScope.setChannelName( &masterChannel );

			pixelOffsets = pixelOffsetsPlug()->getValue();
		}

		vector<V2i>::const_iterator offsetsIt = pixelOffsets->readable().begin();
		V2i p;
		for( p.y = tileBound.min.y; p.y < tileBound.max.y; ++p.y )
		{
			for( p.x = tileBound.min.x; p.x < tileBound.max.x; ++p.x )
			{
				const V2i &offset = *offsetsIt++;
				V2i sourcePixel = p + offset;
				result.push_back( sampler.sample( sourcePixel.x, sourcePixel.y ) );
			}
		}

		return resultData;
	}

	result.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );

	switch( m_mode )
	{
		case MedianRank:
			processTile<RankMedianBuffer>( sampler, radius, tileBound, result, context->canceller() );
			break;
		case ErodeRank:
			processTile<RankMinBuffer>( sampler, radius, tileBound, result, context->canceller() );
			break;
		case DilateRank:
			processTile<RankMaxBuffer>( sampler, radius, tileBound, result, context->canceller() );
			break;
	}

	return resultData;
}
