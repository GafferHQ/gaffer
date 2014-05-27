//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, John Haddon. All rights reserved.
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

#include "IECore/CompoundData.h"

#include "Gaffer/Context.h"
#include "Gaffer/Box.h"

#include "GafferScene/ShaderSwitch.h"

#include "GafferOSL/OSLImage.h"
#include "GafferOSL/OSLShader.h"
#include "GafferOSL/OSLRenderer.h"

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
	
	addChild( new Plug( "shader" ) );
	
	addChild( new Gaffer::ObjectPlug( "__shading", Gaffer::Plug::Out, new CompoundData() ) );

	// we disable caching for the channel data plug, because our compute
	// simply references data direct from the shading plug, which will itself
	// be cached. we don't want to count the memory usage for that twice.
	outPlug()->channelDataPlug()->setFlags( Plug::Cacheable, false );
}

OSLImage::~OSLImage()
{
}

Gaffer::Plug *OSLImage::shaderPlug()
{
	return getChild<Plug>( g_firstPlugIndex );
}

const Gaffer::Plug *OSLImage::shaderPlug() const
{
	return getChild<Plug>( g_firstPlugIndex );
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
	
	if( input == shaderPlug() )
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
		const Node *sourceNode = inputPlug->source<Plug>()->node();
		if( const OSLShader *shader = runTimeCast<const OSLShader>( sourceNode ) )
		{
			return shader->typePlug()->getValue() == "osl:surface";
		}
		else
		{
			// as for the GafferScene::ShaderAssignment, we accept Box and ShaderSwitch
			// inputs as an indirect means of later getting a connection to a Shader.
			if(
				runTimeCast<const Gaffer::Box>( sourceNode ) ||
				runTimeCast<const GafferScene::ShaderSwitch>( sourceNode )
			)
			{
				return true;
			}
		}
		return false;
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
	return shaderPlug()->getInput<Plug>();
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

void OSLImage::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->formatPlug()->hash();
}

GafferImage::Format OSLImage::computeFormat( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const
{
	return inPlug()->formatPlug()->getValue();
}

void OSLImage::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->dataWindowPlug()->hash();
}

Imath::Box2i OSLImage::computeDataWindow( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const
{
	return inPlug()->dataWindowPlug()->getValue();
}

void OSLImage::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelNames( output, context, h );
	inPlug()->channelNamesPlug()->hash( h );
	
	const Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();
	if( !dataWindow.isEmpty() )
	{
		ContextPtr c = new Context( *context, Context::Borrowed );
		c->set( ImagePlug::tileOriginContextName, ImagePlug::tileOrigin( dataWindow.min ) );
		Context::Scope s( c );
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
		ContextPtr c = new Context( *context, Context::Borrowed );
		c->set( ImagePlug::tileOriginContextName, ImagePlug::tileOrigin( dataWindow.min ) );
		Context::Scope s( c );
	
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
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	h.append( tileOrigin );
	inPlug()->formatPlug()->hash( h );
	
	ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
	const vector<string> &channelNames = channelNamesData->readable();
	for( vector<string>::const_iterator it = channelNames.begin(), eIt = channelNames.end(); it != eIt; ++it )
	{
		h.append( inPlug()->channelDataHash( *it, tileOrigin ) );
	}

	const OSLShader *shader = runTimeCast<const OSLShader>( shaderPlug()->source<Plug>()->node() );
	if( shader )
	{
		shader->stateHash( h );
	}
}

IECore::ConstCompoundDataPtr OSLImage::computeShading( const Gaffer::Context *context ) const
{
	OSLRenderer::ConstShadingEnginePtr shadingEngine;
	if( const OSLShader *shader = runTimeCast<const OSLShader>( shaderPlug()->source<Plug>()->node() ) )
	{
		shadingEngine = shader->shadingEngine();
	}
	
	if( !shadingEngine )
	{
		return static_cast<const CompoundData *>( shadingPlug()->defaultValue() );	
	}
			
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const Format format = inPlug()->formatPlug()->getValue();
	
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

	/// \todo Non-zero display window origins - do we have those?
	const float uStep = 1.0f / format.width();
	const float uMin = 0.5f * uStep;
	
	const float vStep = 1.0f / format.height();
	const float vMin = 0.5f * vStep;
	
	const size_t xMax = tileOrigin.x + tileSize;
	const size_t yMax = tileOrigin.y + tileSize;
	for( size_t y = tileOrigin.y; y < yMax; ++y )
	{
		const float v = vMin + y * vStep;
		for( size_t x = tileOrigin.x; x < xMax; ++x )
		{
			uWritable.push_back( uMin + x * uStep );
			vWritable.push_back( v );
			pWritable.push_back( V3f( x, y, 0.0f ) );
		}
	}
	
	shadingPoints->writable()["P"] = pData;
	shadingPoints->writable()["u"] = uData;
	shadingPoints->writable()["v"] = vData;
	
	ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
	const vector<string> &channelNames = channelNamesData->readable();
	for( vector<string>::const_iterator it = channelNames.begin(), eIt = channelNames.end(); it != eIt; ++it )
	{
		shadingPoints->writable()[*it] = constPointerCast<FloatVectorData>( inPlug()->channelData( *it, tileOrigin ) );
	}
	
	CompoundDataPtr result = shadingEngine->shade( shadingPoints );
	
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
