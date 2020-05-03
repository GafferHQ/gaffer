//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#include "SceneAlgoBinding.h"

#include "GafferScene/Filter.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/ShaderTweaks.h"

#include "GafferImage/ImagePlug.h"

#include "IECoreScene/Camera.h"

#include "IECorePython/RefCountedBinding.h"
#include "IECorePython/ScopedGILRelease.h"

#include "boost/python/suite/indexing/container_utils.hpp"
#include "boost/python/suite/indexing/vector_indexing_suite.hpp"

using namespace boost::python;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

bool existsWrapper( const ScenePlug *scene, const ScenePlug::ScenePath &path )
{
	// gil release in case the scene traversal dips back into python:
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::exists( scene, path );
}

bool visibleWrapper( const ScenePlug *scene, const ScenePlug::ScenePath &path )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::visible( scene, path );
}

object filteredNodesWrapper( Filter &filter )
{
	const auto nodes = SceneAlgo::filteredNodes( &filter );
	list nodesList;
	for( const auto &n : nodes )
	{
		nodesList.append( FilteredSceneProcessorPtr( n ) );
	}

	PyObject *nodesSet = PySet_New( nodesList.ptr() );
	return object( handle<>( nodesSet ) );
}

void matchingPathsWrapper1( const Filter *filter, const ScenePlug *scene, PathMatcher &paths )
{
	// gil release in case the scene traversal dips back into python:
	IECorePython::ScopedGILRelease r;
	SceneAlgo::matchingPaths( filter, scene, paths );
}

void matchingPathsWrapper2( const Gaffer::IntPlug *filterPlug, const ScenePlug *scene, PathMatcher &paths )
{
	// gil release in case the scene traversal dips back into python:
	IECorePython::ScopedGILRelease r;
	SceneAlgo::matchingPaths( filterPlug, scene, paths );
}

void matchingPathsWrapper3( const PathMatcher &filter, const ScenePlug *scene, PathMatcher &paths )
{
	// gil release in case the scene traversal dips back into python:
	IECorePython::ScopedGILRelease r;
	SceneAlgo::matchingPaths( filter, scene, paths );
}

Imath::V2f shutterWrapper( const IECore::CompoundObject *globals, const ScenePlug *scene )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::shutter( globals, scene );
}

bool setExistsWrapper( const ScenePlug *scene, const IECore::InternedString &setName )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::setExists( scene, setName );
}

IECore::CompoundDataPtr setsWrapper1( const ScenePlug *scene, bool copy )
{
	IECorePython::ScopedGILRelease r;
	IECore::ConstCompoundDataPtr result = SceneAlgo::sets( scene );
	return copy ? result->copy() : boost::const_pointer_cast<IECore::CompoundData>( result );
}

IECore::CompoundDataPtr setsWrapper2( const ScenePlug *scene, object pythonSetNames, bool copy )
{
	std::vector<IECore::InternedString> setNames;
	boost::python::container_utils::extend_container( setNames, pythonSetNames );

	IECorePython::ScopedGILRelease r;
	IECore::ConstCompoundDataPtr result = SceneAlgo::sets( scene, setNames );
	return copy ? result->copy() : boost::const_pointer_cast<IECore::CompoundData>( result );
}

ScenePlugPtr historyGetScene( SceneAlgo::History &h )
{
	return h.scene;
}

void historySetScene( SceneAlgo::History &h, const ScenePlugPtr &s )
{
	h.scene = s;
}

Gaffer::ContextPtr historyGetContext( SceneAlgo::History &h )
{
	return h.context;
}

void historySetContext( SceneAlgo::History &h, const Gaffer::ContextPtr &c )
{
	h.context = c;
}

SceneAlgo::History::Ptr historyWrapper( const ValuePlug &scenePlugChild, const ScenePlug::ScenePath &path )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::history( &scenePlugChild, path );
}

std::string attributeHistoryGetAttributeName( const SceneAlgo::AttributeHistory &h )
{
	return h.attributeName.string();
}

