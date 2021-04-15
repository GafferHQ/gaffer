//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/ImageAlgo.h"

#include "IECore/CompoundData.h"

#include "OpenEXR/ImathBox.h"

#include <set>

using namespace std;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

class CopyTile
{

	public :

		CopyTile(
				const vector<float *> &imageChannelData,
				const vector<string> &channelNames,
				const Imath::Box2i &dataWindow
			) :
				m_imageChannelData( imageChannelData ),
				m_channelNames( channelNames ),
				m_dataWindow( dataWindow )
		{}

		void operator()( const ImagePlug *imagePlug, const string &channelName, const Imath::V2i &tileOrigin )
		{
			const Imath::Box2i tileBound( tileOrigin, tileOrigin + Imath::V2i( ImagePlug::tileSize() ) );
			const Imath::Box2i b = BufferAlgo::intersection( tileBound, m_dataWindow );

			const size_t imageStride = m_dataWindow.size().x;
			const size_t tileStrideSize = sizeof(float) * b.size().x;

			const int channelIndex = std::find( m_channelNames.begin(), m_channelNames.end(), channelName ) - m_channelNames.begin();
			float *channelBegin = m_imageChannelData[channelIndex];

			IECore::ConstFloatVectorDataPtr tileData = imagePlug->channelDataPlug()->getValue();
			const float *tileDataBegin = &(tileData->readable()[0]);

			for( int y = b.min.y; y < b.max.y; y++ )
			{
				const float *tilePtr = tileDataBegin + ( y - tileOrigin.y ) * ImagePlug::tileSize() + ( b.min.x - tileOrigin.x );
				float *channelPtr = channelBegin + ( m_dataWindow.size().y - ( 1 + y - m_dataWindow.min.y ) ) * imageStride + ( b.min.x - m_dataWindow.min.x );
				std::memcpy( channelPtr, tilePtr, tileStrideSize );
			}
		}

	private :

		const vector<float *> &m_imageChannelData;
		const vector<string> &m_channelNames;
		const Imath::Box2i &m_dataWindow;

};


// \todo : We likely need to come up with a better general way of iterating tiles, which could
// translate back and forth from a tileOrigin to a flat index.  This potentially be used in
// parallelProcessTiles, and could potentially be public so that code that uses tiles() would
// have an easy way to look up tile data for a particular tileOrigin.
//
// When that gets implemented, it should replace these private functions.
Imath::Box2i tileRangeFromDataWindow( const Imath::Box2i &dataWindow )
{
	return Imath::Box2i(
		ImagePlug::tileOrigin( dataWindow.min ) / ImagePlug::tileSize(),
		ImagePlug::tileOrigin( dataWindow.max - Imath::V2i( 1 ) ) / ImagePlug::tileSize()
	);
}

int tileIndex( const Imath::V2i &tileOrigin, const Imath::Box2i &tileRange )
{
	Imath::V2i offset = tileOrigin / ImagePlug::tileSize() - tileRange.min;
	return offset.y * ( tileRange.size().x + 1 ) + offset.x;
}

} // namespace


std::vector<std::string> GafferImage::ImageAlgo::layerNames( const std::vector<std::string> &channelNames )
{
	set<string> visited;
	vector<string> result;
	for( vector<string>::const_iterator it = channelNames.begin(), eIt = channelNames.end(); it != eIt; ++it )
	{
		string l = layerName( *it );
		if( visited.insert( l ).second )
		{
			result.push_back( l );
		}
	}

	return result;
}

const std::string GafferImage::ImageAlgo::channelNameA( "A" );
const std::string GafferImage::ImageAlgo::channelNameR( "R" );
const std::string GafferImage::ImageAlgo::channelNameG( "G" );
const std::string GafferImage::ImageAlgo::channelNameB( "B" );
const std::string GafferImage::ImageAlgo::channelNameZ( "Z" );
const std::string GafferImage::ImageAlgo::channelNameZBack( "ZBack" );

