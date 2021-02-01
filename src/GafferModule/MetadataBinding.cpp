//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "MetadataBinding.h"

#include "GafferBindings/DataBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"

#include "IECorePython/ScopedGILLock.h"

#include "IECore/SimpleTypedData.h"

#include "boost/format.hpp"
#include "boost/python/raw_function.hpp"

using namespace boost::python;
using namespace IECore;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

InternedString g_descriptionName( "description" );

struct PythonValueFunction
{
	PythonValueFunction( object fn )
		:	m_fn( fn )
	{
	}

	ConstDataPtr operator()()
	{
		IECorePython::ScopedGILLock gilLock;
		ConstDataPtr result = extract<ConstDataPtr>( m_fn() );
		return result;
	}

	private :

		object m_fn;

};

struct PythonGraphComponentValueFunction
{
	PythonGraphComponentValueFunction( object fn )
		:	m_fn( fn )
	{
	}

	ConstDataPtr operator()( const GraphComponent *graphComponent )
	{
		IECorePython::ScopedGILLock gilLock;
		ConstDataPtr result = extract<ConstDataPtr>( m_fn( GraphComponentPtr( const_cast<GraphComponent *>( graphComponent ) ) ) );
		return result;
	}

	private :

		object m_fn;

};

struct PythonPlugValueFunction
{
	PythonPlugValueFunction( object fn )
		:	m_fn( fn )
	{
	}

	ConstDataPtr operator()( const Plug *plug )
	{
		IECorePython::ScopedGILLock gilLock;
		ConstDataPtr result = extract<ConstDataPtr>( m_fn( PlugPtr( const_cast<Plug *>( plug ) ) ) );
		return result;
	}

	private :

		object m_fn;

};

ConstDataPtr dedent( InternedString name, IECore::ConstDataPtr data )
{
	if( name != g_descriptionName )
	{
		return data;
	}
	if( const StringData *stringData = runTimeCast<const StringData>( data.get() ) )
	{
		// Perform special processing to strip blank lines from the start and
		// end of descriptions and common indents from all lines. This allows the
		// use of indendented triple-quoted strings for formatting long descriptions.
		object inspect = import( "inspect" );
		object pythonString( stringData->readable() );
		pythonString = inspect.attr( "cleandoc" )( pythonString );
		return new StringData( extract<const char *>( pythonString )() );
	}
	return data;
}

Metadata::ValueFunction objectToValueFunction( InternedString name, object o )
{
	extract<IECore::DataPtr> dataExtractor( o );
	if( dataExtractor.check() )
	{
		ConstDataPtr data = dedent( name, dataExtractor() );
		return [data]{ return data; };
	}
	else
	{
		return PythonValueFunction( o );
	}
}

Metadata::GraphComponentValueFunction objectToGraphComponentValueFunction( InternedString name, object o )
{
	extract<IECore::DataPtr> dataExtractor( o );
	if( dataExtractor.check() )
	{
		ConstDataPtr data = dedent( name, dataExtractor() );
		return [data](const GraphComponent *) { return data; };
	}
	else
	{
		return PythonGraphComponentValueFunction( o );
	}
}

Metadata::PlugValueFunction objectToPlugValueFunction( InternedString name, object o )
{
	extract<IECore::DataPtr> dataExtractor( o );
	if( dataExtractor.check() )
	{
		ConstDataPtr data = dedent( name, dataExtractor() );
		return [data](const Plug *) { return data; };
	}
	else
	{
		return PythonPlugValueFunction( o );
	}
}

void registerValue( IECore::InternedString target, IECore::InternedString key, object &value )
{
	Metadata::registerValue( target, key, objectToValueFunction( key, value ) );
}

object value( IECore::InternedString target, IECore::InternedString key, bool copy )
{
	ConstDataPtr d = Metadata::value( target, key );
	return dataToPython( d.get(), copy );
}

object graphComponentValue( const GraphComponent &graphComponent, IECore::InternedString key, bool instanceOnly, bool copy )
{
	ConstDataPtr d = Metadata::value( &graphComponent, key, instanceOnly );
	return dataToPython( d.get(), copy );
}

void registerNodeValue( IECore::TypeId nodeTypeId, IECore::InternedString key, object &value )
{
	Metadata::registerValue( nodeTypeId, key, objectToGraphComponentValueFunction( key, value ) );
}

object registerNode( tuple args, dict kw )
{
	IECore::TypeId nodeTypeId = extract<IECore::TypeId>( args[0] );

	for( size_t i = 1, e = len( args ); i < e; i += 2 )
	{
		IECore::InternedString name = extract<IECore::InternedString>( args[i] )();
		Metadata::registerValue( nodeTypeId, name, objectToGraphComponentValueFunction( name, args[i+1] ) );
	}

