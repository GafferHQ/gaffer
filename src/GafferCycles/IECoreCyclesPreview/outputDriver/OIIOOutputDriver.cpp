//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Alex Fuller. All rights reserved.
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
//      * Neither the name of Alex Fuller nor the names of
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

#include "OIIOOutputDriver.h"

#include "scene/pass.h"
#include "util/murmurhash.h"
#include "util/string.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/VectorTypedData.h"

#include "OpenImageIO/imageio.h"

namespace
{

int interleave( float *tileData,
				const int width, const int height,
				const int numChannels,
				const int numOutputChannels,
				const int outChannelOffset,
				float *interleavedData )
{
	int offset = outChannelOffset;
	for( int c = 0; c < numChannels; c++ )
	{
		float *in = &(tileData[0]) + c;
		float *out = interleavedData + offset;
		for( int j = 0; j < height; j++ )
		{
			for( int i = 0; i < width; i++ )
			{
				*out = *in;
				out += numOutputChannels;
				in += numChannels;
			}
		}
		offset += 1;
	}
	return offset;
}

void applyCryptomatteMetadata( OIIO::ImageSpec &spec, std::string name, IECore::ConstCompoundDataPtr cryptomatte )
{
	std::string identifier = ccl::string_printf( "%08x", ccl::util_murmur_hash3( name.c_str(), name.length(), 0 ) );
	std::string prefix = "cryptomatte/" + identifier.substr( 0, 7 ) + "/";
	spec.attribute( prefix + "name", cryptomatte->member<IECore::StringData>( prefix + "name", true )->readable() );
	spec.attribute( prefix + "hash", cryptomatte->member<IECore::StringData>( prefix + "hash", true )->readable() );
	spec.attribute( prefix + "conversion", cryptomatte->member<IECore::StringData>( prefix + "conversion", true )->readable() );
	spec.attribute( prefix + "manifest", cryptomatte->member<IECore::StringData>( prefix + "manifest", true )->readable() );
}

} // namespace

