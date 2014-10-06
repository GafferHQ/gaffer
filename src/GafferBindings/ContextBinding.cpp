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

namespace
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

// In the C++ API, get() returns "const Data *". Because python has no idea of constness,
// by default we return a copy from the bindings because we don't want the unwitting Python
// scripter to accidentally modify the internals of a Context. We do however expose the
// option to get the original object returned using an "_copy = False" keyword argument,
// in the same way as we do for the TypedObjectPlug::getValue() binding. This is mainly of
// use in the unit tests, but may also have the odd application where performance is critical.
// As a general rule, you should be wary of using this parameter.
object get( Context &c, const IECore::InternedString &name, bool copy )
{
	ConstDataPtr d = c.get<Data>( name );
	try
	{
		return despatchTypedData<SimpleTypedDataGetter, TypeTraits::IsSimpleTypedData>( const_cast<Data *>( d.get() ) );
	}
	catch( const InvalidArgumentException &e )
	{
		return object( copy ? d->copy() : boost::const_pointer_cast<Data>( d ) );
	}
}

object getWithDefault( Context &c, const IECore::InternedString &name, object defaultValue, bool copy )
{
	ConstDataPtr d = c.get<Data>( name, NULL );
	if( !d )
	{
		return defaultValue;
	}

	try
	{
		return despatchTypedData<SimpleTypedDataGetter, TypeTraits::IsSimpleTypedData>( const_cast<Data *>( d.get() ) );
	}
	catch( const InvalidArgumentException &e )
	{
		return object( copy ? d->copy() : boost::const_pointer_cast<Data>( d ) );
	}
}

object getItem( Context &c, const IECore::InternedString &name )
{
	return get( c, name, /* copy = */ true );
}

void delItem( Context &context, const IECore::InternedString &name )
{
	context.remove( name );
}

list names( const Context &context )
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
			slot( boost::const_pointer_cast<Context>( context ), name.value() );
		}
		catch( const error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
		return boost::signals::detail::unusable();
	}
};

ContextPtr current()
{
	return const_cast<Context *>( Context::current() );
}

} // namespace

void GafferBindings::bindContext()
{
	IECorePython::RefCountedClass<Context, IECore::RefCounted> contextClass( "Context" );
	scope s = contextClass;

	enum_<Context::Ownership>( "Ownership" )
		.value( "Copied", Context::Copied )
		.value( "Shared", Context::Shared )
		.value( "Borrowed", Context::Borrowed )
	;

	contextClass
		.def( init<>() )
		.def( init<const Context &, Context::Ownership>( ( arg( "other" ), arg( "ownership" ) = Context::Copied ) ) )
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
		.def( "get", &get, arg( "_copy" ) = true )
		.def( "get", &getWithDefault, ( arg( "defaultValue" ), arg( "_copy" ) = true ) )
		.def( "__getitem__", &getItem )
		.def( "remove", &Context::remove )
		.def( "__delitem__", &delItem )
		.def( "changed", &Context::changed )
		.def( "names", &names )
		.def( "keys", &names )
		.def( "changedSignal", &Context::changedSignal, return_internal_reference<1>() )
		.def( "hash", &Context::hash )
		.def( self == self )
		.def( self != self )
		.def( "substitute", &Context::substitute )
		.def( "hasSubstitutions", &Context::hasSubstitutions ).staticmethod( "hasSubstitutions" )
		.def( "current", &current ).staticmethod( "current" )
		;

	SignalBinder<Context::ChangedSignal, DefaultSignalCaller<Context::ChangedSignal>, ChangedSlotCaller>::bind( "ChangedSignal" );

	class_<Context::Scope, boost::noncopyable>( "_Scope", init<Context *>() )
	;

}