	object plugsObject = kw.get( "plugs" );
	if( plugsObject )
	{
		dict plugs = extract<dict>( plugsObject )();
		list plugsItems = plugs.items();
		for( size_t i = 0, e = len( plugsItems ); i < e; ++i )
		{
			StringAlgo::MatchPattern plugPath = extract<StringAlgo::MatchPattern>( plugsItems[i][0] )();
			object plugValues = plugsItems[i][1];
			for( size_t vi = 0, ve = len( plugValues ); vi < ve; vi += 2 )
			{
				InternedString name = extract<InternedString>( plugValues[vi] );
				Metadata::registerValue(
					nodeTypeId,
					plugPath,
					name,
					objectToPlugValueFunction( name, plugValues[vi+1] )
				);
			}
		}
	}

	return object(); // none
}

void registerPlugValue( IECore::TypeId nodeTypeId, const char *plugPath, IECore::InternedString key, object &value )
{
	Metadata::registerValue( nodeTypeId, plugPath, key, objectToPlugValueFunction( key, value ) );
}

struct ValueChangedSlotCaller
{

	boost::signals::detail::unusable operator()( boost::python::object slot, IECore::InternedString target, IECore::InternedString key )
	{
		slot( target.c_str(), key.c_str() );
		return boost::signals::detail::unusable();
	}

	boost::signals::detail::unusable operator()( boost::python::object slot, Node *node, IECore::InternedString key, Metadata::ValueChangedReason reason )
	{
		slot( NodePtr( node ), key.c_str(), reason );
		return boost::signals::detail::unusable();
	}

	boost::signals::detail::unusable operator()( boost::python::object slot, Plug *plug, IECore::InternedString key, Metadata::ValueChangedReason reason )
	{
		slot( PlugPtr( plug ), key.c_str(), reason );
		return boost::signals::detail::unusable();
	}

	boost::signals::detail::unusable operator()( boost::python::object slot, IECore::TypeId nodeTypeId, IECore::InternedString key, Node *node )
	{
		slot( nodeTypeId, key.c_str(), NodePtr( node ) );
		return boost::signals::detail::unusable();
	}

	boost::signals::detail::unusable operator()( boost::python::object slot, IECore::TypeId nodeTypeId, const StringAlgo::MatchPattern &plugPath, IECore::InternedString key, Plug *plug )
	{
		slot( nodeTypeId, plugPath.c_str(), key.c_str(), PlugPtr( plug ) );
		return boost::signals::detail::unusable();
	}

};

void registerInstanceValue( GraphComponent &instance, InternedString key, ConstDataPtr value, bool persistent )
{
	IECorePython::ScopedGILRelease gilRelease;
	Metadata::registerValue( &instance, key, value, persistent );
}

void deregisterInstanceValue( GraphComponent &target, IECore::InternedString key )
{
	IECorePython::ScopedGILRelease gilRelease;
	Metadata::deregisterValue( &target, key );
}

list keysToList( const std::vector<InternedString> &keys )
{
	list result;
	for( std::vector<InternedString>::const_iterator it = keys.begin(); it != keys.end(); ++it )
	{
		result.append( it->c_str() );
	}

	return result;
}

list registeredValues( IECore::InternedString target )
{
	std::vector<InternedString> keys;
	Metadata::registeredValues( target, keys );
	return keysToList( keys );
}

list registeredGraphComponentValues( const GraphComponent *target, bool instanceOnly, bool persistentOnly )
{
	std::vector<InternedString> keys;
	Metadata::registeredValues( target, keys, instanceOnly, persistentOnly );
	return keysToList( keys );
}

list plugsWithMetadata( GraphComponent *root, const std::string &key, bool instanceOnly )
{
	std::vector<Plug*> plugs = Metadata::plugsWithMetadata( root, key, instanceOnly );
	list result;
	for( std::vector<Plug*>::const_iterator it = plugs.begin(); it != plugs.end(); ++it )
	{
		result.append( PlugPtr(*it) );
	}

	return result;
}

list nodesWithMetadata( GraphComponent *root, const std::string &key, bool instanceOnly )
{
	std::vector<Node*> nodes = Metadata::nodesWithMetadata( root, key, instanceOnly );
	list result;
	for( std::vector<Node*>::const_iterator it = nodes.begin(); it != nodes.end(); ++it )
	{
		result.append( NodePtr(*it) );
	}

	return result;
}

} // namespace

