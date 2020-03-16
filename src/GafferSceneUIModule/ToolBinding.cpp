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
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneUI;

namespace
{

struct StatusChangedSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, CropWindowTool &t )
	{
		try
		{
			slot( CropWindowToolPtr( &t ) );
		}
		catch( const error_already_set &e )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
		return boost::signals::detail::unusable();
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

struct SelectionChangedSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, TransformTool &t )
	{
		try
		{
			slot( TransformToolPtr( &t ) );
		}
		catch( const error_already_set &e )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
		return boost::signals::detail::unusable();
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

TransformPlugPtr transformPlug( const TransformTool::Selection &s )
{
	return s.transformPlug();
}

} // namespace

void GafferSceneUIModule::bindTools()
{

	GafferBindings::NodeClass<SelectionTool>( nullptr, no_init );

	{
		GafferBindings::NodeClass<CropWindowTool>( nullptr, no_init )
			.def( "status", &CropWindowTool::status )
			.def( "statusChangedSignal", &CropWindowTool::statusChangedSignal, return_internal_reference<1>() )
		;

		GafferBindings::SignalClass<CropWindowTool::StatusChangedSignal, GafferBindings::DefaultSignalCaller<CropWindowTool::StatusChangedSignal>, StatusChangedSlotCaller>( "StatusChangedSignal" );
	}

	{
		scope s = GafferBindings::NodeClass<TransformTool>( nullptr, no_init )
			.def( "selection", &selection )
			.def( "selectionChangedSignal", &TransformTool::selectionChangedSignal, return_internal_reference<1>() )
			.def( "handlesTransform", &TransformTool::handlesTransform )
		;

		class_<TransformTool::Selection>( "Selection", no_init )

			.def( init<const ConstScenePlugPtr &, const ScenePlug::ScenePath &, const ConstContextPtr &>() )

			.def( "scene", &scene )
			.def( "path", &path )
			.def( "context", &context )

			.def( "upstreamScene", &upstreamScene )
			.def( "upstreamPath", &upstreamPath )
			.def( "upstreamContext", &upstreamContext )

			.def( "editable", &TransformTool::Selection::editable )
			.def( "warning", &TransformTool::Selection::warning, return_value_policy<copy_const_reference>() )
			.def( "transformPlug", &transformPlug )
			.def( "transformSpace", &TransformTool::Selection::transformSpace, return_value_policy<copy_const_reference>() )

		;

		enum_<TransformTool::Orientation>( "Orientation" )
			.value( "Local", TransformTool::Local )
			.value( "Parent", TransformTool::Parent )
			.value( "World", TransformTool::World )
		;

		GafferBindings::SignalClass<TransformTool::SelectionChangedSignal, GafferBindings::DefaultSignalCaller<TransformTool::SelectionChangedSignal>, SelectionChangedSlotCaller>( "SelectionChangedSignal" );
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

}
