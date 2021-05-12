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

#include "ContextBinding.h"

#include "GafferBindings/DataBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Context.h"

#include "IECorePython/RefCountedBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;
using namespace IECore;

namespace
{

void setFrame( Context &c, float frame )
{
	IECorePython::ScopedGILRelease gilRelease;
	c.setFrame( frame );
}

void setFramesPerSecond( Context &c, float framesPerSecond )
{
	IECorePython::ScopedGILRelease gilRelease;
	c.setFramesPerSecond( framesPerSecond );
}

void setTime( Context &c, float time )
{
	IECorePython::ScopedGILRelease gilRelease;
	c.setTime( time );
}

template<typename T>
void set( Context &c, const IECore::InternedString &name, const T &value )
{
	IECorePython::ScopedGILRelease gilRelease;
	c.set( name, value );
}

// In the C++ API, get() returns "const Data *". Because python has no idea of constness,
// by default we return a copy from the bindings because we don't want the unwitting Python
// scripter to accidentally modify the internals of a Context. We do however expose the
// option to get the original object returned using an "_copy = False" keyword argument,
// in the same way as we do for the TypedObjectPlug::getValue() binding. This is mainly of
// use in the unit tests, but may also have the odd application where performance is critical.
// As a general rule, you should be wary of using this parameter.
object get( Context &c, const IECore::InternedString &name, object defaultValue, bool copy )
{
	ConstDataPtr d = c.get<Data>( name, nullptr );
	return dataToPython( d.get(), copy, defaultValue );
}

object getItem( Context &c, const IECore::InternedString &name )
{
	ConstDataPtr d = c.get<Data>( name );
	return dataToPython( d.get(), /* copy = */ true );
}

bool contains( Context &c, const IECore::InternedString &name )
{
	return c.get<Data>( name, nullptr );
}

void delItem( Context &context, const IECore::InternedString &name )
{
	IECorePython::ScopedGILRelease gilRelease;
	context.remove( name );
}

void removeMatching( Context &context, const StringAlgo::MatchPattern& pattern )
{
	IECorePython::ScopedGILRelease gilRelease;
	context.removeMatching( pattern );
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

void GafferModule::bindContext()
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
		.def(
			init<const Context &, const IECore::Canceller &>( ( arg( "other" ), arg( "canceller" ) ) ) [
				with_custodian_and_ward<1,3>()
			]
		)
		.def( init<const Context &, bool>( ( arg( "other" ), arg( "omitCanceller" ) ) ) )
		.def( "setFrame", &setFrame )
		.def( "getFrame", &Context::getFrame )
		.def( "setFramesPerSecond", &setFramesPerSecond )
		.def( "getFramesPerSecond", &Context::getFramesPerSecond )
		.def( "setTime", &setTime )
		.def( "getTime", &Context::getTime )
		.def( "set", &set<float> )
		.def( "set", &set<int> )
		.def( "set", &set<std::string> )
		.def( "set", &set<Imath::V2i> )
		.def( "set", &set<Imath::V3i> )
		.def( "set", &set<Imath::V2f> )
		.def( "set", &set<Imath::V3f> )
		.def( "set", &set<Imath::Color3f> )
		.def( "set", &set<Imath::Box2i> )
		.def( "set", &set<Data *> )
		.def( "__setitem__", &set<float> )
		.def( "__setitem__", &set<int> )
		.def( "__setitem__", &set<std::string> )
		.def( "__setitem__", &set<Imath::V2i> )
		.def( "__setitem__", &set<Imath::V3i> )
		.def( "__setitem__", &set<Imath::V2f> )
		.def( "__setitem__", &set<Imath::V3f> )
		.def( "__setitem__", &set<Imath::Color3f> )
		.def( "__setitem__", &set<Imath::Box2i> )
		.def( "__setitem__", &set<Data *> )
		.def( "get", &get, ( arg( "defaultValue" ) = object(), arg( "_copy" ) = true ) )
		.def( "__getitem__", &getItem )
		.def( "__contains__", &contains )
		.def( "remove", &delItem )
		.def( "__delitem__", &delItem )
		.def( "removeMatching", &removeMatching )
		.def( "changed", &Context::changed )
		.def( "names", &names )
		.def( "keys", &names )
		.def( "changedSignal", &Context::changedSignal, return_internal_reference<1>() )
		.def( "hash", &Context::hash )
		.def( self == self )
		.def( self != self )
		.def( "substitute", &Context::substitute, ( arg( "input" ), arg( "substitutions" ) = IECore::StringAlgo::AllSubstitutions ) )
		.def( "canceller", &Context::canceller, return_internal_reference<1>() )
		.def( "current", &current ).staticmethod( "current" )
		;

	SignalClass<Context::ChangedSignal, DefaultSignalCaller<Context::ChangedSignal>, ChangedSlotCaller>( "ChangedSignal" );

	class_<Context::Scope, boost::noncopyable>( "_Scope", init<Context *>() )
	;

}
