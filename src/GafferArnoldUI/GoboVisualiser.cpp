//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine. All rights reserved.
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

#include "GafferOSL/ShadingEngineAlgo.h"

#include "GafferSceneUI/StandardLightVisualiser.h"

#include "GafferScene/Private/IECoreGLPreview/LightFilterVisualiser.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECoreGL/Group.h"
#include "IECoreGL/Primitive.h"
#include "IECoreGL/QuadPrimitive.h"
#include "IECoreGL/Renderable.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/ShaderStateComponent.h"
#include "IECoreGL/TextureLoader.h"

#include "IECoreScene/Shader.h"

#include "IECore/VectorTypedData.h"

#include "boost/format.hpp"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreGL;
using namespace IECoreGLPreview;
using namespace GafferSceneUI;

namespace
{

/// \todo We have similar methods in several places. Can we consolidate them all somewhere? Perhaps a new
/// method of CompoundData?
template<typename T>
T parameterOrDefault( const IECore::CompoundData *parameters, const IECore::InternedString &name, const T &defaultValue )
{
	typedef IECore::TypedData<T> DataType;
	if( const DataType *d = parameters->member<DataType>( name ) )
	{
		return d->readable();
	}
	else
	{
		return defaultValue;
	}
}

struct OSLTextureCacheGetterKey
{

	OSLTextureCacheGetterKey()
		:	shaderNetwork( nullptr ), resolution( 512 )
	{
	}

	OSLTextureCacheGetterKey( const IECoreScene::ShaderNetwork::Parameter &out, const IECoreScene::ShaderNetwork *shaderNetwork, int resolution )
		:	output( out ), shaderNetwork( shaderNetwork ), resolution( resolution )
	{
		shaderNetwork->hash( hash );
		hash.append( resolution );
		hash.append( output.shader );
		hash.append( output.name );
	}

	operator const IECore::MurmurHash & () const
	{
		return hash;
	}

	IECoreScene::ShaderNetwork::Parameter output;
	const IECoreScene::ShaderNetwork *shaderNetwork;
	int resolution;
	MurmurHash hash;

};

CompoundDataPtr getter( const OSLTextureCacheGetterKey &key, size_t &cost )
{
	// make the cost be image data in bytes
	cost = key.resolution * key.resolution * 3 * 4;
	return GafferOSL::ShadingEngineAlgo::shadeUVTexture( key.shaderNetwork, V2i( key.resolution ), key.output );
}

typedef IECorePreview::LRUCache<IECore::MurmurHash, CompoundDataPtr, IECorePreview::LRUCachePolicy::Parallel, OSLTextureCacheGetterKey> OSLTextureCache;
OSLTextureCache g_oslTextureCache( getter, 1024 * 1024 * 64 );

const char *goboFragSource()
{
	return
		"#if __VERSION__ <= 120\n"
		"#define in varying\n"
		"#endif\n"
		""
		"#include \"IECoreGL/ColorAlgo.h\"\n"
		""
		"in vec2 fragmentuv;"
		""
		"uniform sampler2D texture;"
		""
		"void main()"
		"{"
			"vec4 t = texture2D( texture, fragmentuv );"
			"gl_FragColor =  vec4( ieLinToSRGB( t.xyz ), t.w );"
		"}"
	;
}

class GoboVisualiser final : public LightFilterVisualiser
{

	public :

		IE_CORE_DECLAREMEMBERPTR( GoboVisualiser )

		GoboVisualiser();
		~GoboVisualiser() override;

