//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "IECorePython/ScopedGILRelease.h"

#include "GafferBindings/DependencyNodeBinding.h"

#include "GafferSceneTest/CompoundObjectSource.h"
#include "GafferSceneTest/TraverseScene.h"
#include "GafferSceneTest/TestShader.h"
#include "GafferSceneTest/TestLight.h"
#include "GafferSceneTest/ScenePlugTest.h"
#include "GafferSceneTest/PathMatcherTest.h"
#include "GafferSceneTest/SceneAlgoTest.h"

using namespace boost::python;
using namespace GafferSceneTest;

static void traverseSceneWrapper( GafferScene::ScenePlug *scenePlug, Gaffer::Context *context )
{
	IECorePython::ScopedGILRelease gilRelease;
	traverseScene( scenePlug, context );
}

void matchingPathsUsingTraverseWrapper1( const Gaffer::IntPlug *filterPlug, const GafferScene::ScenePlug *scene, GafferScene::PathMatcher &paths )
{
    // gil release in case the scene traversal dips back into python:
    IECorePython::ScopedGILRelease r;
    matchingPathsUsingTraverse( filterPlug, scene, paths );
}

void matchingPathsUsingTraverseWrapper2( const GafferScene::Filter *filter, const GafferScene::ScenePlug *scene, GafferScene::PathMatcher &paths )
{
    // gil release in case the scene traversal dips back into python:
    IECorePython::ScopedGILRelease r;
    matchingPathsUsingTraverse( filter, scene, paths );
}



BOOST_PYTHON_MODULE( _GafferSceneTest )
{

	GafferBindings::DependencyNodeClass<CompoundObjectSource>();
	GafferBindings::NodeClass<TestShader>();
	GafferBindings::NodeClass<TestLight>();

	def( "traverseScene", &traverseSceneWrapper );
	def( "testManyStringToPathCalls", &testManyStringToPathCalls );

	def( "testPathMatcherRawIterator", &testPathMatcherRawIterator );
	def( "testPathMatcherIteratorPrune", &testPathMatcherIteratorPrune );

	def( "matchingPathsUsingTraverse", &matchingPathsUsingTraverseWrapper1 );
	def( "matchingPathsUsingTraverse", &matchingPathsUsingTraverseWrapper2 );

}
