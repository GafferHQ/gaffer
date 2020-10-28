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

#include "GafferImage/Merge.h"

#include "GafferImage/ImageAlgo.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"

#include "IECore/BoxOps.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

namespace
{

enum SingleInputMode
{
	Operate,
	Black,
	Copy
};

struct OpAdd
{
	static float operate( float A, float B, float a, float b){ return A + B; }
	static const SingleInputMode onlyA = Copy;
	static const SingleInputMode onlyB = Copy;
};
struct OpAtop
{
	static float operate( float A, float B, float a, float b){ return A*b + B*(1.-a); }
	static const SingleInputMode onlyA = Black;
	static const SingleInputMode onlyB = Copy;
};
struct OpDivide
{
	static float operate( float A, float B, float a, float b){ return A / B; }
	static const SingleInputMode onlyA = Operate;
	static const SingleInputMode onlyB = Black;
};
struct OpIn
{
	static float operate( float A, float B, float a, float b){ return A*b; }
	static const SingleInputMode onlyA = Black;
	static const SingleInputMode onlyB = Black;
};
struct OpOut
{
	static float operate( float A, float B, float a, float b){ return A*(1.-b); }
	static const SingleInputMode onlyA = Copy;
	static const SingleInputMode onlyB = Black;
};
struct OpMask
{
	static float operate( float A, float B, float a, float b){ return B*a; }
	static const SingleInputMode onlyA = Black;
	static const SingleInputMode onlyB = Black;
};
struct OpMatte
{
	static float operate( float A, float B, float a, float b){ return A*a + B*(1.-a); }
	static const SingleInputMode onlyA = Operate;
	static const SingleInputMode onlyB = Copy;
};
struct OpMultiply
{
	static float operate( float A, float B, float a, float b){ return A * B; }
	static const SingleInputMode onlyA = Black;
	static const SingleInputMode onlyB = Black;
};
struct OpOver
{
	static float operate( float A, float B, float a, float b){ return A + B*(1.-a); }
	static const SingleInputMode onlyA = Copy;
	static const SingleInputMode onlyB = Copy;
};
struct OpSubtract
{
	static float operate( float A, float B, float a, float b){ return A - B; }
	static const SingleInputMode onlyA = Copy;
	static const SingleInputMode onlyB = Operate;
};
struct OpDifference
{
	static float operate( float A, float B, float a, float b){ return fabs( A - B ); }
	static const SingleInputMode onlyA = Operate;
	static const SingleInputMode onlyB = Operate;
};
struct OpUnder
{
	static float operate( float A, float B, float a, float b){ return A*(1.-b) + B; }
	static const SingleInputMode onlyA = Copy;
	static const SingleInputMode onlyB = Copy;
};
struct OpMin
{
	static float operate( float A, float B, float a, float b){ return std::min( A, B ); }
	static const SingleInputMode onlyA = Operate;
	static const SingleInputMode onlyB = Operate;
};
struct OpMax
{
	static float operate( float A, float B, float a, float b){ return std::max( A, B ); }
	static const SingleInputMode onlyA = Operate;
	static const SingleInputMode onlyB = Operate;
};

template< class Functor, typename... Args >
typename Functor::ReturnType dispatchOperation( Merge::Operation op, Functor &&functor, Args&&... args )
{
    switch( op )
    {
        case Merge::Add : return functor.template operator()<OpAdd>( std::forward<Args>( args )... );
        case Merge::Atop : return functor.template operator()<OpAtop>( std::forward<Args>( args )... );
        case Merge::Divide : return functor.template operator()<OpDivide>( std::forward<Args>( args )... );
        case Merge::In : return functor.template operator()<OpIn>( std::forward<Args>( args )... );
        case Merge::Out : return functor.template operator()<OpOut>( std::forward<Args>( args )... );
        case Merge::Mask : return functor.template operator()<OpMask>( std::forward<Args>( args )... );
        case Merge::Matte : return functor.template operator()<OpMatte>( std::forward<Args>( args )... );
        case Merge::Multiply : return functor.template operator()<OpMultiply>( std::forward<Args>( args )... );
        case Merge::Over : return functor.template operator()<OpOver>( std::forward<Args>( args )... );
        case Merge::Subtract : return functor.template operator()<OpSubtract>( std::forward<Args>( args )... );
        case Merge::Difference : return functor.template operator()<OpDifference>( std::forward<Args>( args )... );
        case Merge::Under : return functor.template operator()<OpUnder>( std::forward<Args>( args )... );
        case Merge::Min : return functor.template operator()<OpMin>( std::forward<Args>( args )... );
        case Merge::Max : return functor.template operator()<OpMax>( std::forward<Args>( args )... );
		default:
			throw InvalidArgumentException( boost::str( boost::format( "Invalid Merge Operation : %1%" ) % op ) );
	}
}

// This somewhat complex function is used only within the implementation of the tileRegion function
// The interface is a bit weird because performance is potentially critical and it's tied directly
// to tileRegion.
// It computes whether a position is inside a given bounding box, and where the next pixel index is
// where this would switch from inside to outside.
// The input position is supplied as both an unwrapped pixel index "i", and also the same position
// is supplied in "coord" as an x/y coordinate relative to the tile origin.
// The bound "b" is a bounding box relative to the tile origin
// The parameter "in" is set based on whether the current index is inside "b", and the return
// value is the next pixel index where the value of "in" would change ( or tilePixels() if we can
// process all the way to the end of the tile without "in" changing )
inline int nextBoxBoundaryIndex( int i, const V2i &coord, const Box2i &b, bool &in )
{
	if( BufferAlgo::contains( b, coord ) )
	{
		in = true;

		if( b.min.x == 0 && b.max.x == ImagePlug::tileSize() )
		{
			// Data fills full width, we will stay in this region until we reach the bottom
			return b.max.y * ImagePlug::tileSize();
		}
		else
		{
			// We will exit this region when we reach the end of it on this scanline
			return coord.y * ImagePlug::tileSize() + b.max.x;
		}
	}
	else
	{
		in = false;

		if( BufferAlgo::empty( b ) )
		{
			// We never enter this box
			return ImagePlug::tilePixels();
		}

		int first = ImagePlug::pixelIndex( b.min, V2i( 0 ) );
		if( i < first )
		{
			// We're before the box, so we'll eventually enter the first pixel of it
			return first;
		}
		else if( i >= ImagePlug::pixelIndex( b.max - V2i( 1 ), V2i( 0 ) ) )
		{
			// We're after the box, we'll never enter
			return ImagePlug::tilePixels();
		}
		else
		{
			// We're within the index region covered by the box, which must mean we're
			// in between scanlines covered by the box
			if( coord.x < b.min.x )
			{
				// We're before the scanline for coord.y
				return coord.y * ImagePlug::tileSize() + b.min.x;
			}
			else
			{
				// We're after the current scanline, return the beginning of the next scanline
				return ( coord.y + 1 ) * ImagePlug::tileSize() + b.min.x;
			}
		}
	}
}

enum MergeRegion
{
	// Values chosen to work as bitmask
	OutsideBoth = 0,
	InsideA = 1,
	InsideB = 2,
	InsideBoth = 3
};

// We divide the tile up into regions of continuous pixels that fit into one of the categories in the MergeRegion
// struct.  This function returns which of the 4 kinds of regions we are in, and the length of the current region.
// This tells us how many pixel values we can process before we need to re-evaluate what region we are in.
// The index i and length are unwrapped pixel indices, which means that if the tile is entirely inside or outside
// both bounds are either completely full or completely empty, length will be set to ImagePlug::tilePixels(), and
// the entire tile can be processed in one go.
// The inputs boundA and boundB are local bounding boxes relative to the origin of the current tile
inline MergeRegion tileRegion( int i, const Box2i &boundA, const Box2i &boundB, int &length )
{
	bool inA = false;
	bool inB = false;

	V2i coord = ImagePlug::indexPixel( i, V2i( 0 ) );
	int next = std::min(
		nextBoxBoundaryIndex( i, coord, boundA, inA ),
		nextBoxBoundaryIndex( i, coord, boundB, inB )
	);

	length = next - i;
	return (MergeRegion)(( InsideA * inA ) | ( InsideB * inB ));
}

struct MergeFunctor
{
	typedef void ReturnType;

