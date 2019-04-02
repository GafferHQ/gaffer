//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "CompoundDataPlugBinding.h"

#include "GafferBindings/ValuePlugBinding.h"

#include "Gaffer/CompoundDataPlug.h"

#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

CompoundDataPlugPtr compoundDataPlugConstructor( const char *name, Plug::Direction direction, unsigned flags, tuple children )
{
	CompoundDataPlugPtr result = new CompoundDataPlug( name, direction, flags );
	size_t s = extract<size_t>( children.attr( "__len__" )() );
	for( size_t i=0; i<s; i++ )
	{
		Gaffer::PlugPtr c = extract<Gaffer::PlugPtr>( children[i] );
		result->addChild( c );
	}
	return result;
}

Gaffer::CompoundDataPlug::MemberPlugPtr addMemberWrapper( CompoundDataPlug &p, const std::string &name, IECore::DataPtr value, const std::string &plugName, unsigned plugFlags )
{
	IECorePython::ScopedGILRelease gilRelease;
	return p.addMember( name, value.get(), plugName, plugFlags );
}

Gaffer::CompoundDataPlug::MemberPlugPtr addMemberWrapper2( CompoundDataPlug &p, const std::string &name, ValuePlug *valuePlug, const std::string &plugName )
{
	IECorePython::ScopedGILRelease gilRelease;
	return p.addMember( name, valuePlug, plugName );
}

Gaffer::CompoundDataPlug::MemberPlugPtr addOptionalMemberWrapper( CompoundDataPlug &p, const std::string &name, IECore::DataPtr value, const std::string plugName, unsigned plugFlags, bool enabled )
{
	IECorePython::ScopedGILRelease gilRelease;
	return p.addOptionalMember( name, value.get(), plugName, plugFlags, enabled );
}

Gaffer::CompoundDataPlug::MemberPlugPtr addOptionalMemberWrapper2( CompoundDataPlug &p, const std::string &name, ValuePlug *valuePlug, const std::string &plugName, bool enabled )
{
	IECorePython::ScopedGILRelease gilRelease;
	return p.addOptionalMember( name, valuePlug, plugName, enabled );
}

void addMembersWrapper( CompoundDataPlug &p, const IECore::CompoundData *members, bool useNameAsPlugName )
{
	IECorePython::ScopedGILRelease gilRelease;
	p.addMembers( members, useNameAsPlugName );
}

tuple memberDataAndNameWrapper( CompoundDataPlug &p, const CompoundDataPlug::MemberPlug *member )
{
	std::string name;
	IECore::DataPtr d;
	{
		IECorePython::ScopedGILRelease gilRelease;
		d = p.memberDataAndName( member, name );
	}
	return boost::python::make_tuple( d, name );
}

void fillCompoundData( const CompoundDataPlug &p, IECore::CompoundData *d )
{
	IECorePython::ScopedGILRelease gilRelease;
	p.fillCompoundData( d->writable() );
}

void fillCompoundObject( const CompoundDataPlug &p, IECore::CompoundObject *o )
{
	IECorePython::ScopedGILRelease gilRelease;
	p.fillCompoundObject( o->members() );
}

class MemberPlugSerialiser : public ValuePlugSerialiser
{

	public :

		bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
		{
			// if the parent is dynamic then all the children will need construction.
			const Plug *parent = child->parent<Plug>();
			return parent->getFlags( Gaffer::Plug::Dynamic );
		}

};

} // namespace

void GafferModule::bindCompoundDataPlug()
{

	scope s = PlugClass<CompoundDataPlug>()
		.def( "__init__", make_constructor( compoundDataPlugConstructor, default_call_policies(),
				(
					arg( "name" ) = GraphComponent::defaultName<CompoundDataPlug>(),
					arg( "direction" ) = Gaffer::Plug::In,
					arg( "flags" ) = Gaffer::Plug::Default,
					arg( "children" ) = tuple()
				)
			)
		)
		.def( "addMember", &addMemberWrapper, ( arg_( "name" ), arg_( "defaultValue" ), arg_( "plugName" ) = "member1", arg_( "plugFlags" ) = Plug::Default | Plug::Dynamic ) )
		.def( "addMember", &addMemberWrapper2, ( arg_( "name" ), arg_( "valuePlug" ), arg_( "plugName" ) = "member1" ) )
		.def( "addOptionalMember", &addOptionalMemberWrapper, ( arg_( "name" ), arg_( "defaultValue" ), arg_( "plugName" ) = "member1", arg_( "plugFlags" ) = Plug::Default | Plug::Dynamic, arg_( "enabled" ) = false ) )
		.def( "addOptionalMember", &addOptionalMemberWrapper2, ( arg_( "name" ), arg_( "valuePlug" ), arg_( "plugName" ) = "member1", arg_( "enabled" ) = false ) )
		.def( "addMembers", &addMembersWrapper, ( arg_( "members" ), arg_( "useNameAsPlugName" ) = false ) )
		.def( "memberDataAndName", &memberDataAndNameWrapper )
		.def( "fillCompoundData", &fillCompoundData )
		.def( "fillCompoundObject", &fillCompoundObject )
	;

	PlugClass<CompoundDataPlug::MemberPlug>()
		.def( init<const char *, Plug::Direction, unsigned>(
				(
					boost::python::arg_( "name" )=GraphComponent::defaultName<CompoundDataPlug::MemberPlug>(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "flags" )=Plug::Default
				)
			)
		)
		.attr( "__qualname__" ) = "CompoundDataPlug.MemberPlug"
	;

	Serialisation::registerSerialiser( Gaffer::CompoundDataPlug::MemberPlug::staticTypeId(), new MemberPlugSerialiser );

}
