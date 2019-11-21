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

#include "GafferOSL/ShadingEngine.h"

#include "GafferSceneUI/LightFilterVisualiser.h"
#include "GafferSceneUI/StandardLightVisualiser.h"

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

CompoundDataPtr evalOSLTexture( const IECoreScene::ShaderNetwork *shaderNetwork, int resolution );

struct OSLTextureCacheGetterKey
{

	OSLTextureCacheGetterKey()
		:	shaderNetwork( nullptr ), resolution( 512 )
	{
	}

	OSLTextureCacheGetterKey( IECoreScene::ShaderNetwork *shaderNetwork, int resolution )
		:	shaderNetwork( shaderNetwork ), resolution( resolution )
	{
		shaderNetwork->hash( hash );
		hash.append( resolution );
	}

	operator const IECore::MurmurHash & () const
	{
		return hash;
	}

	IECoreScene::ShaderNetwork *shaderNetwork;
	int resolution;
	MurmurHash hash;

};

CompoundDataPtr getter( const OSLTextureCacheGetterKey &key, size_t &cost )
{
	cost = 1;
	return evalOSLTexture( key.shaderNetwork, key.resolution );
}

typedef IECorePreview::LRUCache<IECore::MurmurHash, CompoundDataPtr, IECorePreview::LRUCachePolicy::Parallel, OSLTextureCacheGetterKey> OSLTextureCache;
OSLTextureCache g_oslTextureCache( getter, 100 );

const char *goboFragSource()
{
	return
		"#if __VERSION__ <= 120\n"
		"#define in varying\n"
		"#endif\n"
		""
		"in vec2 fragmentuv;"
		""
		"uniform sampler2D texture;"
		""
		"void main()"
		"{"
			"gl_FragColor = texture2D( texture, fragmentuv );"
		"}"
	;
}

// OSLTextureEvaluation

CompoundDataPtr evalOSLTexture( const IECoreScene::ShaderNetwork *shaderNetwork, int resolution )
{
	GafferOSL::ShadingEnginePtr shadingEngine = new GafferOSL::ShadingEngine( shaderNetwork );

	CompoundDataPtr shadingPoints = new CompoundData();

	V3fVectorDataPtr pData = new V3fVectorData;
	FloatVectorDataPtr uData = new FloatVectorData;
	FloatVectorDataPtr vData = new FloatVectorData;

	vector<V3f> &pWritable = pData->writable();
	vector<float> &uWritable = uData->writable();
	vector<float> &vWritable = vData->writable();

	int numPoints = resolution * resolution;

	pWritable.reserve( numPoints );
	uWritable.reserve( numPoints );
	vWritable.reserve( numPoints );

	for( int y = 0; y < resolution; ++y )
	{
		for( int x = 0; x < resolution; ++x )
		{
			uWritable.push_back( (float)(x + 0.5f) / resolution );
			// V is flipped because we're generating a Cortex image,
			// and Cortex has the pixel origin at the top left.
			vWritable.push_back( 1.0f - ( (y + 0.5f) / resolution ) );
			pWritable.push_back( V3f( x + 0.5f, y + 0.5f, 0.0f ) );
		}
	}

	shadingPoints->writable()["P"] = pData;
	shadingPoints->writable()["u"] = uData;
	shadingPoints->writable()["v"] = vData;

	CompoundDataPtr shadingResult = shadingEngine->shade( shadingPoints.get() );
	ConstColor3fVectorDataPtr colors = shadingResult->member<Color3fVectorData>( "Ci" );

	CompoundDataPtr result = new CompoundData();

	if( colors )
	{
		Imath::Box2i dataWindow( Imath::V2i( 0.0f ), Imath::V2i( resolution - 1 ) );
		Imath::Box2i displayWindow( Imath::V2i( 0.0f ), Imath::V2i( resolution - 1 ) );

		result->writable()["dataWindow"] = new Box2iData( dataWindow );
		result->writable()["displayWindow"] = new Box2iData( displayWindow );

		FloatVectorDataPtr redChannelData = new FloatVectorData();
		FloatVectorDataPtr greenChannelData = new FloatVectorData();
		FloatVectorDataPtr blueChannelData = new FloatVectorData();
		std::vector<float> &r = redChannelData->writable();
		std::vector<float> &g = greenChannelData->writable();
		std::vector<float> &b = blueChannelData->writable();

		vector<Color3f>::size_type numColors = colors->readable().size();
		r.reserve( numColors );
		g.reserve( numColors );
		b.reserve( numColors );

		for( vector<Color3f>::size_type u = 0; u < numColors; ++u )
		{
			Color3f c = colors->readable()[u];

			r.push_back( c[0] );
			g.push_back( c[1] );
			b.push_back( c[2] );
		}

		CompoundDataPtr channelData = new CompoundData;
		channelData->writable()["R"] = redChannelData;
		channelData->writable()["G"] = greenChannelData;
		channelData->writable()["B"] = blueChannelData;

		result->writable()["channels"] = channelData;
	}

	return result;
}

class GoboVisualiser final : public LightFilterVisualiser
{

	public :

		IE_CORE_DECLAREMEMBERPTR( GoboVisualiser )

		GoboVisualiser();
		~GoboVisualiser() override;

		IECoreGL::ConstRenderablePtr visualise( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, const IECoreScene::ShaderNetwork *lightShaderNetwork, const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const override;

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

IECoreGL::ConstRenderablePtr GoboVisualiser::visualise( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, const IECoreScene::ShaderNetwork *lightShaderNetwork, const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const
{
	IECoreGL::GroupPtr result = new IECoreGL::Group();

	const ShaderNetwork::Parameter slideMapInput = shaderNetwork->input( ShaderNetwork::Parameter( shaderNetwork->getOutput().shader, "slidemap" ) );

	CompoundDataPtr imageData = new CompoundData;
	if( slideMapInput )
	{
		IECoreScene::ShaderNetworkPtr surfaceNetwork = shaderNetwork->copy();
		IECore::InternedString surface = surfaceNetwork->addShader( "surface", new IECoreScene::Shader( "Surface/Constant", "osl:shader" ) );
		surfaceNetwork->addConnection( { slideMapInput, { surface, "Cs" } } );
		surfaceNetwork->setOutput( { surface, "" } );

		const IntData *maxTextureResolutionData = attributes->member<IntData>( "gl:visualiser:maxTextureResolution" );
		const int resolution = maxTextureResolutionData ? maxTextureResolutionData->readable() : 512;

		try
		{
			imageData = g_oslTextureCache.get( OSLTextureCacheGetterKey( surfaceNetwork.get(), resolution ) );
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
	float lensRadius;

	StandardLightVisualiser::spotlightParameters( "ai:light", lightShaderNetwork, innerAngle, coneAngle, lensRadius );

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

	return result;
}

} // namespace