	// Merge channelData based on the current Op
	// Based on our convention for merges we output to channelDataB and alphaDataB - we accumulate to the
	// first input
	// The result may just be repointing these pointers to do a whole tile passthrough.
	// If both bounds are non-zero however, it will require allocating the merge buffers,
	// and actually performing per-pixel operations into them
	// boundB and boundA are local tile bounds, relative to the tile origin
	template< class Op >
	ReturnType operator()(
		const Box2i &boundB,
		ConstFloatVectorDataPtr &channelDataB,
		ConstFloatVectorDataPtr &alphaDataB,
		const Box2i &boundA,
		const ConstFloatVectorDataPtr &channelDataA,
		const ConstFloatVectorDataPtr &alphaDataA,
		FloatVectorDataPtr &mergeChannelBuffer,
		FloatVectorDataPtr &mergeAlphaBuffer,
		bool partialBound
	)
	{
		if( !channelDataB )
		{
			// If we have no prior input, just initialize
			channelDataB = channelDataA;
			alphaDataB = alphaDataA;

			/// \todo If we have no connection
			/// to in[0] then should that not be treated as being a black image, so
			/// we should unconditionally initaliase with in[0] and then always use
			/// the operation for in[1:], even if in[0] is disconnected. In other
			/// words, shouldn't multiplying a white constant over an unconnected
			/// in[0] produce black?
			/// Note:  More recently John and I have discussed this, and I think
			/// we're happy with the status quo.  There isn't an obviously clear
			/// answer to what should happen with unconnected inputs.  The
			/// current behaviour isn't confusing, and it's pretty reasonable to
			/// connect a black input if you actually want to multiply to black

			return;
		}

		bool emptyA = BufferAlgo::empty( boundA ) ||
			( channelDataA == ImagePlug::blackTile() && alphaDataA == ImagePlug::blackTile() );
		bool emptyB = BufferAlgo::empty( boundB ) ||
			( channelDataB == ImagePlug::blackTile() && alphaDataB == ImagePlug::blackTile() );

		// If both inputs are blackTile, or the operator is black when one input is black,
		// we may be able to just pass through blackTile for the whole tile
		if(
			( emptyA && emptyB ) ||
			( !partialBound && emptyA && Op::onlyB == SingleInputMode::Black ) ||
			( !partialBound && emptyB && Op::onlyA == SingleInputMode::Black )
		)
		{
			channelDataB = ImagePlug::blackTile();
			alphaDataB = ImagePlug::blackTile();
			return;
		}
		else if( !partialBound && emptyA && Op::onlyB == SingleInputMode::Copy )
		{
			// We're outside the data window of this layer, and this op
			// does nothing outside the data window
			return;
		}
		else if( !partialBound && emptyB && Op::onlyA == SingleInputMode::Copy )
		{
			// We're only within the data window of the new layer, and
			// this op just copies in the new layer, so we can just point
			// to the whole new tile
			channelDataB = channelDataA;
			alphaDataB = alphaDataA;
			return;
		}

		// The base layer (B) with the current result
		const float *B = &channelDataB->readable().front();
		const float *b = &alphaDataB->readable().front();

		// A higher layer (A) which must be composited over the result
		const float *A = &channelDataA->readable().front();
		const float *a = &alphaDataA->readable().front();

		if( !mergeChannelBuffer )
		{
			// None of the passthrough conditions have triggered, and we're actually performing
			// an operation, time to allocate the merge buffers
			mergeChannelBuffer = new FloatVectorData();
			mergeAlphaBuffer = new FloatVectorData();
			mergeChannelBuffer->writable().resize( ImagePlug::tilePixels() );
			mergeAlphaBuffer->writable().resize( ImagePlug::tilePixels() );
		}
		float *R = &mergeChannelBuffer->writable().front();
		float *r = &mergeAlphaBuffer->writable().front();


		// Iterate through all the pixels in the tile, using the wrapped
		// pixelIndex which corresponds directly to the index in the
		// channelData vector
		int i = 0;
		int length;
		MergeRegion region;

		while( i < ImagePlug::tilePixels() )
		{
			// Compute the MergeRegion which tells us which bounding boxes
			// we are in, and also how many pixel indices we can process
			// in a row with the same MergeRegion
			region = tileRegion( i, boundA, boundB, length );

			if(
				( region == OutsideBoth ) ||
				( region == InsideB && Op::onlyB == Black ) ||
				( region == InsideA && Op::onlyA == Black )
			)
			{
				// If we are outside both inputs, or the Op is black when one input is
				// black, then everything is this region is black
				memset( R, 0, length * sizeof( float ) );
				memset( r, 0, length * sizeof( float ) );
				A += length; a += length;
				B += length; b += length;
				R += length; r += length;
			}
			else if( region == InsideB )
			{
				if( Op::onlyB == SingleInputMode::Copy )
				{
					if( R == B )
					{
						// We're already working in the merge buffers, so we don't need to do anything
						// if input B is left untouched
					}
					else
					{
						// In a region with one input where we know the operator just passes through
						// an input, we can just copy it over.
						// Note: that this does not actually currently improve performance measurably,
						// the compiler probably does quite a good job of inlining Op::operate,
						// noticing that it is a passthrough, and translating it into something memcpy'ish
						// This structure still feels worthwhile since it's a bit more explicit about what
						// is happening, and this structure could be useful if we pursue a bit of
						// vectorization
						memcpy( R, B, length * sizeof( float ) );
						memcpy( r, b, length * sizeof( float ) );
					}
					A += length; a += length;
					B += length; b += length;
					R += length; r += length;
				}
				else
				{
					// Outside A dataWindow, so call operator with 0 substituted for A and a
					for( int j = 0; j < length; j++ )
					{
						*R = Op::operate( 0.0f, *B, 0.0f, *b );
						*r = Op::operate( 0.0f, *b, 0.0f, *b );
						++B; ++b;
						++R; ++r;
					}
					A += length; a += length;
				}
			}
			else if( region == InsideA )
			{
				if( Op::onlyA == SingleInputMode::Copy )
				{
					// In a region with one input where we know the operator just passes through
					// an input, we can just copy it over.
					memcpy( R, A, length * sizeof( float ) );
					memcpy( r, a, length * sizeof( float ) );
					A += length; a += length;
					B += length; b += length;
					R += length; r += length;
				}
				else
				{
					// Outside B dataWindow, so call operator with 0 substituted for B and b
					for( int j = 0; j < length; j++ )
					{
						*R = Op::operate( *A, 0.0f, *a, 0.0f );
						*r = Op::operate( *a, 0.0f, *a, 0.0f );
						++A; ++a;
						++R; ++r;
					}
					B += length; b += length;
				}
			}
			else
			{
				// Within both data windows, this is when we actually need to run the full operate()
				for( int j = 0; j < length; j++ )
				{
					*R = Op::operate( *A, *B, *a, *b );
					*r = Op::operate( *a, *b, *a, *b );
					++A; ++a;
					++B; ++b;
					++R; ++r;
				}
			}
			i += length;
		}

		// Now that we've written to the merge buffers, they are now the valid output
		channelDataB = mergeChannelBuffer;
		alphaDataB = mergeAlphaBuffer;
	}

};

struct PassthroughHashFunctor
{
	typedef void ReturnType;

