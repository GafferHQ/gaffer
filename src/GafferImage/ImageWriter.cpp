//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/ImageWriter.h"

#include "GafferImage/BufferAlgo.h"
#include "GafferImage/ColorSpace.h"
#include "GafferImage/FormatPlug.h"
#include "GafferImage/ImageAlgo.h"
#include "GafferImage/ImagePlug.h"

#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringAlgo.h"
#include "Gaffer/StringPlug.h"

#include "IECoreImage/OpenImageIOAlgo.h"

#include "IECore/MessageHandler.h"

#include "OpenImageIO/imageio.h"

#include "OpenColorIO/OpenColorIO.h"

#include "boost/filesystem.hpp"

#include "tbb/spin_mutex.h"

#include <memory>

#include <sys/utsname.h>
#include <zlib.h>

OIIO_NAMESPACE_USING

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferDispatch;
using namespace GafferImage;

static InternedString g_modePlugName( "mode" );
static InternedString g_compressionPlugName( "compression" );
static InternedString g_compressionQualityPlugName( "compressionQuality" );
static InternedString g_chromaSubSamplingPlugName( "chromaSubSampling" );
static InternedString g_compressionLevelPlugName( "compressionLevel" );
static InternedString g_dataTypePlugName( "dataType" );

namespace
{

void copyBufferArea( const float *inData, const Imath::Box2i &inArea, float *outData, const Imath::Box2i &outArea, const size_t outOffset = 0, const size_t outInc = 1, const bool outYDown = false, Imath::Box2i copyArea = Imath::Box2i() )
{
	if( BufferAlgo::empty( copyArea ) )
	{
		copyArea = BufferAlgo::intersection( inArea, outArea );
	}

	assert( BufferAlgo::contains( inArea, copyArea ) );
	assert( BufferAlgo::contains( outArea, copyArea ) );

	for( int y = copyArea.min.y; y < copyArea.max.y; ++y )
	{
		size_t yOffsetIn = y - inArea.min.y;
		size_t yOffsetOut = y - outArea.min.y;

		if( outYDown )
		{
			yOffsetOut = outArea.max.y - y - 1;
		}

		const float *inPtr = inData + ( yOffsetIn * inArea.size().x ) + ( copyArea.min.x - inArea.min.x );
		float *outPtr = outData + ( ( ( yOffsetOut * outArea.size().x ) + ( copyArea.min.x - outArea.min.x ) ) * outInc ) + outOffset;

		for( int x = copyArea.min.x; x < copyArea.max.x; x++, outPtr += outInc )
		{
			*outPtr = *inPtr++;
		}
	}
}

typedef std::shared_ptr<ImageOutput> ImageOutputPtr;

class TileProcessor
{
	public:
		typedef ConstFloatVectorDataPtr Result;

		TileProcessor() {}

		Result operator()( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin )
		{
			return imagePlug->channelDataPlug()->getValue();
		}
};

class FlatTileWriter
{
	// This class is created to be used by parallelGatherTiles, and called in
	// series for each Gaffer tile/channel from the top down.
	//
	// This class has been designed to support any size of output tile. Because
	// only rare cases of output image will involve the output tiles lining up
	// exactly with the Gaffer tiles, it would already need to collect the
	// tile data as it goes, and so there was not a massive amount of extra
	// complexity to not assume the same tile size, allowing for the
	// possibility that multiple output tiles may be contained within a single
	// Gaffer tile.
	//
	// The instance of the class stores a vector of tile data storage vectors,
	// all of which start off empty. We only allocate the space for the tiles
	// when we need to start filling them, and free the space once the tiles
	// have been written to the ImageOutput. We also store a vector of bool
	// values (m_tilesFilled) to determine which output tiles have been filled
	// with data, and are therefore ready to write.
	//
	// The instance stores the index (m_nextTileIndex) of the next output tile
	// that it is expecting to write. This is because some formats require
	// tiles to be written in order, and we are holding to that for all
	// formats.
	//
	// As Gaffer tiles are passed in, the data is copied into any output tiles
	// they intersect with. Once that is done, any output tiles whose bottom
	// right corners are above and to the left (or equal) to the bottom right
	// corner of the tile we've just written can be considered to be filled,
	// so set the appropriate m_tilesFilled value.
	//
	// After flagging filled tiles, it iterates through tiles, starting at
	// m_nextTileIndex, and for each tile, if the tile is marked as filled,
	// write it, and if the tile does not intersect the region covered by the
	// input tiles, write a black tile. If neither of these is the case, stop,
	// and set m_nextTileIndex to the tile that it stopped on, which is the
	// next tile to write.
	//
	// Once all Gaffer tiles have been processed, there may still be partially
	// unfilled tiles, which will be fine, as their unfilled areas will be
	// black, which is what we want. So iterate over the remaining tiles, and
	// if memory has been allocated for that tile, write it to the file, and if
	// nothing has been allocated, write a black tile.
	public:
		FlatTileWriter(
				ImageOutputPtr out,
				const std::string &fileName,
				const Imath::Box2i &processWindow,
				const GafferImage::Format &format
			) :
				m_out( out ),
				m_fileName( fileName ),
				m_format( format ),
				m_spec( m_out->spec() ),
				m_processWindow( processWindow ),
				m_inputTilesBounds( Imath::Box2i( ImagePlug::tileOrigin( processWindow.min ), ImagePlug::tileOrigin( processWindow.max - Imath::V2i( 1 ) ) + Imath::V2i( ImagePlug::tileSize() ) ) ),
				m_outputDataWindow( m_format.fromEXRSpace( Imath::Box2i( Imath::V2i( m_spec.x, m_spec.y ), Imath::V2i( m_spec.x + m_spec.width - 1, m_spec.y + m_spec.height - 1 ) ) ) ),
				m_numTiles( Imath::V2i( (int)ceil( float( m_spec.width ) / m_spec.tile_width ), (int)ceil( float( m_spec.height ) / m_spec.tile_height ) ) ),
				m_nextTileIndex( 0 ),
				m_blackTile( nullptr )
		{
			m_tilesData.resize( m_numTiles.x * m_numTiles.y );
			m_tilesFilled.resize( m_numTiles.x * m_numTiles.y, false );

			for( size_t i = 0; i < m_tilesData.size(); ++i )
			{
				m_tilesData[i] = new FloatVectorData;
			}
		}

