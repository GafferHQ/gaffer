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

void setFromData( Context &c, const IECore::InternedString &name, const IECore::Data * value )
{
	IECorePython::ScopedGILRelease gilRelease;
	c.set( name, value );
}

// In the C++ API, the untemplated get() returns a freshly copied ConstDataPtr, so it is safe
// to just pass to Python without copying again.
object get( Context &c, const IECore::InternedString &name, object defaultValue )
{
	DataPtr d = c.getAsData( name, nullptr );
	return dataToPython( d.get(), false, defaultValue );
}

object getItem( Context &c, const IECore::InternedString &name )
{
	DataPtr d = c.getAsData( name );
	return dataToPython( d.get(), /* copy = */ false );
}

bool contains( Context &c, const IECore::InternedString &name )
{
	return bool( c.getAsData( name, nullptr ) );
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
	void operator()( boost::python::object slot, ConstContextPtr context, const IECore::InternedString &name )
	{
		try
		{
			slot( boost::const_pointer_cast<Context>( context ), name.value() );
		}
		catch( const error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
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

	contextClass
		.def( init<>() )
		.def( init<const Context &>( ( arg( "other" ) ) ) )
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
		.def( "set", &setFromData )
		.def( "__setitem__", &set<float> )
		.def( "__setitem__", &set<int> )
		.def( "__setitem__", &set<std::string> )
		.def( "__setitem__", &set<Imath::V2i> )
		.def( "__setitem__", &set<Imath::V3i> )
		.def( "__setitem__", &set<Imath::V2f> )
		.def( "__setitem__", &set<Imath::V3f> )
		.def( "__setitem__", &set<Imath::Color3f> )
		.def( "__setitem__", &set<Imath::Box2i> )
		.def( "__setitem__", &setFromData )
		.def( "get", &get, ( arg( "defaultValue" ) = object() ) )
		.def( "__getitem__", &getItem )
		.def( "__contains__", &contains )
		.def( "remove", &delItem )
		.def( "__delitem__", &delItem )
		.def( "removeMatching", &removeMatching )
		.def( "names", &names )
		.def( "keys", &names )
		.def( "changedSignal", &Context::changedSignal, return_internal_reference<1>() )
		.def( "hash", &Context::hash )
		.def( "variableHash", &Context::variableHash )
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
