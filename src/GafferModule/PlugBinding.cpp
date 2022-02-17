//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "PlugBinding.h"

#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/MetadataBinding.h"

#include "Gaffer/Plug.h"
#include "Gaffer/Node.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

std::string repr( const Plug *plug )
{
	return PlugSerialiser::repr( plug, Plug::All );
}

boost::python::tuple outputs( Plug &p )
{
	const Plug::OutputContainer &o = p.outputs();
	boost::python::list l;
	for( Plug::OutputContainer::const_iterator it=o.begin(); it!=o.end(); it++ )
	{
		l.append( PlugPtr( *it ) );
	}
	return boost::python::tuple( l );
}

NodePtr node( Plug &p )
{
	return p.node();
}

void setFlags1( Plug &p, unsigned flags )
{
	IECorePython::ScopedGILRelease gilRelease;
	p.setFlags( flags );
}

void setFlags2( Plug &p, unsigned flags, bool enable )
{
	IECorePython::ScopedGILRelease gilRelease;
	p.setFlags( flags, enable );
}

PlugPtr getInput( Plug &p )
{
	return p.getInput();
}

PlugPtr source( Plug &p )
{
	return p.source();
}

} // namespace

void GafferModule::bindPlug()
{
	using Wrapper = PlugWrapper<Plug>;

	PlugClass<Plug, Wrapper> c;
	{
		scope s( c );
		enum_<Plug::Direction>( "Direction" )
			.value( "Invalid", Plug::Invalid )
			.value( "In", Plug::In )
			.value( "Out", Plug::Out )
		;
		enum_<Plug::Flags>( "Flags" )
			.value( "None", Plug::None )
			.value( "None_", Plug::None )
			.value( "Dynamic", Plug::Dynamic )
			.value( "Serialisable", Plug::Serialisable )
			.value( "AcceptsInputs", Plug::AcceptsInputs )
			.value( "Cacheable", Plug::Cacheable )
			.value( "AcceptsDependencyCycles", Plug::AcceptsDependencyCycles )
			.value( "Default", Plug::Default )
			.value( "All", Plug::All )
		;
	}

	c.def(  init< const std::string &, Plug::Direction, unsigned >
			(
				(
					arg( "name" ) = GraphComponent::defaultName<Plug>(),
					arg( "direction" ) = Plug::In,
					arg( "flags" ) = Plug::Default
				)
			)
		)
		.def( "node", &node )
		.def( "direction", &Plug::direction )
		.def( "getFlags", (unsigned (Plug::*)() const )&Plug::getFlags )
		.def( "getFlags", (bool (Plug::*)( unsigned ) const )&Plug::getFlags )
		.def( "setFlags", &setFlags1 )
		.def( "setFlags", &setFlags2 )
		.def( "getInput", &getInput )
		.def( "source", &source )
		.def( "removeOutputs", &Plug::removeOutputs )
		.def( "outputs", &outputs )
		.def( "__repr__", &repr )
	;

	Serialisation::registerSerialiser( Gaffer::Plug::staticTypeId(), new PlugSerialiser );

}