		void finish()
		{
			for( size_t tileIndex = m_nextTileIndex; tileIndex < m_tilesData.size(); ++tileIndex )
			{
				Imath::V2i tileOrigin = outTileOrigin( tileIndex );
				if( !m_tilesData[tileIndex]->readable().empty() )
				{
					writeTile( tileOrigin, m_tilesData[tileIndex] );
				}
				else
				{
					// If the tileData object hasn't been resized, then
					// we have never even tried to write data to this
					// tile, so write the static black tile.
					writeTile( tileOrigin, blackTile() );
				}
			}
		}

		void operator()( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin, ConstFloatVectorDataPtr data )
		{
			const size_t channelIndex = std::find( m_spec.channelnames.begin(), m_spec.channelnames.end(), channelName ) - m_spec.channelnames.begin();

			const Imath::Box2i inTileBounds( tileOrigin, tileOrigin + Imath::V2i( ImagePlug::tileSize() ) );

			Box2i tilesWrite = BufferAlgo::intersection( outTilesBounds(), Imath::Box2i( outTileOrigin( inTileBounds.min ), outTileOrigin( inTileBounds.max - Imath::V2i( 1 ) ) + Imath::V2i( m_spec.tile_width, m_spec.tile_height ) ) );

			Imath::V2i outTileOrig( tilesWrite.min.x, tilesWrite.max.y - m_spec.tile_height );

			for( ; outTileOrig.y >= tilesWrite.min.y; outTileOrig.y -= m_spec.tile_height )
			{
				for( outTileOrig.x = tilesWrite.min.x; outTileOrig.x < tilesWrite.max.x; outTileOrig.x += m_spec.tile_width )
				{
					size_t tileIndex = outTileIndex( outTileOrig );
					Imath::Box2i outTileBnds = outTileBounds( outTileOrig );

					vector<float> &tile = m_tilesData[tileIndex]->writable();
					if( tile.empty() )
					{
						tile.resize( m_spec.tile_width * m_spec.tile_height * m_spec.channelnames.size(), 0. );
					}

					Imath::Box2i copyArea( BufferAlgo::intersection( m_processWindow, BufferAlgo::intersection( inTileBounds, outTileBnds ) ) );

					copyBufferArea( &data->readable()[0], inTileBounds, &tile[0], outTileBnds, channelIndex, m_spec.channelnames.size(), true, copyArea );
				}
			}

			if( lastChannelOfTile( channelIndex ) )
			{
				flagFilledTiles( inTileBounds );
			}

			writeFilledTiles();
		}

	private:

		inline ConstFloatVectorDataPtr blackTile()
		{
			if( m_blackTile == nullptr )
			{
				m_blackTile = new IECore::FloatVectorData( std::vector<float>( m_spec.tile_width * m_spec.tile_height * m_spec.channelnames.size(), 0. ) );
			}

			return m_blackTile;
		}

		inline size_t outTileIndex( const Imath::V2i &tileOrigin ) const
		{
			return ( ( ( m_outputDataWindow.max.y - m_spec.tile_height - tileOrigin.y ) / m_spec.tile_height ) * m_numTiles.x ) + ( ( tileOrigin.x - m_outputDataWindow.min.x ) / m_spec.tile_width );
		}

		inline Imath::V2i outTileOrigin( const size_t tileIndex ) const
		{
			return Imath::V2i( ( ( tileIndex % m_numTiles.x ) * m_spec.tile_width ) + m_outputDataWindow.min.x, m_outputDataWindow.max.y - m_spec.tile_height - ( ( tileIndex / m_numTiles.x ) * m_spec.tile_height ) );
		}

