//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#include "boost/filesystem.hpp"
#include "boost/algorithm/string/predicate.hpp"

#include "IECore/PreWorldRenderable.h"
#include "IECore/Camera.h"
#include "IECore/WorldBlock.h"
#include "IECore/Light.h"
#include "IECore/Shader.h"
#include "IECore/AttributeBlock.h"
#include "IECore/Display.h"
#include "IECore/TransformBlock.h"
#include "IECore/CoordinateSystem.h"
#include "IECore/ClippingPlane.h"
#include "IECore/VisibleRenderable.h"
#include "IECore/Primitive.h"
#include "IECore/MotionBlock.h"

#include "Gaffer/Context.h"
#include "Gaffer/Metadata.h"

#include "GafferScene/RendererAlgo.h"
#include "GafferScene/SceneProcedural.h"
#include "GafferScene/PathMatcherData.h"
#include "GafferScene/SceneAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

void motionTimes( size_t segments, const V2f &shutter, std::set<float> &times )
{
	for( size_t i = 0; i<segments + 1; ++i )
	{
		times.insert( lerp( shutter[0], shutter[1], (float)i / (float)segments ) );
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// RendererAlgo implementation
//////////////////////////////////////////////////////////////////////////

namespace GafferScene
{

namespace RendererAlgo
{

void outputScene( const ScenePlug *scene, IECore::Renderer *renderer )
{
	ConstCompoundObjectPtr globals = scene->globalsPlug()->getValue();
	outputOptions( globals.get(), renderer );
	outputOutputs( globals.get(), renderer );
	outputCamera( scene, globals.get(), renderer );
	{
		WorldBlock world( renderer );

		outputGlobalAttributes( globals.get(), renderer );
		outputCoordinateSystems( scene, globals.get(), renderer );
		outputLights( scene, globals.get(), renderer );

		SceneProceduralPtr proc = new SceneProcedural( scene, Context::current() );
		renderer->procedural( proc );
	}
}

void outputOutputs( const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	CompoundObject::ObjectMap::const_iterator it, eIt;
	for( it = globals->members().begin(), eIt = globals->members().end(); it != eIt; it++ )
	{
		if( !boost::starts_with( it->first.c_str(), "output:" ) )
		{
			continue;
		}
		if( const Display *d = runTimeCast<Display>( it->second.get() ) )
		{
			d->render( renderer );
		}
		else
		{
			throw IECore::Exception( "Global \"" + it->first.string() + "\" is not an IECore::Display" );
		}
	}
}

void outputOptions( const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	CompoundObject::ObjectMap::const_iterator it, eIt;
	for( it = globals->members().begin(), eIt = globals->members().end(); it != eIt; it++ )
	{
		if( !boost::starts_with( it->first.c_str(), "option:" ) )
		{
			continue;
		}
		if( const Data *d = runTimeCast<Data>( it->second.get() ) )
		{
			renderer->setOption( it->first.c_str() + 7, d );
		}
		else if( const PreWorldRenderable *r = runTimeCast<PreWorldRenderable>( it->second.get() ) )
		{
			r->render( renderer );
		}
		else
		{
			throw IECore::Exception( "Global \"" + it->first.string() + "\" is not IECore::Data or an IECore::PreWorldRenderable" );
		}
	}
}

void outputCameras( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	ConstPathMatcherDataPtr cameraSetData =  scene->set( "__cameras" );
	const PathMatcher &cameraSet = cameraSetData->readable();

	// Output all the cameras, skipping the primary one - we need to output this
	// last, as that's how cortex determines the primary camera.
	ScenePlug::ScenePath primaryCameraPath;
	if( const StringData *primaryCameraPathData = globals->member<StringData>( "option:render:camera" ) )
	{
		ScenePlug::stringToPath( primaryCameraPathData->readable(), primaryCameraPath );
	}

	for( PathMatcher::Iterator it = cameraSet.begin(), eIt = cameraSet.end(); it != eIt; ++it )
	{
		if( *it != primaryCameraPath )
		{
			outputCamera( scene, *it, globals, renderer );
		}
	}

	// Output the primary camera, or a default if it doesn't exist.

	outputCamera( scene, globals, renderer );

}

void outputCamera( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	IECore::CameraPtr camera = SceneAlgo::camera( scene, globals );
	camera->render( renderer );
}

void outputCamera( const ScenePlug *scene, const ScenePlug::ScenePath &cameraPath, const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	IECore::CameraPtr camera = SceneAlgo::camera( scene, cameraPath, globals );
	camera->render( renderer );
}

void outputGlobalAttributes( const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	CompoundObject::ObjectMap::const_iterator it, eIt;
	for( it = globals->members().begin(), eIt = globals->members().end(); it != eIt; it++ )
	{
		if( !boost::starts_with( it->first.c_str(), "attribute:" ) )
		{
			continue;
		}
		if( const Data *d = runTimeCast<Data>( it->second.get() ) )
		{
			renderer->setAttribute( it->first.c_str() + 10, d );
		}
		else
		{
			throw IECore::Exception( "Global \"" + it->first.string() + "\" is not IECore::Data" );
		}
	}
}

void outputLights( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	ConstPathMatcherDataPtr lightSetData = scene->set( "__lights" );
	const PathMatcher &lightSet = lightSetData->readable();

	for( PathMatcher::Iterator it = lightSet.begin(), eIt = lightSet.end(); it != eIt; ++it )
	{
		outputLight( scene, *it, renderer );
	}
}

bool outputLight( const ScenePlug *scene, const ScenePlug::ScenePath &path, IECore::Renderer *renderer )
{
	if( !SceneAlgo::visible( scene, path ) )
	{
		/// \todo Since both visible() and fullAttributes() perform similar work,
		/// we may want to combine them into one query if we see this function
		/// being a significant fraction of render time. Maybe something like
		/// `fullAttributes( returnNullIfInvisible = true )`? It probably also
		/// makes sense to migrate all the convenience functions from ScenePlug
		/// into SceneAlgo.
		return false;
	}

	ConstCompoundObjectPtr attributes = scene->fullAttributes( path );
	ConstObjectPtr object = scene->object( path );
	const M44f transform = scene->fullTransform( path );

	std::string lightHandle;
	ScenePlug::pathToString( path, lightHandle );

	{
		AttributeBlock attributeBlock( renderer );

		renderer->setAttribute( "name", new StringData( lightHandle ) );
		outputAttributes( attributes.get(), renderer );
		renderer->concatTransform( transform );


		/// \todo Outputting a light object is now optional
		/// We are currently setting up lights like shaders, as attributes instead of objects
		/// Support for light objects is just for backwards compatibility with old light rig sccs,
		/// and can be removed in the future.
		IECore::ConstLightPtr lightObject = runTimeCast<const IECore::Light>( scene->object( path ) );
		if( lightObject )
		{
			LightPtr light = lightObject->copy();
			light->setHandle( lightHandle );
			light->render( renderer );
		}


		for( IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().begin();
			it != attributes->members().end(); it++ )
		{
			if( boost::ends_with( it->first.string(), ":light"  ) || it->first.string() == "light" )
			{
				const IECore::ObjectVector *lightShaders = runTimeCast<const IECore::ObjectVector>( it->second.get() );
				if( !lightShaders || lightShaders->members().empty() )
				{
					continue;
				}

				LightPtr light;
				if( const Light *constLight = runTimeCast<const Light >( lightShaders->members().back().get() ) )
				{
					light = constLight->copy();
				}
				else if( const Shader *constShader = runTimeCast<const Shader >( lightShaders->members().back().get() ) )
				{
					// In the past Gaffer used IECore::Light to represent lights, but has moved
					// to simply using IECore::Shader now that lights are just shaders assigned
					// to a location. The new renderer backends implemented in IECoreScene::Preview
					// make no use of IECore::Light at all, but here in the legacy backend it's
					// still easier to convert the shader back to the old IECore::Light form rather
					// than rewrite the output code.
					light = new Light( constShader->getName(), "", constShader->parameters() );
				}

				if( !light )
				{
					continue;
				}

				bool areaLight = false;
				const BoolData *areaLightParm = light->parametersData()->member<BoolData>( "__areaLight" );
				if( areaLightParm )
				{
					areaLight = areaLightParm->readable();
				}

				/// If this is a non-areaLight which could have orientation metadata,
				/// add an extra attribute block to contain it
				AttributeBlock attributeBlock( renderer, !areaLight );

				if( !areaLight )
				{
					InternedString metadataTarget = "light:" + light->getName();
					ConstM44fDataPtr orientation = Metadata::value<M44fData>( metadataTarget, "renderOrientation" );

					if( orientation )
					{
						renderer->concatTransform( orientation->readable() );
					}
				}

				for( unsigned int i = 0; i < lightShaders->members().size() - 1; i++ )
				{
					IECore::ConstStateRenderablePtr shader = runTimeCast< const IECore::StateRenderable >( lightShaders->members()[i] );
					if( shader )
					{
						shader->render( renderer );
					}
				}

				light->setHandle( lightHandle );

				light->render( renderer );
			}
		}

		if( const VisibleRenderable* renderable = runTimeCast< const VisibleRenderable >( object.get() ) )
		{
			renderable->render( renderer );
		}
	}


	renderer->illuminate( lightHandle, true );

	return true;
}

void outputCoordinateSystems( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	ConstPathMatcherDataPtr coordinateSystemSetData = scene->set( "__coordinateSystems" );
	const PathMatcher &coordinateSystemSet = coordinateSystemSetData->readable();

	for( PathMatcher::Iterator it = coordinateSystemSet.begin(), eIt = coordinateSystemSet.end(); it != eIt; ++it )
	{
		outputCoordinateSystem( scene, *it, renderer );
	}
}

bool outputCoordinateSystem( const ScenePlug *scene, const ScenePlug::ScenePath &path, IECore::Renderer *renderer )
{
	IECore::ConstCoordinateSystemPtr constCoordinateSystem = runTimeCast<const IECore::CoordinateSystem>( scene->object( path ) );
	if( !constCoordinateSystem )
	{
		return false;
	}

	if( !SceneAlgo::visible( scene, path ) )
	{
		return false;
	}

	const M44f transform = scene->fullTransform( path );

	std::string coordinateSystemName;
	ScenePlug::pathToString( path, coordinateSystemName );

	CoordinateSystemPtr coordinateSystem = constCoordinateSystem->copy();
	coordinateSystem->setName( coordinateSystemName );

	{
		TransformBlock transformBlock( renderer );
		renderer->concatTransform( transform );
		coordinateSystem->render( renderer );
	}

	return true;
}

void outputClippingPlanes( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	ConstPathMatcherDataPtr clippingPlanesSetData = scene->set( "__clippingPlanes" );
	const PathMatcher &clippingPlanesSet = clippingPlanesSetData->readable();

	for( PathMatcher::Iterator it = clippingPlanesSet.begin(), eIt = clippingPlanesSet.end(); it != eIt; ++it )
	{
		outputClippingPlane( scene, *it, renderer );
	}
}

bool outputClippingPlane( const ScenePlug *scene, const ScenePlug::ScenePath &path, IECore::Renderer *renderer )
{
	IECore::ConstClippingPlanePtr clippingPlane = runTimeCast<const IECore::ClippingPlane>( scene->object( path ) );
	if( !clippingPlane )
	{
		return false;
	}

	if( !SceneAlgo::visible( scene, path ) )
	{
		return false;
	}

	const M44f transform = scene->fullTransform( path );

	TransformBlock transformBlock( renderer );
	renderer->concatTransform( transform );
	clippingPlane->render( renderer );

	return true;
}

void createDisplayDirectories( const IECore::CompoundObject *globals )
{
	CompoundObject::ObjectMap::const_iterator it, eIt;
	for( it = globals->members().begin(), eIt = globals->members().end(); it != eIt; it++ )
	{
		if( const Display *d = runTimeCast<Display>( it->second.get() ) )
		{
			boost::filesystem::path fileName( d->getName() );
			boost::filesystem::path directory = fileName.parent_path();
			if( !directory.empty() )
			{
				boost::filesystem::create_directories( directory );
			}
		}
	}
}

void outputAttributes( const IECore::CompoundObject *attributes, IECore::Renderer *renderer )
{
	// Output attributes before other state
	// This covers a special case in 3delight:  when reading attributes in the construct() of a shader, they will only be visible
	// if they are declared before the shader
	for( CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; it++ )
	{
		if( const Data *d = runTimeCast<const Data>( it->second.get() ) )
		{
			renderer->setAttribute( it->first, d );
		}
	}

	for( CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; it++ )
	{
		if( boost::ends_with( it->first.c_str(), ":light" ) || it->first == "light" )
		{
			// Currently lights are output in separate prepass
			continue;
		}

		if( const StateRenderable *s = runTimeCast<const StateRenderable>( it->second.get() ) )
		{
			s->render( renderer );
		}
		else if( const ObjectVector *o = runTimeCast<const ObjectVector>( it->second.get() ) )
		{
			for( ObjectVector::MemberContainer::const_iterator it = o->members().begin(), eIt = o->members().end(); it != eIt; it++ )
			{
				const StateRenderable *s = runTimeCast<const StateRenderable>( it->get() );
				if( s )
				{
					s->render( renderer );
				}
			}
		}
	}
}

void transformSamples( const ScenePlug *scene, size_t segments, const Imath::V2f &shutter, std::vector<Imath::M44f> &samples, std::set<float> &sampleTimes )
{
	// Static case

	if( !segments )
	{
		samples.push_back( scene->transformPlug()->getValue() );
		return;
	}

	// Motion case

	motionTimes( segments, shutter, sampleTimes );

	ContextPtr timeContext = new Context( *Context::current(), Context::Borrowed );
	Context::Scope scopedTimeContext( timeContext.get() );

	bool moving = false;
	samples.reserve( sampleTimes.size() );
	for( std::set<float>::const_iterator it = sampleTimes.begin(), eIt = sampleTimes.end(); it != eIt; ++it )
	{
		timeContext->setFrame( *it );
		const M44f m = scene->transformPlug()->getValue();
		if( !moving && !samples.empty() && m != samples.front() )
		{
			moving = true;
		}
		samples.push_back( m );
	}

	if( !moving )
	{
		samples.resize( 1 );
		sampleTimes.clear();
	}
}

void outputTransform( const ScenePlug *scene, IECore::Renderer *renderer, size_t segments, const Imath::V2f &shutter )
{
	vector<M44f> samples;
	set<float> sampleTimes;
	transformSamples( scene, segments, shutter, samples, sampleTimes );

	MotionBlock motionBlock( renderer, sampleTimes );
	for( vector<M44f>::const_iterator it = samples.begin(), eIt = samples.end(); it != eIt; ++it )
	{
		renderer->concatTransform( *it );
	}
}

void objectSamples( const ScenePlug *scene, size_t segments, const Imath::V2f &shutter, std::vector<IECore::ConstVisibleRenderablePtr> &samples, std::set<float> &sampleTimes )
{

	// Static case

	if( !segments )
	{
		ConstObjectPtr object = scene->objectPlug()->getValue();
		if( const VisibleRenderable *renderable = runTimeCast<const VisibleRenderable>( object.get() ) )
		{
			samples.push_back( renderable );
		}
		return;
	}

	// Motion case

	motionTimes( segments, shutter, sampleTimes );

	ContextPtr timeContext = new Context( *Context::current(), Context::Borrowed );
	Context::Scope scopedTimeContext( timeContext.get() );

	bool moving = false;
	MurmurHash lastHash;
	samples.reserve( sampleTimes.size() );
	for( std::set<float>::const_iterator it = sampleTimes.begin(), eIt = sampleTimes.end(); it != eIt; ++it )
	{
		timeContext->setFrame( *it );

		const MurmurHash objectHash = scene->objectPlug()->hash();
		ConstObjectPtr object = scene->objectPlug()->getValue( &objectHash );

		if( const Primitive *primitive = runTimeCast<const Primitive>( object.get() ) )
		{
			// We can support multiple samples for these, so check to see
			// if we actually have something moving.
			if( !moving && !samples.empty() && objectHash != lastHash )
			{
				moving = true;
			}
			samples.push_back( primitive );
			lastHash = objectHash;
		}
		else if( const VisibleRenderable *renderable = runTimeCast< const VisibleRenderable >( object.get() ) )
		{
			// We can't motion blur these chappies, so just take the one
			// sample.
			samples.push_back( renderable );
			break;
		}
		else
		{
			// We don't even know what these chappies are, so
			// don't take any samples at all.
			break;
		}
	}

	if( !moving )
	{
		samples.resize( std::min<size_t>( samples.size(), 1 ) );
		sampleTimes.clear();
	}
}

void outputObject( const ScenePlug *scene, IECore::Renderer *renderer, size_t segments, const Imath::V2f &shutter )
{
	vector<ConstVisibleRenderablePtr> samples;
	set<float> sampleTimes;
	objectSamples( scene, segments, shutter, samples, sampleTimes );

	MotionBlock motionBlock( renderer, sampleTimes );
	for( vector<ConstVisibleRenderablePtr>::const_iterator it = samples.begin(), eIt = samples.end(); it != eIt; ++it )
	{
		(*it)->render( renderer );
	}
}

} // namespace RendererAlgo

} // namespace GafferScene
