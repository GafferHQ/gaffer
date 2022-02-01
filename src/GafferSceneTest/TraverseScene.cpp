//////////////////////////////////////////////////////////////////////////
//
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

#include "GafferSceneTest/TraverseScene.h"

#include "GafferScene/SceneAlgo.h"

#include "GafferDispatch/Dispatcher.h"

#include "boost/bind.hpp"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneTest;

namespace
{

struct SceneEvaluateFunctor
{
	bool operator()( const GafferScene::ScenePlug *scene, const GafferScene::ScenePlug::ScenePath &path )
	{
		scene->transformPlug()->getValue();
		scene->boundPlug()->getValue();
		scene->attributesPlug()->getValue();
		scene->objectPlug()->getValue();
		return true;
	}
};

void traverseOnDirty( const Gaffer::Plug *dirtiedPlug, ConstScenePlugPtr scene )
{
	if( dirtiedPlug == scene.get() )
	{
		traverseScene( scene.get() );
	}
}

void traverseOnChanged( ConstScenePlugPtr scene, ConstContextPtr context )
{
	Context::Scope scopedContext( context.get() );
	traverseScene( scene.get() );
}

bool traverseOnPreDispatch( ConstScenePlugPtr scene )
{
	traverseScene( scene.get() );
	return false;
}

} // namespace

void GafferSceneTest::traverseScene( const GafferScene::ScenePlug *scenePlug )
{
	SceneEvaluateFunctor f;
	SceneAlgo::parallelTraverse( scenePlug, f );
}

void GafferSceneTest::traverseScene( GafferScene::ScenePlug *scenePlug )
{
	traverseScene( const_cast<const ScenePlug *>( scenePlug ) );
}

Signals::Connection GafferSceneTest::connectTraverseSceneToPlugDirtiedSignal( const GafferScene::ConstScenePlugPtr &scene )
{
	const Node *node = scene->node();
	if( !node )
	{
		throw IECore::Exception( "Plug does not belong to a node." );
	}

	return const_cast<Node *>( node )->plugDirtiedSignal().connect( boost::bind( &traverseOnDirty, ::_1, scene ) );
}

Signals::Connection GafferSceneTest::connectTraverseSceneToContextChangedSignal( const GafferScene::ConstScenePlugPtr &scene, const Gaffer::ContextPtr &context )
{
	return context->changedSignal().connect( boost::bind( &traverseOnChanged, scene, context ) );
}

Signals::Connection GafferSceneTest::connectTraverseSceneToPreDispatchSignal( const GafferScene::ConstScenePlugPtr &scene )
{
	return GafferDispatch::Dispatcher::preDispatchSignal().connect( boost::bind( traverseOnPreDispatch, scene ) );
}
