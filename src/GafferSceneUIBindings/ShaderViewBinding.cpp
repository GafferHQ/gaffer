//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Reference.h"
#include "Gaffer/ScriptNode.h"

#include "GafferBindings/NodeBinding.h"
#include "GafferBindings/ExceptionAlgo.h"
#include "GafferBindings/SignalBinding.h"

#include "GafferSceneUI/ShaderView.h"
#include "GafferSceneUIBindings/ShaderViewBinding.h"

using namespace std;
using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferSceneUI;

namespace
{

struct CreatorWrapper
{

	CreatorWrapper( object fn )
		:	m_fn( fn )
	{
	}

	NodePtr operator()()
	{
		ScopedGILLock gilLock;
		NodePtr result = extract<NodePtr>( m_fn() );
		return result;
	}

	private :

		object m_fn;

};

// Utility class for loading custom shader scenes from
// reference files. Ideally we would be doing this directly
// in ShaderView.cpp, but we can't because we can only do
// serialisation/loading with python, and libGaffer.so does
// not have a python dependency. Ideally I think we'd make
// it so that Serialiser was in libGaffer.so, but stubbed out,
// and when libGafferBindings.so was loaded it would insert the
// implementation. This would allow `Reference::load()` to use
// the Serialiser directly, making it independent of ScriptNode
// (it needs ScriptNode because this is currently the only access
// to serialisation in libGaffer.so).
struct ReferenceCreator
{

	ReferenceCreator( const std::string &referenceFileName )
		:	m_referenceFileName( referenceFileName )
	{
	}

	NodePtr operator()()
	{
		ScopedGILLock gilLock;
		object gafferModule = import( "Gaffer" );
		ScriptNodePtr script = extract<ScriptNodePtr>( gafferModule.attr( "ScriptNode" )() );

		ReferencePtr reference = new Reference;
		script->addChild( reference );

		reference->load( m_referenceFileName );

		return reference;
	}

	private :

		std::string m_referenceFileName;

};

void registerRenderer( const std::string &shaderPrefix, object creator )
{
	ShaderView::registerRenderer( shaderPrefix, CreatorWrapper( creator ) );
}

void registerScene( const std::string &shaderPrefix, const std::string &name, object creator )
{
	ShaderView::registerScene( shaderPrefix, name, CreatorWrapper( creator ) );
}

void registerReferenceScene( const std::string &shaderPrefix, const std::string &name, const std::string &referenceFileName )
{
	ShaderView::registerScene( shaderPrefix, name, ReferenceCreator( referenceFileName ) );
}

boost::python::list registeredScenes( const IECore::InternedString &shaderPrefix )
{
	vector<string> n;
	ShaderView::registeredScenes( shaderPrefix, n );
	boost::python::list result;
	for( vector<string>::const_iterator it = n.begin(), eIt = n.end(); it != eIt; ++it )
	{
		result.append( *it );
	}

	return result;
}

struct SceneChangedSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, ShaderViewPtr v )
	{
		try
		{
			slot( v );
			return boost::signals::detail::unusable();
		}
		catch( const boost::python::error_already_set &e )
		{
			ExceptionAlgo::translatePythonException();
		}
		return boost::signals::detail::unusable();
	}
};

} // namespace

void GafferSceneUIBindings::bindShaderView()
{

	GafferBindings::NodeClass<ShaderView>()
		.def( "shaderPrefix", &ShaderView::shaderPrefix )
		.def( "scene", (Gaffer::Node *(ShaderView::*)())&ShaderView::scene, return_value_policy<CastToIntrusivePtr>() )
		.def( "sceneChangedSignal", &ShaderView::sceneChangedSignal, return_internal_reference<1>() )
		.def( "registerRenderer", &registerRenderer )
		.staticmethod( "registerRenderer" )
		.def( "registerScene", &registerScene )
		.def( "registerScene", &registerReferenceScene )
		.staticmethod( "registerScene" )
		.def( "registeredScenes", &registeredScenes )
		.staticmethod( "registeredScenes" )
	;

	SignalClass<ShaderView::SceneChangedSignal, DefaultSignalCaller<ShaderView::SceneChangedSignal>, SceneChangedSlotCaller>( "SceneChangedSignal" );

}
