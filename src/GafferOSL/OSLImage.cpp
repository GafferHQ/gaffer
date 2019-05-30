//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, John Haddon. All rights reserved.
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

#include "GafferOSL/OSLImage.h"

#include "GafferOSL/OSLShader.h"
#include "GafferOSL/ShadingEngine.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

#include "IECore/CompoundData.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;
using namespace GafferOSL;

IE_CORE_DEFINERUNTIMETYPED( OSLImage );

size_t OSLImage::g_firstPlugIndex = 0;

OSLImage::OSLImage( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new GafferScene::ShaderPlug( "shader" ) );

	addChild( new Gaffer::ObjectPlug( "__shading", Gaffer::Plug::Out, new CompoundData() ) );

	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
}

OSLImage::~OSLImage()
{
}

GafferScene::ShaderPlug *OSLImage::shaderPlug()
{
	return getChild<GafferScene::ShaderPlug>( g_firstPlugIndex );
}

const GafferScene::ShaderPlug *OSLImage::shaderPlug() const
{
	return getChild<GafferScene::ShaderPlug>( g_firstPlugIndex );
}

Gaffer::ObjectPlug *OSLImage::shadingPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::ObjectPlug *OSLImage::shadingPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 1 );
}

void OSLImage::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if(
		input == shaderPlug() ||
		input == inPlug()->formatPlug() ||
		input == inPlug()->channelNamesPlug() ||
		input == inPlug()->channelDataPlug()
	)
	{
		outputs.push_back( shadingPlug() );
	}
	else if( input == shadingPlug() )
	{
		outputs.push_back( outPlug()->channelNamesPlug() );
		outputs.push_back( outPlug()->channelDataPlug()	);
	}
}

bool OSLImage::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
{
	if( !ImageProcessor::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( !inputPlug )
	{
		return true;
	}

	if( plug == shaderPlug() )
	{
		if( const GafferScene::Shader *shader = runTimeCast<const GafferScene::Shader>( inputPlug->source()->node() ) )
		{
			const OSLShader *oslShader = runTimeCast<const OSLShader>( shader );
			return oslShader && oslShader->typePlug()->getValue() == "osl:surface";
		}
	}

	return true;
}

bool OSLImage::enabled() const
{
	if( !ImageProcessor::enabled() )
	{
		return false;
	}
	// generally the connectedness of plugs should not be queried by compute() or hash() (which
	// will end up calling this function), because Shaders are not ComputeNodes and must be
	// accessed directly anyway, it's ok.
	return shaderPlug()->getInput();
}

void OSLImage::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );

	if( output == shadingPlug() )
	{
		hashShading( context, h );
	}
}

void OSLImage::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == shadingPlug() )
	{
		static_cast<ObjectPlug *>( output )->setValue( computeShading( context ) );
		return;
	}

	ImageProcessor::compute( output, context );
}

Gaffer::ValuePlug::CachePolicy OSLImage::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == outPlug()->channelDataPlug() )
	{
		// We disable caching for the channel data plug, because our compute
		// simply references data direct from the shading plug, which will itself
		// be cached. We don't want to count the memory usage for that twice.
		return ValuePlug::CachePolicy::Uncached;
	}

	return ImageProcessor::computeCachePolicy( output );
}

void OSLImage::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelNames( output, context, h );
	inPlug()->channelNamesPlug()->hash( h );

	const Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();
	if( !dataWindow.isEmpty() )
	{
		ImagePlug::ChannelDataScope channelDataScope( context );
		channelDataScope.setTileOrigin( ImagePlug::tileOrigin( dataWindow.min ) );
		shadingPlug()->hash( h );
	}
}

IECore::ConstStringVectorDataPtr OSLImage::computeChannelNames( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const
{
	ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();

	set<string> result( channelNamesData->readable().begin(), channelNamesData->readable().end() );

	const Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();
	if( !dataWindow.isEmpty() )
	{
		ImagePlug::ChannelDataScope channelDataScope( context );
		channelDataScope.setTileOrigin( ImagePlug::tileOrigin( dataWindow.min ) );

		ConstCompoundDataPtr shading = runTimeCast<const CompoundData>( shadingPlug()->getValue() );
		for( CompoundDataMap::const_iterator it = shading->readable().begin(), eIt = shading->readable().end(); it != eIt; ++it )
		{
			result.insert( it->first );
		}
	}

	return new StringVectorData( vector<string>( result.begin(), result.end() ) );
}

void OSLImage::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelData( output, context, h );
	h.append( context->get<std::string>( ImagePlug::channelNameContextName ) );
	shadingPlug()->hash( h );
	inPlug()->channelDataPlug()->hash( h );
}

