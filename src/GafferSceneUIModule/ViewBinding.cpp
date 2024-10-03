//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2013, John Haddon. All rights reserved.
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "ViewBinding.h"

#include "GafferSceneUI/SceneView.h"
#include "GafferSceneUI/ShaderView.h"
#include "GafferSceneUI/UVView.h"

#include "GafferScene/SceneProcessor.h"

#include "GafferBindings/NodeBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Reference.h"
#include "Gaffer/ScriptNode.h"

#include "IECorePython/ExceptionAlgo.h"

#include <string>
#include <filesystem>

using namespace std;
using namespace boost::python;
using namespace IECore;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// SceneView binding utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

struct ShadingModeCreator
{

	ShadingModeCreator( object fn )
		:	m_fn( fn )
	{
	}

	SceneProcessorPtr operator()()
	{
		IECorePython::ScopedGILLock gilLock;
		SceneProcessorPtr result = extract<SceneProcessorPtr>( m_fn() );
		return result;
	}

	private :

		object m_fn;

};

void registerShadingMode( const std::string &name, object creator )
{
	SceneView::registerShadingMode( name, ShadingModeCreator( creator ) );
}

boost::python::list registeredShadingModes()
{
	vector<string> n;
	SceneView::registeredShadingModes( n );
	boost::python::list result;
	for( vector<string>::const_iterator it = n.begin(), eIt = n.end(); it != eIt; ++it )
	{
		result.append( *it );
	}

	return result;
}

void sceneViewRegisterRenderer( const std::string &name, object settingsCreator )
{
	SceneView::registerRenderer(
		name,
		// Deliberately "leaking" `settingsCreator` because this lambda will be
		// stored in a static map which will be destroyed _after_ Python is shutdown,
		// at which point deleting a PyObject will crash.
		[settingsCreator = new object( settingsCreator )] {
			IECorePython::ScopedGILLock gilLock;
			SceneProcessorPtr result = extract<SceneProcessorPtr>( (*settingsCreator)() );
			return result;
		}
	);
}

boost::python::list sceneViewRegisteredRenderers()
{
	boost::python::list result;
	for( auto &r : SceneView::registeredRenderers() )
	{
		result.append( r );
	}
	return result;
}

void frame( SceneView &view, PathMatcher &filter, Imath::V3f &direction )
{
	IECorePython::ScopedGILRelease gilRelease;
	view.frame( filter, direction );
}

void expandSelection( SceneView &view, size_t depth )
{
	IECorePython::ScopedGILRelease gilRelease;
	view.expandSelection( depth );
}

void collapseSelection( SceneView &view )
{
	IECorePython::ScopedGILRelease gilRelease;
	view.collapseSelection();
}