		inline Imath::V2i outTileOrigin( const Imath::V2i &point ) const
		{
			Imath::V2i tempPoint = point - Imath::V2i( m_outputDataWindow.min.x, m_outputDataWindow.max.y );
			Imath::V2i tileOrigin;
			tileOrigin.x = tempPoint.x < 0 && tempPoint.x % m_spec.tile_width != 0 ? ( tempPoint.x / m_spec.tile_width - 1 ) * m_spec.tile_width : ( tempPoint.x / m_spec.tile_width ) * m_spec.tile_width;
			tileOrigin.y = tempPoint.y < 0 && tempPoint.y % m_spec.tile_height != 0 ? ( tempPoint.y / m_spec.tile_height - 1 ) * m_spec.tile_height : ( tempPoint.y / m_spec.tile_height ) * m_spec.tile_height;
			return tileOrigin + Imath::V2i( m_outputDataWindow.min.x, m_outputDataWindow.max.y );
		}

		inline Imath::Box2i outTileBounds( const Imath::V2i &point ) const
		{
			Imath::V2i origin = outTileOrigin( point );
			return Imath::Box2i( origin, origin + Imath::V2i( m_spec.tile_width, m_spec.tile_height ) );
		}

		inline Imath::Box2i outTilesBounds() const
		{
			return Imath::Box2i( outTileOrigin( m_outputDataWindow.min ), outTileOrigin( m_outputDataWindow.max - Imath::V2i( 1 ) ) + Imath::V2i( m_spec.tile_width, m_spec.tile_height) );
		}

		inline bool firstChannelOfTile( const size_t channelIndex )
		{
			return channelIndex == 0;
		}

		inline bool lastChannelOfTile( const size_t channelIndex )
		{
			return channelIndex == ( m_spec.channelnames.size() - 1 );
		}

		void flagFilledTiles( const Imath::Box2i &inTileBounds )
		{
			for( size_t i = m_nextTileIndex; i < m_tilesData.size(); ++i )
			{
				if( !m_tilesFilled[i] )
				{
					Imath::Box2i outTileBnds( outTileBounds( outTileOrigin( i ) ) );
					if( inTileBounds.max.x >= outTileBnds.max.x && inTileBounds.min.y <= outTileBnds.min.y )
					{
						m_tilesFilled[i] = true;
					}
					else
					{
						break;
					}
				}
			}
		}

		void writeFilledTiles()
		{
			size_t tileIndex;
			for( tileIndex = m_nextTileIndex; tileIndex < m_tilesData.size(); ++tileIndex )
			{
				Imath::V2i tileOrigin = outTileOrigin( tileIndex );

				if( m_tilesFilled[tileIndex] )
				{
					writeTile( tileOrigin, m_tilesData[tileIndex] );
					m_tilesData[tileIndex].reset();
				}
				else if( !BufferAlgo::intersects( m_inputTilesBounds, outTileBounds( tileOrigin ) ) )
				{
					writeTile( tileOrigin, blackTile() );
				}
				else
				{
					break;
				}
			}

			m_nextTileIndex = tileIndex;
		}


		void writeTile( const Imath::V2i &tileOrigin, ConstFloatVectorDataPtr tileData ) const
		{
			Imath::V2i exrTileOrigin = m_format.toEXRSpace( tileOrigin + Imath::V2i( 0, m_spec.tile_height - 1 ) );

			if( !m_out->write_tile( exrTileOrigin.x, exrTileOrigin.y, 0, TypeDesc::FLOAT, &tileData->readable()[0] ) )
			{
				throw IECore::Exception( boost::str( boost::format( "Could not write tile to \"%s\", error = %s" ) % m_fileName % m_out->geterror() ) );
			}
		}

		ImageOutputPtr m_out;
		const std::string &m_fileName;
		const GafferImage::Format &m_format;
		const ImageSpec m_spec;
		const Imath::Box2i m_processWindow;
		const Imath::Box2i m_inputTilesBounds;
		const Imath::Box2i m_outputDataWindow;
		const Imath::V2i m_numTiles;
		size_t m_nextTileIndex;
		std::vector<FloatVectorDataPtr> m_tilesData;
		std::vector<bool> m_tilesFilled;
		ConstFloatVectorDataPtr m_blackTile;
};

class FlatScanlineWriter
{
	// This class is created to be used by parallelGatherTiles, and called in
	// series for each Gaffer tile/channel from the top down.
	//
	// When it is first created, it writes to the ImageOutput object any blank
	// scanlines that fall between the start of the image and the start of the
	// data that it is going to be given.
	//
	// It stores a vector of floats big enough to hold ImagePlug::tileSize()
	// scanlines. As it receives each tile, it copies the data into the
	// appropriate location in the buffer. When it's copied the last channel
	// of the last tile of each row, it writes all of the data from the buffer
	// into the ImageOutput object.
	public:
		FlatScanlineWriter(
				ImageOutputPtr out,
				const std::string &fileName,
				const Imath::Box2i &processWindow,
				const GafferImage::Format &format
			) :
				m_out( out ),
				m_fileName( fileName ),
				m_format( format ),
				m_spec( m_out->spec() ),
				m_processWindow( processWindow ),
				m_tilesBounds( Imath::Box2i( ImagePlug::tileOrigin( processWindow.min ), ImagePlug::tileOrigin( processWindow.max - Imath::V2i( 1 ) ) + Imath::V2i( ImagePlug::tileSize() ) ) )
		{
			m_scanlinesData.resize( m_spec.width * ImagePlug::tileSize() * m_spec.channelnames.size(), 0.0 );

			writeInitialBlankScanlines();
		}

