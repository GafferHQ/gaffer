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
#include "IECore/AttributeBlock.h"
#include "IECore/Display.h"
#include "IECore/TransformBlock.h"
#include "IECore/CoordinateSystem.h"
#include "IECore/ClippingPlane.h"

#include "Gaffer/Context.h"

#include "GafferScene/RendererAlgo.h"
#include "GafferScene/SceneProcedural.h"
#include "GafferScene/PathMatcherData.h"
#include "GafferScene/SceneAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;

namespace GafferScene
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
		else
		{
			throw IECore::Exception( "Global \"" + it->first.string() + "\" is not IECore::Data" );
		}
	}
}

void outputCameras( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	const PathMatcherData *cameraSet = NULL;
	if( const CompoundData *sets = globals->member<CompoundData>( "gaffer:sets" ) )
	{
		cameraSet = sets->member<PathMatcherData>( "__cameras" );
	}

	if( cameraSet )
	{
		// Output all the cameras, skipping the primary one - we need to output this
		// last, as that's how cortex determines the primary camera.
		ScenePlug::ScenePath primaryCameraPath;
		if( const StringData *primaryCameraPathData = globals->member<StringData>( "option:render:camera" ) )
		{
			ScenePlug::stringToPath( primaryCameraPathData->readable(), primaryCameraPath );
		}

		vector<string> paths;
		cameraSet->readable().paths( paths );
		for( vector<string>::const_iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
		{
			ScenePlug::ScenePath path;
			ScenePlug::stringToPath( *it, path );
			if( path != primaryCameraPath )
			{
				outputCamera( scene, path, globals, renderer );
			}
		}
	}

	// output the primary camera, or a default if it doesn't exist.

	outputCamera( scene, globals, renderer );

}

void outputCamera( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	IECore::CameraPtr camera = GafferScene::camera( scene, globals );
	camera->render( renderer );
}

void outputCamera( const ScenePlug *scene, const ScenePlug::ScenePath &cameraPath, const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	IECore::CameraPtr camera = GafferScene::camera( scene, cameraPath, globals );
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
	const CompoundData *sets = globals->member<CompoundData>( "gaffer:sets" );
	if( !sets )
	{
		return;
	}

	const PathMatcherData *lightSet = sets->member<PathMatcherData>( "__lights" );
	if( !lightSet )
	{
		return;
	}

	vector<string> paths;
	lightSet->readable().paths( paths );
	for( vector<string>::const_iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
	{
		/// \todo We should be able to get paths out of the PathMatcher in
		/// the first place, rather than have to convert from strings.
		ScenePlug::ScenePath path;
		ScenePlug::stringToPath( *it, path );
		outputLight( scene, path, renderer );
	}
}

bool outputLight( const ScenePlug *scene, const ScenePlug::ScenePath &path, IECore::Renderer *renderer )
{
	IECore::ConstLightPtr constLight = runTimeCast<const IECore::Light>( scene->object( path ) );
	if( !constLight )
	{
		return false;
	}

	if( !visible( scene, path ) )
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
	const M44f transform = scene->fullTransform( path );

	std::string lightHandle;
	ScenePlug::pathToString( path, lightHandle );

	LightPtr light = constLight->copy();
	light->setHandle( lightHandle );

	{
		AttributeBlock attributeBlock( renderer );

		renderer->setAttribute( "name", new StringData( lightHandle ) );

		CompoundObject::ObjectMap::const_iterator aIt, aeIt;
		for( aIt = attributes->members().begin(), aeIt = attributes->members().end(); aIt != aeIt; aIt++ )
		{
			if( const Data *attribute = runTimeCast<const Data>( aIt->second.get() ) )
			{
				renderer->setAttribute( aIt->first.string(), attribute );
			}
		}

		renderer->concatTransform( transform );
		light->render( renderer );
	}

	renderer->illuminate( lightHandle, true );

	return true;
}

void outputCoordinateSystems( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	const CompoundData *sets = globals->member<CompoundData>( "gaffer:sets" );
	if( !sets )
	{
		return;
	}

	const PathMatcherData *coordinateSystemSet = sets->member<PathMatcherData>( "__coordinateSystems" );
	if( !coordinateSystemSet )
	{
		return;
	}

	vector<string> paths;
	coordinateSystemSet->readable().paths( paths );
	for( vector<string>::const_iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
	{
		/// \todo We should be able to get paths out of the PathMatcher in
		/// the first place, rather than have to convert from strings.
		ScenePlug::ScenePath path;
		ScenePlug::stringToPath( *it, path );
		outputCoordinateSystem( scene, path, renderer );
	}
}

bool outputCoordinateSystem( const ScenePlug *scene, const ScenePlug::ScenePath &path, IECore::Renderer *renderer )
{
	IECore::ConstCoordinateSystemPtr constCoordinateSystem = runTimeCast<const IECore::CoordinateSystem>( scene->object( path ) );
	if( !constCoordinateSystem )
	{
		return false;
	}

	if( !visible( scene, path ) )
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
	const CompoundData *sets = globals->member<CompoundData>( "gaffer:sets" );
	if( !sets )
	{
		return;
	}

	const PathMatcherData *clippingPlanesSet = sets->member<PathMatcherData>( "__clippingPlanes" );
	if( !clippingPlanesSet )
	{
		return;
	}

	vector<string> paths;
	clippingPlanesSet->readable().paths( paths );
	for( vector<string>::const_iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
	{
		/// \todo We should be able to get paths out of the PathMatcher in
		/// the first place, rather than have to convert from strings.
		ScenePlug::ScenePath path;
		ScenePlug::stringToPath( *it, path );
		outputClippingPlane( scene, path, renderer );
	}
}

bool outputClippingPlane( const ScenePlug *scene, const ScenePlug::ScenePath &path, IECore::Renderer *renderer )
{
	IECore::ConstClippingPlanePtr clippingPlane = runTimeCast<const IECore::ClippingPlane>( scene->object( path ) );
	if( !clippingPlane )
	{
		return false;
	}

	if( !visible( scene, path ) )
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

} // namespace GafferScene
