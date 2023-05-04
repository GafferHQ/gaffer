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

#include "GafferImage/CopyChannels.h"

#include "GafferImage/BufferAlgo.h"
#include "GafferImage/ImageAlgo.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"

#include "IECore/StringAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo Maybe move this to BufferAlgo.h? It could probably be reused
/// in Offset::computeChannelData() at least.
void copyRegion( const float *fromBuffer, const Box2i &fromWindow, const Box2i &fromRegion, float *toBuffer, const Box2i &toWindow, const V2i &toOrigin )
{
	const int width = fromRegion.max.x - fromRegion.min.x;

	V2i fromP = fromRegion.min;
	V2i toP = toOrigin;
	for( int maxY = fromRegion.max.y; fromP.y < maxY; ++fromP.y, ++toP.y )
	{
		memcpy(
			toBuffer + BufferAlgo::index( toP, toWindow ),
			fromBuffer + BufferAlgo::index( fromP, fromWindow ),
			sizeof( float ) * width
		);
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// CopyChannels
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( CopyChannels );

size_t CopyChannels::g_firstPlugIndex = 0;

CopyChannels::CopyChannels( const std::string &name )
	:	FlatImageProcessor( name, /* minInputs = */ 2 )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "channels" ) );
	addChild( new CompoundObjectPlug( "__mapping", Plug::Out, new CompoundObject() ) );

	outPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
}

CopyChannels::~CopyChannels()
{
}

Gaffer::StringPlug *CopyChannels::channelsPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *CopyChannels::channelsPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

Gaffer::CompoundObjectPlug *CopyChannels::mappingPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::CompoundObjectPlug *CopyChannels::mappingPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 1 );
}

void CopyChannels::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageProcessor::affects( input, outputs );

	if( input == inPlug()->viewNamesPlug() )
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( mappingPlug() );
		return;
	}

	const ImagePlug *imagePlug = input->parent<ImagePlug>();
	if( imagePlug && imagePlug->parent<Plug>() != inPlugs() )
	{
		imagePlug = nullptr;
	}

	if( imagePlug && input == imagePlug->dataWindowPlug() )
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
	}

	if(
		( imagePlug && input == imagePlug->channelNamesPlug() ) ||
		input == channelsPlug()
	)
	{
		outputs.push_back( mappingPlug() );
	}

	if( input == mappingPlug() )
	{
		outputs.push_back( outPlug()->channelNamesPlug() );
	}

	if(
		( imagePlug && input == imagePlug->channelDataPlug() ) ||
		input == mappingPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void CopyChannels::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hash( output, context, h );

	if( output == mappingPlug() )
	{
		for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++it )
		{
			if( !(*it)->getInput() || !ImageAlgo::viewIsValid( context, (*it)->viewNames()->readable() ) )
			{
				continue;
			}
			(*it)->channelNamesPlug()->hash( h );
		}
		channelsPlug()->hash( h );
	}
}

void CopyChannels::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == mappingPlug() )
	{
		const string channelMatchPatterns = channelsPlug()->getValue();

		CompoundObjectPtr result = new CompoundObject();
		StringVectorDataPtr channelNamesData = new StringVectorData;
		result->members()["__channelNames"] = channelNamesData;
		vector<string> &channelNames = channelNamesData->writable();
		size_t i = 0;
		for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++i, ++it )
		{
			/// \todo We need this check because an unconnected input
			/// has a default channelNames value of [ "R", "G", "B" ],
			/// when it should have an empty default instead. Fix
			/// the ImagePlug constructor and remove the check.
			if( !(*it)->getInput() || !ImageAlgo::viewIsValid( context, (*it)->viewNames()->readable() ) )
			{
				continue;
			}
			ConstStringVectorDataPtr inputChannelNamesData = (*it)->channelNamesPlug()->getValue();
			const vector<string> &inputChannelNames = inputChannelNamesData->readable();
			for( vector<string>::const_iterator cIt = inputChannelNames.begin(), ceIt = inputChannelNames.end(); cIt != ceIt; ++cIt )
			{
				if( i > 0 && !StringAlgo::matchMultiple( *cIt, channelMatchPatterns ) )
				{
					continue;
				}
				if( find( channelNames.begin(), channelNames.end(), *cIt ) == channelNames.end() )
				{
					channelNames.push_back( *cIt );
				}
				result->members()[*cIt] = new IntData( i );
			}
		}
		static_cast<CompoundObjectPlug *>( output )->setValue( result );
		return;
	}

	FlatImageProcessor::compute( output, context );
}


