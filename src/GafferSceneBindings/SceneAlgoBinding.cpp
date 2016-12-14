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

#include "boost/python.hpp"
#include "boost/python/suite/indexing/container_utils.hpp"

#include "IECore/Camera.h"

#include "IECorePython/ScopedGILRelease.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/Filter.h"
#include "GafferScene/PathMatcher.h"

#include "GafferSceneBindings/SceneAlgoBinding.h"

using namespace boost::python;
using namespace GafferScene;

namespace
{

bool existsWrapper( const ScenePlug *scene, const ScenePlug::ScenePath &path )
{
	// gil release in case the scene traversal dips back into python:
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::exists( scene, path );
}

bool visibleWrapper( const ScenePlug *scene, const ScenePlug::ScenePath &path )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::visible( scene, path );
}

void matchingPathsWrapper1( const Filter *filter, const ScenePlug *scene, PathMatcher &paths )
{
	// gil release in case the scene traversal dips back into python:
	IECorePython::ScopedGILRelease r;
	SceneAlgo::matchingPaths( filter, scene, paths );
}

void matchingPathsWrapper2( const Gaffer::IntPlug *filterPlug, const ScenePlug *scene, PathMatcher &paths )
{
	// gil release in case the scene traversal dips back into python:
	IECorePython::ScopedGILRelease r;
	SceneAlgo::matchingPaths( filterPlug, scene, paths );
}

void matchingPathsWrapper3( const PathMatcher &filter, const ScenePlug *scene, PathMatcher &paths )
{
	// gil release in case the scene traversal dips back into python:
	IECorePython::ScopedGILRelease r;
	SceneAlgo::matchingPaths( filter, scene, paths );
}

Imath::V2f shutterWrapper( const IECore::CompoundObject *globals )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::shutter( globals );
}

IECore::CameraPtr cameraWrapper1( const ScenePlug *scene, const IECore::CompoundObject *globals )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::camera( scene, globals );
}

IECore::CameraPtr cameraWrapper2( const ScenePlug *scene, const ScenePlug::ScenePath &cameraPath, const IECore::CompoundObject *globals )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::camera( scene, cameraPath, globals );
}

bool setExistsWrapper( const ScenePlug *scene, const IECore::InternedString &setName )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::setExists( scene, setName );
}

IECore::CompoundDataPtr setsWrapper1( const ScenePlug *scene, bool copy )
{
	IECorePython::ScopedGILRelease r;
	IECore::ConstCompoundDataPtr result = SceneAlgo::sets( scene );
	return copy ? result->copy() : boost::const_pointer_cast<IECore::CompoundData>( result );
}

IECore::CompoundDataPtr setsWrapper2( const ScenePlug *scene, object pythonSetNames, bool copy )
{
	std::vector<IECore::InternedString> setNames;
	boost::python::container_utils::extend_container( setNames, pythonSetNames );

	IECorePython::ScopedGILRelease r;
	IECore::ConstCompoundDataPtr result = SceneAlgo::sets( scene, setNames );
	return copy ? result->copy() : boost::const_pointer_cast<IECore::CompoundData>( result );
}

} // namespace

namespace GafferSceneBindings
{

void bindSceneAlgo()
{
	object module( borrowed( PyImport_AddModule( "GafferScene.SceneAlgo" ) ) );
	scope().attr( "SceneAlgo" ) = module;
	scope moduleScope( module );

	def( "exists", &existsWrapper );
	def( "visible", visibleWrapper );
	def( "matchingPaths", &matchingPathsWrapper1 );
	def( "matchingPaths", &matchingPathsWrapper2 );
	def( "matchingPaths", &matchingPathsWrapper3 );
	def( "shutter", &shutterWrapper );
	def(
		"camera",
		&cameraWrapper1,
		( arg( "scene" ), arg( "globals" ) = object() )
	);
	def(
		"camera",
		&cameraWrapper2,
		( arg( "scene" ), args( "cameraPath" ), arg( "globals" ) = object() )
	);
	def( "setExists", &setExistsWrapper );
	def(
		"sets",
		&setsWrapper1,
		( arg( "scene" ), arg( "_copy" ) = true )
	);
	def(
		"sets",
		&setsWrapper2,
		( arg( "scene" ), arg( "setNames" ), arg( "_copy" ) = true )
	);
}

} // namespace GafferSceneBindings
