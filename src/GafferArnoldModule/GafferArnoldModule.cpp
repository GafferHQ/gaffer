//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferArnold/ArnoldAOVShader.h"
#include "GafferArnold/ArnoldAtmosphere.h"
#include "GafferArnold/ArnoldAttributes.h"
#include "GafferArnold/ArnoldBackground.h"
#include "GafferArnold/ArnoldCameraShaders.h"
#include "GafferArnold/ArnoldColorManager.h"
#include "GafferArnold/ArnoldDisplacement.h"
#include "GafferArnold/ArnoldLight.h"
#include "GafferArnold/ArnoldMeshLight.h"
#include "GafferArnold/ArnoldOptions.h"
#include "GafferArnold/ArnoldRender.h"
#include "GafferArnold/ArnoldShader.h"
#include "GafferArnold/ArnoldVDB.h"
#include "GafferArnold/ArnoldLightFilter.h"
#include "GafferArnold/InteractiveArnoldRender.h"
#include "GafferArnold/Private/IECoreArnoldPreview/ShaderNetworkAlgo.h"

#include "GafferDispatchBindings/TaskNodeBinding.h"

#include "GafferBindings/DependencyNodeBinding.h"

using namespace boost::python;
using namespace GafferArnold;
using namespace IECoreArnoldPreview;

namespace
{

void loadColorManagerWrapper( ArnoldColorManager &c, const std::string &name, bool keepExistingValues )
{
	IECorePython::ScopedGILRelease gilRelease;
	c.loadColorManager( name, keepExistingValues );
}

class ArnoldColorManagerSerialiser : public GafferBindings::NodeSerialiser
{

	std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, GafferBindings::Serialisation &serialisation ) const override
	{
		std::string result = GafferBindings::NodeSerialiser::postConstructor( graphComponent, identifier, serialisation );

		const std::string name = static_cast<const ArnoldColorManager *>( graphComponent )->getChild<ArnoldShader>( "__shader" )->namePlug()->getValue();
		if( name.size() )
		{
			result += boost::str( boost::format( "\n%s.loadColorManager( \"%s\" )\n" ) % identifier % name );
		}

		return result;
	}

};

void flushCaches( int flags )
{
	IECorePython::ScopedGILRelease gilRelease;
	InteractiveArnoldRender::flushCaches( flags );
}

boost::python::object atNodeToPythonObject( AtNode *node )
{
	if( !node )
	{
		return object();
	}

	object ctypes = import( "ctypes" );
	object arnold = import( "arnold" );

	object atNodeType = arnold.attr( "AtNode" );
	object pointerType = ctypes.attr( "POINTER" )( atNodeType );
	object converted = ctypes.attr( "cast" )( (size_t)node, pointerType );
	return converted;
}

AtNode *atNodeFromPythonObject( object o )
{
	object ctypes = import( "ctypes" );
	object ctypesPointer = ctypes.attr( "POINTER" );
	object arnoldAtNode = import( "arnold" ).attr( "AtNode" );
	object atNodePtrType = ctypesPointer( arnoldAtNode );

	if( !PyObject_IsInstance( o.ptr(), atNodePtrType.ptr() ) )
	{
		PyErr_SetString( PyExc_TypeError, "Expected an AtNode" );
		throw_error_already_set();
	}

	object oContents = o.attr( "contents" );
	object pythonAddress = ctypes.attr( "addressof" )( oContents );
	const size_t address = extract<size_t>( pythonAddress );
	return reinterpret_cast<AtNode *>( address );
}

AtUniverse *pythonObjectToAtUniverse( const boost::python::object &universe )
{
	if( universe.is_none() )
	{
		return nullptr;
	}

	const std::string className = extract<std::string>( universe.attr( "__class__" ).attr( "__name__" ) );
	if( className != "LP_AtUniverse" )
	{
		throw IECore::Exception( boost::str( boost::format( "%1% is not an AtUniverse" ) % className ) );
	}

	object ctypes = import( "ctypes" );
	object address = ctypes.attr( "addressof" )( object( universe.attr( "contents" ) ) );

	return reinterpret_cast<AtUniverse *>( extract<size_t>( address )() );
}