	// There are two completely different strategies we can use for determining a channelData hash
	// The first is to append hashes for everything that affects the current tile, producing a fully
	// unique hash.
	// The second is to actually compute enough about the tile to realize that we can fully
	// characterize the operation as a passthrough, and just pass through an input hash.  This is a
	// big performance win, when possible.
	// This function is responsible for the second approach.  Like our other functors, it accumulates
	// into the "B" inputs channelHashB and alphaHashB.  alphaHashB is not outside this method, but by
	// tracking it, we can detect situations where the input is entirely black.
	// If a passthrough is not possible, this just sets passthrough to false, and hashChannelData
	// will just use the first approach instead
	template< class Op >
	ReturnType operator()(
		MurmurHash &channelHashB,
		MurmurHash &alphaHashB,
		const MurmurHash &channelHashA,
		const MurmurHash &alphaHashA,
		bool partialBound,
		bool &passthroughValid
	)
	{
		if( partialBound && Op::onlyA != SingleInputMode::Black && Op::onlyB != SingleInputMode::Black )
		{
			// If the Op is non-black even if either input is black, then that means it can expand
			// the data window larger than the input, so we need to make sure to that we zero out any
			// regions outside the original data window, and we can't do a passthrough
			passthroughValid = false;
		}

		if( channelHashB == IECore::MurmurHash() )
		{
			channelHashB = channelHashA;
			alphaHashB = alphaHashA;
		}
		else
		{
			const MurmurHash &blackTileHash = ImagePlug::blackTile()->Object::hash();
			bool emptyB = channelHashB == blackTileHash && alphaHashB == blackTileHash;
			bool emptyA = channelHashA == blackTileHash && alphaHashA == blackTileHash;
			if(
				( emptyB && emptyA ) ||
				( emptyB && Op::onlyA == SingleInputMode::Black ) ||
				( emptyA && Op::onlyB == SingleInputMode::Black )
			)
			{
				channelHashB = blackTileHash;
				alphaHashB = blackTileHash;
			}
			else if( emptyB && Op::onlyA == SingleInputMode::Copy )
			{
				// No background yet, we can pass through foreground
				channelHashB = channelHashA;
				alphaHashB = alphaHashA;
			}
			else if( emptyA && Op::onlyB == SingleInputMode::Copy )
			{
				// No foreground, and we can just leave background
			}
			else
			{
				passthroughValid = false;
			}
		}
	}

};

struct MergeDataWindowFunctor
{
	typedef void ReturnType;


