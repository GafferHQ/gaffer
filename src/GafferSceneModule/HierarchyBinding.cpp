//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "HierarchyBinding.h"

#include "GafferScene/Capsule.h"
#include "GafferScene/CollectScenes.h"
#include "GafferScene/Duplicate.h"
#include "GafferScene/Encapsulate.h"
#include "GafferScene/Group.h"
#include "GafferScene/Instancer.h"
#include "GafferScene/Isolate.h"
#include "GafferScene/MergeScenes.h"
#include "GafferScene/Parent.h"
#include "GafferScene/Prune.h"
#include "GafferScene/Rename.h"
#include "GafferScene/Scatter.h"
#include "GafferScene/SubTree.h"
#include "GafferScene/Unencapsulate.h"
#include "GafferScene/MotionPath.h"
#include "GafferScene/MeshSplit.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/PlugBinding.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;

namespace
{

object getRenderOptionsWrapper( const Capsule &c )
{
	if( auto o = c.getRenderOptions() )
	{
		return object( *o );
	}
	return object();
}

ScenePlugPtr scene( const Capsule &c )
{
	return const_cast<ScenePlug *>( c.scene() );
}

std::string root( const Capsule &c )
{
	std::string result;
	ScenePlug::pathToString( c.root(), result );
	return result;
}

ContextPtr context( const Capsule &c )
{
	return const_cast<Context *>( c.context() );
}

} // namespace

void GafferSceneModule::bindHierarchy()
{

	IECorePython::RunTimeTypedClass<Capsule>()
		.def(
			init<
				const ScenePlug *,
				const ScenePlug::ScenePath &,
				const Gaffer::Context &,
				const IECore::MurmurHash &,
				const Imath::Box3f &
			>()
		)
		.def( "scene", &scene )
		.def( "root", &root )
		.def( "context", &context )
		.def( "setRenderOptions", &Capsule::setRenderOptions )
		.def( "getRenderOptions", &getRenderOptionsWrapper )
	;

	GafferBindings::DependencyNodeClass<Group>()
		.def( "nextInPlug", (ScenePlug *(Group::*)())&Group::nextInPlug, return_value_policy<CastToIntrusivePtr>() )
	;

	GafferBindings::DependencyNodeClass<BranchCreator>();
	GafferBindings::DependencyNodeClass<GafferScene::Parent>();
	GafferBindings::DependencyNodeClass<GafferScene::Duplicate>();
	GafferBindings::DependencyNodeClass<SubTree>();
	GafferBindings::DependencyNodeClass<Prune>();
	GafferBindings::DependencyNodeClass<Isolate>();
	GafferBindings::DependencyNodeClass<CollectScenes>();
	GafferBindings::DependencyNodeClass<Scatter>();
	GafferBindings::DependencyNodeClass<Encapsulate>();
	GafferBindings::DependencyNodeClass<Unencapsulate>();
	GafferBindings::DependencyNodeClass<Rename>();
	GafferBindings::DependencyNodeClass<MeshSplit>();

	{
		scope s = GafferBindings::DependencyNodeClass<MergeScenes>();
		enum_<MergeScenes::Mode>( "Mode" )
			.value( "Keep", MergeScenes::Mode::Keep )
			.value( "Replace", MergeScenes::Mode::Replace )
			.value( "Merge", MergeScenes::Mode::Merge )
		;
	}

	{
		scope s = GafferBindings::DependencyNodeClass<Instancer>();
		enum_<Instancer::PrototypeMode>( "PrototypeMode" )
			.value( "IndexedRootsList", Instancer::PrototypeMode::IndexedRootsList )
			.value( "IndexedRootsVariable", Instancer::PrototypeMode::IndexedRootsVariable )
			.value( "RootPerVertex", Instancer::PrototypeMode::RootPerVertex )
		;

		GafferBindings::PlugClass<Instancer::ContextVariablePlug>()
			.def( init<const char *, Plug::Direction, bool, unsigned>(
					(
						boost::python::arg_( "name" )=GraphComponent::defaultName<Instancer::ContextVariablePlug>(),
						boost::python::arg_( "direction" )=Plug::In,
						boost::python::arg_( "defaultEnable" )=true,
						boost::python::arg_( "flags" )=Plug::Default
					)
				)
			)
			.attr( "__qualname__" ) = "Instancer.ContextVariablePlug"
		;

	}

	{
		scope s = GafferBindings::DependencyNodeClass<MotionPath>();

		enum_<MotionPath::FrameMode>( "FrameMode" )
			.value( "Relative", MotionPath::FrameMode::Relative )
			.value( "Absolute", MotionPath::FrameMode::Absolute )
			;

		enum_<MotionPath::SamplingMode>( "SamplingMode" )
			.value( "Variable", MotionPath::SamplingMode::Variable )
			.value( "Fixed", MotionPath::SamplingMode::Fixed )
			;
	}
}