list shaderNetworkAlgoConvert( const IECoreScene::ShaderNetwork *shaderNetwork, object universe, const std::string &name )
{
	std::vector<AtNode *> nodes = ShaderNetworkAlgo::convert( shaderNetwork, pythonObjectToAtUniverse( universe ), name );
	list result;
	for( const auto &n : nodes )
	{
		result.append( atNodeToPythonObject( n ) );
	}
	return result;
}

bool shaderNetworkAlgoUpdate( list pythonNodes, const IECoreScene::ShaderNetwork *shaderNetwork )
{
	std::vector<AtNode *> nodes;
	for( size_t i = 0, l = len( pythonNodes ); i < l; ++i )
	{
		nodes.push_back( atNodeFromPythonObject( pythonNodes[i] ) );
	}

	bool result = ShaderNetworkAlgo::update( nodes, shaderNetwork );

	del( pythonNodes[slice()] );
	for( const auto &n : nodes )
	{
		pythonNodes.append( atNodeToPythonObject( n ) );
	}

	return result;
}

} // namespace

BOOST_PYTHON_MODULE( _GafferArnold )
{

	GafferBindings::DependencyNodeClass<ArnoldShader>();
	GafferBindings::DependencyNodeClass<ArnoldAtmosphere>();
	GafferBindings::DependencyNodeClass<ArnoldBackground>();

	GafferBindings::NodeClass<ArnoldLight>()
		.def( "loadShader", (void (ArnoldLight::*)( const std::string & ) )&ArnoldLight::loadShader )
	;

	GafferBindings::DependencyNodeClass<ArnoldColorManager>()
		.def( "loadColorManager", &loadColorManagerWrapper, ( arg( "name" ), arg( "keepExistingValues" ) = false ) )
	;

	GafferBindings::Serialisation::registerSerialiser( ArnoldColorManager::staticTypeId(), new ArnoldColorManagerSerialiser() );

	GafferBindings::DependencyNodeClass<ArnoldLightFilter>();
	GafferBindings::DependencyNodeClass<ArnoldOptions>();
	GafferBindings::DependencyNodeClass<ArnoldAttributes>();
	GafferBindings::DependencyNodeClass<ArnoldVDB>();
	GafferBindings::DependencyNodeClass<ArnoldDisplacement>();
	GafferBindings::DependencyNodeClass<ArnoldCameraShaders>();
	GafferBindings::DependencyNodeClass<ArnoldMeshLight>();
	GafferBindings::DependencyNodeClass<ArnoldAOVShader>();
	GafferBindings::NodeClass<InteractiveArnoldRender>()
		.def( "flushCaches", &flushCaches )
		.staticmethod( "flushCaches" )
	;
	GafferDispatchBindings::TaskNodeClass<ArnoldRender>();

	object ieCoreArnoldPreviewModule( borrowed( PyImport_AddModule( "GafferArnold.IECoreArnoldPreview" ) ) );
	scope().attr( "IECoreArnoldPreview" ) = ieCoreArnoldPreviewModule;
	scope ieCoreArnoldPreviewScope( ieCoreArnoldPreviewModule );

	object shaderNetworkAlgoModule( borrowed( PyImport_AddModule( "GafferArnold.IECoreArnoldPreview.ShaderNetworkAlgo" ) ) );
	scope().attr( "ShaderNetworkAlgo" ) = shaderNetworkAlgoModule;
	scope shaderNetworkAlgoScope( shaderNetworkAlgoModule );

	def( "convert", &shaderNetworkAlgoConvert );
	def( "update", &shaderNetworkAlgoUpdate );

}
