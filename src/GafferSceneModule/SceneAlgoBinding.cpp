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
#include "IECorePython/ScopedGILLock.h"
#include "IECorePython/ScopedGILRelease.h"

#include "boost/python/suite/indexing/container_utils.hpp"
#include "boost/python/suite/indexing/vector_indexing_suite.hpp"

using namespace boost::python;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

bool existsWrapper( const ScenePlug &scene, const ScenePlug::ScenePath &path )
{
	// gil release in case the scene traversal dips back into python:
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::exists( &scene, path );
}

bool visibleWrapper( const ScenePlug &scene, const ScenePlug::ScenePath &path )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::visible( &scene, path );
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

void matchingPathsWrapper1( const Filter &filter, const ScenePlug &scene, PathMatcher &paths )
{
	// gil release in case the scene traversal dips back into python:
	IECorePython::ScopedGILRelease r;
	SceneAlgo::matchingPaths( &filter, &scene, paths );
}

void matchingPathsWrapper2( const FilterPlug &filterPlug, const ScenePlug &scene, PathMatcher &paths )
{
	// gil release in case the scene traversal dips back into python:
	IECorePython::ScopedGILRelease r;
	SceneAlgo::matchingPaths( &filterPlug, &scene, paths );
}

void matchingPathsWrapper3( const FilterPlug &filterPlug, const ScenePlug &scene, const ScenePlug::ScenePath &root, PathMatcher &paths )
{
	// gil release in case the scene traversal dips back into python:
	IECorePython::ScopedGILRelease r;
	SceneAlgo::matchingPaths( &filterPlug, &scene, root, paths );
}

void matchingPathsWrapper4( const PathMatcher &filter, const ScenePlug &scene, PathMatcher &paths )
{
	// gil release in case the scene traversal dips back into python:
	IECorePython::ScopedGILRelease r;
	SceneAlgo::matchingPaths( filter, &scene, paths );
}

IECore::MurmurHash matchingPathsHashWrapper1( const GafferScene::FilterPlug &filterPlug, const ScenePlug &scene, const ScenePlug::ScenePath &root )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::matchingPathsHash( &filterPlug, &scene, root );
}

IECore::MurmurHash matchingPathsHashWrapper2( const IECore::PathMatcher &filter, const ScenePlug &scene )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::matchingPathsHash( filter, &scene );
}

IECore::PathMatcher findAllWrapper( const ScenePlug &scene, object predicate, const ScenePlug::ScenePath &root )
{
	IECorePython::ScopedGILRelease gilRelease;
	return SceneAlgo::findAll(
		&scene,
		[&] ( ConstScenePlugPtr scene, const ScenePlug::ScenePath &path ) {
			const std::string pathString = ScenePlug::pathToString( path );
			IECorePython::ScopedGILLock gilLock;
			return predicate( boost::const_pointer_cast<ScenePlug>( scene ), pathString );
		},
		root
	);
}

IECore::PathMatcher findAllWithAttributeWrapper( const ScenePlug &scene, InternedString name, const Object *value, const ScenePlug::ScenePath &root )
{
	IECorePython::ScopedGILRelease gilRelease;
	return SceneAlgo::findAllWithAttribute( &scene, name, value, root );
}

Imath::V2f shutterWrapper( const IECore::CompoundObject &globals, const ScenePlug &scene )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::shutter( &globals, &scene );
}

bool setExistsWrapper( const ScenePlug &scene, const IECore::InternedString &setName )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::setExists( &scene, setName );
}

IECore::CompoundDataPtr setsWrapper1( const ScenePlug &scene, bool copy )
{
	IECorePython::ScopedGILRelease r;
	IECore::ConstCompoundDataPtr result = SceneAlgo::sets( &scene );
	return copy ? result->copy() : boost::const_pointer_cast<IECore::CompoundData>( result );
}

IECore::CompoundDataPtr setsWrapper2( const ScenePlug &scene, object pythonSetNames, bool copy )
{
	std::vector<IECore::InternedString> setNames;
	boost::python::container_utils::extend_container( setNames, pythonSetNames );

	IECorePython::ScopedGILRelease r;
	IECore::ConstCompoundDataPtr result = SceneAlgo::sets( &scene, setNames );
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

SceneAlgo::History::Ptr historyWrapper2( const ValuePlug &scenePlugChild )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::history( &scenePlugChild );
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

std::string optionHistoryGetOptionName( const SceneAlgo::OptionHistory &h )
{
	return h.optionName.string();
}

void optionHistorySetOptionName( SceneAlgo::OptionHistory &h, IECore::InternedString n )
{
	h.optionName = n;
}

ObjectPtr optionHistoryGetOptionValue( const SceneAlgo::OptionHistory &h )
{
	// Returning a copy because `optionValue` is const, and owned by Gaffer's cache.
	// Allowing modification in Python would be catastrophic and hard to debug.
	return h.optionValue ? h.optionValue->copy() : nullptr;
}

void optionHistorySetOptionValue( SceneAlgo::OptionHistory &h, ConstObjectPtr v )
{
	h.optionValue = v;
}

SceneAlgo::OptionHistory::Ptr optionHistoryWrapper( const SceneAlgo::History &globalsHistory, const InternedString &optionName )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::optionHistory( &globalsHistory, optionName );
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

IECore::PathMatcher linkedObjectsWrapper1( const GafferScene::ScenePlug &scene, const ScenePlug::ScenePath &light )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::linkedObjects( &scene, light );
}

