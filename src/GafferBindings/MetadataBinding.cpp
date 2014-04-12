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

#include "IECore/DespatchTypedData.h"
#include "IECorePython/ScopedGILLock.h"

#include "Gaffer/Plug.h"
#include "Gaffer/Node.h"
#include "Gaffer/Metadata.h"

#include "GafferBindings/MetadataBinding.h"
#include "GafferBindings/SignalBinding.h"

using namespace boost::python;
using namespace IECore;
using namespace Gaffer;

namespace GafferBindings
{

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

struct SimpleTypedDataGetter
{
	typedef object ReturnType;
	
	template<typename T>
	object operator()( typename T::Ptr data )
	{
		return object( data->readable() );
	}
};

/// \todo Consider implementing this as an automatic conversion
/// for any bound TypeId argument anywhere. This is implemented
/// already in https://gist.github.com/johnhaddon/7943557 but
/// I'm unsure if we want this behaviour everywhere or not - erring
/// on the side of caution for now.
static IECore::TypeId objectToTypeId( object o )
{
	extract<IECore::TypeId> typeIdExtractor( o );
	if( typeIdExtractor.check() )
	{
		return typeIdExtractor();
	}
	else
	{
		object t = o.attr( "staticTypeId" )();
		return extract<IECore::TypeId>( t );
	}
}

static Metadata::NodeValueFunction objectToNodeValueFunction( object o )
{
	extract<IECore::DataPtr> dataExtractor( o );
	if( dataExtractor.check() )
	{
		return boost::lambda::constant( dataExtractor() );
	}
	else
	{
		return PythonNodeValueFunction( o );
	}
}

static Metadata::PlugValueFunction objectToPlugValueFunction( object o )
{
	extract<IECore::DataPtr> dataExtractor( o );
	if( dataExtractor.check() )
	{
		return boost::lambda::constant( dataExtractor() );
	}
	else
	{
		return PythonPlugValueFunction( o );
	}
}

static void registerNodeValue( object nodeTypeId, IECore::InternedString key, object &value )
{
	Metadata::registerNodeValue( objectToTypeId( nodeTypeId ), key, objectToNodeValueFunction( value ) );
}

static object nodeValue( const Node *node, const char *key, bool inherit, bool instanceOnly )
{
	ConstDataPtr d = Metadata::nodeValue<Data>( node, key, inherit, instanceOnly );
	if( d )
	{
		return despatchTypedData<SimpleTypedDataGetter, TypeTraits::IsSimpleTypedData>( constPointerCast<Data>( d ) );
	}
	else
	{
		return object(); // none
	}
}

static object registerNodeDescription( tuple args, dict kw )
{
	IECore::TypeId nodeTypeId = objectToTypeId( args[0] );
	Metadata::registerNodeDescription( nodeTypeId, objectToNodeValueFunction( args[1] ) );

	for( size_t i = 2, e = len( args ); i < e; i += 2 )
	{
		MatchPattern plugPath = extract<MatchPattern>( args[i] )();
		extract<dict> dictExtractor( args[i+1] );
		if( dictExtractor.check() )
		{
			list dictItems = dictExtractor().items();
			for( size_t di = 0, de = len( dictItems ); di < de; ++di )
			{
				Metadata::registerPlugValue(
					nodeTypeId, plugPath,
					extract<const char *>( dictItems[di][0] )(),
					objectToPlugValueFunction( dictItems[di][1] )
				);
			}
		}
		else
		{
			Metadata::registerPlugDescription( nodeTypeId, plugPath, objectToPlugValueFunction( args[i+1] ) );
		}
	}

