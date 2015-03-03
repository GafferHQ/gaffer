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

#include "IECore/Camera.h"

#include "IECorePython/ScopedGILRelease.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/Filter.h"
#include "GafferScene/PathMatcher.h"

#include "GafferSceneBindings/SceneAlgoBinding.h"

using namespace boost::python;
using namespace GafferScene;

namespace GafferSceneBindings
{

static void matchingPathsHelper1( const Filter *filter, const ScenePlug *scene, PathMatcher &paths )
{
	// gil release in case the scene traversal dips back into python:
	IECorePython::ScopedGILRelease r;
	matchingPaths( filter, scene, paths );
}

static void matchingPathsHelper2( const Gaffer::IntPlug *filterPlug, const ScenePlug *scene, PathMatcher &paths )
{
	// gil release in case the scene traversal dips back into python:
	IECorePython::ScopedGILRelease r;
	matchingPaths( filterPlug, scene, paths );
}

void bindSceneAlgo()
{
	def( "exists", exists );
	def( "visible", visible );
	def( "matchingPaths", &matchingPathsHelper1 );
	def( "matchingPaths", &matchingPathsHelper2 );
	def( "shutter", &shutter );
	def(
		"camera",
		(IECore::CameraPtr (*)( const ScenePlug *, const IECore::CompoundObject * ) )&camera,
		( arg( "scene" ), arg( "globals" ) = object() )
	);
	def(
		"camera",
		(IECore::CameraPtr (*)( const ScenePlug *, const ScenePlug::ScenePath &, const IECore::CompoundObject * ) )&camera,
		( arg( "scene" ), args( "cameraPath" ), arg( "globals" ) = object() )
	);
}

} // namespace GafferSceneBindings
