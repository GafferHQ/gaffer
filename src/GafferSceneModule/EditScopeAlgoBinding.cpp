//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

#include "EditScopeAlgoBinding.h"

#include "GafferScene/EditScopeAlgo.h"

#include "IECorePython/RefCountedBinding.h"
#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

void setPrunedWrapper1( Gaffer::EditScope &scope, const ScenePlug::ScenePath &path, bool pruned )
{
	IECorePython::ScopedGILRelease gilRelease;
	EditScopeAlgo::setPruned( &scope, path, pruned );
}

void setPrunedWrapper2( Gaffer::EditScope &scope, const IECore::PathMatcher &paths, bool pruned )
{
	IECorePython::ScopedGILRelease gilRelease;
	EditScopeAlgo::setPruned( &scope, paths, pruned );
}

bool getPrunedWrapper( Gaffer::EditScope &scope, const ScenePlug::ScenePath &path )
{
	IECorePython::ScopedGILRelease gilRelease;
	return EditScopeAlgo::getPruned( &scope, path );
}

GraphComponentPtr prunedReadOnlyReasonWrapper( Gaffer::EditScope &scope )
{
	return const_cast<GraphComponent *>( EditScopeAlgo::prunedReadOnlyReason( &scope ) );
}

bool hasTransformEditWrapper( const Gaffer::EditScope &scope, const ScenePlug::ScenePath &path )
{
	IECorePython::ScopedGILRelease gilRelease;
	return EditScopeAlgo::hasTransformEdit( &scope, path );
}

object acquireTransformEditWrapper( Gaffer::EditScope &scope, const ScenePlug::ScenePath &path, bool createIfNecessary )
{
	IECorePython::ScopedGILRelease gilRelease;
	auto p = EditScopeAlgo::acquireTransformEdit( &scope, path, createIfNecessary );
	return p ? object( *p ) : object();
}

void removeTransformEditWrapper( Gaffer::EditScope &scope, const ScenePlug::ScenePath &path )
{
	IECorePython::ScopedGILRelease gilRelease;
	EditScopeAlgo::removeTransformEdit( &scope, path );
}

GraphComponentPtr transformEditReadOnlyReasonWrapper( Gaffer::EditScope &scope, const ScenePlug::ScenePath &path )
{
	return const_cast<GraphComponent *>( EditScopeAlgo::transformEditReadOnlyReason( &scope, path ) );
}

V3fPlugPtr translateAccessor( EditScopeAlgo::TransformEdit &e )
{
	return e.translate;
}

V3fPlugPtr rotateAccessor( EditScopeAlgo::TransformEdit &e )
{
	return e.rotate;
}

V3fPlugPtr scaleAccessor( EditScopeAlgo::TransformEdit &e )
{
	return e.scale;
}

V3fPlugPtr pivotAccessor( EditScopeAlgo::TransformEdit &e )
{
	return e.pivot;
}

Imath::M44f matrixWrapper( EditScopeAlgo::TransformEdit &e )
{
	IECorePython::ScopedGILRelease gilRelease;
	return e.matrix();
}


// Shaders
// =======

bool hasParameterEditWrapper( const Gaffer::EditScope &scope, const ScenePlug::ScenePath &path, const std::string &attribute, const IECoreScene::ShaderNetwork::Parameter &parameter )
{
	return EditScopeAlgo::hasParameterEdit( &scope, path, attribute, parameter );
}

TweakPlugPtr acquireParameterEditWrapper( Gaffer::EditScope &scope, const ScenePlug::ScenePath &path, const std::string &attribute, const IECoreScene::ShaderNetwork::Parameter &parameter, bool createIfNecessary )
{
	IECorePython::ScopedGILRelease gilRelease;
	return EditScopeAlgo::acquireParameterEdit( &scope, path, attribute, parameter, createIfNecessary );
}

void removeParameterEditWrapper( Gaffer::EditScope &scope, const ScenePlug::ScenePath &path, const std::string &attribute, const IECoreScene::ShaderNetwork::Parameter &parameter )
{
	IECorePython::ScopedGILRelease gilRelease;
	return EditScopeAlgo::removeParameterEdit( &scope, path, attribute, parameter );
}

GraphComponentPtr parameterEditReadOnlyReasonWrapper( Gaffer::EditScope &scope, const ScenePlug::ScenePath &path, const std::string &attribute, const IECoreScene::ShaderNetwork::Parameter &parameter )
{
	return const_cast<GraphComponent *>( EditScopeAlgo::parameterEditReadOnlyReason( &scope, path, attribute, parameter ) );
}


// Attributes
// ==========

bool hasAttributeEditWrapper( const Gaffer::EditScope &scope, const ScenePlug::ScenePath &path, const std::string &attribute )
{
	return EditScopeAlgo::hasAttributeEdit( &scope, path, attribute );
}

