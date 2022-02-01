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

#ifndef GAFFERSCENETEST_TRAVERSESCENE_H
#define GAFFERSCENETEST_TRAVERSESCENE_H

#include "GafferSceneTest/Export.h"

#include "GafferScene/ScenePlug.h"

#include "Gaffer/Context.h"

namespace GafferSceneTest
{

/// Traverses the entire scene once, evaluating every aspect of the scene, using parallel
/// threads to process different children. It's useful to use this in test cases to exercise
/// any thread related crashes, and also in profiling for performance improvement.
GAFFERSCENETEST_API void traverseScene( const GafferScene::ScenePlug *scenePlug );
/// \todo Remove.
GAFFERSCENETEST_API void traverseScene( GafferScene::ScenePlug *scenePlug );

/// Arranges for traverseScene() to be called every time the scene is dirtied. This is useful
/// for exposing bugs caused by things like InteractiveRender and SceneView, where threaded
/// traversals will be triggered automatically by plugDirtiedSignal().
GAFFERSCENETEST_API Gaffer::Signals::Connection connectTraverseSceneToPlugDirtiedSignal( const GafferScene::ConstScenePlugPtr &scene );

/// Arranges for traverseScene() to be called every time the context is changed. This is useful
/// for exposing bugs caused by things like InteractiveRender and SceneView, where threaded
/// traversals will be triggered automatically from Context::changedSignal().
GAFFERSCENETEST_API Gaffer::Signals::Connection connectTraverseSceneToContextChangedSignal( const GafferScene::ConstScenePlugPtr &scene, const Gaffer::ContextPtr &context );

/// Arranges for traverseScene() to be called when Dispatcher::preDispatchSignal() is emitted.
GAFFERSCENETEST_API Gaffer::Signals::Connection connectTraverseSceneToPreDispatchSignal( const GafferScene::ConstScenePlugPtr &scene );

} // namespace GafferSceneTest

#endif // GAFFERSCENETEST_TRAVERSESCENE_H
