//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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
//      * Neither the name of Cinesite VFX Ltd. nor the names of
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

#include "GafferArnoldUI/Private/VisualiserAlgo.h"

#include "GafferSceneUI/StandardLightVisualiser.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "GafferOSL/ShadingEngineAlgo.h"

#include "IECoreGL/PointsPrimitive.h"

#include "IECore/MessageHandler.h"
#include "IECore/Exception.h"
#include "IECore/TypedData.h"
#include "IECore/VectorTypedData.h"

#include "ai.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreGLPreview;
using namespace IECoreScene;
using namespace GafferArnoldUI::Private;

// The ArnoldLightVisualiser provides an implementation of surfaceTexture,
// rendering a lights color input network via OSL.
//
// Native OSL networks are fully supported, with basic conversion of
// Arnold shaders networks to OSL for common scenarios. If unsupported
// Arnold shaders are present in the network, a fallback of the last image
// node found will be used instead:.

namespace
{

//////////////////////////////////////////////////////////////////////////
// Surface texture LRU cache
//////////////////////////////////////////////////////////////////////////

struct SurfaceTextureCacheGetterKey
{
	SurfaceTextureCacheGetterKey()
		: shaderNetwork( nullptr ), resolution( Imath::V2i( 512 ) )
	{
	}

	SurfaceTextureCacheGetterKey( const IECoreScene::ShaderNetwork::Parameter &out, const IECoreScene::ShaderNetwork *shaderNetwork, const Imath::V2i &resolution )
		:	output( out ), shaderNetwork( shaderNetwork ), resolution( resolution )
	{
		shaderNetwork->hash( hash );
		hash.append( resolution.x );
		hash.append( resolution.y );
		hash.append( output.shader );
		hash.append( output.name );
	}

	operator const IECore::MurmurHash & () const
	{
		return hash;
	}

	IECoreScene::ShaderNetwork::Parameter output;
	const IECoreScene::ShaderNetwork *shaderNetwork;
	Imath::V2i resolution;
	MurmurHash hash;
};

CompoundDataPtr surfaceTextureGetter( const SurfaceTextureCacheGetterKey &key, size_t &cost, const IECore::Canceller *canceller )
{
	cost = key.resolution.x * key.resolution.y * 3 * 4; // 3 x 32bit float channels;

	if( ShaderNetworkPtr textureNetwork = VisualiserAlgo::conformToOSLNetwork( key.output, key.shaderNetwork ) )
	{
		return GafferOSL::ShadingEngineAlgo::shadeUVTexture( textureNetwork.get(), key.resolution );
	}
	return nullptr;
}

typedef IECorePreview::LRUCache<IECore::MurmurHash, CompoundDataPtr, IECorePreview::LRUCachePolicy::Parallel, SurfaceTextureCacheGetterKey> SurfaceTextureCache;
// Cache cost is in bytes
SurfaceTextureCache g_surfaceTextureCache( surfaceTextureGetter, 1024 * 1024 * 64 );

//////////////////////////////////////////////////////////////////////////
// IESVisualisation helpers
//////////////////////////////////////////////////////////////////////////

IECoreGL::RenderablePtr iesVisualisation( const std::string &filename )
{

#if AI_VERSION_ARCH_NUM < 6
	return nullptr;
#else

	// It's not entirely clear from rendered results exactly how radius
	// interacts with the profile, so we just draw the normalised distribution
	// of the profile.

	const AtString f( filename.c_str() );

	const unsigned int w = 64;
	const unsigned int h = 32;

	float maxIntensity = 0.0f;
	std::unique_ptr<float[]> iesIntensities( new float[ w * h ] );

	if( !AiLightIESLoad( f, w, h, &maxIntensity, iesIntensities.get() ) )
	{
		return nullptr;
	}

	V3fVectorDataPtr pData = new V3fVectorData;
	std::vector<V3f> &p = pData->writable();

	for( unsigned int x = 0; x < w; ++x )
	{
		for( unsigned int y = 0; y < h; ++y )
		{
			const float theta = 2.0f * M_PI * ( float(x) / w );
			const float phi = M_PI * ( float(y) / h );
			const unsigned int i = y * w + x;

			if( iesIntensities[i] > 0.0f )
			{
				p.push_back(
					iesIntensities[i] * V3f(
						sin( phi ) * cos( theta ),
						sin( phi ) * sin( theta ),
						cos( phi )
					)
				);
			}
		}
	}

	IECoreGL::PointsPrimitivePtr points = new IECoreGL::PointsPrimitive( IECoreGL::PointsPrimitive::Point );
	points->addPrimitiveVariable( "P", PrimitiveVariable( PrimitiveVariable::Interpolation::Vertex, pData ) );
	return points;

#endif
}

//////////////////////////////////////////////////////////////////////////
// ArnoldLightVisualiser implementation
//////////////////////////////////////////////////////////////////////////

class GAFFERSCENEUI_API ArnoldLightVisualiser : public GafferSceneUI::StandardLightVisualiser
{