	// Merge two datawindows based on the current Op
	// Some ops will return black anywhere where only one input is non-black, and
	// for these ops, we don't need to extend the dataWindow to include both inputs
	// Based on our convention for merges we output to windowB - we accumulate to the
	// first input
	template<class Op>
	ReturnType operator()( Box2i &windowB, const Box2i &windowA, bool initialize )
	{
		if( initialize )
		{
			// For the first data window we encounter, we always take it directly.
			// Depending on the Op, doing a regular combine with an empty window
			// is not the same as initializing
			windowB = windowA;
		}
		else if( Op::onlyA == SingleInputMode::Black && Op::onlyB == SingleInputMode::Black )
		{
			windowB = BufferAlgo::intersection( windowB, windowA );
		}
		else if( Op::onlyA == SingleInputMode::Black )
		{
			// Leave the windowB
		}
		else if( Op::onlyB == SingleInputMode::Black )
		{
			windowB = windowA;
		}
		else
		{
			// Box2i::extendBy fails to handle empty boxes correctly
			if( BufferAlgo::empty( windowB ) )
			{
				windowB = windowA;
			}
			else if( BufferAlgo::empty( windowA ) )
			{
				// Pass
			}
			else
			{
				windowB.extendBy( windowA );
			}
		}
	}

};

} // namespace