IECoreImage::ImagePrimitivePtr GafferImage::ImageAlgo::image( const ImagePlug *imagePlug )
{
	if( imagePlug->deepPlug()->getValue() )
	{
		throw( IECore::Exception( "ImageAlgo::image() only works on flat image data ") );
	}

	Format format = imagePlug->formatPlug()->getValue();
	Imath::Box2i dataWindow = imagePlug->dataWindowPlug()->getValue();
	Imath::Box2i newDataWindow( Imath::V2i( 0 ) );

	if( !BufferAlgo::empty( dataWindow ) )
	{
		newDataWindow = format.toEXRSpace( dataWindow );
	}
	else
	{
		dataWindow = newDataWindow;
	}

	Imath::Box2i newDisplayWindow = format.toEXRSpace( format.getDisplayWindow() );

	IECoreImage::ImagePrimitivePtr result = new IECoreImage::ImagePrimitive( newDataWindow, newDisplayWindow );

	IECore::ConstCompoundDataPtr metadata = imagePlug->metadataPlug()->getValue();
	result->blindData()->Object::copyFrom( metadata.get() );

	IECore::ConstStringVectorDataPtr channelNamesData = imagePlug->channelNamesPlug()->getValue();
	const vector<string> &channelNames = channelNamesData->readable();

	vector<float *> imageChannelData;
	for( vector<string>::const_iterator it = channelNames.begin(), eIt = channelNames.end(); it!=eIt; it++ )
	{
		IECore::FloatVectorDataPtr cd = new IECore::FloatVectorData;
		vector<float> &c = cd->writable();
		c.resize( result->channelSize(), 0.0f );
		result->channels[*it] = cd;
		imageChannelData.push_back( &(c[0]) );
	}

	CopyTile copyTile( imageChannelData, channelNames, dataWindow );
	ImageAlgo::parallelProcessTiles( imagePlug, channelNames, copyTile, dataWindow );

	return result;

}

IECore::MurmurHash GafferImage::ImageAlgo::imageHash( const ImagePlug *imagePlug )
{
	const Imath::Box2i dataWindow = imagePlug->dataWindowPlug()->getValue();
	IECore::ConstStringVectorDataPtr channelNamesData = imagePlug->channelNamesPlug()->getValue();
	const vector<string> &channelNames = channelNamesData->readable();

	IECore::MurmurHash result = imagePlug->formatPlug()->hash();
	result.append( imagePlug->dataWindowPlug()->hash() );
	result.append( imagePlug->metadataPlug()->hash() );
	result.append( imagePlug->channelNamesPlug()->hash() );

	bool deep = imagePlug->deepPlug()->getValue();
	result.append( deep );
	if( deep )
	{
		ImageAlgo::parallelGatherTiles(
			imagePlug,
			// Tile
			[] ( const ImagePlug *imageP, const Imath::V2i &tileOrigin )
			{
				return imageP->sampleOffsetsPlug()->hash();
			},
			// Gather
			[ &result ] ( const ImagePlug *imageP, const Imath::V2i &tileOrigin, const IECore::MurmurHash &tileHash )
			{
				result.append( tileHash );
			},
			dataWindow,
			ImageAlgo::BottomToTop
		);
	}

	ImageAlgo::parallelGatherTiles(
		imagePlug, channelNames,
		// Tile
		[] ( const ImagePlug *imageP, const string &channelName, const Imath::V2i &tileOrigin )
		{
			return imageP->channelDataPlug()->hash();
		},
		// Gather
		[ &result ] ( const ImagePlug *imageP, const string &channelName, const Imath::V2i &tileOrigin, const IECore::MurmurHash &tileHash )
		{
			result.append( tileHash );
		},
		dataWindow,
		ImageAlgo::BottomToTop
	);

	return result;
}

