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

#include "GafferSceneTest/ContextSanitiser.h"
#include "GafferSceneTest/CompoundObjectSource.h"
#include "GafferSceneTest/ScenePlugTest.h"
#include "GafferSceneTest/TestLight.h"
#include "GafferSceneTest/TestLightFilter.h"
#include "GafferSceneTest/TestShader.h"
#include "GafferSceneTest/TraverseScene.h"

#include "GafferBindings/DependencyNodeBinding.h"

#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace GafferSceneTest;

static void traverseSceneWrapper( const GafferScene::ScenePlug *scenePlug )
{
	IECorePython::ScopedGILRelease gilRelease;
	traverseScene( scenePlug );
}

BOOST_PYTHON_MODULE( _GafferSceneTest )
{

	IECorePython::RefCountedClass<ContextSanitiser, Gaffer::Monitor>( "ContextSanitiser" )
		.def( init<>() )
	;

	GafferBindings::DependencyNodeClass<CompoundObjectSource>();
	GafferBindings::NodeClass<TestShader>();
	GafferBindings::NodeClass<TestLight>()
		.def( "loadShader", &TestLight::loadShader )
	;
	GafferBindings::NodeClass<TestLightFilter>();

	def( "traverseScene", &traverseSceneWrapper );
	def( "connectTraverseSceneToPlugDirtiedSignal", &connectTraverseSceneToPlugDirtiedSignal );
	def( "connectTraverseSceneToContextChangedSignal", &connectTraverseSceneToContextChangedSignal );
	def( "connectTraverseSceneToPreDispatchSignal", &connectTraverseSceneToPreDispatchSignal );

	def( "testManyStringToPathCalls", &testManyStringToPathCalls );

}
