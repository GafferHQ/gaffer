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

#include "ContextAlgoBinding.h"

#include "GafferSceneUI/ContextAlgo.h"

#include "GafferScene/ScenePlug.h"

#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneUI::ContextAlgo;

namespace
{

void setExpandedPathsWrapper( Context &context, const IECore::PathMatcher &paths )
{
	IECorePython::ScopedGILRelease gilRelease;
	setExpandedPaths( &context, paths );
}

void setVisibleSetWrapper( Context &context, const GafferScene::VisibleSet &visibleSet )
{
	IECorePython::ScopedGILRelease gilRelease;
	setVisibleSet( &context, visibleSet );
}

void expandWrapper( Context &context, const IECore::PathMatcher &paths, bool expandAncestors )
{
	IECorePython::ScopedGILRelease gilRelease;
	expand( &context, paths, expandAncestors );
}

PathMatcher expandDescendantsWrapper( Context &context, PathMatcher &paths, ScenePlug &scene, int depth )
{
	IECorePython::ScopedGILRelease gilRelease;
	return expandDescendants( &context, paths, &scene, depth );
}

void clearExpansionWrapper( Context &context )
{
	IECorePython::ScopedGILRelease gilRelease;
	clearExpansion( &context );
}

void setSelectedPathsWrapper( Context &context, const IECore::PathMatcher &paths )
{
	IECorePython::ScopedGILRelease gilRelease;
	setSelectedPaths( &context, paths );
}

void setLastSelectedPathWrapper( Gaffer::Context *context, const std::vector<IECore::InternedString> &path )
{
	IECorePython::ScopedGILRelease gilRelease;
	setLastSelectedPath( context, path );
}

std::string getLastSelectedPathWrapper( const Gaffer::Context *context )
{
	std::vector<InternedString> path = getLastSelectedPath( context );
	if( path.empty() )
	{
		return "";
	}

	std::string result;
	ScenePlug::pathToString( path, result );
	return result;
}

} // namespace

void GafferSceneUIModule::bindContextAlgo()
{
	object module( borrowed( PyImport_AddModule( "GafferSceneUI.ContextAlgo" ) ) );
	scope().attr( "ContextAlgo" ) = module;
	scope moduleScope( module );

	def( "setExpandedPaths", &setExpandedPathsWrapper );
	def( "getExpandedPaths", &getExpandedPaths );
	def( "affectsExpandedPaths", &affectsExpandedPaths );
	def( "setVisibleSet", &setVisibleSetWrapper );
	def( "getVisibleSet", &getVisibleSet );
	def( "affectsVisibleSet", &affectsVisibleSet );
	def( "setLastSelectedPath", &setLastSelectedPathWrapper );
	def( "getLastSelectedPath", &getLastSelectedPathWrapper );
	def( "affectsLastSelectedPath", &affectsLastSelectedPath );
	def( "expand", &expandWrapper, ( arg( "expandAncestors" ) = true ) );
	def( "expandDescendants", &expandDescendantsWrapper, ( arg( "context" ), arg( "paths" ), arg( "scene" ), arg( "depth" ) = Imath::limits<int>::max() ) );
	def( "clearExpansion", &clearExpansionWrapper );
	def( "setSelectedPaths", &setSelectedPathsWrapper );
	def( "getSelectedPaths", &getSelectedPaths );
	def( "affectsSelectedPaths", &affectsSelectedPaths );

}