void CopyChannels::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashDataWindow( output, context, h );

	for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++it )
	{
		if( ImageAlgo::viewIsValid( context, (*it)->viewNames()->readable() ) )
		{
			(*it)->dataWindowPlug()->hash( h );
		}
	}
}

Imath::Box2i CopyChannels::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Imath::Box2i dataWindow;
	for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++it )
	{
		if( ImageAlgo::viewIsValid( context, (*it)->viewNames()->readable() ) )
		{
			dataWindow.extendBy( (*it)->dataWindowPlug()->getValue() );
		}
	}

	return dataWindow;
}

void CopyChannels::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashChannelNames( output, context, h );

	mappingPlug()->hash( h );
}

IECore::ConstStringVectorDataPtr CopyChannels::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstCompoundObjectPtr mapping = mappingPlug()->getValue();
	return mapping->member<StringVectorData>( "__channelNames" );
}

void CopyChannels::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	// Fast shortcut when there is a single input
	if( inPlugs()->children().size() == 2 && inPlugs()->getChild<ImagePlug>( 0 )->getInput() && !inPlugs()->getChild<ImagePlug>( 1 )->getInput() )
	{
		h = inPlugs()->getChild<ImagePlug>( 0 )->channelDataPlug()->hash();
		return;
	}

	ConstCompoundObjectPtr mapping;
	{
		ImagePlug::GlobalScope c( context );
		mapping = mappingPlug()->getValue();
	}
	if( const IntData *i = mapping->member<const IntData>( context->get<string>( ImagePlug::channelNameContextName ) ) )
	{
		const ImagePlug *inputImage = inPlugs()->getChild<ImagePlug>( i->readable() );
		const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
		const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

		if( !ImageAlgo::viewIsValid( context, inputImage->viewNames()->readable() ) )
		{
			h = ImagePlug::blackTile()->Object::hash();
			return;
		}

		Box2i inputDataWindow;
		{
			ImagePlug::GlobalScope c( context );
			inputDataWindow = inputImage->dataWindowPlug()->getValue();
		}

		const Box2i validBound = BufferAlgo::intersection( tileBound, inputDataWindow );
		if( validBound == tileBound )
		{
			h = inputImage->channelDataPlug()->hash();
		}
		else
		{
			FlatImageProcessor::hashChannelData( parent, context, h );
			if( !BufferAlgo::empty( validBound ) )
			{
				inputImage->channelDataPlug()->hash( h );
				h.append( BufferAlgo::intersection( inputDataWindow, tileBound ) );
			}
		}
	}
	else
	{
		h = ImagePlug::blackTile()->Object::hash();
	}
}

IECore::ConstFloatVectorDataPtr CopyChannels::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// Fast shortcut when there is a single input
	if( inPlugs()->children().size() == 2 && inPlugs()->getChild<ImagePlug>( 0 )->getInput() && !inPlugs()->getChild<ImagePlug>( 1 )->getInput() )
	{
		return inPlugs()->getChild<ImagePlug>( 0 )->channelDataPlug()->getValue();
	}

	ConstCompoundObjectPtr mapping;
	{
		ImagePlug::GlobalScope c( context );
		mapping = mappingPlug()->getValue();
	}
	if( const IntData *i = mapping->member<const IntData>( channelName ) )
	{
		const ImagePlug *inputImage = inPlugs()->getChild<ImagePlug>( i->readable() );
		const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

		if( !ImageAlgo::viewIsValid( context, inputImage->viewNames()->readable() ) )
		{
			return ImagePlug::blackTile();
		}

		Box2i inputDataWindow;
		{
			ImagePlug::GlobalScope c( context );
			inputDataWindow = inputImage->dataWindowPlug()->getValue();
		}
		const Box2i validBound = BufferAlgo::intersection( tileBound, inputDataWindow );
		if( validBound == tileBound )
		{
			return inputImage->channelDataPlug()->getValue();
		}
		else
		{
			FloatVectorDataPtr resultData = new FloatVectorData;
			vector<float> &result = resultData->writable();
			result.resize( ImagePlug::tileSize() * ImagePlug::tileSize(), 0.0f );
			if( !BufferAlgo::empty( validBound ) )
			{
				ConstFloatVectorDataPtr inputData = inputImage->channelDataPlug()->getValue();
				copyRegion(
					&inputData->readable().front(),
					tileBound,
					validBound,
					&result.front(),
					tileBound,
					validBound.min
				);
			}
			return resultData;
		}
	}
	else
	{
		return ImagePlug::blackTile();
	}
}