		Visualisations visualise( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, const IECoreScene::ShaderNetwork *lightShaderNetwork, const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const override;

	protected :

		static LightFilterVisualiser::LightFilterVisualiserDescription<GoboVisualiser> g_visualiserDescription;

};

IE_CORE_DECLAREPTR( GoboVisualiser )

// register the new visualiser
LightFilterVisualiser::LightFilterVisualiserDescription<GoboVisualiser> GoboVisualiser::g_visualiserDescription( "ai:lightFilter", "gobo" );

GoboVisualiser::GoboVisualiser()
{
}

GoboVisualiser::~GoboVisualiser()
{
}

Visualisations GoboVisualiser::visualise( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, const IECoreScene::ShaderNetwork *lightShaderNetwork, const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const
{
	IECoreGL::GroupPtr result = new IECoreGL::Group();

	const ShaderNetwork::Parameter slideMapInput = shaderNetwork->input( ShaderNetwork::Parameter( shaderNetwork->getOutput().shader, "slidemap" ) );

	CompoundDataPtr imageData = new CompoundData;
	if( slideMapInput )
	{
		const IntData *maxTextureResolutionData = attributes->member<IntData>( "gl:visualiser:maxTextureResolution" );
		const int resolution = maxTextureResolutionData ? maxTextureResolutionData->readable() : 512;

		try
		{
			imageData = g_oslTextureCache.get( OSLTextureCacheGetterKey( slideMapInput, shaderNetwork, resolution ) );
		}
		catch( const Exception &e )
		{
			// The osl evaluation system didn't work, but we just want to paint a
			// white gobo in these cases instead of failing completely.
			msg( Msg::Warning, "GoboVisualiser", e.what() );
		}
	}

	const CompoundData *filterParameters = shaderNetwork->outputShader()->parametersData();

	if( imageData->readable().empty() )
	{
		const Color3f goboColor = parameterOrDefault( filterParameters, "slidemap", Color3f( 1 ) );

		Box2iDataPtr singlePixelWindow = new Box2iData( { V2i( 0.0f ), V2i( 0.0f ) } );
		imageData->writable()["dataWindow"] = singlePixelWindow;
		imageData->writable()["displayWindow"] = singlePixelWindow;

		CompoundDataPtr channels = new CompoundData;
		channels->writable()["R"] = new FloatVectorData( { goboColor[0] } );
		channels->writable()["G"] = new FloatVectorData( { goboColor[1] } );
		channels->writable()["B"] = new FloatVectorData( { goboColor[2] } );
		imageData->writable()["channels"] = channels;
	}

	result->getState()->add( new IECoreGL::Primitive::Selectable( false ) );

	IECore::CompoundObjectPtr shaderParameters = new CompoundObject;
	shaderParameters->members()["texture"] = imageData;

	result->getState()->add(
		new IECoreGL::ShaderStateComponent(
			ShaderLoader::defaultShaderLoader(),
			TextureLoader::defaultTextureLoader(),
			"",
			"",
			goboFragSource(),
			shaderParameters
		)
	);

	float innerAngle;
	float coneAngle;
	float radius;
	float lensRadius;

	StandardLightVisualiser::spotlightParameters( "ai:light", lightShaderNetwork, innerAngle, coneAngle, radius, lensRadius );

	float halfPi = 0.5 * M_PI;

	const float halfAngle = halfPi * coneAngle / 180.0;
	const float baseRadius = sin( halfAngle ) + lensRadius;
	const float baseDistance = cos( halfAngle );

	float rotate = parameterOrDefault( filterParameters, "rotate", 0.0f );
	float scaleS = parameterOrDefault( filterParameters, "scale_s", 1.0f );
	float scaleT = parameterOrDefault( filterParameters, "scale_t", 1.0f );
	V2f offset = parameterOrDefault( filterParameters, "offset", V2f( 0.0f ) );

	Imath::M44f goboTrans;

	goboTrans.translate( V3f( 0.0f, 0.0f, -baseDistance ) );
	goboTrans.rotate( V3f( 0, 0, M_PI * rotate / 180.0 ) );
	goboTrans.scale( V3f( 2 * baseRadius / scaleS, 2 * baseRadius / scaleT, 0 ) );
	goboTrans.translate( V3f( offset.x, offset.y, 0.0f ) );

	result->setTransform( goboTrans );

	result->addChild( new IECoreGL::QuadPrimitive( 1.0f, 1.0f ) );

	return { Visualisation::createOrnament( result, true ) };
}

} // namespace