IECore::ConstCompoundObjectPtr GafferImage::ImageAlgo::tiles( const ImagePlug *imagePlug )
{
	const Imath::Box2i dataWindow = imagePlug->dataWindowPlug()->getValue();
	IECore::ConstStringVectorDataPtr channelNamesData = imagePlug->channelNamesPlug()->getValue();
	const vector<string> &channelNames = channelNamesData->readable();

	bool deep = imagePlug->deepPlug()->getValue();

	Imath::Box2i tileRange = tileRangeFromDataWindow( dataWindow );

	int numTiles = tileIndex( ImagePlug::tileOrigin( dataWindow.max - Imath::V2i( 1 ) ), tileRange ) + 1;

	IECore::V2iVectorDataPtr tileOrigins = new IECore::V2iVectorData();
	std::vector<Imath::V2i> &tileOriginsWritable = tileOrigins->writable();
	tileOriginsWritable.resize( numTiles );

	IECore::ObjectVectorPtr sampleOffsetResults = new IECore::ObjectVector();
	sampleOffsetResults->members().resize( numTiles );

	std::vector<IECore::ObjectVectorPtr> channelDataResults( channelNames.size() );
	for( unsigned int i = 0; i < channelNames.size(); i++ )
	{
		channelDataResults[i] = new IECore::ObjectVector();
		channelDataResults[i]->members().resize( numTiles );
	}

	ImageAlgo::parallelProcessTiles(
		imagePlug,
		// Tile
		[ &tileOriginsWritable, &sampleOffsetResults, &channelDataResults, &channelNames, &tileRange, deep ] ( const ImagePlug *imageP, const Imath::V2i &tileOrigin )
		{
			int tileI = tileIndex( tileOrigin, tileRange );
			tileOriginsWritable[tileI] = tileOrigin;

			IECore::ConstIntVectorDataPtr sampleOffsets = imageP->sampleOffsetsPlug()->getValue();
			if( deep )
			{
				// As is kinda common, we have to cheat with a const cast while we're stuffing members into
				// a data structure that is safe because it will be become const as soon as we're done filling it
				sampleOffsetResults->members()[ tileI ] = const_cast<IECore::IntVectorData*>( sampleOffsets.get() );
			}
			else
			{
				// For flat images, we don't actually need to access the sampleOffsets, since they must always be
				// flat.  But it's a good check to make sure that the sample offsets are actually correct.
				// Currently, tiles() is used mostly in tests, so it seem good to verify this.
				// If tiles() gets used in somewhere performance critical, it would be good to make this check
				// optional.
				if( sampleOffsets != ImagePlug::flatTileSampleOffsets() )
				{
					throw IECore::Exception( "Accessing tiles on flat image with invalid sample offsets" );
				}
			}

			ImagePlug::ChannelDataScope channelDataScope( Gaffer::Context::current() );
			for( unsigned int i = 0; i < channelNames.size(); i++ )
			{
				channelDataScope.setChannelName( &channelNames[i] );
				channelDataResults[i]->members()[tileI] = const_cast<IECore::FloatVectorData*>(
					imageP->channelDataPlug()->getValue().get()
				);
			}
		},
		dataWindow
	);

	IECore::CompoundObjectPtr result = new IECore::CompoundObject();
	result->members()["tileOrigins"] = tileOrigins;
	if( deep )
	{
		result->members()["sampleOffsets"] = sampleOffsetResults;
	}

	for( unsigned int i = 0; i < channelNames.size(); i++ )
	{
		result->members()[channelNames[i]] = channelDataResults[i];
	}

	return result;
}

void GafferImage::ImageAlgo::throwIfSampleOffsetsMismatch( const IECore::IntVectorData* sampleOffsetsDataA, const IECore::IntVectorData* sampleOffsetsDataB, const Imath::V2i &tileOrigin, const std::string &message )
{
	if( sampleOffsetsDataA != sampleOffsetsDataB )
	{
		const std::vector<int> &sampleOffsetsA = sampleOffsetsDataA->readable();
		const std::vector<int> &sampleOffsetsB = sampleOffsetsDataB->readable();
		for( int i = 0; i < ImagePlug::tilePixels(); i++ )
		{
			if( sampleOffsetsA[i] != sampleOffsetsB[i] )
			{
				int prevOffset = i > 0 ? sampleOffsetsA[i - 1] : 0;

				int y = i / ImagePlug::tileSize();
				int x = i - y * ImagePlug::tileSize();

				throw IECore::Exception( message + boost::str( boost::format(
					" Pixel %i,%i received both %i and %i samples"
					) % ( x + tileOrigin.x )  % ( y + tileOrigin.y ) %
					( sampleOffsetsA[i] - prevOffset ) % ( sampleOffsetsB[i] - prevOffset )
				) );
			}
		}
	}
}