GAFFER_NODE_DEFINE_TYPE( Merge );

size_t Merge::g_firstPlugIndex = 0;

Merge::Merge( const std::string &name )
	:	FlatImageProcessor( name, 2 )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild(
		new IntPlug(
			"operation", // name
			Plug::In,    // direction
			Add,         // default
			Add,         // min
			Max          // the maximum value in the enum, which just happens to currently be named "Max"
		)
	);

	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
}

Merge::~Merge()
{
}

Gaffer::IntPlug *Merge::operationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Merge::operationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

void Merge::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageProcessor::affects( input, outputs );

	if( input == operationPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
		outputs.push_back( outPlug()->dataWindowPlug() );
	}
	else if( const ImagePlug *inputImage = input->parent<ImagePlug>() )
	{
		if( inputImage->parent<ArrayPlug>() == inPlugs() )
		{
			outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
		}
	}
}

void Merge::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashDataWindow( output, context, h );

	operationPlug()->hash( h );
	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<ValuePlug>() )
		{
			(*it)->dataWindowPlug()->hash( h );
		}
	}
}

Imath::Box2i Merge::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Imath::Box2i dataWindow;
	Operation op = (Operation)operationPlug()->getValue();
	bool first = true;
	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<ValuePlug>() )
		{
			dispatchOperation( op, MergeDataWindowFunctor(), dataWindow, (*it)->dataWindowPlug()->getValue(), first );
			first = false;
		}
	}

	return dataWindow;
}

void Merge::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashChannelNames( output, context, h );

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<ValuePlug>() )
		{
			(*it)->channelNamesPlug()->hash( h );
		}
	}
}