		void finish()
		{
			if( BufferAlgo::empty( m_processWindow ) )
			{
				// If the source data window is empty, we handle everything during construct
				return;
			}

			const int scanlinesEnd = m_format.toEXRSpace( m_tilesBounds.min.y - 1 );
			if( scanlinesEnd < ( m_spec.y + m_spec.height ) )
			{
				writeBlankScanlines( scanlinesEnd, m_spec.y + m_spec.height );
			}
		}

		void operator()( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin, ConstFloatVectorDataPtr data )
		{
			const size_t channelIndex = std::find( m_spec.channelnames.begin(), m_spec.channelnames.end(), channelName ) - m_spec.channelnames.begin();

			const Imath::Box2i inTileBounds( tileOrigin, tileOrigin + Imath::V2i( ImagePlug::tileSize() ) );
			const Imath::Box2i exrInTileBounds( m_format.toEXRSpace( inTileBounds ) );

			const Imath::Box2i exrScanlinesBounds( Imath::V2i( m_spec.x, exrInTileBounds.min.y ), Imath::V2i( m_spec.x + m_spec.width - 1, exrInTileBounds.max.y ) );
			const Imath::Box2i scanlinesBounds( m_format.fromEXRSpace( exrScanlinesBounds ) );

			if( firstTileOfRow( channelIndex, tileOrigin ) )
			{
				std::fill( m_scanlinesData.begin(), m_scanlinesData.end(), 0.0 );
			}

			Imath::Box2i copyArea( BufferAlgo::intersection( m_processWindow, BufferAlgo::intersection( inTileBounds, scanlinesBounds ) ) );

			copyBufferArea( &data->readable()[0], inTileBounds, &m_scanlinesData[0], scanlinesBounds, channelIndex, m_spec.channelnames.size(), true, copyArea );

			if( lastTileOfRow( channelIndex, tileOrigin ) )
			{
				writeScanlines(
					std::max( exrInTileBounds.min.y, m_spec.y ),
					std::min( exrInTileBounds.max.y + 1, m_spec.y + m_spec.height ),
					std::max( m_spec.y - exrInTileBounds.min.y, 0 )
				);
			}
		}

	private:

		inline bool firstTileOfRow( const size_t channelIndex, const Imath::V2i &tileOrigin ) const
		{
			return channelIndex == 0 && tileOrigin.x == m_tilesBounds.min.x;
		}

		inline bool lastTileOfRow( const size_t channelIndex, const Imath::V2i &tileOrigin ) const
		{
			return channelIndex == ( m_spec.channelnames.size() - 1 ) && tileOrigin.x == ( m_tilesBounds.max.x - ImagePlug::tileSize() ) ;
		}

		void writeScanlines( const int exrYBegin, const int exrYEnd, const int scanlinesYOffset = 0 ) const
		{
			if ( !m_out->write_scanlines( exrYBegin, exrYEnd, 0, TypeDesc::FLOAT, &m_scanlinesData[0] + ( scanlinesYOffset * m_spec.width * m_spec.channelnames.size() ) ) )
			{
				throw IECore::Exception( boost::str( boost::format( "Could not write scanline to \"%s\", error = %s" ) % m_fileName % m_out->geterror() ) );
			}
		}

		void writeBlankScanlines( int yBegin, int yEnd )
		{
			float *scanlines = &m_scanlinesData[0];
			memset( scanlines, 0, sizeof(float) * m_spec.width * std::min( ImagePlug::tileSize(), yEnd - yBegin ) * m_spec.channelnames.size() );
			while( yBegin < yEnd )
			{
				const int numLines = std::min( yEnd - yBegin, ImagePlug::tileSize() );
				writeScanlines( yBegin, yBegin + numLines );
				yBegin += numLines;
			}
		}

		void writeInitialBlankScanlines()
		{
			if( BufferAlgo::empty( m_processWindow ) )
			{
				// There is no data to process, so everything should be blank
				writeBlankScanlines( m_spec.y, m_spec.y + m_spec.height );
			}
			else
			{
				const int scanlinesBegin = m_format.toEXRSpace( m_tilesBounds.max.y - 1 );
				if( scanlinesBegin > m_spec.y )
				{
					writeBlankScanlines( m_spec.y, scanlinesBegin );
				}
			}
		}