	public :

		IE_CORE_DECLAREMEMBERPTR( ArnoldLightVisualiser )

		ArnoldLightVisualiser();
		~ArnoldLightVisualiser() override;

		Visualisations visualise( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const override;

	protected :

		IECore::DataPtr surfaceTexture( const IECoreScene::ShaderNetwork *shaderNetwork, const IECore::CompoundObject *attributes, int maxTextureResolution ) const override;

	private :

		static LightVisualiser::LightVisualiserDescription<ArnoldLightVisualiser> g_description;

};

IE_CORE_DECLAREPTR( ArnoldLightVisualiser )


IECoreGLPreview::LightVisualiser::LightVisualiserDescription<ArnoldLightVisualiser> ArnoldLightVisualiser::g_description( "ai:light", "*" );


ArnoldLightVisualiser::ArnoldLightVisualiser()
{
}

ArnoldLightVisualiser::~ArnoldLightVisualiser()
{
}

Visualisations ArnoldLightVisualiser::visualise( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const
{
	Visualisations v = StandardLightVisualiser::visualise( attributeName, shaderNetwork, attributes, state );

	if( shaderNetwork->outputShader()->getName() == "photometric_light" )
	{
		const CompoundData *shaderParameters = shaderNetwork->outputShader()->parametersData();
		if( const StringData *iesFilenameData = shaderParameters->member<StringData>( "filename" ) )
		{
			IECoreGL::RenderablePtr iesVis = iesVisualisation( iesFilenameData->readable() );
			if( iesVis )
			{
				if( ConstM44fDataPtr visOrientationData = Gaffer::Metadata::value<M44fData>( "ai:light:photometric_light", "visualiserOrientation" ) )
				{
					IECoreGL::GroupPtr group = new IECoreGL::Group();
					group->addChild( iesVis );
					group->setTransform( visOrientationData->readable() );
					iesVis = group;
				}
				v.push_back( Visualisation::createOrnament( iesVis, true ) );
			}
		}
	}

	return v;
}

IECore::DataPtr ArnoldLightVisualiser::surfaceTexture( const IECoreScene::ShaderNetwork *shaderNetwork, const IECore::CompoundObject *attributes, int maxTextureResolution ) const
{
	const ShaderNetwork::Parameter &output = shaderNetwork->getOutput();
	if( !output )
	{
		return nullptr;
	}

	const IECoreScene::Shader *outputShader = shaderNetwork->outputShader();
	const IECore::InternedString metadataTarget = outputShader->getType() + ":" + outputShader->getName();

	ConstStringDataPtr colorParamData = Gaffer::Metadata::value<StringData>( metadataTarget, "colorParameter" );
	if( !colorParamData )
	{
		return nullptr;
	}

	ShaderNetwork::Parameter colorParam( output.shader, colorParamData->readable() );
	const ShaderNetwork::Parameter &colorInput = shaderNetwork->input( colorParam );
	if( !colorInput )
	{
		return nullptr;
	}

	// skydome and quad_light may specify a resolution, so use that.
	const IntData *textureResolutionData = shaderNetwork->outputShader()->parametersData()->member<IntData>( "resolution" );
	int textureResolution = textureResolutionData ? textureResolutionData->readable() : 512;
	Imath::V2i resolution( std::min( textureResolution, maxTextureResolution ) );

	ConstStringDataPtr typeData = Gaffer::Metadata::value<StringData>( metadataTarget, "type" );
	if( typeData && typeData->readable() == "environment" )
	{
		resolution.y /= 2;
	}

	CompoundDataPtr surfaceTexture = nullptr;
	try
	{
		surfaceTexture = g_surfaceTextureCache.get( SurfaceTextureCacheGetterKey( colorInput, shaderNetwork, resolution ) );
	}
	catch( const Exception &e )
	{
		msg( Msg::Warning, "ArnoldLightVisualiser", e.what() );
		return nullptr;
	}

	return surfaceTexture;
}

}