IECore::ConstStringVectorDataPtr Merge::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IECore::StringVectorDataPtr outChannelStrVectorData( new IECore::StringVectorData() );
	std::vector<std::string> &outChannels( outChannelStrVectorData->writable() );

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<ValuePlug>() )
		{
			IECore::ConstStringVectorDataPtr inChannelStrVectorData((*it)->channelNamesPlug()->getValue() );
			const std::vector<std::string> &inChannels( inChannelStrVectorData->readable() );
			for ( std::vector<std::string>::const_iterator cIt( inChannels.begin() ); cIt != inChannels.end(); ++cIt )
			{
				if ( std::find( outChannels.begin(), outChannels.end(), *cIt ) == outChannels.end() )
				{
					outChannels.push_back( *cIt );
				}
			}
		}
	}

	if ( !outChannels.empty() )
	{
		return outChannelStrVectorData;
	}

	return inPlug()->channelNamesPlug()->defaultValue();
}

void Merge::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashChannelData( output, context, h );

	const std::string channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	bool passthroughValid = true;
	MurmurHash passthroughHash;
	MurmurHash passthroughAlphaHash;

	Operation op = (Operation)operationPlug()->getValue();
	h.append( op );

	Box2i finalTileDataWindowLocal;
	{
		ImagePlug::GlobalScope c( context );
		Box2i finalDataWindow = outPlug()->dataWindowPlug()->getValue();
		const Box2i fullBound = Box2i( V2i( 0 ), V2i( ImagePlug::tileSize() ) );
		Box2i finalDataWindowLocal( finalDataWindow.min - tileOrigin, finalDataWindow.max - tileOrigin );
		finalTileDataWindowLocal = boxIntersection( fullBound, finalDataWindowLocal );
	}

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( !(*it)->getInput<ValuePlug>() )
		{
			continue;
		}

		IECore::ConstStringVectorDataPtr channelNamesData;
		Box2i dataWindow;

		{
			ImagePlug::GlobalScope c( context );
			channelNamesData = (*it)->channelNamesPlug()->getValue();
			dataWindow = (*it)->dataWindowPlug()->getValue();
		}

		// The hash of the channel data we do below represents just the data in
		// the tile itself, and takes no account of the possibility that parts of the
		// tile may be outside of the data window. This simplifies the implementation of
		// nodes like Constant (where all tiles are identical, even the edge tiles) and
		// Crop (which does no processing of tiles at all). For most nodes this doesn't
		// matter, because they don't change the data window, or they use a Sampler to
		// deal with invalid pixels. But because our data window is the union of all
		// input data windows, we may be using/revealing the invalid parts of a tile. We
		// deal with this in computeChannelData() by treating the invalid parts as black,
		// and must therefore hash in the valid bound here to take that into account.
		//
		// Working with a "local" dataWindow ( relative to the current tileOrigin ) is consistent with
		// what we need to do in the compute, and also has this advantage:  the valid bound could be
		// identical for two tiles with different origins, in which case it's OK to reuse the hash
		// For example, if performing a merge of two large constants, any tiles that are fully inside
		// the dataWindow of both can be reused.
		Box2i dataWindowLocal( dataWindow.min - tileOrigin, dataWindow.max - tileOrigin );
		const Box2i validBound = boxIntersection( finalTileDataWindowLocal, dataWindowLocal );
		h.append( validBound );

		const MurmurHash &blackTileHash = ImagePlug::blackTile()->Object::hash();
		MurmurHash channelHash = blackTileHash;
		MurmurHash alphaHash = blackTileHash;

		bool partialBound = false;
		if( !BufferAlgo::empty( validBound ) )
		{
			const std::vector<std::string> &channelNames = channelNamesData->readable();

			if( ImageAlgo::channelExists( channelNames, channelName ) )
			{
				channelHash = (*it)->channelDataPlug()->hash();
				h.append( channelHash );
			}

			if( ImageAlgo::channelExists( channelNames, "A" ) )
			{
				alphaHash =  (*it)->channelDataHash( "A", tileOrigin );
				h.append( alphaHash );
			}

			if( validBound != finalTileDataWindowLocal )
			{
				partialBound = true;
			}
		}

		// Try computing a passthrough hash if it's possible
		dispatchOperation( op, PassthroughHashFunctor(), passthroughHash, passthroughAlphaHash, channelHash, alphaHash, partialBound, passthroughValid );
	}

	if( passthroughValid )
	{
		// We found one input which is all that affects the output
		h = passthroughHash;
		return;
	}

}

