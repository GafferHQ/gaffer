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

#include "IECoreArnold/NodeAlgo.h"
#include "IECoreArnold/ParameterAlgo.h"
#include "IECoreArnold/ShaderNetworkAlgo.h"
#include "IECoreArnold/UniverseBlock.h"

#include "boost/python/suite/indexing/container_utils.hpp"

#include "fmt/format.h"

using namespace boost::python;
using namespace IECoreArnold;

namespace
{

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
		throw IECore::Exception( fmt::format( "{} is not an AtUniverse", className ) );
	}

	object ctypes = import( "ctypes" );
	object address = ctypes.attr( "addressof" )( object( universe.attr( "contents" ) ) );

	return reinterpret_cast<AtUniverse *>( extract<size_t>( address )() );
}

object universeWrapper( UniverseBlock &universeBlock )
{
	AtUniverse *universe = universeBlock.universe();
	if( universe )
	{
		object arnold = import( "arnold" );
		object ctypes = import( "ctypes" );
		return ctypes.attr( "cast" )(
			(uint64_t)universeBlock.universe(),
			ctypes.attr( "POINTER" )( object( arnold.attr( "AtUniverse" ) ) )
		);
	}
	else
	{
		// Default universe, represented as `None` in Python.
		return object();
	}
}

object convertWrapper( const IECore::Object *object, boost::python::object universe, const std::string &nodeName )
{
	return atNodeToPythonObject( NodeAlgo::convert( object, pythonObjectToAtUniverse( universe ), nodeName, nullptr ) );
}

object convertWrapper2( object pythonSamples, float motionStart, float motionEnd, boost::python::object universe, const std::string &nodeName )
{
	std::vector<const IECore::Object *> samples;
	container_utils::extend_container( samples, pythonSamples );

	return atNodeToPythonObject( NodeAlgo::convert( samples, motionStart, motionEnd, pythonObjectToAtUniverse( universe ), nodeName, nullptr ) );
}

void setParameter( object &pythonNode, const char *name, const IECore::Data *data, const std::string &messageContext )
{
	AtNode *node = atNodeFromPythonObject( pythonNode );
	ParameterAlgo::setParameter( node, name, data, messageContext );
}

IECore::DataPtr getParameter( object &pythonNode, const char *name )
{
	AtNode *node = atNodeFromPythonObject( pythonNode );
	return ParameterAlgo::getParameter( node, name );
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

BOOST_PYTHON_MODULE( _IECoreArnold )
{

	// This is bound with a preceding _ and then turned into a context
	// manager for the "with" statement in IECoreArnold/UniverseBlock.py
	class_<UniverseBlock, boost::noncopyable>( "_UniverseBlock", init<bool>( ( arg( "writable" ) ) ) )
		.def( "universe", &universeWrapper )
	;

	{
		object nodeAlgoModule( handle<>( borrowed( PyImport_AddModule( "IECoreArnold.NodeAlgo" ) ) ) );
		scope().attr( "NodeAlgo" ) = nodeAlgoModule;
		scope nodeAlgoModuleScope( nodeAlgoModule );

		def( "convert", &convertWrapper );
		def( "convert", &convertWrapper2 );
	}

	{
		object parameterAlgoModule( handle<>( borrowed( PyImport_AddModule( "IECoreArnold.ParameterAlgo" ) ) ) );
		scope().attr( "ParameterAlgo" ) = parameterAlgoModule;
		scope parameterAlgoModuleScope( parameterAlgoModule );

		def( "setParameter", &setParameter, ( arg( "node" ), arg( "name" ), arg( "data" ), arg( "messageContext" ) = "ParameterAlgo::setParameter" ) );
		def( "getParameter", &getParameter );
	}

	{
		object shaderNetworkAlgoModule( borrowed( PyImport_AddModule( "IECoreArnold.ShaderNetworkAlgo" ) ) );
		scope().attr( "ShaderNetworkAlgo" ) = shaderNetworkAlgoModule;
		scope shaderNetworkAlgoScope( shaderNetworkAlgoModule );

		def( "convert", &shaderNetworkAlgoConvert );
		def( "update", &shaderNetworkAlgoUpdate );
		def( "convertUSDShaders", &ShaderNetworkAlgo::convertUSDShaders );
	}

}
