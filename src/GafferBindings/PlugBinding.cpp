//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

#include "GafferBindings/PlugBinding.h"
#include "Gaffer/Plug.h"
#include "Gaffer/Node.h"

#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/Wrapper.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

class PlugWrapper : public Plug, public IECorePython::Wrapper<Plug>
{

	public :
	
		PlugWrapper( PyObject *self, const std::string &name, Direction direction, unsigned flags )
			:	Plug( name, direction, flags ), IECorePython::Wrapper<Plug>( self, this )
		{
		}

		GAFFERBINDINGS_PLUGWRAPPERFNS( Plug )

};

IE_CORE_DECLAREPTR( PlugWrapper );

std::string GafferBindings::serialisePlugDirection( Plug::Direction direction )
{
	switch( direction )
	{
		case Plug::In :
			return "Gaffer.Plug.Direction.In";
		case Plug::Out :
			return "Gaffer.Plug.Direction.Out";
		default :
			return "Gaffer.Plug.Direction.Invalid";
	}
}

std::string GafferBindings::serialisePlugFlags( unsigned flags )
{
	if( flags == Plug::Default )
	{
		return "Gaffer.Plug.Flags.Default";
	}
	else if( flags == Plug::All )
	{
		return "Gaffer.Plug.Flags.All";
	}
	
	static const Plug::Flags values[] = { Plug::Dynamic, Plug::Serialisable, Plug::AcceptsInputs, Plug::PerformsSubstitutions, Plug::Cacheable, Plug::None };
	static const char *names[] = { "Dynamic", "Serialisable", "AcceptsInputs", "PerformsSubstitutions", "Cacheable", 0 };
	
	std::string result;
	for( int i=0; names[i]; i++ )
	{
		if( flags & values[i] )
		{
			if( result.size() )
			{
				result += " | ";
			}
			result += std::string( "Gaffer.Plug.Flags." ) + names[i];
		}
	}
	
	return result;
}

std::string GafferBindings::serialisePlugInput( Serialiser &s, ConstPlugPtr plug )
{
	std::string result = "";
	ConstPlugPtr srcPlug = plug->getInput<Plug>();
	if( srcPlug && srcPlug->node() )
	{
		std::string srcNodeName = s.add( srcPlug->node() );
		if( srcNodeName!="" )
		{
			result = srcNodeName + "[\"" + srcPlug->relativeName( srcPlug->node() ) + "\"]";
		}
	}

	return result;
}

static std::string serialise( Serialiser &s, ConstGraphComponentPtr g )
{
	ConstPlugPtr plug = IECore::staticPointerCast<const Plug>( g );
	std::string result = s.modulePath( g ) + ".Plug( \"" + g->getName() + "\", ";
	
	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + serialisePlugDirection( plug->direction() ) + ", ";
	}
		
	if( plug->getFlags() != Plug::Default )
	{
		result += "flags = " + serialisePlugFlags( plug->getFlags() ) + ", ";
	}
	
	std::string input = serialisePlugInput( s, plug );
	if( input.size() )
	{
		result += "input = " + input + ", ";
	}
		
	result += ")";

	return result;
}

static boost::python::tuple outputs( Plug &p )
{
	const Plug::OutputContainer &o = p.outputs();
	boost::python::list l;
	for( Plug::OutputContainer::const_iterator it=o.begin(); it!=o.end(); it++ )
	{
		l.append( PlugPtr( *it ) );
	}
	return boost::python::tuple( l );
}

static NodePtr node( Plug &p )
{
	return p.node();
}

void GafferBindings::bindPlug()
{

	IECorePython::RunTimeTypedClass<Plug, PlugWrapperPtr> c;
	{
		scope s( c );
		enum_<Plug::Direction>( "Direction" )
			.value( "Invalid", Plug::Invalid )
			.value( "In", Plug::In )
			.value( "Out", Plug::Out )
		;
		enum_<Plug::Flags>( "Flags" )
			.value( "None", Plug::None )
			.value( "Dynamic", Plug::Dynamic )
			.value( "Serialisable", Plug::Serialisable )
			.value( "AcceptsInputs", Plug::AcceptsInputs )
			.value( "PerformsSubstitutions", Plug::PerformsSubstitutions )
			.value( "Cacheable", Plug::Cacheable )
			.value( "Default", Plug::Default )
			.value( "All", Plug::All )
		;
	}
			
	c.def(  init< const std::string &, Plug::Direction, unsigned >
			(
				(
					arg( "name" ) = Plug::staticTypeName(),
					arg( "direction" ) = Plug::In,
					arg( "flags" ) = Plug::Default
				)
			)	
		)
		.def( "node", &node )
		.def( "direction", &Plug::direction )
		.def( "getFlags", (unsigned (Plug::*)() const )&Plug::getFlags )
		.def( "getFlags", (bool (Plug::*)( unsigned ) const )&Plug::getFlags )
		.def( "setFlags", (void (Plug::*)( unsigned ) )&Plug::setFlags )
		.def( "setFlags", (void (Plug::*)( unsigned, bool ) )&Plug::setFlags )
		.GAFFERBINDINGS_DEFPLUGWRAPPERFNS( Plug )
		.def( "getInput", (PlugPtr (Plug::*)())&Plug::getInput<Plug> )
		.def( "removeOutputs", &Plug::removeOutputs )
		.def( "outputs", &outputs )
	;

	Serialiser::registerSerialiser( Plug::staticTypeId(), serialise );
	
}