void GafferModule::bindMetadata()
{
	scope s = class_<Metadata>( "Metadata", no_init )

		.def( "registerValue", &registerValue )
		.def( "registerValue", &registerNodeValue )
		.def( "registerValue", &registerPlugValue )
		.def( "registerValue", &registerInstanceValue,
			(
				boost::python::arg( "target" ),
				boost::python::arg( "value" ),
				boost::python::arg( "persistent" ) = true
			)
		)
		.staticmethod( "registerValue" )

		.def( "registeredValues", &registeredValues )
		.def( "registeredValues", &registeredGraphComponentValues,
			(
				boost::python::arg( "target" ),
				boost::python::arg( "instanceOnly" ) = false,
				boost::python::arg( "persistentOnly" ) = false
			)
		)
		.staticmethod( "registeredValues" )

		.def( "value", &value,
			(
				boost::python::arg( "target" ),
				boost::python::arg( "key" ),
				boost::python::arg( "_copy" ) = true
			)
		)
		.def( "value", &graphComponentValue,
			(
				boost::python::arg( "target" ),
				boost::python::arg( "key" ),
				boost::python::arg( "instanceOnly" ) = false,
				boost::python::arg( "_copy" ) = true
			)
		)
		.staticmethod( "value" )

		.def( "deregisterValue", (void (*)( IECore::InternedString, IECore::InternedString ) )&Metadata::deregisterValue )
		.def( "deregisterValue", (void (*)( IECore::TypeId, IECore::InternedString ) )&Metadata::deregisterValue )
		.def( "deregisterValue", (void (*)( IECore::TypeId, const StringAlgo::MatchPattern &, IECore::InternedString ) )&Metadata::deregisterValue )
		.def( "deregisterValue", &deregisterInstanceValue )
		.staticmethod( "deregisterValue" )

		.def( "registerNode", boost::python::raw_function( &registerNode, 1 ) )
		.staticmethod( "registerNode" )

		.def( "valueChangedSignal", &Metadata::valueChangedSignal, return_value_policy<reference_existing_object>() )
		.staticmethod( "valueChangedSignal" )

		.def( "nodeValueChangedSignal", (Metadata::NodeValueChangedSignal &(*)() )&Metadata::nodeValueChangedSignal, return_value_policy<reference_existing_object>() )
		.def( "nodeValueChangedSignal", (Metadata::NodeValueChangedSignal2 &(*)( Gaffer::Node * ) )&Metadata::nodeValueChangedSignal, return_value_policy<reference_existing_object>() )
		.staticmethod( "nodeValueChangedSignal" )

		.def( "plugValueChangedSignal", (Metadata::PlugValueChangedSignal &(*)() )&Metadata::plugValueChangedSignal, return_value_policy<reference_existing_object>() )
		.def( "plugValueChangedSignal", (Metadata::PlugValueChangedSignal2 &(*)( Gaffer::Node * ) )&Metadata::plugValueChangedSignal, return_value_policy<reference_existing_object>() )
		.staticmethod( "plugValueChangedSignal" )

		.def( "plugsWithMetadata", &plugsWithMetadata,
			(
				boost::python::arg( "root" ),
				boost::python::arg( "key" ),
				boost::python::arg( "instanceOnly" ) = false
			)
		)
		.staticmethod( "plugsWithMetadata" )

		.def( "nodesWithMetadata", &nodesWithMetadata,
			(
				boost::python::arg( "root" ),
				boost::python::arg( "key" ),
				boost::python::arg( "instanceOnly" ) = false
			)
		)
		.staticmethod( "nodesWithMetadata" )
	;

	enum_<Metadata::ValueChangedReason>( "ValueChangedReason" )
		.value( "StaticRegistration", Metadata::ValueChangedReason::StaticRegistration )
		.value( "StaticDeregistration", Metadata::ValueChangedReason::StaticDeregistration )
		.value( "InstanceRegistration", Metadata::ValueChangedReason::InstanceRegistration )
		.value( "InstanceDeregistration", Metadata::ValueChangedReason::InstanceDeregistration )
	;

	SignalClass<Metadata::ValueChangedSignal, DefaultSignalCaller<Metadata::ValueChangedSignal>, ValueChangedSlotCaller>( "ValueChangedSignal" );
	SignalClass<Metadata::NodeValueChangedSignal2, DefaultSignalCaller<Metadata::NodeValueChangedSignal2>, ValueChangedSlotCaller>( "NodeValueChangedSignal2" );
	SignalClass<Metadata::PlugValueChangedSignal2, DefaultSignalCaller<Metadata::PlugValueChangedSignal2>, ValueChangedSlotCaller>( "PlugValueChangedSignal2" );
	SignalClass<Metadata::NodeValueChangedSignal, DefaultSignalCaller<Metadata::NodeValueChangedSignal>, ValueChangedSlotCaller>( "NodeValueChangedSignal" );
	SignalClass<Metadata::PlugValueChangedSignal, DefaultSignalCaller<Metadata::PlugValueChangedSignal>, ValueChangedSlotCaller>( "PlugValueChangedSignal" );

}
