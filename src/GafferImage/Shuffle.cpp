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

#include "GafferImage/Shuffle.h"

#include "GafferImage/ImageAlgo.h"

#include "IECore/NullObject.h"

#include <unordered_map>

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

namespace
{

struct MappingData : public IECore::Data
{

	MappingData( const StringVectorData *inChannelNames, const ShufflesPlug *shuffles, Shuffle::MissingSourceMode mode )
	{
		for( const auto &channelName : inChannelNames->readable() )
		{
			m_mapping[channelName] = channelName;
		}

		Map extraSources = {
			{ "__white", "__white" },
			{ "__black", "__black" }
		};
		if( mode == Shuffle::MissingSourceMode::Black )
		{
			extraSources["*"] = "__black";
		}

		m_mapping = shuffles->shuffleWithExtraSources( m_mapping, extraSources, mode == Shuffle::MissingSourceMode::Ignore );

		m_outChannelNames = new StringVectorData();
		for( const auto &m : m_mapping )
		{
			m_outChannelNames->writable().push_back( m.first );
		}
		m_outChannelNames->writable() = ImageAlgo::sortedChannelNames( m_outChannelNames->readable() );
	}

	const StringVectorData *outChannelNames() const { return m_outChannelNames.get(); }

	const string &inChannelName( const string &outChannelName ) const
	{
		auto it = m_mapping.find( outChannelName );
		if( it == m_mapping.end() )
		{
			throw IECore::Exception( fmt::format( "Invalid output channel {}", outChannelName ) );
		}
		return it->second;
	}

	private :

		StringVectorDataPtr m_outChannelNames;

		using Map = unordered_map<string, string>;
		Map m_mapping;

};

IE_CORE_DECLAREPTR( MappingData )

} // namespace

size_t Shuffle::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( Shuffle );

Shuffle::Shuffle( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "missingSourceMode", Plug::In, (int)MissingSourceMode::Black, (int)MissingSourceMode::Ignore, (int)MissingSourceMode::Black ) );
	addChild( new ShufflesPlug( "shuffles" ) );
	addChild( new ObjectPlug( "__mapping", Plug::Out, IECore::NullObject::defaultNullObject() ) );

	// Pass-through the things we don't want to modify.
	outPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->deepPlug()->setInput( inPlug()->deepPlug() );
	outPlug()->sampleOffsetsPlug()->setInput( inPlug()->sampleOffsetsPlug() );
}

Shuffle::~Shuffle()
{
}

Gaffer::IntPlug *Shuffle::missingSourceModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Shuffle::missingSourceModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::ShufflesPlug *Shuffle::shufflesPlug()
{
	return getChild<ShufflesPlug>( g_firstPlugIndex +1 );
}

const Gaffer::ShufflesPlug *Shuffle::shufflesPlug() const
{
	return getChild<ShufflesPlug>( g_firstPlugIndex + 1 );
}

Gaffer::ObjectPlug *Shuffle::mappingPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::ObjectPlug *Shuffle::mappingPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 2 );
}

void Shuffle::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if(
		input == inPlug()->channelNamesPlug() ||
		shufflesPlug()->isAncestorOf( input ) ||
		input == missingSourceModePlug()
	)
	{
		outputs.push_back( mappingPlug() );
	}

	if( input == mappingPlug() )
	{
		outputs.push_back( outPlug()->channelNamesPlug() );
	}

	if(
		input == mappingPlug() ||
		input == inPlug()->channelDataPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void Shuffle::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );

	if( output == mappingPlug() )
	{
		inPlug()->channelNamesPlug()->hash( h );
		shufflesPlug()->hash( h );
		missingSourceModePlug()->hash( h );
	}
}

void Shuffle::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == mappingPlug() )
	{
		ConstStringVectorDataPtr inChannelNames = inPlug()->channelNamesPlug()->getValue();
		static_cast<ObjectPlug *>( output )->setValue(
			new MappingData( inChannelNames.get(), shufflesPlug(), (MissingSourceMode)missingSourceModePlug()->getValue() )
		);
	}

	return ImageProcessor::compute( output, context );
}

void Shuffle::hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelNames( parent, context, h );
	mappingPlug()->hash( h );
}

IECore::ConstStringVectorDataPtr Shuffle::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstMappingDataPtr mapping = boost::static_pointer_cast<const MappingData>( mappingPlug()->getValue() );
	return mapping->outChannelNames();
}


void Shuffle::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	std::string c = inChannelName( context->get<string>( ImagePlug::channelNameContextName ) );

	if( c == "__black" || c == "" || c == "__white")
	{
		const Imath::V2i tileOrigin = context->get<Imath::V2i>( ImagePlug::tileOriginContextName );

		ImagePlug::ChannelDataScope channelDataScope( context );
		channelDataScope.remove( ImagePlug::channelNameContextName );
		channelDataScope.remove( ImagePlug::tileOriginContextName );
		bool deep = inPlug()->deepPlug()->getValue();

		if( !deep )
		{
			h = ( c == "__white" ) ? ImagePlug::whiteTile()->Object::hash() : ImagePlug::blackTile()->Object::hash();
		}
		else
		{
			channelDataScope.setTileOrigin( &tileOrigin );
			inPlug()->sampleOffsetsPlug()->hash( h );
			h.append( c == "__white" );
		}
	}
	else
	{
		ImagePlug::ChannelDataScope channelDataScope( context );
		channelDataScope.setChannelName( &c );
		h = inPlug()->channelDataPlug()->hash();
	}
}

IECore::ConstFloatVectorDataPtr Shuffle::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string c = inChannelName( context->get<string>( ImagePlug::channelNameContextName ) );

	if( c == "__black" || c == "" || c == "__white")
	{
		ImagePlug::ChannelDataScope channelDataScope( context );
		channelDataScope.remove( ImagePlug::channelNameContextName );
		channelDataScope.remove( ImagePlug::tileOriginContextName );
		bool deep = inPlug()->deepPlug()->getValue();

		if( !deep )
		{
			return ( c == "__white" ) ? ImagePlug::whiteTile() : ImagePlug::blackTile();
		}
		else
		{
			channelDataScope.setTileOrigin( &tileOrigin );
			ConstIntVectorDataPtr sampleOffsets = inPlug()->sampleOffsetsPlug()->getValue();

			FloatVectorDataPtr result = new FloatVectorData();
			result->writable().resize(
				sampleOffsets->readable()[ ImagePlug::tileSize() * ImagePlug::tileSize() - 1 ],
				( c == "__white" ) ? 1.0f : 0.0f
			);

			return result;
		}
	}
	else
	{
		ImagePlug::ChannelDataScope channelDataScope( context );
		channelDataScope.setChannelName( &c );
		return inPlug()->channelDataPlug()->getValue();
	}
}

std::string Shuffle::inChannelName( const std::string &outChannelName ) const
{
	ImagePlug::GlobalScope s( Context::current() );
	ConstMappingDataPtr mapping = boost::static_pointer_cast<const MappingData>( mappingPlug()->getValue() );
	return mapping->inChannelName( outChannelName );
}