IECore::ConstFloatVectorDataPtr OSLImage::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const
{
	ConstCompoundDataPtr shadedPoints = runTimeCast<const CompoundData>( shadingPlug()->getValue() );
	ConstFloatVectorDataPtr result = shadedPoints->member<FloatVectorData>( channelName );

	if( !result )
	{
		result = inPlug()->channelDataPlug()->getValue();
	}

	return result;
}

void OSLImage::hashShading( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ConstShadingEnginePtr shadingEngine;
	if( auto shader = runTimeCast<const OSLShader>( shaderPlug()->source()->node() ) )
	{
		ImagePlug::GlobalScope globalScope( context );
		shadingEngine = shader->shadingEngine();
	}

	if( !shadingEngine )
	{
		h = shadingPlug()->defaultValue()->hash();
		return;
	}

	h.append( context->get<V2i>( ImagePlug::tileOriginContextName ) );

	ConstStringVectorDataPtr channelNamesData;
	{
		ImagePlug::GlobalScope c( context );
		inPlug()->formatPlug()->hash( h );
		channelNamesData = inPlug()->channelNamesPlug()->getValue();
	}

	{
		ImagePlug::ChannelDataScope c( context );
		for( const auto &channelName : channelNamesData->readable() )
		{
			if( shadingEngine->needsAttribute( channelName ) )
			{
				c.setChannelName( channelName );
				inPlug()->channelDataPlug()->hash( h );
			}
		}
	}

	shadingEngine->hash( h );
}

IECore::ConstCompoundDataPtr OSLImage::computeShading( const Gaffer::Context *context ) const
{
	ConstShadingEnginePtr shadingEngine;
	if( auto shader = runTimeCast<const OSLShader>( shaderPlug()->source()->node() ) )
	{
		ImagePlug::GlobalScope globalScope( context );
		shadingEngine = shader->shadingEngine();
	}

	if( !shadingEngine )
	{
		return static_cast<const CompoundData *>( shadingPlug()->defaultValue() );
	}

	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	Format format;
	ConstStringVectorDataPtr channelNamesData;
	{
		ImagePlug::GlobalScope c( context );
		format = inPlug()->formatPlug()->getValue();
		channelNamesData = inPlug()->channelNamesPlug()->getValue();
	}

	CompoundDataPtr shadingPoints = new CompoundData();

	V3fVectorDataPtr pData = new V3fVectorData;
	FloatVectorDataPtr uData = new FloatVectorData;
	FloatVectorDataPtr vData = new FloatVectorData;

	vector<V3f> &pWritable = pData->writable();
	vector<float> &uWritable = uData->writable();
	vector<float> &vWritable = vData->writable();

	const size_t tileSize = ImagePlug::tileSize();
	pWritable.reserve( tileSize * tileSize );
	uWritable.reserve( tileSize * tileSize );
	vWritable.reserve( tileSize * tileSize );

	const V2f uvStep = V2f( 1.0f ) / format.getDisplayWindow().size();
	// UV value for the pixel at 0,0
	const V2f uvOrigin = (V2f(0.5) - format.getDisplayWindow().min) * uvStep;

	const V2i pMax = tileOrigin + V2i( tileSize );
	V2i p;
	for( p.y = tileOrigin.y; p.y < pMax.y; ++p.y )
	{
		const float v = uvOrigin.y + p.y * uvStep.y;
		for( p.x = tileOrigin.x; p.x < pMax.x; ++p.x )
		{
			uWritable.push_back( uvOrigin.x + p.x * uvStep.x );
			vWritable.push_back( v );
			pWritable.push_back( V3f( p.x + 0.5f, p.y + 0.5f, 0.0f ) );
		}
	}

	shadingPoints->writable()["P"] = pData;
	shadingPoints->writable()["u"] = uData;
	shadingPoints->writable()["v"] = vData;

	{
		ImagePlug::ChannelDataScope c( context );
		for( const auto &channelName : channelNamesData->readable() )
		{
			if( shadingEngine->needsAttribute( channelName ) )
			{
				c.setChannelName( channelName );
				shadingPoints->writable()[channelName] = boost::const_pointer_cast<FloatVectorData>(
					inPlug()->channelDataPlug()->getValue()
				);
			}
		}
	}

	CompoundDataPtr result = shadingEngine->shade( shadingPoints.get() );

	// remove results that aren't suitable to become channels
	for( CompoundDataMap::iterator it = result->writable().begin(); it != result->writable().end();  )
	{
		CompoundDataMap::iterator nextIt = it; nextIt++;
		if( !runTimeCast<FloatVectorData>( it->second ) )
		{
			result->writable().erase( it );
		}
		it = nextIt;
	}

	return result;
}
