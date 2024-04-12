//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, John Haddon. All rights reserved.
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

#include "ToolBinding.h"

#include "GafferSceneUI/CameraTool.h"
#include "GafferSceneUI/CropWindowTool.h"
#include "GafferSceneUI/LightPositionTool.h"
#include "GafferSceneUI/LightTool.h"
#include "GafferSceneUI/RotateTool.h"
#include "GafferSceneUI/ScaleTool.h"
#include "GafferSceneUI/SceneView.h"
#include "GafferSceneUI/SelectionTool.h"
#include "GafferSceneUI/TransformTool.h"
#include "GafferSceneUI/TranslateTool.h"

#include "GafferUI/Gadget.h"

#include "GafferBindings/NodeBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Context.h"

#include "IECorePython/ExceptionAlgo.h"

using namespace std;
using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneUI;

namespace
{

Gaffer::Box2fPlugPtr cropWindowToolPlugWrapper( CropWindowTool &tool )
{
	IECorePython::ScopedGILRelease gilRelease;
	return tool.plug();
}

Gaffer::BoolPlugPtr cropWindowToolEnabledPlugWrapper( CropWindowTool &tool )
{
	IECorePython::ScopedGILRelease gilRelease;
	return tool.enabledPlug();
}

struct StatusChangedSlotCaller
{
	void operator()( boost::python::object slot, CropWindowTool &t )
	{
		try
		{
			slot( CropWindowToolPtr( &t ) );
		}
		catch( const error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}
};

boost::python::list selection( const TransformTool &tool )
{
	vector<TransformTool::Selection> selection;
	{
		IECorePython::ScopedGILRelease gilRelease;
		selection = tool.selection();
	}

	boost::python::list result;
	for( const auto &s : selection )
	{
		result.append( s );
	}
	return result;
}

IECore::PathMatcher lightToolSelection( const LightTool &tool )
{
	IECorePython::ScopedGILRelease gilRelease;
	return tool.selection();
}

bool selectionEditable( const TransformTool &tool )
{
	IECorePython::ScopedGILRelease gilRelease;
	return tool.selectionEditable();
}

template<typename T>
struct SelectionChangedSlotCaller
{
	void operator()( boost::python::object slot, T &t )
	{
		try
		{
			slot( typename T::Ptr( &t ) );
		}
		catch( const error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}
};

ScenePlugPtr scene( const TransformTool::Selection &s )
{
	return const_cast<ScenePlug *>( s.scene() );
}

std::string path( const TransformTool::Selection &s )
{
	std::string result;
	ScenePlug::pathToString( s.path(), result );
	return result;
}

ContextPtr context( const TransformTool::Selection &s )
{
	return const_cast<Context *>( s.context() );
}

ScenePlugPtr upstreamScene( const TransformTool::Selection &s )
{
	return const_cast<ScenePlug *>( s.upstreamScene() );
}

std::string upstreamPath( const TransformTool::Selection &s )
{
	std::string result;
	ScenePlug::pathToString( s.upstreamPath(), result );
	return result;
}

ContextPtr upstreamContext( const TransformTool::Selection &s )
{
	return const_cast<Context *>( s.upstreamContext() );
}

EditScopePtr editScope( const TransformTool::Selection &s )
{
	return const_cast<EditScope *>( s.editScope() );
}

object acquireTransformEdit( const TransformTool::Selection &s, bool createIfNecessary )
{
	std::optional<EditScopeAlgo::TransformEdit> p;
	{
		IECorePython::ScopedGILRelease gilRelease;
		p = s.acquireTransformEdit( createIfNecessary );
	}
	return p ? object( *p ) : object();
}

void registerSelectMode( const std::string &modifierName, object modifier )
{
	auto selectModePtr = std::shared_ptr<boost::python::object>(
		new boost::python::object( modifier ),
		[]( boost::python::object *o ) {
			IECorePython::ScopedGILLock gilLock;
			delete o;
		}
	);

	SelectionTool::registerSelectMode(
		modifierName,
		[selectModePtr](
			const GafferScene::ScenePlug *scene,
			const GafferScene::ScenePlug::ScenePath &path
		) -> GafferScene::ScenePlug::ScenePath
		{
			IECorePython::ScopedGILLock gilLock;
			try
			{
				const std::string pathString = GafferScene::ScenePlug::pathToString( path );
				return extract<GafferScene::ScenePlug::ScenePath>(
					(*selectModePtr)( GafferScene::ScenePlugPtr( const_cast<GafferScene::ScenePlug *>( scene ) ), pathString )
				);
			}
			catch( const boost::python::error_already_set & )
			{
				ExceptionAlgo::translatePythonException();
			}
		}
	);
}

} // namespace

void GafferSceneUIModule::bindTools()
{

	GafferBindings::NodeClass<SelectionTool>( nullptr, no_init )
		.def( "registerSelectMode", &registerSelectMode, ( boost::python::arg( "modifierName" ), boost::python::arg( "modifier" ) ) )
		.staticmethod( "registerSelectMode" )
		.def( "registeredSelectModes", &SelectionTool::registeredSelectModes )
		.staticmethod( "registeredSelectModes" )
		.def( "deregisterSelectMode", &SelectionTool::deregisterSelectMode )
		.staticmethod( "deregisterSelectMode" )
	;

	{
		GafferBindings::NodeClass<CropWindowTool>( nullptr, no_init )
			.def( init<GafferUI::View *>() )
			.def( "status", &CropWindowTool::status )
			.def( "plug", &cropWindowToolPlugWrapper )
			.def( "enabledPlug", &cropWindowToolEnabledPlugWrapper )
			.def( "statusChangedSignal", &CropWindowTool::statusChangedSignal, return_internal_reference<1>() )
		;

		GafferBindings::SignalClass<CropWindowTool::StatusChangedSignal, GafferBindings::DefaultSignalCaller<CropWindowTool::StatusChangedSignal>, StatusChangedSlotCaller>( "StatusChangedSignal" );
	}

	{
		scope s = GafferBindings::NodeClass<TransformTool>( nullptr, no_init )
			.def( "selection", &selection )
			.def( "selectionEditable", &selectionEditable )
			.def( "selectionChangedSignal", &TransformTool::selectionChangedSignal, return_internal_reference<1>() )
			.def( "handlesTransform", &TransformTool::handlesTransform )
		;

		class_<TransformTool::Selection>( "Selection", no_init )

			.def( init<const ConstScenePlugPtr &, const ScenePlug::ScenePath &, const ConstContextPtr &, const EditScopePtr &>() )

			.def( "scene", &scene )
			.def( "path", &path )
			.def( "context", &context )

			.def( "upstreamScene", &upstreamScene )
			.def( "upstreamPath", &upstreamPath )
			.def( "upstreamContext", &upstreamContext )

			.def( "editable", &TransformTool::Selection::editable )
			.def( "warning", &TransformTool::Selection::warning, return_value_policy<copy_const_reference>() )
			.def( "editScope", &editScope )
			.def( "acquireTransformEdit", &acquireTransformEdit, ( boost::python::arg( "createIfNecessary" ) = true ) )
			.def( "editTarget", &TransformTool::Selection::editTarget, return_value_policy<CastToIntrusivePtr>() )
			.def( "transformSpace", &TransformTool::Selection::transformSpace, return_value_policy<copy_const_reference>() )

		;

		enum_<TransformTool::Orientation>( "Orientation" )
			.value( "Local", TransformTool::Local )
			.value( "Parent", TransformTool::Parent )
			.value( "World", TransformTool::World )
		;

		GafferBindings::SignalClass<TransformTool::SelectionChangedSignal, GafferBindings::DefaultSignalCaller<TransformTool::SelectionChangedSignal>, SelectionChangedSlotCaller<TransformTool>>( "SelectionChangedSignal" );
	}

	GafferBindings::NodeClass<TranslateTool>( nullptr, no_init )
		.def( init<SceneView *>() )
		.def( "translate", &TranslateTool::translate )
	;

	GafferBindings::NodeClass<ScaleTool>( nullptr, no_init )
		.def( init<SceneView *>() )
		.def( "scale", &ScaleTool::scale )
	;

	GafferBindings::NodeClass<RotateTool>( nullptr, no_init )
		.def( init<SceneView *>() )
		.def( "rotate", &RotateTool::rotate )
	;

	GafferBindings::NodeClass<CameraTool>( nullptr, no_init )
		.def( init<SceneView *>() )
	;

	{
		scope s = GafferBindings::NodeClass<LightTool>( nullptr, no_init )
			.def( init<SceneView *>() )
			.def( "selection", &lightToolSelection )
			.def( "selectionChangedSignal", &LightTool::selectionChangedSignal, return_internal_reference<1>() )
		;

		GafferBindings::SignalClass<LightTool::SelectionChangedSignal, GafferBindings::DefaultSignalCaller<LightTool::SelectionChangedSignal>, SelectionChangedSlotCaller<LightTool>>( "SelectionChangedSignal" );
	}

	{
		scope s = GafferBindings::NodeClass<LightPositionTool>( nullptr, no_init )
			.def( init<SceneView *>() )
			.def( "positionShadow", &LightPositionTool::positionShadow )
			.def( "positionHighlight", &LightPositionTool::positionHighlight )
			.def( "positionAlongNormal", &LightPositionTool::positionAlongNormal )
		;

		enum_<LightPositionTool::Mode>( "Mode" )
			.value( "Shadow", LightPositionTool::Mode::Shadow )
			.value( "Highlight", LightPositionTool::Mode::Highlight )
			.value( "Diffuse", LightPositionTool::Mode::Diffuse )
		;
	}

}