		ImageOutputPtr m_out;
		const std::string &m_fileName;
		const GafferImage::Format &m_format;
		const ImageSpec m_spec;
		const Imath::Box2i &m_processWindow;
		const Imath::Box2i m_tilesBounds;
		vector<float> m_scanlinesData;
};

//////////////////////////////////////////////////////////////////////////
// Utility for converting IECore::Data types to OIIO::TypeDesc types.
//////////////////////////////////////////////////////////////////////////

void metadataToImageSpecAttributes( const CompoundData *metadata, ImageSpec &spec )
{
	const CompoundData::ValueType &members = metadata->readable();
	for( CompoundData::ValueType::const_iterator it = members.begin(); it != members.end(); ++it )
	{
		const IECoreImage::OpenImageIOAlgo::DataView dataView( it->second.get() );
		if( dataView.data )
		{
			spec.attribute( it->first.c_str(), dataView.type, dataView.data );
		}
	}
}

void setImageSpecFormatOptions( const ImageWriter *node, ImageSpec *spec, const std::string &fileFormatName )
{
	const ValuePlug *optionsPlug = node->getChild<ValuePlug>( fileFormatName );

	if( optionsPlug == nullptr)
	{
		return;
	}

	const StringPlug *dataTypePlug = optionsPlug->getChild<StringPlug>( g_dataTypePlugName );
	std::string dataType;

	if( dataTypePlug != nullptr )
	{
		dataType = dataTypePlug->getValue();

		if( dataType == "int8" )
		{
			spec->set_format( TypeDesc::INT8 );
		}
		else if( dataType == "int16" )
		{
			spec->set_format( TypeDesc::INT16 );
		}
		else if( dataType == "int32" )
		{
			spec->set_format( TypeDesc::INT32 );
		}
		else if( dataType == "int64" )
		{
			spec->set_format( TypeDesc::INT64 );
		}
		else if( dataType == "uint8" )
		{
			spec->set_format( TypeDesc::UINT8 );
		}
		else if( dataType == "uint16" )
		{
			spec->set_format( TypeDesc::UINT16 );
		}
		else if( dataType == "uint32" )
		{
			spec->set_format( TypeDesc::UINT32 );
		}
		else if( dataType == "uint64" )
		{
			spec->set_format( TypeDesc::UINT64 );
		}
		else if( dataType == "half" )
		{
			spec->set_format( TypeDesc::HALF );
		}
		else if( dataType == "float" )
		{
			spec->set_format( TypeDesc::FLOAT );
		}
		else if( dataType == "double" )
		{
			spec->set_format( TypeDesc::DOUBLE );
		}
	}

	const IntPlug *modePlug = optionsPlug->getChild<IntPlug>( g_modePlugName );

	if( modePlug != nullptr && modePlug->getValue() == ImageWriter::Tile )
	{
		spec->tile_width = spec->tile_height = ImagePlug::tileSize();
	}

	const StringPlug *compressionPlug = optionsPlug->getChild<StringPlug>( g_compressionPlugName );

	if( compressionPlug != nullptr )
	{
		spec->attribute( "compression", compressionPlug->getValue() );
	}

	if( fileFormatName == "jpeg" )
	{
		spec->attribute( "CompressionQuality", optionsPlug->getChild<IntPlug>( g_compressionQualityPlugName )->getValue() );
		std::string subSampling = optionsPlug->getChild<StringPlug>( g_chromaSubSamplingPlugName )->getValue();
		if( subSampling != "" ){
			spec->attribute( "jpeg:subsampling", subSampling );
		}
	}
	else if( fileFormatName == "dpx" )
	{
		if( dataType == "uint10" )
		{
			spec->set_format( TypeDesc::UINT16 );
			spec->attribute ("oiio:BitsPerSample", 10);
		}
		else if( dataType == "uint12" )
		{
			spec->set_format( TypeDesc::UINT16 );
			spec->attribute ("oiio:BitsPerSample", 12);
		}
	}
	else if( fileFormatName == "png" )
	{
		spec->attribute( "png:compressionLevel", optionsPlug->getChild<IntPlug>( g_compressionLevelPlugName )->getValue() );
	}
	else if( fileFormatName == "webp" )
	{
		spec->attribute( "CompressionQuality", optionsPlug->getChild<IntPlug>( g_compressionQualityPlugName )->getValue() );
	}
}

ImageSpec createImageSpec( const ImageWriter *node, const ImageOutput *out, const Imath::Box2i &dataWindow, const Imath::Box2i &displayWindow )
{
	const std::string fileFormatName = out->format_name();
	const bool supportsDisplayWindow = out->supports( "displaywindow" ) && fileFormatName != "dpx";

	ImageSpec spec( TypeDesc::UNKNOWN );

	// Specify the display window.
	spec.full_x = displayWindow.min.x;
	spec.full_y = displayWindow.min.y;
	spec.full_width = displayWindow.size().x + 1;
	spec.full_height = displayWindow.size().y + 1;

	if ( supportsDisplayWindow )
	{
		spec.x = dataWindow.min.x;
		spec.y = dataWindow.min.y;
		spec.width = dataWindow.size().x + 1;
		spec.height = dataWindow.size().y + 1;
	}
	else
	{
		spec.x = spec.full_x;
		spec.y = spec.full_y;
		spec.width = spec.full_width;
		spec.height = spec.full_height;
	}

	// Add the metadata to the spec, removing metadata that could affect the resulting channel data,
	// and file-format-specific metadata created by the OpenImageIOReader.
	CompoundDataPtr metadata = node->inPlug()->metadataPlug()->getValue()->copy();

	metadata->writable().erase( "oiio:ColorSpace" );
	metadata->writable().erase( "oiio:Gamma" );
	metadata->writable().erase( "oiio:UnassociatedAlpha" );
	metadata->writable().erase( "fileFormat" );
	metadata->writable().erase( "dataType" );

	metadataToImageSpecAttributes( metadata.get(), spec );

	// Apply the spec format options. Note this must happen
	// after we transfer the input metadata to ensure the
	// settings override anything from upstream data.
	setImageSpecFormatOptions( node, &spec, fileFormatName );

	// Add common attribs to the spec
	std::string software = ( boost::format( "Gaffer %d.%d.%d.%d" ) % GAFFER_MILESTONE_VERSION % GAFFER_MAJOR_VERSION % GAFFER_MINOR_VERSION % GAFFER_PATCH_VERSION ).str();
	spec.attribute( "Software", software );
	struct utsname info;
	if ( !uname( &info ) )
	{
		spec.attribute( "HostComputer", info.nodename );
	}
	if ( const char *artist = getenv( "USER" ) )
	{
		spec.attribute( "Artist", artist );
	}
	std::string document = "untitled";
	if ( const ScriptNode *script = node->ancestor<ScriptNode>() )
	{
		const std::string scriptFile = script->fileNamePlug()->getValue();
		document = ( scriptFile == "" ) ? document : scriptFile;
	}
	spec.attribute( "DocumentName", document );

	// PixelAspectRatio must be defined by the FormatPlug
	spec.attribute( "PixelAspectRatio", (float)node->inPlug()->formatPlug()->getValue().getPixelAspect() );

	return spec;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ImageWriter implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ImageWriter );

size_t ImageWriter::g_firstPlugIndex = 0;

ImageWriter::ImageWriter( const std::string &name )
	:	TaskNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "in" ) );
	addChild( new StringPlug( "fileName" ) );
	addChild( new StringPlug( "channels", Gaffer::Plug::In, "*" ) );
	addChild( new StringPlug( "colorSpace" ) );
	addChild( new ImagePlug( "out", Plug::Out, Plug::Default & ~Plug::Serialisable ) );
	outPlug()->setInput( inPlug() );

	ColorSpacePtr colorSpaceChild = new ColorSpace( "__colorSpace" );
	addChild( colorSpaceChild );

	OpenColorIO::ConstConfigRcPtr config = OpenColorIO::GetCurrentConfig();
	colorSpaceChild->inputSpacePlug()->setValue( config->getColorSpace( OpenColorIO::ROLE_SCENE_LINEAR )->getName() );
	colorSpaceChild->inPlug()->setInput( inPlug() );

	colorSpaceChild->outputSpacePlug()->setValue( "${__imageWriter:colorSpace}" );

	createFileFormatOptionsPlugs();
}