TweakPlugPtr acquireAttributeEditWrapper( Gaffer::EditScope &scope, const ScenePlug::ScenePath &path, const std::string &attribute, bool createIfNecessary )
{
	IECorePython::ScopedGILRelease gilRelease;
	return EditScopeAlgo::acquireAttributeEdit( &scope, path, attribute, createIfNecessary );
}

void removeAttributeEditWrapper( Gaffer::EditScope &scope, const ScenePlug::ScenePath &path, const std::string &attribute )
{
	IECorePython::ScopedGILRelease gilRelease;
	return EditScopeAlgo::removeAttributeEdit( &scope, path, attribute );
}

GraphComponentPtr attributeEditReadOnlyReasonWrapper( Gaffer::EditScope &scope, const ScenePlug::ScenePath &path, const std::string &attribute )
{
	return const_cast<GraphComponent *>( EditScopeAlgo::attributeEditReadOnlyReason( &scope, path, attribute ) );
}

// Set Membership
// ==============

ValuePlugPtr acquireSetEditsWrapper( Gaffer::EditScope &scope, const std::string &set, bool createIfNecessary )
{
	IECorePython::ScopedGILRelease gilRelease;
	return EditScopeAlgo::acquireSetEdits( &scope, set, createIfNecessary );
}

void setSetMembershipWrapper( Gaffer::EditScope &scope, const IECore::PathMatcher &paths, const std::string &set, EditScopeAlgo::SetMembership state )
{
	IECorePython::ScopedGILRelease gilRelease;
	EditScopeAlgo::setSetMembership( &scope, paths, set, state );
}

EditScopeAlgo::SetMembership getSetMembershipWrapper( Gaffer::EditScope &scope, const ScenePlug::ScenePath &path, const std::string &set )
{
	IECorePython::ScopedGILRelease gilRelease;
	return EditScopeAlgo::getSetMembership( &scope, path, set );
}

GraphComponentPtr setMembershipReadOnlyReasonWrapper( Gaffer::EditScope &scope, const std::string &set, EditScopeAlgo::SetMembership state )
{
	return const_cast<GraphComponent *>( EditScopeAlgo::setMembershipReadOnlyReason( &scope, set, state ) );
}

// Options
// =======

bool hasOptionEditWrapper( const Gaffer::EditScope &scope, const std::string &option )
{
	return EditScopeAlgo::hasOptionEdit( &scope, option );
}

TweakPlugPtr acquireOptionEditWrapper( Gaffer::EditScope &scope, const std::string &option, bool createIfNecessary )
{
	IECorePython::ScopedGILRelease gilRelease;
	return EditScopeAlgo::acquireOptionEdit( &scope, option, createIfNecessary );
}

void removeOptionEditWrapper( Gaffer::EditScope &scope, const std::string &option )
{
	IECorePython::ScopedGILRelease gilRelease;
	return EditScopeAlgo::removeOptionEdit( &scope, option );
}

GraphComponentPtr optionEditReadOnlyReasonWrapper( Gaffer::EditScope &scope, const std::string &option )
{
	return const_cast<GraphComponent *>( EditScopeAlgo::optionEditReadOnlyReason( &scope, option ) );
}

// Render Pass Option Edits
// ========================

bool hasRenderPassOptionEditWrapper( const Gaffer::EditScope &scope, const std::string &renderPass, const std::string &option )
{
	return EditScopeAlgo::hasRenderPassOptionEdit( &scope, renderPass, option );
}

TweakPlugPtr acquireRenderPassOptionEditWrapper( Gaffer::EditScope &scope, const std::string &renderPass, const std::string &option, bool createIfNecessary )
{
	IECorePython::ScopedGILRelease gilRelease;
	return EditScopeAlgo::acquireRenderPassOptionEdit( &scope, renderPass, option, createIfNecessary );
}

void removeRenderPassOptionEditWrapper( Gaffer::EditScope &scope, const std::string &renderPass, const std::string &option )
{
	IECorePython::ScopedGILRelease gilRelease;
	return EditScopeAlgo::removeRenderPassOptionEdit( &scope, renderPass, option );
}

GraphComponentPtr renderPassOptionEditReadOnlyReasonWrapper( Gaffer::EditScope &scope, const std::string &renderPass, const std::string &option )
{
	return const_cast<GraphComponent *>( EditScopeAlgo::renderPassOptionEditReadOnlyReason( &scope, renderPass, option ) );
}


} // namespace