IECore::PathMatcher linkedObjectsWrapper2( const GafferScene::ScenePlug &scene, const IECore::PathMatcher &lights )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::linkedObjects( &scene, lights );
}

IECore::PathMatcher linkedLightsWrapper1( const GafferScene::ScenePlug &scene, const ScenePlug::ScenePath &object )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::linkedLights( &scene, object );
}

IECore::PathMatcher linkedLightsWrapper2( const GafferScene::ScenePlug &scene, const IECore::PathMatcher &objects )
{
	IECorePython::ScopedGILRelease r;
	return SceneAlgo::linkedLights( &scene, objects );
}

struct RenderAdaptorWrapper
{

	RenderAdaptorWrapper( object pythonAdaptor )
		:   m_pythonAdaptor( pythonAdaptor )
	{
	}

	SceneProcessorPtr operator()()
	{
		IECorePython::ScopedGILLock gilLock;
		SceneProcessorPtr result = extract<SceneProcessorPtr>( m_pythonAdaptor() );
		return result;
	}

	private :

		object m_pythonAdaptor;

};

void registerRenderAdaptorWrapper( const std::string &name, object adaptor )
{
	SceneAlgo::registerRenderAdaptor( name, RenderAdaptorWrapper( adaptor ) );
}

void applyCameraGlobalsWrapper( IECoreScene::Camera &camera, const IECore::CompoundObject &globals, const ScenePlug &scene )
{
	IECorePython::ScopedGILRelease gilRelease;
	SceneAlgo::applyCameraGlobals( &camera, &globals, &scene );
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
	def( "validateName", &SceneAlgo::validateName );

	def( "filteredNodes", &filteredNodesWrapper );
	def( "matchingPaths", &matchingPathsWrapper1 );
	def( "matchingPaths", &matchingPathsWrapper2 );
	def( "matchingPaths", &matchingPathsWrapper3 );
	def( "matchingPaths", &matchingPathsWrapper4 );
	def( "matchingPathsHash", &matchingPathsHashWrapper1, ( arg( "filter" ), arg( "scene" ), arg( "root" ) = "/" ) );
	def( "matchingPathsHash", &matchingPathsHashWrapper2, ( arg( "filter" ), arg( "scene" ) ) );

	def( "findAll", &findAllWrapper, ( arg( "scene" ), arg( "predicate" ), arg( "root" ) = "/" ) );
	def( "findAllWithAttribute", &findAllWithAttributeWrapper, ( arg( "scene" ), arg( "name" ), arg( "value" ) = object(), arg( "root" ) = "/" ) );

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
	def( "history", &historyWrapper2 );

	IECorePython::RefCountedClass<SceneAlgo::AttributeHistory, SceneAlgo::History>( "AttributeHistory" )
		.add_property( "attributeName", &attributeHistoryGetAttributeName, &attributeHistorySetAttributeName )
		.add_property( "attributeValue", &attributeHistoryGetAttributeValue, &attributeHistorySetAttributeValue )
	;

	def( "attributeHistory", &attributeHistoryWrapper );

	IECorePython::RefCountedClass<SceneAlgo::OptionHistory, SceneAlgo::History>( "OptionHistory" )
		.add_property( "optionName", &optionHistoryGetOptionName, &optionHistorySetOptionName )
		.add_property( "optionValue", &optionHistoryGetOptionValue, &optionHistorySetOptionValue )
	;

	def( "optionHistory", &optionHistoryWrapper );

	def( "source", &sourceWrapper );
	def( "objectTweaks", &objectTweaksWrapper );
	def( "shaderTweaks", &shaderTweaksWrapper );

	// Render metadata

	def( "sourceSceneName", &sourceSceneNameWrapper );
	def( "sourceScene", &sourceSceneWrapper );

	// Light linking

	def( "linkedObjects", &linkedObjectsWrapper1 );
	def( "linkedObjects", &linkedObjectsWrapper2 );
	def( "linkedLights", &linkedLightsWrapper1 );
	def( "linkedLights", &linkedLightsWrapper2 );

	// Render adaptors

	def( "registerRenderAdaptor", &registerRenderAdaptorWrapper );
	def( "deregisterRenderAdaptor", &SceneAlgo::deregisterRenderAdaptor );
	def( "createRenderAdaptors", &SceneAlgo::createRenderAdaptors );

	// Camera globals

	def( "applyCameraGlobals", &applyCameraGlobalsWrapper );

}

} // namespace GafferSceneModule
