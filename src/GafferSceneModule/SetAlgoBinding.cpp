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

#include "GafferScene/SetAlgo.h"

#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace IECore;
using namespace GafferScene;

namespace
{

PathMatcher evaluateSetExpressionWrapper( const std::string &setExpression, const ScenePlug *scene )
{
	IECorePython::ScopedGILRelease r;
	return SetAlgo::evaluateSetExpression( setExpression, scene );
}

IECore::MurmurHash setExpressionHashWrapper1( const std::string &setExpression, const ScenePlug *scene )
{
	IECorePython::ScopedGILRelease r;
	return SetAlgo::setExpressionHash( setExpression, scene );
}

void setExpressionHashWrapper2( const std::string &setExpression, const ScenePlug *scene, IECore::MurmurHash &h )
{
	IECorePython::ScopedGILRelease r;
	SetAlgo::setExpressionHash( setExpression, scene, h );
}

} // namespace

namespace GafferSceneModule
{

void bindSetAlgo()
{
	object module( borrowed( PyImport_AddModule( "GafferScene.SetAlgo" ) ) );
	scope().attr( "SetAlgo" ) = module;
	scope moduleScope( module );

	def(
		"evaluateSetExpression",
		&evaluateSetExpressionWrapper,
		( arg( "expression" ), arg( "scene" ) )
	);

	def(
		"setExpressionHash",
		&setExpressionHashWrapper1,
		( arg( "expression" ), arg( "scene" ) )
	);

	def(
		"setExpressionHash",
		&setExpressionHashWrapper2,
		( arg( "expression" ), arg( "scene" ), arg( "h" ) )
	);

	def( "affectsSetExpression", &SetAlgo::affectsSetExpression );

}

} // namespace GafferSceneModule
