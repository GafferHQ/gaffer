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

#include "IEDisplayOutputDriver.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "scene/pass.h"
#include "util/murmurhash.h"
#include "util/string.h"
IECORE_POP_DEFAULT_VISIBILITY

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"


namespace IECoreCycles
{

IEDisplayOutputDriver::IEDisplayOutputDriver( const Imath::Box2i &displayWindow, const Imath::Box2i &dataWindow, IECore::ConstCompoundDataPtr parameters )
{
	const IECore::CompoundData *layersData = parameters->member<IECore::CompoundData>( "layers", true );
	const IECore::StringData *defaultPass = parameters->member<IECore::StringData>( "default", false );
	const IECore::CompoundDataMap &layers = layersData->readable();
	const ccl::NodeEnum &typeEnum = *ccl::Pass::get_type_enum();
	IECore::CompoundDataPtr params;
	bool defaultFound = false;

	for( IECore::CompoundDataMap::const_iterator it = layers.begin(), eIt = layers.end(); it != eIt; ++it )
	{
		std::vector<std::string> channelNames;
		Layer layer;
		const IECore::CompoundData *layerData = IECore::runTimeCast<IECore::CompoundData>( it->second.get() );
		layer.name = layerData->member<IECore::StringData>( "name", true )->readable();

		const IECore::StringData *passTypeData = layerData->member<IECore::StringData>( "type", true );
		ccl::ustring passType( passTypeData->readable() );
		if( passType == ccl::ustring( "lightgroup" ) )
		{
			layer.numChannels = 3;
		}
		else if( typeEnum.exists( passType ) )
		{
			ccl::PassInfo passInfo = ccl::Pass::get_info( static_cast<ccl::PassType>( typeEnum[passType] ) );
			layer.numChannels = passInfo.num_components;
		}

		if( !defaultFound )
		{
			if( defaultPass && layer.name == defaultPass->readable() )
			{
				// Get params from default pass
				params = layerData->copy();
				defaultFound = true;
			}
		}
		if( layer.name == "rgba" )
		{
			channelNames.push_back( "R" );
			channelNames.push_back( "G" );
			channelNames.push_back( "B" );
			channelNames.push_back( "A" );
		}
		else if( layer.name == "rgba_denoised" )
		{
			channelNames.push_back( "denoised.R" );
			channelNames.push_back( "denoised.G" );
			channelNames.push_back( "denoised.B" );
			channelNames.push_back( "denoised.A" );
		}
		else if( layer.numChannels == 1 )
		{
			channelNames.push_back( layer.name );
		}
		else if( layer.numChannels == 2 )
		{
			channelNames.push_back( layer.name + ".R" );
			channelNames.push_back( layer.name + ".G" );
		}
		else if( layer.numChannels == 3 )
		{
			channelNames.push_back( layer.name + ".R" );
			channelNames.push_back( layer.name + ".G" );
			channelNames.push_back( layer.name + ".B" );
		}
		else if( layer.numChannels == 4 )
		{
			channelNames.push_back( layer.name + ".R" );
			channelNames.push_back( layer.name + ".G" );
			channelNames.push_back( layer.name + ".B" );
			channelNames.push_back( layer.name + ".A" );
		}

		const IECore::StringData *driverType = layerData->member<IECore::StringData>( "driverType", true );

		layer.displayDriver = IECoreImage::DisplayDriver::create(
								driverType->readable(),
								displayWindow,
								dataWindow,
								channelNames,
								layerData
		);

		m_layers.push_back( layer );
	}
}

IEDisplayOutputDriver::~IEDisplayOutputDriver()
{
	for( auto layer : m_layers )
	{
		if( layer.displayDriver )
		{
			try
			{
				layer.displayDriver->imageClose();
			}
			catch( const std::exception &e )
			{
				// We have to catch and report exceptions because letting them out into pure c land
				// just causes aborts.
				IECore::msg( IECore::Msg::Error, "IEDisplayOutputDriver:driverClose", e.what() );
			}
			layer.displayDriver = nullptr;
		}
	}
}

void IEDisplayOutputDriver::write_render_tile( const Tile &tile )
{
	const float *imageData = nullptr;

	const int x = tile.offset.x;
	const int y = tile.offset.y;
	const int w = tile.size.x;
	const int h = tile.size.y;

	Imath::Box2i _tile( Imath::V2i( x, y ), Imath::V2i( x + w - 1, y + h - 1 ) );

	std::vector<float> pixels( w * h * 4 );

	for ( Layer layer : m_layers )
	{
		if( !tile.get_pass_pixels( layer.name, layer.numChannels, &pixels[0] ) )
		{
			memset( &pixels[0], 0, pixels.size() * sizeof(float) );
		}

		imageData = &pixels[0];

		try
		{
			layer.displayDriver->imageData( _tile, imageData, w * h * layer.numChannels );
		}
		catch( const std::exception &e )
		{
			// we have to catch and report exceptions because letting them out into pure c land
			// just causes aborts.
			IECore::msg( IECore::Msg::Error, "IEDisplayOutputDriver:write_render_tile", e.what() );
		}
	}
}

bool IEDisplayOutputDriver::update_render_tile( const Tile &tile )
{
	for ( Layer layer : m_layers )
	{
		if( !layer.displayDriver )
		{
			return false;
		}
		if( !layer.displayDriver->acceptsRepeatedData() )
		{
			return false;
		}
	}

	write_render_tile( tile );
	return true;
}

} // namespace IECoreCycles