	return object(); // none
}

static void registerPlugValue( object nodeTypeId, const char *plugPath, IECore::InternedString key, object &value )
{
	Metadata::registerPlugValue( objectToTypeId( nodeTypeId ), plugPath, key, objectToPlugValueFunction( value ) );
}

static object plugValue( const Plug *plug, const char *key, bool inherit, bool instanceOnly )
{
	ConstDataPtr d = Metadata::plugValue<Data>( plug, key, inherit, instanceOnly );
	if( d )
	{
		return despatchTypedData<SimpleTypedDataGetter, TypeTraits::IsSimpleTypedData>( constPointerCast<Data>( d ) );
	}
	else
	{
		return object(); // none
	}
}

static void registerPlugDescription( object nodeTypeId, const char *plugPath, object &description )
{
	Metadata::registerPlugDescription( objectToTypeId( nodeTypeId ), plugPath, objectToPlugValueFunction( description ) );
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

static list keysToList( const std::vector<InternedString> &keys )
{
	list result;
	for( std::vector<InternedString>::const_iterator it = keys.begin(); it != keys.end(); ++it )
	{
		result.append( it->c_str() );
	}
	
	return result;
}

static list registeredNodeValues( const Node *node, bool inherit, bool instanceOnly )
{
	std::vector<InternedString> keys;
	Metadata::registeredNodeValues( node, keys, inherit, instanceOnly );
	return keysToList( keys );
}

static list registeredPlugValues( const Plug *plug, bool inherit, bool instanceOnly )
{
	std::vector<InternedString> keys;
	Metadata::registeredPlugValues( plug, keys, inherit, instanceOnly );
	return keysToList( keys );
}

void bindMetadata()
{	
	scope s = class_<Metadata>( "Metadata", no_init )
		
		.def( "registerNodeValue", &registerNodeValue )
		.def( "registerNodeValue", (void (*)( Node *, InternedString key, ConstDataPtr value ))&Metadata::registerNodeValue )
		.staticmethod( "registerNodeValue" )
		
		.def( "registeredNodeValues", &registeredNodeValues,
			(
				boost::python::arg( "node" ),
				boost::python::arg( "inherit" ) = true,
				boost::python::arg( "instanceOnly" ) = false
			)
		)
		.staticmethod( "registeredNodeValues" )

		.def( "nodeValue", &nodeValue,
			(
				boost::python::arg( "node" ),
				boost::python::arg( "key" ),
				boost::python::arg( "inherit" ) = true,
				boost::python::arg( "instanceOnly" ) = false
			)
		)
		.staticmethod( "nodeValue" )
		
		.def( "registerNodeDescription", boost::python::raw_function( &registerNodeDescription, 2 ) )
		.staticmethod( "registerNodeDescription" )
		
		.def( "nodeDescription", &Metadata::nodeDescription, 
			(
				boost::python::arg( "node" ),
				boost::python::arg( "inherit" ) = true
			)
		)
		.staticmethod( "nodeDescription" )
		
		.def( "registerPlugValue", &registerPlugValue )
		.def( "registerPlugValue", (void (*)( Plug *, InternedString key, ConstDataPtr value ))&Metadata::registerPlugValue )
		.staticmethod( "registerPlugValue" )
		
		.def( "registeredPlugValues", &registeredPlugValues,
			(
				boost::python::arg( "plug" ),
				boost::python::arg( "inherit" ) = true,
				boost::python::arg( "instanceOnly" ) = false
			)
		)
		.staticmethod( "registeredPlugValues" )
		
		.def( "plugValue", &plugValue,
			(
				boost::python::arg( "plug" ),
				boost::python::arg( "key" ),
				boost::python::arg( "inherit" ) = true,
				boost::python::arg( "instanceOnly" ) = false
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
	Metadata::registeredNodeValues( node, keys, false, true );
	
	std::string result;
	for( std::vector<InternedString>::const_iterator it = keys.begin(), eIt = keys.end(); it != eIt; ++it )
	{
		const Data *value = Metadata::nodeValue<Data>( node, *it );
		object pythonValue( DataPtr( const_cast<Data *>( value ) ) );
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
	Metadata::registeredPlugValues( plug, keys, false, true );
	
	std::string result;
	for( std::vector<InternedString>::const_iterator it = keys.begin(), eIt = keys.end(); it != eIt; ++it )
	{
		const Data *value = Metadata::plugValue<Data>( plug, *it );
		object pythonValue( DataPtr( const_cast<Data *>( value ) ) );
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