IECore::ConstFloatVectorDataPtr Merge::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Operation op = (Operation)operationPlug()->getValue();

	// We start by tracking the result using a const pointer
	ConstFloatVectorDataPtr resultChannelData = nullptr;
	// We also need to track alpha of intermediate composited layers.
	ConstFloatVectorDataPtr resultAlphaData = nullptr;

	Box2i resultBound;

	// Scratch buffers that may be needed by MergeFunctor if we actually need to compute an operation,
	// rather than doing a passthrough
	FloatVectorDataPtr mergeChannelBuffer = nullptr;
	FloatVectorDataPtr mergeAlphaBuffer = nullptr;

	Box2i finalTileDataWindowLocal;
	{
		ImagePlug::GlobalScope c( context );
		Box2i finalDataWindow = outPlug()->dataWindowPlug()->getValue();
		const Box2i fullBound = Box2i( V2i( 0 ), V2i( ImagePlug::tileSize() ) );
		Box2i finalDataWindowLocal( finalDataWindow.min - tileOrigin, finalDataWindow.max - tileOrigin );
		finalTileDataWindowLocal = boxIntersection( fullBound, finalDataWindowLocal );
	}

	bool partialBound = false;

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( !(*it)->getInput<ValuePlug>() )
		{
			continue;
		}

		IECore::ConstStringVectorDataPtr channelNamesData;
		Box2i dataWindow;
		{
			ImagePlug::GlobalScope c( Context::current() );
			channelNamesData = (*it)->channelNamesPlug()->getValue();
			dataWindow = (*it)->dataWindowPlug()->getValue();
		}
		Box2i dataWindowLocal( dataWindow.min - tileOrigin, dataWindow.max - tileOrigin );

		const std::vector<std::string> &channelNames = channelNamesData->readable();

		ConstFloatVectorDataPtr channelData;
		ConstFloatVectorDataPtr alphaData;

		const Box2i validBound = boxIntersection( finalTileDataWindowLocal, dataWindowLocal );

		// \todo : There is opportunity for optimizing using pass-throughs for missing channel cases.
		// If both channel and alpha are missing, we could check for SingleInputMode::Copy.  If one or
		// the other is missing, we would need extra information about the Op to know how to proceed.
		// For the moment, I'm assuming that optimizing for merging channels that don't exist is not
		// a performance priority.
		if( ImageAlgo::channelExists( channelNames, channelName ) && !BufferAlgo::empty( validBound ) )
		{
			channelData = (*it)->channelDataPlug()->getValue();
		}
		else
		{
			channelData = ImagePlug::blackTile();
		}

		if( ImageAlgo::channelExists( channelNames, "A" ) && !BufferAlgo::empty( validBound ) )
		{
			alphaData = (*it)->channelData( "A", tileOrigin );
		}
		else
		{
			alphaData = ImagePlug::blackTile();
		}

		if( (int)alphaData->readable().size() != ImagePlug::tilePixels()  )
		{
			throw IECore::Exception( "Merge::computeChannelData : Cannot process deep data." );
		}
		if( (int)channelData->readable().size() != ImagePlug::tilePixels() )
		{
			throw IECore::Exception( "Merge::computeChannelData : Cannot process deep data." );
		}

		partialBound |= !BufferAlgo::empty( validBound ) && validBound != finalTileDataWindowLocal;

		// MergeFunctor contains all the complexity, we just pass in the bounds and channel data,
		// and it will either point resultChannelData to something we can pass through, or allocate
		// the merge buffers, operate in there, and then point resultChannelData to that
		bool first = !resultChannelData;
		dispatchOperation( op, MergeFunctor(), resultBound, resultChannelData, resultAlphaData, validBound, channelData, alphaData, mergeChannelBuffer, mergeAlphaBuffer, partialBound );
		dispatchOperation( op, MergeDataWindowFunctor(), resultBound, validBound, first );

	}

	return resultChannelData;
}
