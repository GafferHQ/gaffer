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

#include "TransformBinding.h"

#include "GafferScene/AimConstraint.h"
#include "GafferScene/Constraint.h"
#include "GafferScene/FreezeTransform.h"
#include "GafferScene/ParentConstraint.h"
#include "GafferScene/PointConstraint.h"
#include "GafferScene/Transform.h"
#include "GafferScene/TransformQuery.h"

#include "GafferBindings/ComputeNodeBinding.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;

void GafferSceneModule::bindTransform()
{

	typedef ComputeNodeWrapper<FilteredSceneProcessor> Wrapper;
	GafferBindings::DependencyNodeClass<FilteredSceneProcessor, Wrapper>()
		.def( init<const std::string &, IECore::PathMatcher::Result>(
				(
					arg( "name" ) = GraphComponent::defaultName<FilteredSceneProcessor>(),
					arg( "filterDefault" ) = IECore::PathMatcher::EveryMatch
				)
			)
		)
		.def( init<const std::string &, size_t, size_t>(
				(
					arg( "name" ),
					arg( "minInputs" ),
					arg( "maxInputs" ) = std::numeric_limits<size_t>::max()
				)
			)
		)
	;

	GafferBindings::DependencyNodeClass<SceneElementProcessor>();

	{
		scope s =  GafferBindings::DependencyNodeClass<Constraint>();

		enum_<Constraint::TargetMode>( "TargetMode" )
			.value( "Origin", Constraint::Origin )
			.value( "BoundMin", Constraint::BoundMin )
			.value( "BoundMax", Constraint::BoundMax )
			.value( "BoundCenter", Constraint::BoundCenter )
		;
	}

	GafferBindings::DependencyNodeClass<AimConstraint>();
	GafferBindings::DependencyNodeClass<PointConstraint>();
	GafferBindings::DependencyNodeClass<ParentConstraint>();
	GafferBindings::DependencyNodeClass<GafferScene::FreezeTransform>();

	{
		scope s = GafferBindings::DependencyNodeClass<Transform>();

		enum_<Transform::Space>( "Space" )
			.value( "Local", Transform::Local )
			.value( "Parent", Transform::Parent )
			.value( "World", Transform::World )
			.value( "ResetLocal", Transform::ResetLocal )
			.value( "ResetWorld", Transform::ResetWorld )
		;
	}

	{
		scope s = GafferBindings::DependencyNodeClass<TransformQuery>();

		enum_<TransformQuery::Space>( "Space" )
			.value( "Local", TransformQuery::Space::Local )
			.value( "World", TransformQuery::Space::World )
			.value( "Relative", TransformQuery::Space::Relative )
		;
	}
}
