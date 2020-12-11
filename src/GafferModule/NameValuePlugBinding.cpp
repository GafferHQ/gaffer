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

#include "NameValuePlugBinding.h"

#include "GafferBindings/ValuePlugBinding.h"
#include "Gaffer/NameValuePlug.h"

#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

class NameValuePlugSerialiser : public ValuePlugSerialiser
{

	public :

		bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
		{
			// The children will be created by the constructor output by repr
			return false;
		}

		std::string constructor( const Gaffer::GraphComponent *graphComponent, Serialisation &serialisation ) const override
		{
			return repr( static_cast<const NameValuePlug *>( graphComponent ), &serialisation );
		}

		static std::string repr( const Gaffer::NameValuePlug *plug, Serialisation *serialisation )
		{
			if( !plug->namePlug() || !plug->valuePlug() )
			{
				throw IECore::Exception( "Cannot serialize: " + plug->fullName() + " - NameValuePlug must have name and value." );
			}

			std::string result = "Gaffer.NameValuePlug( ";
			result += "\"" + plug->namePlug()->defaultValue() + "\", ";

			result += Serialisation::acquireSerialiser( plug->valuePlug() )->constructor( plug->valuePlug(), *serialisation ) + ", ";

			if( plug->enabledPlug() )
			{
				result += std::string( plug->enabledPlug()->defaultValue() ? "True" : "False" ) + ", ";
			}

			result += "\"" + plug->getName().string() + "\", ";

			result += flagsRepr( plug->getFlags() ) + " )";

			return result;
		}

};

std::string repr( const NameValuePlug *plug )
{
	Serialisation tempSerialisation( plug );
	return NameValuePlugSerialiser::repr( plug, &tempSerialisation );
}

NameValuePlugPtr nameValuePlugConstructor1( const std::string &nameDefault, const IECore::DataPtr valueDefault, const std::string &name, Plug::Direction direction, unsigned flags )
{
	return new NameValuePlug( nameDefault, valueDefault.get(), name, direction, flags );
}

NameValuePlugPtr nameValuePlugConstructor2( const std::string &nameDefault, const Gaffer::PlugPtr valuePlug, const std::string &name, object flags )
{
	if( flags == object() )
	{
		return new NameValuePlug( nameDefault, valuePlug, name );
	}
	else
	{
		return new NameValuePlug( nameDefault, valuePlug, name, extract<unsigned>( flags ) );
	}
}

NameValuePlugPtr nameValuePlugConstructor3( const std::string &nameDefault, const IECore::DataPtr valueDefault, bool defaultEnabled, const std::string &name, Plug::Direction direction, unsigned flags )
{
	return new NameValuePlug( nameDefault, valueDefault.get(), defaultEnabled, name, direction, flags );
}

NameValuePlugPtr nameValuePlugConstructor4( const std::string &nameDefault, const Gaffer::PlugPtr valuePlug, bool defaultEnabled, const std::string &name, object flags )
{
	if( flags == object() )
	{
		return new NameValuePlug( nameDefault, valuePlug, defaultEnabled, name );
	}
	else
	{
		return new NameValuePlug( nameDefault, valuePlug, defaultEnabled, name, extract<unsigned>( flags ) );
	}
}

} // namespace

void GafferModule::bindNameValuePlug()
{

	PlugClass<NameValuePlug>()
		.def( init<const char *, Plug::Direction, unsigned>(
				(
					boost::python::arg_( "name" )=GraphComponent::defaultName<NameValuePlug>(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "flags" )=Plug::Default
				)
			)
		)
		.def( "__init__", make_constructor( nameValuePlugConstructor1, default_call_policies(),
				(
					arg( "nameDefault" ),
					arg( "valueDefault" ),
					arg( "name" ) = GraphComponent::defaultName<NameValuePlug>(),
					arg( "direction" ) = Gaffer::Plug::In,
					arg( "flags" ) = Gaffer::Plug::Default
				)
			)
		)
		.def( "__init__", make_constructor( nameValuePlugConstructor2, default_call_policies(),
				(
					arg( "nameDefault" ),
					arg( "valuePlug" ),
					arg( "name" ) = GraphComponent::defaultName<NameValuePlug>(),
					arg( "flags" ) = object()
				)
			)
		)
		.def( "__init__", make_constructor( nameValuePlugConstructor3, default_call_policies(),
				(
					arg( "nameDefault" ),
					arg( "valueDefault" ),
					arg( "defaultEnabled" ),
					arg( "name" ) = GraphComponent::defaultName<NameValuePlug>(),
					arg( "direction" ) = Gaffer::Plug::In,
					arg( "flags" ) = Gaffer::Plug::Default
				)
			)
		)
		.def( "__init__", make_constructor( nameValuePlugConstructor4, default_call_policies(),
				(
					arg( "nameDefault" ),
					arg( "valuePlug" ),
					arg( "defaultEnabled" ),
					arg( "name" ) = GraphComponent::defaultName<NameValuePlug>(),
					arg( "flags" ) = object()
				)
			)
		)
		.def( "__repr__", &repr )
	;

	Serialisation::registerSerialiser( Gaffer::NameValuePlug::staticTypeId(), new NameValuePlugSerialiser );

}