ImageWriter::~ImageWriter()
{
}

void ImageWriter::createFileFormatOptionsPlugs()
{
	ValuePlug *exrOptionsPlug = new ValuePlug( "openexr" );
	addChild( exrOptionsPlug );
	exrOptionsPlug->addChild( new IntPlug( g_modePlugName, Plug::In, Scanline ) );
	exrOptionsPlug->addChild( new StringPlug( g_compressionPlugName, Plug::In, "zips" ) );
	exrOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "half" ) );

	ValuePlug *dpxOptionsPlug = new ValuePlug( "dpx" );
	addChild( dpxOptionsPlug );
	dpxOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "uint10" ) );

	ValuePlug *tifOptionsPlug = new ValuePlug( "tiff" );
	addChild( tifOptionsPlug );
	tifOptionsPlug->addChild( new IntPlug( g_modePlugName, Plug::In, Scanline ) );
	tifOptionsPlug->addChild( new StringPlug( g_compressionPlugName, Plug::In, "zip" ) );
	tifOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "uint8" ) );

	ValuePlug *f3dOptionsPlug = new ValuePlug( "field3d" );
	addChild( f3dOptionsPlug );
	f3dOptionsPlug->addChild( new IntPlug( g_modePlugName, Plug::In, Scanline ) );
	f3dOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "float" ) );

	ValuePlug *fitsOptionsPlug = new ValuePlug( "fits" );
	addChild( fitsOptionsPlug );
	fitsOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "float" ) );

	ValuePlug *iffOptionsPlug = new ValuePlug( "iff" );
	addChild( iffOptionsPlug );
	iffOptionsPlug->addChild( new IntPlug( g_modePlugName, Plug::In, Tile ) );

	ValuePlug *jpgOptionsPlug = new ValuePlug( "jpeg" );
	addChild( jpgOptionsPlug );
	jpgOptionsPlug->addChild( new IntPlug( g_compressionQualityPlugName, Plug::In, 98, 0, 100 ) );
	jpgOptionsPlug->addChild( new StringPlug( g_chromaSubSamplingPlugName ) );

	ValuePlug *jpeg2000OptionsPlug = new ValuePlug( "jpeg2000" );
	addChild( jpeg2000OptionsPlug );
	jpeg2000OptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "uint8" ) );

	ValuePlug *pngOptionsPlug = new ValuePlug( "png" );
	addChild( pngOptionsPlug );
	pngOptionsPlug->addChild( new StringPlug( g_compressionPlugName, Plug::In, "filtered" ) );
	pngOptionsPlug->addChild( new IntPlug( g_compressionLevelPlugName, Plug::In, 6, Z_NO_COMPRESSION, Z_BEST_COMPRESSION ) );

	ValuePlug *rlaOptionsPlug = new ValuePlug( "rla" );
	addChild( rlaOptionsPlug );
	rlaOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "uint8" ) );

	ValuePlug *sgiOptionsPlug = new ValuePlug( "sgi" );
	addChild( sgiOptionsPlug );
	sgiOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "uint8" ) );

	ValuePlug *targaOptionsPlug = new ValuePlug( "targa" );
	addChild( targaOptionsPlug );
	targaOptionsPlug->addChild( new StringPlug( g_compressionPlugName, Plug::In, "rle" ) );

	ValuePlug *webpOptionsPlug = new ValuePlug( "webp" );
	addChild( webpOptionsPlug );
	webpOptionsPlug->addChild( new IntPlug( g_compressionQualityPlugName, Plug::In, 100, 0, 100 ) );
}