void attributeHistorySetAttributeName( SceneAlgo::AttributeHistory &h, IECore::InternedString n )
{
	h.attributeName = n;
}

ObjectPtr attributeHistoryGetAttributeValue( const SceneAlgo::AttributeHistory &h )
{
	// Returning a copy because `attributeValue` is const, and owned by Gaffer's cache.
	// Allowing modification in Python would be catastrophic and hard to debug.
	return h.attributeValue ? h.attributeValue->copy() : nullptr;
}

void attributeHistorySetAttributeValue( SceneAlgo::AttributeHistory &h, ConstObjectPtr v )
{
	h.attributeValue = v;
}

SceneAlgo::AttributeHistory::Ptr attributeHistoryWrapper( const SceneAlgo::History &attributesHistory, const InternedString &attributeName )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::attributeHistory( &attributesHistory, attributeName );
}

ScenePlugPtr sourceWrapper( const ScenePlug &scene, const ScenePlug::ScenePath &path )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::source( &scene, path );
}

SceneProcessorPtr objectTweaksWrapper( const ScenePlug &scene, const ScenePlug::ScenePath &path )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::objectTweaks( &scene, path );
}

ShaderTweaksPtr shaderTweaksWrapper( const ScenePlug &scene, const ScenePlug::ScenePath &path, const InternedString &attributeName )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::shaderTweaks( &scene, path, attributeName );
}

std::string sourceSceneNameWrapper( const GafferImage::ImagePlug &image )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::sourceSceneName( &image );
}

ScenePlugPtr sourceSceneWrapper( GafferImage::ImagePlug &image )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::sourceScene( &image );
}

} // namespace

namespace GafferSceneModule
{

void bindSceneAlgo()
{
	object module( borrowed( PyImport_AddModule( "GafferScene.SceneAlgo" ) ) );
	scope().attr( "SceneAlgo" ) = module;
	scope moduleScope( module );

	def( "exists", &existsWrapper );
	def( "visible", visibleWrapper );

	def( "filteredNodes", &filteredNodesWrapper );
	def( "matchingPaths", &matchingPathsWrapper1 );
	def( "matchingPaths", &matchingPathsWrapper2 );
	def( "matchingPaths", &matchingPathsWrapper3 );
	def( "shutter", &shutterWrapper );
	def( "setExists", &setExistsWrapper );
	def(
		"sets",
		&setsWrapper1,
		( arg( "scene" ), arg( "_copy" ) = true )
	);
	def(
		"sets",
		&setsWrapper2,
		( arg( "scene" ), arg( "setNames" ), arg( "_copy" ) = true )
	);

	// History

	{
		scope s = IECorePython::RefCountedClass<SceneAlgo::History, IECore::RefCounted>( "History" )
			.def( init<>() )
			.def( init<ScenePlugPtr, Gaffer::ContextPtr>() )
			.add_property( "scene", &historyGetScene, &historySetScene )
			.add_property( "context", &historyGetContext, &historySetContext )
			.def_readonly( "predecessors", &SceneAlgo::History::predecessors )
		;

		class_<SceneAlgo::History::Predecessors>( "Predecessors" )
			.def( vector_indexing_suite<SceneAlgo::History::Predecessors, true>() )
		;
	}

	def( "history", &historyWrapper );

	IECorePython::RefCountedClass<SceneAlgo::AttributeHistory, SceneAlgo::History>( "AttributeHistory" )
		.add_property( "attributeName", &attributeHistoryGetAttributeName, &attributeHistorySetAttributeName )
		.add_property( "attributeValue", &attributeHistoryGetAttributeValue, &attributeHistorySetAttributeValue )
	;

	def( "attributeHistory", &attributeHistoryWrapper );

	def( "source", &sourceWrapper );
	def( "objectTweaks", &objectTweaksWrapper );
	def( "shaderTweaks", &shaderTweaksWrapper );
	def( "sourceSceneName", &sourceSceneNameWrapper );
	def( "sourceScene", &sourceSceneWrapper );

}

} // namespace GafferSceneModule
