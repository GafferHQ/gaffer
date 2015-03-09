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
#include "boost/python/raw_function.hpp"
#include "boost/lambda/lambda.hpp"
#include "boost/format.hpp"

#include "IECorePython/ScopedGILLock.h"

#include "Gaffer/Plug.h"
#include "Gaffer/Node.h"
#include "Gaffer/Metadata.h"

#include "GafferBindings/MetadataBinding.h"
#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/DataBinding.h"

using namespace boost::python;
using namespace IECore;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

InternedString g_descriptionName( "description" );

struct PythonNodeValueFunction
{
	PythonNodeValueFunction( object fn )
		:	m_fn( fn )
	{
	}

	ConstDataPtr operator()( const Node *node )
	{
		IECorePython::ScopedGILLock gilLock;
		ConstDataPtr result = extract<ConstDataPtr>( m_fn( NodePtr( const_cast<Node *>( node ) ) ) );
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

Metadata::NodeValueFunction objectToNodeValueFunction( InternedString name, object o )
{
	extract<IECore::DataPtr> dataExtractor( o );
	if( dataExtractor.check() )
	{
		return boost::lambda::constant( dedent( name, dataExtractor() ) );
	}
	else
	{
		return PythonNodeValueFunction( o );
	}
}

Metadata::PlugValueFunction objectToPlugValueFunction( InternedString name, object o )
{
	extract<IECore::DataPtr> dataExtractor( o );
	if( dataExtractor.check() )
	{
		return boost::lambda::constant( dedent( name, dataExtractor() ) );
	}
	else
	{
		return PythonPlugValueFunction( o );
	}
}

void registerNodeValue( IECore::TypeId nodeTypeId, IECore::InternedString key, object &value )
{
	Metadata::registerNodeValue( nodeTypeId, key, objectToNodeValueFunction( key, value ) );
}

object nodeValue( const Node *node, const char *key, bool inherit, bool instanceOnly, bool copy )
{
	ConstDataPtr d = Metadata::nodeValue<Data>( node, key, inherit, instanceOnly );
	return dataToPython( d.get(), copy );
}

object registerNodeDescription( tuple args, dict kw )
{
	IECore::TypeId nodeTypeId = extract<IECore::TypeId>( args[0] );
	Metadata::registerNodeDescription( nodeTypeId, objectToNodeValueFunction( g_descriptionName, args[1] ) );

	for( size_t i = 2, e = len( args ); i < e; i += 2 )
	{
		MatchPattern plugPath = extract<MatchPattern>( args[i] )();
		extract<dict> dictExtractor( args[i+1] );
		if( dictExtractor.check() )
		{
			list dictItems = dictExtractor().items();
			for( size_t di = 0, de = len( dictItems ); di < de; ++di )
			{
				InternedString name = extract<const char *>( dictItems[di][0] )();
				Metadata::registerPlugValue(
					nodeTypeId, plugPath,
					name,
					objectToPlugValueFunction( name, dictItems[di][1] )
				);
			}
		}
		else
		{
			Metadata::registerPlugDescription( nodeTypeId, plugPath, objectToPlugValueFunction( g_descriptionName, args[i+1] ) );
		}
	}

	return object(); // none
}

object registerNode( tuple args, dict kw )
{
	IECore::TypeId nodeTypeId = extract<IECore::TypeId>( args[0] );

	for( size_t i = 1, e = len( args ); i < e; i += 2 )
	{
		IECore::InternedString name = extract<IECore::InternedString>( args[i] )();
		Metadata::registerNodeValue( nodeTypeId, name, objectToNodeValueFunction( name, args[i+1] ) );
	}

	object plugsObject = kw.get( "plugs" );
	if( plugsObject )
	{
		dict plugs = extract<dict>( plugsObject )();
		list plugsItems = plugs.items();
		for( size_t i = 0, e = len( plugsItems ); i < e; ++i )
		{
			MatchPattern plugPath = extract<MatchPattern>( plugsItems[i][0] )();
			object plugValues = plugsItems[i][1];
			for( size_t vi = 0, ve = len( plugValues ); vi < ve; vi += 2 )
			{
				InternedString name = extract<InternedString>( plugValues[vi] );
				Metadata::registerPlugValue(
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
	Metadata::registerPlugValue( nodeTypeId, plugPath, key, objectToPlugValueFunction( key, value ) );
}

object plugValue( const Plug *plug, const char *key, bool inherit, bool instanceOnly, bool copy )
{
	ConstDataPtr d = Metadata::plugValue<Data>( plug, key, inherit, instanceOnly );
	return dataToPython( d.get(), copy );
}

void registerPlugDescription( IECore::TypeId nodeTypeId, const char *plugPath, object &description )
{
	Metadata::registerPlugDescription( nodeTypeId, plugPath, objectToPlugValueFunction( g_descriptionName, description ) );
}

struct ValueChangedSlotCaller
{

	boost::signals::detail::unusable operator()( boost::python::object slot, IECore::TypeId nodeTypeId, IECore::InternedString key )
	{
		slot( nodeTypeId, key.c_str() );
		return boost::signals::detail::unusable();
	}

	boost::signals::detail::unusable operator()( boost::python::object slot, IECore::TypeId nodeTypeId, const MatchPattern &plugPath, IECore::InternedString key )
	{
		slot( nodeTypeId, plugPath.c_str(), key.c_str() );
		return boost::signals::detail::unusable();
	}

};

list keysToList( const std::vector<InternedString> &keys )
{
	list result;
	for( std::vector<InternedString>::const_iterator it = keys.begin(); it != keys.end(); ++it )
	{
		result.append( it->c_str() );
	}

	return result;
}

list registeredNodeValues( const Node *node, bool inherit, bool instanceOnly, bool persistentOnly )
{
	std::vector<InternedString> keys;
	Metadata::registeredNodeValues( node, keys, inherit, instanceOnly, persistentOnly );
	return keysToList( keys );
}

list registeredPlugValues( const Plug *plug, bool inherit, bool instanceOnly, bool persistentOnly )
{
	std::vector<InternedString> keys;
	Metadata::registeredPlugValues( plug, keys, inherit, instanceOnly, persistentOnly );
	return keysToList( keys );
}

} // namespace

namespace GafferBindings
{

void bindMetadata()
{
	scope s = class_<Metadata>( "Metadata", no_init )

		.def( "registerNodeValue", &registerNodeValue )
		.def( "registerNodeValue", (void (*)( Node *, InternedString key, ConstDataPtr value, bool ))&Metadata::registerNodeValue,
			(
				boost::python::arg( "node" ),
				boost::python::arg( "value" ),
				boost::python::arg( "persistent" ) = true
			)
		)
		.staticmethod( "registerNodeValue" )

		.def( "registeredNodeValues", &registeredNodeValues,
			(
				boost::python::arg( "node" ),
				boost::python::arg( "inherit" ) = true,
				boost::python::arg( "instanceOnly" ) = false,
				boost::python::arg( "persistentOnly" ) = false			
			)
		)
		.staticmethod( "registeredNodeValues" )

		.def( "nodeValue", &nodeValue,
			(
				boost::python::arg( "node" ),
				boost::python::arg( "key" ),
				boost::python::arg( "inherit" ) = true,
				boost::python::arg( "instanceOnly" ) = false,
				boost::python::arg( "_copy" ) = true
			)
		)
		.staticmethod( "nodeValue" )

		.def( "registerNodeDescription", boost::python::raw_function( &registerNodeDescription, 2 ) )
		.staticmethod( "registerNodeDescription" )

		.def( "registerNode", boost::python::raw_function( &registerNode, 1 ) )
		.staticmethod( "registerNode" )

		.def( "nodeDescription", &Metadata::nodeDescription,
			(
				boost::python::arg( "node" ),
				boost::python::arg( "inherit" ) = true
			)
		)
		.staticmethod( "nodeDescription" )

		.def( "registerPlugValue", &registerPlugValue )
		.def( "registerPlugValue", (void (*)( Plug *, InternedString key, ConstDataPtr value, bool ))&Metadata::registerPlugValue,
			(
				boost::python::arg( "plug" ),
				boost::python::arg( "value" ),
				boost::python::arg( "persistent" ) = true
			)
		)
		.staticmethod( "registerPlugValue" )

		.def( "registeredPlugValues", &registeredPlugValues,
			(
				boost::python::arg( "plug" ),
				boost::python::arg( "inherit" ) = true,
				boost::python::arg( "instanceOnly" ) = false,
				boost::python::arg( "persistentOnly" ) = false			
			)
		)
		.staticmethod( "registeredPlugValues" )

		.def( "plugValue", &plugValue,
			(
				boost::python::arg( "plug" ),
				boost::python::arg( "key" ),
				boost::python::arg( "inherit" ) = true,
				boost::python::arg( "instanceOnly" ) = false,
				boost::python::arg( "_copy" ) = true
			)
		)
		.staticmethod( "plugValue" )

		.def( "registerPlugDescription", &registerPlugDescription )
		.staticmethod( "registerPlugDescription" )

		.def( "plugDescription", &Metadata::plugDescription,
			(
				boost::python::arg( "plug" ),
				boost::python::arg( "inherit" ) = true
			)
		)
		.staticmethod( "plugDescription" )

		.def( "nodeValueChangedSignal", &Metadata::nodeValueChangedSignal, return_value_policy<reference_existing_object>() )
		.staticmethod( "nodeValueChangedSignal" )

		.def( "plugValueChangedSignal", &Metadata::plugValueChangedSignal, return_value_policy<reference_existing_object>() )
		.staticmethod( "plugValueChangedSignal" )
	;

	SignalBinder<Metadata::NodeValueChangedSignal, DefaultSignalCaller<Metadata::NodeValueChangedSignal>, ValueChangedSlotCaller>::bind( "NodeValueChangedSignal" );
	SignalBinder<Metadata::PlugValueChangedSignal, DefaultSignalCaller<Metadata::NodeValueChangedSignal>, ValueChangedSlotCaller>::bind( "PlugValueChangedSignal" );

}

std::string metadataSerialisation( const Gaffer::Node *node, const std::string &identifier )
{
	std::vector<InternedString> keys;
	Metadata::registeredNodeValues( node, keys, /* inherit = */ false, /* instanceOnly = */ true, /* persistentOnly = */ true );

	std::string result;
	for( std::vector<InternedString>::const_iterator it = keys.begin(), eIt = keys.end(); it != eIt; ++it )
	{
		ConstDataPtr value = Metadata::nodeValue<Data>( node, *it );
		object pythonValue( boost::const_pointer_cast<Data>( value ) );
		std::string stringValue = extract<std::string>( pythonValue.attr( "__repr__" )() );

		result += boost::str(
			boost::format( "Gaffer.Metadata.registerNodeValue( %s, \"%s\", %s )\n" ) %
				identifier %
				*it %
				stringValue
		);
	}

	return result;
}

std::string metadataSerialisation( const Plug *plug, const std::string &identifier )
{
	std::vector<InternedString> keys;
	Metadata::registeredPlugValues( plug, keys, /* inherit = */ false, /* instanceOnly = */ true, /* persistentOnly = */ true );

	std::string result;
	for( std::vector<InternedString>::const_iterator it = keys.begin(), eIt = keys.end(); it != eIt; ++it )
	{
		ConstDataPtr value = Metadata::plugValue<Data>( plug, *it );
		object pythonValue( boost::const_pointer_cast<Data>( value ) );
		std::string stringValue = extract<std::string>( pythonValue.attr( "__repr__" )() );

		result += boost::str(
			boost::format( "Gaffer.Metadata.registerPlugValue( %s, \"%s\", %s )\n" ) %
				identifier %
				*it %
				stringValue
		);
	}

	return result;
}

} // namespace GafferBindings