namespace IECoreCycles
{

OIIOOutputDriver::OIIOOutputDriver( const Imath::Box2i &displayWindow, const Imath::Box2i &dataWindow, IECore::ConstCompoundDataPtr parameters )
	: m_displayWindow( displayWindow ), m_dataWindow( dataWindow )
{
	const IECore::CompoundData *layersData = parameters->member<IECore::CompoundData>( "layers", true );
	const IECore::CompoundDataMap &layers = layersData->readable();
	const ccl::NodeEnum &typeEnum = *ccl::Pass::get_type_enum();
	std::vector<std::string> channelNames;
	IECore::CompoundDataPtr params;
	bool defaultFound = false;

	for( IECore::CompoundDataMap::const_iterator it = layers.begin(), eIt = layers.end(); it != eIt; ++it )
	{
		Layer layer;
		layer.name = it->first.string();
		const IECore::CompoundData *layerData = IECore::runTimeCast<IECore::CompoundData>( it->second.get() );

		const IECore::StringData *passTypeData = layerData->member<IECore::StringData>( "type", true );
		ccl::ustring passType( passTypeData->readable() );
		layer.passType = ccl::PASS_NONE;
		if( typeEnum.exists( passType ) )
		{
			layer.passType = static_cast<ccl::PassType>( typeEnum[passType] );
			ccl::PassInfo passInfo = ccl::Pass::get_info( layer.passType );
			layer.numChannels = passInfo.num_components;
		}

		const IECore::StringData *pathData = layerData->member<IECore::StringData>( "path", true );
		layer.path = pathData->readable();

		layer.typeDesc = OIIO::TypeDesc::FLOAT;
		const IECore::IntVectorData *quantizeData = layerData->member<IECore::IntVectorData>( "quantize", false );
		const std::vector<int> quantize = quantizeData->readable();
		if( quantize == std::vector<int>( { 0, 255, 0, 255 } ) )
		{
			layer.typeDesc = OIIO::TypeDesc::UINT8;
		}
		else if( quantize == std::vector<int>( { 0, 65536, 0, 65536 } ) )
		{
			layer.typeDesc = OIIO::TypeDesc::UINT16;
		}

		const IECore::BoolData *half = layerData->member<IECore::BoolData>( "halfFloat", false );
		if( half && half->readable() && layer.typeDesc == OIIO::TypeDesc::FLOAT )
		{
			layer.typeDesc = OIIO::TypeDesc::HALF;
		}

		if( layer.passType == ccl::PASS_CRYPTOMATTE )
		{
			layer.name = layer.name.substr( 0, layer.name.length() - 2 );
			bool cryptoFound = false;
			for( Layer &_layer : m_layers )
			{
				if( layer.passType != _layer.passType )
					continue;

				if( layer.name == _layer.name )
				{
					_layer.numChannels += layer.numChannels;
					cryptoFound = true;
					break;
				}
			}

			if( !cryptoFound )
			{
				layer.metadata = layerData->copy();
				m_layers.push_back( layer );
			}
		}
		else
		{
			m_layers.push_back( layer );
		}
	}
}

OIIOOutputDriver::~OIIOOutputDriver()
{
}

void OIIOOutputDriver::write_render_tile( const Tile &tile )
{
	const float *imageData;

	const int x = tile.offset.x;
	const int y = tile.offset.y;
	const int w = tile.size.x;
	const int h = tile.size.y;

	std::vector<float> pixels;
	std::vector<float> interleavedData;

	for( Layer layer : m_layers )
	{
		std::unique_ptr<OIIO::ImageOutput> imageOutput( OIIO::ImageOutput::create( layer.path ) );

		OIIO::ImageSpec spec( w, h, layer.numChannels, layer.typeDesc );
		spec.channelnames.clear();
		if( layer.passType == ccl::PASS_CRYPTOMATTE )
		{
			int depth = layer.numChannels / 4;
			for( int i = 0; i < depth; ++i )
			{
				spec.channelnames.push_back( ccl::string_printf( "%s%02d", layer.name.c_str(), i ) + ".R" );
				spec.channelnames.push_back( ccl::string_printf( "%s%02d", layer.name.c_str(), i ) + ".G" );
				spec.channelnames.push_back( ccl::string_printf( "%s%02d", layer.name.c_str(), i ) + ".B" );
				spec.channelnames.push_back( ccl::string_printf( "%s%02d", layer.name.c_str(), i ) + ".A" );
			}

			applyCryptomatteMetadata( spec, layer.name, layer.metadata );
		}
		else
		{
			spec.channelnames.push_back( "R" );
			spec.channelnames.push_back( "G" );
			spec.channelnames.push_back( "B" );
			spec.channelnames.push_back( "A" );
		}
		//spec.full_x = m_displayWindow.min.x;
		//spec.full_y = m_displayWindow.min.y;
		//spec.full_width = m_displayWindow.max.x;
		//spec.full_height = m_displayWindow.max.y;
		//spec.x = x;
		//spec.y = y;
		if( !imageOutput->open( layer.path, spec ) )
		{
			IECore::msg( IECore::Msg::Error, "OIIOOutputDriver:write_render_tile", "Failed to create image file." );
			return;
		}

		if( layer.passType == ccl::PassType::PASS_CRYPTOMATTE )
		{
			int outChannelOffset = 0;
			pixels.resize( w * h * 4 );
			interleavedData.resize( w * h * layer.numChannels );
			int depth = layer.numChannels / 4;
			for( int i = 0; i < depth; ++i )
			{
				if( !tile.get_pass_pixels( ccl::string_printf( "%s%02d", layer.name.c_str(), i ), 4, &pixels[0] ) )
				{
					IECore::msg( IECore::Msg::Error, "OIIOOutputDriver:write_render_tile", "Failed to read render pass pixels." );
					return;
				}
				outChannelOffset = interleave( &pixels[0], w, h, 4, layer.numChannels, outChannelOffset, &interleavedData[0] );
			}

			imageData = &interleavedData[0];
		}
		else
		{
			pixels.resize( w * h * layer.numChannels );
			if( !tile.get_pass_pixels( layer.name, layer.numChannels, &pixels[0] ) )
			{
				IECore::msg( IECore::Msg::Error, "OIIOOutputDriver:write_render_tile", "Failed to read render pass pixels." );
				return;
			}

			imageData = &pixels[0];
		}

		imageOutput->write_image( OIIO::TypeDesc::FLOAT, imageData );

		imageOutput->close();
	}
}

} // namespace IECoreCycles
