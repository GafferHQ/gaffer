//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "RenderControllerBinding.h"

#include "GafferScene/RenderController.h"

#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Context.h"

#include "IECorePython/RefCountedBinding.h"

using namespace boost::python;

using namespace Imath;
using namespace IECoreScenePreview;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;

namespace
{

void setScene( RenderController &r, const ScenePlug &scene )
{
	IECorePython::ScopedGILRelease gilRelease;
	r.setScene( &scene );
}

ScenePlugPtr getScene( RenderController &r )
{
	return const_cast<ScenePlug *>( r.getScene() );
}

void setContext( RenderController &r, Gaffer::Context &c )
{
	IECorePython::ScopedGILRelease gilRelease;
	r.setContext( &c );
}

ContextPtr getContext( RenderController &r )
{
	return const_cast<Context *>( r.getContext() );
}

void setVisibleSet( RenderController &r, const GafferScene::VisibleSet &visibleSet )
{
	IECorePython::ScopedGILRelease gilRelease;
	r.setVisibleSet( visibleSet );
}

void setMinimumExpansionDepth( RenderController &r, size_t depth )
{
	IECorePython::ScopedGILRelease gilRelease;
	r.setMinimumExpansionDepth( depth );
}

RenderController::ProgressCallback progressCallbackFromPython( object &callback )
{
	if( callback.is_none() )
	{
		return RenderController::ProgressCallback();
	}

	return [callback] ( Gaffer::BackgroundTask::Status status ) {
		IECorePython::ScopedGILLock gilLock;
		callback( status );
	};
}

void update( RenderController &r, object &pythonCallback )
{
	// Callback owns a Python object, so must be destroyed outside of the GIL release scope.
	RenderController::ProgressCallback callback = progressCallbackFromPython( pythonCallback );
	{
		IECorePython::ScopedGILRelease gilRelease;
		r.update( callback );
	}
}

std::shared_ptr<Gaffer::BackgroundTask> updateInBackground( RenderController &r, object &pythonCallback, const IECore::PathMatcher &priorityPaths )
{
	RenderController::ProgressCallback callback = progressCallbackFromPython( pythonCallback );
	{
		IECorePython::ScopedGILRelease gilRelease;
		return r.updateInBackground( callback, priorityPaths );
	}
}

void updateMatchingPaths( RenderController &r, const IECore::PathMatcher &pathsToUpdate, object &pythonCallback )
{
	RenderController::ProgressCallback callback = progressCallbackFromPython( pythonCallback );
	{
		IECorePython::ScopedGILRelease gilRelease;
		r.updateMatchingPaths( pathsToUpdate, callback );
	}
}

object pathForID( RenderController &r, uint32_t id )
{
	if( auto path = r.pathForID( id ) )
	{
		return object( ScenePlug::pathToString( *path ) );
	}
	return object();
}

IECore::UIntVectorDataPtr idsForPaths( RenderController &r, const IECore::PathMatcher &paths, bool createIfNecessary )
{
	return new IECore::UIntVectorData( r.idsForPaths( paths, createIfNecessary ) );
}

} // namespace

void GafferSceneModule::bindRenderController()
{

	scope s = class_<RenderController, boost::noncopyable>( "RenderController", no_init )
		.def( init<ConstScenePlugPtr, ConstContextPtr, RendererPtr>() )
		.def( "renderer", &RenderController::renderer, return_value_policy<IECorePython::CastToIntrusivePtr>() )
		.def( "setScene", &setScene )
		.def( "getScene", &getScene )
		.def( "setContext", &setContext )
		.def( "getContext", &getContext )
		.def( "setVisibleSet", &setVisibleSet )
		.def( "getVisibleSet", &RenderController::getVisibleSet, return_value_policy<copy_const_reference>() )
		.def( "setMinimumExpansionDepth", &setMinimumExpansionDepth )
		.def( "getMinimumExpansionDepth", &RenderController::getMinimumExpansionDepth )
		.def( "updateRequiredSignal", &RenderController::updateRequiredSignal, return_internal_reference<1>() )
		.def( "updateRequired", &RenderController::updateRequired )
		.def( "update", &update, ( arg( "callback" ) = object() ) )
		.def( "updateMatchingPaths", &updateMatchingPaths, ( arg( "pathsToUpdate" ), arg( "callback" ) = object() ) )
		.def( "updateInBackground", &updateInBackground, ( arg( "callback" ) = object(), arg( "priorityPaths" ) = IECore::PathMatcher() ) )
		.def( "pathForID", &pathForID )
		.def( "pathsForIDs", &RenderController::pathsForIDs )
		.def( "idForPath", &RenderController::idForPath, ( arg( "path" ), arg( "createIfNecessary" ) = false ) )
		.def( "idsForPaths", &idsForPaths, ( arg( "paths" ), arg( "createIfNecessary" ) = false ) )
	;

	SignalClass<RenderController::UpdateRequiredSignal>( "UpdateRequiredSignal" );

}
