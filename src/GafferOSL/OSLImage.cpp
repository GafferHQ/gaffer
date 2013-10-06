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

#include "tbb/mutex.h"

#include "IECore/CompoundData.h"
#include "IECore/AttributeBlock.h"
#include "IECore/LRUCache.h"

#include "Gaffer/Context.h"

#include "GafferImage/ChannelMaskPlug.h"

#include "GafferOSL/OSLImage.h"
#include "GafferOSL/OSLShader.h"
#include "GafferOSL/OSLRenderer.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;
using namespace GafferOSL;

//////////////////////////////////////////////////////////////////////////
// LRUCache of ShadingEngines
//////////////////////////////////////////////////////////////////////////

namespace GafferOSL
{

namespace Detail
{

struct ShadingEngineCacheKey
{
	
	ShadingEngineCacheKey( const OSLShader *s )
		:	shader( s ), hash( s->stateHash() )
	{
	}

	bool operator == ( const ShadingEngineCacheKey &other ) const
	{
		return hash == other.hash;
	}
	
	bool operator != ( const ShadingEngineCacheKey &other ) const
	{
		return hash != other.hash;
	}

	bool operator < ( const ShadingEngineCacheKey &other ) const
	{
		return hash < other.hash;
	}
	
	mutable const OSLShader *shader;	
	MurmurHash hash;

};

static OSLRenderer::ConstShadingEnginePtr getter( const ShadingEngineCacheKey &key, size_t &cost )
{
	cost = 1;
	
	ConstObjectVectorPtr state = key.shader->state();
	key.shader = NULL; // there's no guarantee the node would even exist after this call, so zero it out to avoid temptation
	
	if( !state->members().size() )
	{
		return NULL;
	}
	
	static OSLRendererPtr g_renderer;	
	static tbb::mutex g_rendererMutex;

	tbb::mutex::scoped_lock lock( g_rendererMutex );
		
	if( !g_renderer )
	{
		g_renderer = new OSLRenderer;
		if( const char *searchPath = getenv( "OSL_SHADER_PATHS" ) )
		{
			g_renderer->setOption( "osl:searchpath:shader", new StringData( searchPath ) );
		}
		g_renderer->worldBegin();
	}
	
	IECore::AttributeBlock attributeBlock( g_renderer );

	for( ObjectVector::MemberContainer::const_iterator it = state->members().begin(), eIt = state->members().end(); it != eIt; it++ )
	{
		const StateRenderable *s = runTimeCast<const StateRenderable>( it->get() );
		if( s )
		{
			s->render( g_renderer );
		}
	}
		
	return g_renderer->shadingEngine();
}

typedef LRUCache<ShadingEngineCacheKey, OSLRenderer::ConstShadingEnginePtr> ShadingEngineCache;
static ShadingEngineCache g_shadingEngineCache( getter, 10000 );

} // namespace Detail

OSLRenderer::ConstShadingEnginePtr OSLImage::shadingEngine( const Gaffer::Plug *shaderPlug )
{
	const OSLShader *shader = runTimeCast<const OSLShader>( shaderPlug->source<Plug>()->node() );
	if( !shader )
	{
		return NULL;
	}

	return Detail::g_shadingEngineCache.get( Detail::ShadingEngineCacheKey( shader ) );
}

} // namespace GafferOSL

//////////////////////////////////////////////////////////////////////////
// OSLImage
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( OSLImage );

size_t OSLImage::g_firstPlugIndex = 0;

OSLImage::OSLImage( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	
	addChild( new Plug( "shader" ) );
	
	addChild( new Gaffer::ObjectPlug( "__shading", Gaffer::Plug::Out, new CompoundData() ) );
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

void OSLImage::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );
	
	if( input == shaderPlug() )
	{
		/// \todo We should really be pushing shadingPlug()
		/// here, and then pushing channelDataPlug() in the
		/// affects for shadingPlug(). However, currently
		/// affects() isn't called for shadingPlug() because
		/// it's an output. We could do the output->input trick
		/// that we're using in GafferScene::Group, but it
		/// seems worth considering allowing affects() to be
		/// called for outputs, to avoid forcing lots of 
		/// implementations to use extra plugs when they're not
		/// really needed.
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

bool OSLImage::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
{
	if( !ImageProcessor::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}
	
	if( plug == shaderPlug() )
	{
		return runTimeCast<const OSLShader>( inputPlug->source<Plug>()->node() );
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

void OSLImage::hashFormatPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->formatPlug()->hash();
}

void OSLImage::hashDataWindowPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->dataWindowPlug()->hash();
}

void OSLImage::hashChannelNamesPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->channelNamesPlug()->hash();
}

void OSLImage::hashChannelDataPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	shadingPlug()->hash( h );
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

GafferImage::Format OSLImage::computeFormat( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const
{
	return inPlug()->formatPlug()->getValue();
}

Imath::Box2i OSLImage::computeDataWindow( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const
{
	return inPlug()->dataWindowPlug()->getValue();
}

IECore::ConstStringVectorDataPtr OSLImage::computeChannelNames( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const
{
	return inPlug()->channelNamesPlug()->getValue();
}

IECore::ConstFloatVectorDataPtr OSLImage::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const
{	
	int channelIndex = ChannelMaskPlug::channelIndex( channelName );
	if( channelIndex > 2 )
	{
		/// \todo Better mapping between arbitrary shading results and channels. Pass-through of
		/// channels without a shading result.
		return inPlug()->channelDataPlug()->getValue();	
	}
	
	ConstCompoundDataPtr shadedPoints = runTimeCast<const CompoundData>( shadingPlug()->getValue() );
	if( !shadedPoints || !shadedPoints->readable().size() )
	{
		return inPlug()->channelDataPlug()->getValue();
	}
	
	const std::vector<Color3f> &ci = shadedPoints->member<Color3fVectorData>( "Ci" )->readable();
	
	FloatVectorDataPtr resultData = new FloatVectorData;
	std::vector<float> &result = resultData->writable();
	result.reserve( ci.size() );
	for( size_t i = 0, e = ci.size(); i < e; ++i )
	{
		result.push_back( ci[i][channelIndex] );
	}
	
	return resultData;
}

Gaffer::ObjectPlug *OSLImage::shadingPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::ObjectPlug *OSLImage::shadingPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 1 );
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
	OSLRenderer::ConstShadingEnginePtr shadingEngine = OSLImage::shadingEngine( shaderPlug() );
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
	
	return shadingEngine->shade( shadingPoints );
}