Imath::Box2f resolutionGateWrapper( SceneView &view )
{
	IECorePython::ScopedGILRelease gilRelease;
	return view.resolutionGate();
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ShaderView binding utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

template<typename T>
struct CreatorWrapper
{

	CreatorWrapper( object fn )
		:	m_fn( fn )
	{
	}

	typename T::Ptr operator()()
	{
		ScopedGILLock gilLock;
		typename T::Ptr result = extract<typename T::Ptr>( m_fn() );
		return result;
	}

	private :

		object m_fn;

};

// Utility class for loading custom shader scenes from
// reference files. Ideally we would be doing this directly
// in ShaderView.cpp, but we can't because we can only do
// serialisation/loading with python, and libGaffer.so does
// not have a python dependency. Ideally I think we'd make
// it so that Serialiser was in libGaffer.so, but stubbed out,
// and when libGafferBindings.so was loaded it would insert the
// implementation. This would allow `Reference::load()` to use
// the Serialiser directly, making it independent of ScriptNode
// (it needs ScriptNode because this is currently the only access
// to serialisation in libGaffer.so).
struct ReferenceCreator
{

	ReferenceCreator( const std::filesystem::path &referenceFileName )
		:	m_referenceFileName( referenceFileName )
	{
	}

	NodePtr operator()()
	{
		ScopedGILLock gilLock;
		object gafferModule = import( "Gaffer" );
		ScriptNodePtr script = extract<ScriptNodePtr>( gafferModule.attr( "ScriptNode" )() );

		ReferencePtr reference = new Reference;
		script->addChild( reference );

		reference->load( m_referenceFileName );

		return reference;
	}

	private :

		std::filesystem::path m_referenceFileName;

};

void registerRenderer( const std::string &shaderPrefix, object creator )
{
	ShaderView::registerRenderer( shaderPrefix, CreatorWrapper<InteractiveRender>( creator ) );
}

void deregisterRenderer( const std::string &shaderPrefix)
{
	ShaderView::deregisterRenderer( shaderPrefix );
}

void registerScene( const std::string &shaderPrefix, const std::string &name, object creator )
{
	ShaderView::registerScene( shaderPrefix, name, CreatorWrapper<Node>( creator ) );
}

void registerReferenceScene( const std::string &shaderPrefix, const std::string &name, const std::filesystem::path &referenceFileName )
{
	ShaderView::registerScene( shaderPrefix, name, ReferenceCreator( referenceFileName ) );
}

boost::python::list registeredScenes( const IECore::InternedString &shaderPrefix )
{
	vector<string> n;
	ShaderView::registeredScenes( shaderPrefix, n );
	boost::python::list result;
	for( vector<string>::const_iterator it = n.begin(), eIt = n.end(); it != eIt; ++it )
	{
		result.append( *it );
	}

	return result;
}

struct SceneChangedSlotCaller
{
	void operator()( boost::python::object slot, ShaderViewPtr v )
	{
		try
		{
			slot( v );
		}
		catch( const boost::python::error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// UVView binding utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

void setPaused( UVView &v, bool paused )
{
	IECorePython::ScopedGILRelease gilRelease;
	v.setPaused( paused );
}

struct UVViewSlotCaller
{
	void operator()( boost::python::object slot, UVViewPtr g )
	{
		try
		{
			slot( g );
		}
		catch( const error_already_set & )
		{
			ExceptionAlgo::translatePythonException();
		}
	}
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Public API
//////////////////////////////////////////////////////////////////////////

void GafferSceneUIModule::bindViews()
{

	GafferBindings::NodeClass<SceneView>( nullptr, no_init )
		.def( init<ScriptNodePtr>() )
		.def( "frame", &frame, ( boost::python::arg_( "filter" ), boost::python::arg_( "direction" ) = Imath::V3f( -0.64, -0.422, -0.64 ) ) )
		.def( "resolutionGate", &resolutionGateWrapper )
		.def( "expandSelection", &expandSelection, ( boost::python::arg_( "depth" ) = 1 ) )
		.def( "collapseSelection", &collapseSelection )
		.def( "registerRenderer", &sceneViewRegisterRenderer )
		.staticmethod( "registerRenderer" )
		.def( "registeredRenderers", &sceneViewRegisteredRenderers )
		.staticmethod( "registeredRenderers" )
		.def( "registerShadingMode", &registerShadingMode )
		.staticmethod( "registerShadingMode" )
		.def( "registeredShadingModes", &registeredShadingModes )
		.staticmethod( "registeredShadingModes" )
	;

	GafferBindings::NodeClass<ShaderView>( nullptr, no_init )
		.def( init<ScriptNodePtr>() )
		.def( "shaderPrefix", &ShaderView::shaderPrefix )
		.def( "scene", (Gaffer::Node *(ShaderView::*)())&ShaderView::scene, return_value_policy<CastToIntrusivePtr>() )
		.def( "sceneChangedSignal", &ShaderView::sceneChangedSignal, return_internal_reference<1>() )
		.def( "registerRenderer", &registerRenderer )
		.staticmethod( "registerRenderer" )
		.def( "deregisterRenderer", &deregisterRenderer )
		.staticmethod( "deregisterRenderer" )
		.def( "registerScene", &registerScene )
		.def( "registerScene", &registerReferenceScene )
		.staticmethod( "registerScene" )
		.def( "registeredScenes", &registeredScenes )
		.staticmethod( "registeredScenes" )
	;

	SignalClass<ShaderView::SceneChangedSignal, DefaultSignalCaller<ShaderView::SceneChangedSignal>, SceneChangedSlotCaller>( "SceneChangedSignal" );

	{
		scope s = GafferBindings::NodeClass<UVView>( nullptr, no_init )
			.def( init<ScriptNodePtr>() )
			.def( "setPaused", &setPaused )
			.def( "getPaused", &UVView::getPaused )
			.def( "state", &UVView::state )
			.def( "stateChangedSignal", &UVView::stateChangedSignal, return_internal_reference<1>() )
		;

		enum_<UVView::State>( "State" )
			.value( "Paused", UVView::Paused )
			.value( "Running", UVView::Running )
			.value( "Complete", UVView::Complete )
		;

		SignalClass<UVView::UVViewSignal, DefaultSignalCaller<UVView::UVViewSignal>, UVViewSlotCaller>( "UVViewSignal" );
	}

}
