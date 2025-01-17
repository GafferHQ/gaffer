//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

#include "ScriptNodeAlgoBinding.h"

#include "GafferSceneUI/ScriptNodeAlgo.h"

#include "GafferScene/ScenePlug.h"

#include "Gaffer/ScriptNode.h"

#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneUI::ScriptNodeAlgo;

namespace
{

void setVisibleSetWrapper( ScriptNode &script, const GafferScene::VisibleSet &visibleSet )
{
	IECorePython::ScopedGILRelease gilRelease;
	setVisibleSet( &script, visibleSet );
}

void expandInVisibleSetWrapper( ScriptNode &script, const IECore::PathMatcher &paths, bool expandAncestors )
{
	IECorePython::ScopedGILRelease gilRelease;
	expandInVisibleSet( &script, paths, expandAncestors );
}

PathMatcher expandDescendantsInVisibleSetWrapper( ScriptNode &script, PathMatcher &paths, ScenePlug &scene, int depth )
{
	IECorePython::ScopedGILRelease gilRelease;
	return expandDescendantsInVisibleSet( &script, paths, &scene, depth );
}

void setSelectedPathsWrapper( ScriptNode &script, const IECore::PathMatcher &paths )
{
	IECorePython::ScopedGILRelease gilRelease;
	setSelectedPaths( &script, paths );
}

void setLastSelectedPathWrapper( ScriptNode &script, const std::vector<IECore::InternedString> &path )
{
	IECorePython::ScopedGILRelease gilRelease;
	setLastSelectedPath( &script, path );
}

std::string getLastSelectedPathWrapper( const ScriptNode &script )
{
	std::vector<InternedString> path = getLastSelectedPath( &script );
	if( path.empty() )
	{
		return "";
	}

	std::string result;
	ScenePlug::pathToString( path, result );
	return result;
}

NameValuePlugPtr acquireRenderPassPlugWrapper( Gaffer::ScriptNode &script, bool createIfMissing )
{
	IECorePython::ScopedGILRelease gilRelease;
	return acquireRenderPassPlug( &script, createIfMissing );
}

void setCurrentRenderPassWrapper( ScriptNode &script, const std::string &renderPass )
{
	IECorePython::ScopedGILRelease gilRelease;
	setCurrentRenderPass( &script, renderPass );
}

std::string getCurrentRenderPassWrapper( ScriptNode &script )
{
	return getCurrentRenderPass( &script );
}

} // namespace

void GafferSceneUIModule::bindScriptNodeAlgo()
{
	object module( borrowed( PyImport_AddModule( "GafferSceneUI.ScriptNodeAlgo" ) ) );
	scope().attr( "ScriptNodeAlgo" ) = module;
	scope moduleScope( module );

	def( "setVisibleSet", &setVisibleSetWrapper );
	def( "getVisibleSet", &getVisibleSet );
	def( "visibleSetChangedSignal", &visibleSetChangedSignal, return_value_policy<reference_existing_object>() );

	def( "expandInVisibleSet", &expandInVisibleSetWrapper, ( arg( "expandAncestors" ) = true ) );
	def( "expandDescendantsInVisibleSet", &expandDescendantsInVisibleSetWrapper, ( arg( "script" ), arg( "paths" ), arg( "scene" ), arg( "depth" ) = std::numeric_limits<int>::max() ) );
	def( "setSelectedPaths", &setSelectedPathsWrapper );
	def( "getSelectedPaths", &getSelectedPaths );
	def( "setLastSelectedPath", &setLastSelectedPathWrapper );
	def( "getLastSelectedPath", &getLastSelectedPathWrapper );
	def( "selectedPathsChangedSignal", &selectedPathsChangedSignal, return_value_policy<reference_existing_object>() );
	def( "acquireRenderPassPlug", &acquireRenderPassPlugWrapper, ( arg( "script" ), arg( "createIfMissing" ) = true ) );
	def( "setCurrentRenderPass", &setCurrentRenderPassWrapper );
	def( "getCurrentRenderPass", &getCurrentRenderPassWrapper );
}
