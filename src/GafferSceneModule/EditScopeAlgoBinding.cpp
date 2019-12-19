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

	class_<EditScopeAlgo::TransformEdit>( "TransformEdit" )
		.add_property( "translate", &translateAccessor )
		.add_property( "rotate", &rotateAccessor )
		.add_property( "scale", &scaleAccessor )
		.add_property( "pivot", &pivotAccessor )
		.def( "matrix", &matrixWrapper )
	;

	def( "acquireTransformEdit", &acquireTransformEditWrapper, ( arg( "scope" ), arg( "path" ), arg( "createIfNecessary" ) = true ) );
	def( "hasTransformEdit", &hasTransformEditWrapper );
	def( "removeTransformEdit", &removeTransformEditWrapper );
}

} // namespace GafferSceneModule