GafferImage::ImagePlug *ImageWriter::inPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const GafferImage::ImagePlug *ImageWriter::inPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *ImageWriter::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex+1 );
}

const Gaffer::StringPlug *ImageWriter::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex+1 );
}

Gaffer::StringPlug *ImageWriter::channelsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex+2 );
}

const Gaffer::StringPlug *ImageWriter::channelsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex+2 );
}

Gaffer::StringPlug *ImageWriter::colorSpacePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex+3 );
}

const Gaffer::StringPlug *ImageWriter::colorSpacePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex+3 );
}

GafferImage::ImagePlug *ImageWriter::outPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex+4 );
}

const GafferImage::ImagePlug *ImageWriter::outPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex+4 );
}

GafferImage::ColorSpace *ImageWriter::colorSpaceNode()
{
	return getChild<ColorSpace>( g_firstPlugIndex+5 );
}

const GafferImage::ColorSpace *ImageWriter::colorSpaceNode() const
{
	return getChild<ColorSpace>( g_firstPlugIndex+5 );
}

Gaffer::ValuePlug *ImageWriter::fileFormatSettingsPlug( const std::string &fileFormat )
{
	return getChild<ValuePlug>( fileFormat );
}

const Gaffer::ValuePlug *ImageWriter::fileFormatSettingsPlug( const std::string &fileFormat ) const
{
	return getChild<ValuePlug>( fileFormat );
}

const std::string ImageWriter::currentFileFormat() const
{
	const std::string fileName = fileNamePlug()->getValue();
	ImageOutputPtr out( ImageOutput::create( fileName.c_str() ) );
	if( out != nullptr )
	{
		return out->format_name();
	}
	else
	{
		return "";
	}
}

void ImageWriter::setDefaultColorSpaceFunction( DefaultColorSpaceFunction f )
{
	defaultColorSpaceFunction() = f;
}

ImageWriter::DefaultColorSpaceFunction ImageWriter::getDefaultColorSpaceFunction()
{
	return defaultColorSpaceFunction();
}

ImageWriter::DefaultColorSpaceFunction &ImageWriter::defaultColorSpaceFunction()
{
	// We deliberately make no attempt to free this, because typically a python
	// function is registered here, and we can't free that at exit because python
	// is already shut down by then.
	static DefaultColorSpaceFunction *g_colorSpaceFunction = new DefaultColorSpaceFunction;
	return *g_colorSpaceFunction;
}

std::string ImageWriter::colorSpace() const
{
	std::string colorSpace = colorSpacePlug()->getValue();
	if( colorSpace != "" )
	{
		return colorSpace;
	}

	const std::string fileFormat = currentFileFormat();
	if( fileFormat.empty() )
	{
		return "";
	}

	std::string dataType;
	if( const ValuePlug *optionsPlug = this->getChild<ValuePlug>( fileFormat ) )
	{
		if( const StringPlug *dataTypePlug = optionsPlug->getChild<StringPlug>( g_dataTypePlugName ) )
		{
			dataType = dataTypePlug->getValue();
		}
	}

	ConstCompoundDataPtr metadata = inPlug()->metadataPlug()->getValue();

	return defaultColorSpaceFunction()(
		fileNamePlug()->getValue(),
		fileFormat,
		dataType,
		metadata.get()
	);
}

