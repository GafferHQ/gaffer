//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "StringPlugBinding.h"

#include "GafferBindings/ValuePlugBinding.h"

#include "Gaffer/StringPlug.h"

#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

void setValue( StringPlug *plug, const std::string& value )
{
	// we use a GIL release here to prevent a lock in the case where this triggers a graph
	// evaluation which decides to go back into python on another thread:
	IECorePython::ScopedGILRelease r;
	plug->setValue( value );
}

void setPathValue( StringPlug *plug, const std::filesystem::path &value )
{
	IECorePython::ScopedGILRelease r;
	plug->setValue( value );
}

std::string getValue( const StringPlug *plug, const IECore::MurmurHash *precomputedHash )
{
	// Must release GIL in case computation spawns threads which need
	// to reenter Python.
	IECorePython::ScopedGILRelease r;
	return plug->getValue( precomputedHash );
}

std::string substitutionsRepr( unsigned substitutions )
{
	static const IECore::StringAlgo::Substitutions values[] = {
		IECore::StringAlgo::FrameSubstitutions,
		IECore::StringAlgo::VariableSubstitutions,
		IECore::StringAlgo::EscapeSubstitutions,
		IECore::StringAlgo::TildeSubstitutions,
		IECore::StringAlgo::NoSubstitutions
	};
	static const char *names[] = { "FrameSubstitutions", "VariableSubstitutions", "EscapeSubstitutions", "TildeSubstitutions", nullptr };

	if( substitutions == IECore::StringAlgo::AllSubstitutions )
	{
		return "IECore.StringAlgo.Substitutions.AllSubstitutions";
	}
	else if( substitutions == IECore::StringAlgo::NoSubstitutions )
	{
		return "IECore.StringAlgo.Substitutions.NoSubstitutions";
	}

	std::string result;
	for( int i = 0; names[i]; ++i )
	{
		if( substitutions & values[i] )
		{
			if( result.size() )
			{
				result += " | ";
			}
			result += "IECore.StringAlgo.Substitutions." + std::string( names[i] );
		}
	}

	return result;
}

std::string serialisationRepr( const Gaffer::StringPlug *plug, Serialisation *serialisation )
{
	std::string extraArguments;
	if( plug->substitutions() != IECore::StringAlgo::AllSubstitutions )
	{
		extraArguments = "substitutions = " + substitutionsRepr( plug->substitutions() );
		if( serialisation )
		{
			serialisation->addModule( "IECore" );
		}
	}
	return ValuePlugSerialiser::repr( plug, extraArguments, serialisation );
}

std::string repr( const Gaffer::StringPlug *plug )
{
	return serialisationRepr( plug, nullptr );
}

class StringPlugSerialiser : public ValuePlugSerialiser
{

	public :

		std::string constructor( const Gaffer::GraphComponent *graphComponent, Serialisation &serialisation ) const override
		{
			return serialisationRepr( static_cast<const StringPlug *>( graphComponent ), &serialisation );
		}

};

} // namespace

void GafferModule::bindStringPlug()
{

	boost::python::scope s = PlugClass<StringPlug>()
		.def(
			boost::python::init<const std::string &, Gaffer::Plug::Direction, const std::string &, unsigned, unsigned>(
				(
					boost::python::arg_( "name" )=Gaffer::GraphComponent::defaultName<StringPlug>(),
					boost::python::arg_( "direction" )=Gaffer::Plug::In,
					boost::python::arg_( "defaultValue" )="",
					boost::python::arg_( "flags" )=Gaffer::Plug::Default,
					boost::python::arg_( "substitutions" )=IECore::StringAlgo::AllSubstitutions
				)
			)
		)
		.def( "__repr__", &repr )
		.def( "substitutions", &StringPlug::substitutions )
		.def( "defaultValue", &StringPlug::defaultValue, return_value_policy<boost::python::copy_const_reference>() )
		// Must be registered before string-based `setValue()`, to give it weaker overloading precedence.
		.def( "setValue", &setPathValue )
		.def( "setValue", &setValue )
		.def( "getValue", &getValue, ( boost::python::arg( "_precomputedHash" ) = object() ) )
	;

	s.attr( "ValueType" ) = boost::python::object( boost::python::handle<>( boost::python::borrowed( &PyUnicode_Type ) ) );

	Serialisation::registerSerialiser( StringPlug::staticTypeId(), new StringPlugSerialiser );

}