namespace GafferSceneModule
{

void bindEditScopeAlgo()
{
	object module( borrowed( PyImport_AddModule( "GafferScene.EditScopeAlgo" ) ) );
	scope().attr( "EditScopeAlgo" ) = module;
	scope moduleScope( module );

	def( "setPruned", &setPrunedWrapper1 );
	def( "setPruned", &setPrunedWrapper2 );
	def( "getPruned", &getPrunedWrapper );
	def( "prunedReadOnlyReason", &prunedReadOnlyReasonWrapper );

	class_<EditScopeAlgo::TransformEdit>( "TransformEdit", no_init )
		.def( init<const V3fPlugPtr &, const V3fPlugPtr &, const V3fPlugPtr &, const V3fPlugPtr &>() )
		.add_property( "translate", &translateAccessor )
		.add_property( "rotate", &rotateAccessor )
		.add_property( "scale", &scaleAccessor )
		.add_property( "pivot", &pivotAccessor )
		.def( "matrix", &matrixWrapper )
		.def( self == self )
		.def( self != self )
	;

	def( "acquireTransformEdit", &acquireTransformEditWrapper, ( arg( "scope" ), arg( "path" ), arg( "createIfNecessary" ) = true ) );
	def( "hasTransformEdit", &hasTransformEditWrapper );
	def( "removeTransformEdit", &removeTransformEditWrapper );
	def( "transformEditReadOnlyReason", &transformEditReadOnlyReasonWrapper );

	def( "acquireParameterEdit", &acquireParameterEditWrapper, ( arg( "scope" ), arg( "path" ), arg( "attribute" ), arg( "parameter" ), arg( "createIfNecessary" ) = true ) );
	def( "hasParameterEdit", &hasParameterEditWrapper, ( arg( "scope" ), arg( "path" ), arg( "attribute" ), arg( "parameter" ) ) );
	def( "removeParameterEdit", &removeParameterEditWrapper, ( arg( "scope" ), arg( "path" ), arg( "attribute" ), arg( "parameter" ) ) );
	def( "parameterEditReadOnlyReason", &parameterEditReadOnlyReasonWrapper, ( arg( "scope" ), arg( "path" ), arg( "attribute" ), arg( "parameter" ) ) );

	def( "acquireAttributeEdit", &acquireAttributeEditWrapper, ( arg( "scope" ), arg( "path" ), arg( "attribute" ), arg( "createIfNecessary" ) = true ) );
	def( "hasAttributeEdit", &hasAttributeEditWrapper, ( arg( "scope" ), arg( "path" ), arg( "attribute" ) ) );
	def( "removeAttributeEdit", &removeAttributeEditWrapper, ( arg( "scope" ), arg( "path" ), arg( "attribute" ) ) );
	def( "attributeEditReadOnlyReason", &attributeEditReadOnlyReasonWrapper, ( arg( "scope" ), arg( "path" ), arg( "attribute" ) ) );

	def( "acquireSetEdits", &acquireSetEditsWrapper, ( arg( "scope" ), arg( "set" ), arg( "createIfNecessary" ) = true ) );
	def( "setSetMembership", &setSetMembershipWrapper );
	def( "getSetMembership", &getSetMembershipWrapper );
	def( "setMembershipReadOnlyReason", &setMembershipReadOnlyReasonWrapper );
	enum_<EditScopeAlgo::SetMembership>( "SetMembership" )
		.value( "Added", EditScopeAlgo::SetMembership::Added )
		.value( "Removed", EditScopeAlgo::SetMembership::Removed )
		.value( "Unchanged", EditScopeAlgo::SetMembership::Unchanged )
	;

	def( "acquireOptionEdit", &acquireOptionEditWrapper, ( arg( "scope" ), arg( "option" ), arg( "createIfNecessary" ) = true ) );
	def( "hasOptionEdit", &hasOptionEditWrapper, ( arg( "scope" ), arg( "option" ) ) );
	def( "removeOptionEdit", &removeOptionEditWrapper, ( arg( "scope" ), arg( "option" ) ) );
	def( "optionEditReadOnlyReason", &optionEditReadOnlyReasonWrapper, ( arg( "scope" ), arg( "option" ) ) );

	def( "acquireRenderPassOptionEdit", &acquireRenderPassOptionEditWrapper, ( arg( "scope" ), arg( "renderPass" ), arg( "option" ), arg( "createIfNecessary" ) = true ) );
	def( "hasRenderPassOptionEdit", &hasRenderPassOptionEditWrapper, ( arg( "scope" ), arg( "renderPass" ), arg( "option" ) ) );
	def( "removeRenderPassOptionEdit", &removeRenderPassOptionEditWrapper, ( arg( "scope" ), arg( "renderPass" ), arg( "option" ) ) );
	def( "renderPassOptionEditReadOnlyReason", &renderPassOptionEditReadOnlyReasonWrapper, ( arg( "scope" ), arg( "renderPass" ), arg( "option" ) ) );

}

} // namespace GafferSceneModule
