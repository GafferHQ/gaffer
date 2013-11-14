//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012-2013, John Haddon. All rights reserved.
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

#include "IECore/SimpleTypedData.h"
#include "IECore/DespatchTypedData.h"
#include "IECore/TypeTraits.h"
#include "IECorePython/RefCountedBinding.h"

#include "Gaffer/Context.h"

#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/ContextBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;
using namespace IECore;

namespace GafferBindings
{

struct SimpleTypedDataGetter
{
	typedef object ReturnType;
	
	template<typename T>
	object operator()( typename T::Ptr data )
	{
		return object( data->readable() );
	}
};

static object get( Context &c, const IECore::InternedString &name )
{
	ConstDataPtr d = c.get<Data>( name );
	try
	{
		return despatchTypedData<SimpleTypedDataGetter, TypeTraits::IsSimpleTypedData>( constPointerCast<Data>( d ) );
	}
	catch( const InvalidArgumentException &e )
	{
		return object( DataPtr( d->copy() ) );
	}
}

static object getWithDefault( Context &c, const IECore::InternedString &name, object defaultValue )
{
	ConstDataPtr d = c.get<Data>( name, 0 );
	if( !d )
	{
		return defaultValue;
	}
	
	try
	{
		return despatchTypedData<SimpleTypedDataGetter, TypeTraits::IsSimpleTypedData>( constPointerCast<Data>( d ) );
	}
	catch( const InvalidArgumentException &e )
	{
		return object( DataPtr( d->copy() ) );
	}
}

static list names( const Context &context )
{
	std::vector<IECore::InternedString> names;
	context.names( names );
	
	list result;
	for( std::vector<IECore::InternedString>::const_iterator it = names.begin(), eIt = names.end(); it != eIt; it++ )
	{
		result.append( it->value() );
	}
	return result;
}

struct ChangedSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, ConstContextPtr context, const IECore::InternedString &name )
	{
		try
		{
			slot( IECore::constPointerCast<Context>( context ), name.value() );
		}
		catch( const error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
		return boost::signals::detail::unusable();
	}
};

static ContextPtr current()
{
	return const_cast<Context *>( Context::current() );
}

void bindContext()
{	
	scope s = IECorePython::RefCountedClass<Context, IECore::RefCounted>( "Context" )
		.def( init<>() )
		.def( init<Context>() )
		.def( "setFrame", &Context::setFrame )
		.def( "getFrame", &Context::getFrame )
		.def( "set", &Context::set<float> )
		.def( "set", &Context::set<int> )
		.def( "set", &Context::set<std::string> )
		.def( "set", &Context::set<Data *> )
		.def( "__setitem__", &Context::set<float> )
		.def( "__setitem__", &Context::set<int> )
		.def( "__setitem__", &Context::set<std::string> )
		.def( "__setitem__", &Context::set<Imath::V2i> )
		.def( "__setitem__", &Context::set<Data *> )
		.def( "get", &get )
		.def( "get", &getWithDefault )
		.def( "__getitem__", &get )
		.def( "names", &names )
		.def( "keys", &names )
		.def( "changedSignal", &Context::changedSignal, return_internal_reference<1>() )
		.def( self == self )
		.def( self != self )
		.def( "substitute", &Context::substitute )
		.def( "hasSubstitutions", &Context::hasSubstitutions ).staticmethod( "hasSubstitutions" )
		.def( "current", &current ).staticmethod( "current" )
		;

	SignalBinder<Context::ChangedSignal, DefaultSignalCaller<Context::ChangedSignal>, ChangedSlotCaller>::bind( "ChangedSignal" );
	
	class_<Context::Scope>( "_Scope", init<Context *>() )
	;

}

} // namespace GafferBindings
