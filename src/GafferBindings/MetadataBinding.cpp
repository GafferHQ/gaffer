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

/// \todo I think we need some sort of standard string
/// matching behaviour throughout Gaffer. In various places
/// in Python we're accepting either a regex or a string we
/// translate with fnmatch.translate(), and in C++ PathMatcher
/// uses glob style matching and various registries use regexes.
/// Ideally I think we'd settle on a glob style behaviour everywhere
/// and have some simple utility class to make it easy to use.
static boost::regex objectToRegex( object o )
{
	extract<std::string> stringExtractor( o );
	if( stringExtractor.check() )
	{
		std::string glob = stringExtractor();
		std::string regex;
		for( const char *c = glob.c_str(); *c; ++c )
		{
			switch( *c )
			{
				case '*' :
					regex += ".*";
					break;
				case '?' :
					regex += ".";
					break;
				case '.' :
					regex += "\\.";
					break;
				default :
					regex += *c;
			}
		}	
		return boost::regex( regex );
	}

	PyErr_SetString( PyExc_TypeError, "Expected a string" );
	throw_error_already_set();
	return boost::regex(); // we can't get here but we need to keep the compiler happy
}

static void registerNodeValue( object nodeTypeId, IECore::InternedString key, object &value )
{
	Metadata::registerNodeValue( objectToTypeId( nodeTypeId ), key, objectToNodeValueFunction( value ) );
}

static object nodeValue( const Node *node, const char *key, bool inherit )
{
	ConstDataPtr d = Metadata::nodeValue<Data>( node, key, inherit );
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
		boost::regex plugPath = objectToRegex( args[i] );
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

static void registerPlugValue( object nodeTypeId, object &plugPath, IECore::InternedString key, object &value )
{
	Metadata::registerPlugValue( objectToTypeId( nodeTypeId ), objectToRegex( plugPath ), key, objectToPlugValueFunction( value ) );
}

static object plugValue( const Plug *plug, const char *key, bool inherit )
{
	ConstDataPtr d = Metadata::plugValue<Data>( plug, key, inherit );
	if( d )
	{
		return despatchTypedData<SimpleTypedDataGetter, TypeTraits::IsSimpleTypedData>( constPointerCast<Data>( d ) );
	}
	else
	{
		return object(); // none
	}
}

static void registerPlugDescription( object nodeTypeId, object &plugPath, object &description )
{
	Metadata::registerPlugDescription( objectToTypeId( nodeTypeId ), objectToRegex( plugPath ), objectToPlugValueFunction( description ) );
}

void bindMetadata()
{	
	class_<Metadata>( "Metadata", no_init )
		
		.def( "registerNodeValue", &registerNodeValue )
		.staticmethod( "registerNodeValue" )
		
		.def( "nodeValue", &nodeValue,
			(
				boost::python::arg( "node" ),
				boost::python::arg( "key" ),
				boost::python::arg( "inherit" ) = true
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
		.staticmethod( "registerPlugValue" )
		
		.def( "plugValue", &plugValue,
			(
				boost::python::arg( "plug" ),
				boost::python::arg( "key" ),
				boost::python::arg( "inherit" ) = true
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
	
	;

}

} // namespace GafferBindings