IECore::MurmurHash ImageWriter::hash( const Context *context ) const
{
	Context::Scope scope( context );
	if ( ( fileNamePlug()->getValue() == "" ) || inPlug()->source<ImagePlug>() == inPlug() )
	{
		return IECore::MurmurHash();
	}

	IECore::MurmurHash h = TaskNode::hash( context );
	h.append( fileNamePlug()->hash() );
	h.append( channelsPlug()->hash() );
	h.append( colorSpacePlug()->hash() );
	const std::string fileFormat = currentFileFormat();

	if( fileFormat != "" )
	{
		const ValuePlug *fmtSettingsPlug = fileFormatSettingsPlug( fileFormat );
		if( fmtSettingsPlug != nullptr )
		{
			h.append( fmtSettingsPlug->hash() );
		}
	}

	return h;
}

void ImageWriter::execute() const
{
	// Set up a context to pass the right colorspace to
	// `colorSpaceNode()`.

	Context::EditableScope colorSpaceScope( Context::current() );
	colorSpaceScope.set( "__imageWriter:colorSpace", colorSpace() );

	// Create an OIIO::ImageOutput

	if( !inPlug()->getInput<ImagePlug>() )
	{
		throw IECore::Exception( "No input image." );
	}

	const std::string fileName = fileNamePlug()->getValue();

	ImageOutputPtr out( ImageOutput::create( fileName.c_str() ) );
	if( !out )
	{
		throw IECore::Exception( OIIO::geterror() );
	}

	// Create an OIIO::ImageSpec describing what we'll write

	const Format imageFormat = inPlug()->formatPlug()->getValue();
	const Imath::Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();
	Imath::Box2i exrDataWindow;

	if( !BufferAlgo::empty( dataWindow ) )
	{
		exrDataWindow = imageFormat.toEXRSpace( dataWindow );
	}
	else
	{
		// Exr doesn't allow images with no pixel, so if the actual data window is empty,
		// we make one pixel at the origin
		exrDataWindow = Imath::Box2i( Imath::V2i( 0 ) );
	}

	const Imath::Box2i exrDisplayWindow = imageFormat.toEXRSpace( imageFormat.getDisplayWindow() );

	ImageSpec spec = createImageSpec( this, out.get(), exrDataWindow, exrDisplayWindow );

	// Decide what channels to write and update the spec with them

	IECore::ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
	const vector<string> &channelNames = channelNamesData->readable();
	const string channels = channelsPlug()->getValue();

	const bool supportsNChannels = out->supports( "nchannels" );
	const bool supportsAlpha = out->supports( "alpha" );

	vector<string> channelsToWrite;
	for( vector<string>::const_iterator it = channelNames.begin(), eIt = channelNames.end(); it != eIt; ++it )
	{
		if( !StringAlgo::matchMultiple( *it, channels ) )
		{
			continue;
		}
		if( !supportsNChannels && *it != "R" && *it != "G" && *it != "B" && *it != "A" )
		{
			continue;
		}
		if( !supportsAlpha && *it == "A" )
		{
			continue;
		}
		channelsToWrite.push_back( *it );
	}

	spec.nchannels = channelsToWrite.size();
	spec.channelnames.clear();
	for( vector<string>::const_iterator it = channelsToWrite.begin(), eIt = channelsToWrite.end(); it != eIt; ++it )
	{
		spec.channelnames.push_back( *it );
		// OIIO has a special attribute for the Alpha and Z channels. If we find some, we should tag them...
		if( *it == "A" )
		{
			spec.alpha_channel = it - channelsToWrite.begin();
		}
		else if( *it == "Z" )
		{
			spec.z_channel = it - channelsToWrite.begin();
		}
	}

	// Create the directory we need and open the file

	boost::filesystem::path directory = boost::filesystem::path( fileName ).parent_path();
	if( !directory.empty() )
	{
		boost::filesystem::create_directories( directory );
	}

	if ( out->open( fileName, spec ) )
	{
		IECore::msg( IECore::MessageHandler::Info, this->relativeName( this->scriptNode() ), "Writing " + fileName );
	}
	else
	{
		throw IECore::Exception( boost::str( boost::format( "Could not open \"%s\", error = %s" ) % fileName % out->geterror() ) );
	}

	// Write out the channel data

	const Imath::Box2i extImageDataWindow( Imath::V2i( spec.x, spec.y ), Imath::V2i( spec.x + spec.width - 1, spec.y + spec.height - 1 ) );
	const Imath::Box2i imageDataWindow( imageFormat.fromEXRSpace( extImageDataWindow ) );
	const Imath::Box2i processDataWindow( BufferAlgo::intersection( imageDataWindow, dataWindow ) );

	TileProcessor processor = TileProcessor();

	if ( spec.tile_width == 0 )
	{
		FlatScanlineWriter flatScanlineWriter( out, fileName, processDataWindow, imageFormat );
		ImageAlgo::parallelGatherTiles( colorSpaceNode()->outPlug(), spec.channelnames, processor, flatScanlineWriter, processDataWindow, ImageAlgo::TopToBottom );
		flatScanlineWriter.finish();
	}
	else
	{
		FlatTileWriter flatTileWriter( out, fileName, processDataWindow, imageFormat );
		ImageAlgo::parallelGatherTiles( colorSpaceNode()->outPlug(), spec.channelnames, processor, flatTileWriter, processDataWindow, ImageAlgo::TopToBottom );
		flatTileWriter.finish();
	}

	out->close();
}
