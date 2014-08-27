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
#include "boost/format.hpp"

#include "IECore/MurmurHash.h"
#include "IECorePython/Wrapper.h"
#include "IECorePython/RunTimeTypedBinding.h"

#include "Gaffer/ValuePlug.h"
#include "Gaffer/Node.h"
#include "Gaffer/Reference.h"

#include "GafferBindings/ValuePlugBinding.h"
#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/Serialisation.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

static std::string maskedRepr( const Plug *plug, unsigned flagsMask )
{
	std::string result = Serialisation::classPath( plug ) + "( \"" + plug->getName().string() + "\", ";

	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + PlugSerialiser::directionRepr( plug->direction() ) + ", ";
	}

	object pythonPlug( PlugPtr( const_cast<Plug *>( plug ) ) );
	if( PyObject_HasAttrString( pythonPlug.ptr(), "defaultValue" ) )
	{
		object pythonDefaultValue = pythonPlug.attr( "defaultValue" )();
		object r = pythonDefaultValue.attr( "__repr__" )();
		extract<std::string> defaultValueExtractor( r );
		std::string defaultValue = defaultValueExtractor();
		if( defaultValue.size() && defaultValue[0] != '<' )
		{
			result += "defaultValue = " + defaultValue + ", ";
		}
		else
		{
			throw IECore::Exception(
				boost::str(
					boost::format( "Default value for plug \"%s\" cannot be serialised" ) % plug->fullName()
				)
			);
		}
	}

	const unsigned flags = plug->getFlags() & flagsMask;
	if( flags != Plug::Default )
	{
		result += "flags = " + PlugSerialiser::flagsRepr( flags ) + ", ";
	}

	result += ")";

	return result;

}

static std::string repr( const Plug *plug )
{
	return maskedRepr( plug, Plug::All );
}

void ValuePlugSerialiser::moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules ) const
{
	PlugSerialiser::moduleDependencies( graphComponent, modules );

	const ValuePlug *valuePlug = static_cast<const ValuePlug *> ( graphComponent );
	object pythonPlug( ValuePlugPtr( const_cast<ValuePlug *>( valuePlug ) ) );
	if( PyObject_HasAttrString( pythonPlug.ptr(), "defaultValue" ) )
	{
		object pythonDefaultValue = pythonPlug.attr( "defaultValue" )();
		std::string module = Serialisation::modulePath( pythonDefaultValue );
		if( module.size() )
		{
			modules.insert( module );
		}
	}
}

std::string ValuePlugSerialiser::constructor( const Gaffer::GraphComponent *graphComponent ) const
{
	return maskedRepr( static_cast<const Plug *>( graphComponent ), Plug::All & ~Plug::ReadOnly );
}

std::string ValuePlugSerialiser::postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
{
	const ValuePlug *plug = static_cast<const ValuePlug *>( graphComponent );
	if( valueNeedsSerialisation( plug, serialisation ) )
	{
		object pythonPlug( ValuePlugPtr( const_cast<ValuePlug *>( plug ) ) );
		if( PyObject_HasAttrString( pythonPlug.ptr(), "getValue" ) )
		{
			object pythonValue = pythonPlug.attr( "getValue" )();

			bool omitDefaultValue = true;
			if( IECore::runTimeCast<const Reference>( plug->node() ) )
			{
				// We always emit setValue() calls for plugs held directly on
				// Reference nodes, even if they are at the default value.
				// This is because the user may have exported the
				// reference with the plug at a non-default value, but then
				// set the value back to the default in a file that references
				// it back in.
				/// \todo Consider whether or not we might like to have a plug flag
				/// to control this behaviour, so that ValuePlugSerialiser doesn't
				/// need explicit knowledge of Reference Nodes.
				omitDefaultValue = false;
			}

			if( omitDefaultValue && PyObject_HasAttrString( pythonPlug.ptr(), "defaultValue" ) )
			{
				object pythonDefaultValue = pythonPlug.attr( "defaultValue" )();
				if( pythonValue == pythonDefaultValue )
				{
					return "";
				}
			}

			std::string value = extract<std::string>( pythonValue.attr( "__repr__" )() );
			return identifier + ".setValue( " + value + " )\n";
		}
	}
	return "";
}

bool ValuePlugSerialiser::valueNeedsSerialisation( const Gaffer::ValuePlug *plug, const Serialisation &serialisation ) const
{
	if(
		plug->direction() != Plug::In ||
		!plug->getFlags( Plug::Serialisable ) ||
		plug->getInput<Plug>()
	)
	{
		return false;
	}

	if( const ValuePlug *parent = plug->parent<ValuePlug>() )
	{
		const Serialiser *parentSerialiser = Serialisation::acquireSerialiser( parent );
		if( parentSerialiser )
		{
			if( const ValuePlugSerialiser *v = dynamic_cast<const ValuePlugSerialiser *>( parentSerialiser ) )
			{
				if( v->valueNeedsSerialisation( parent, serialisation ) )
				{
					// the parent will be serialising the value,
					// so we don't need to.
					return false;
				}
			}
		}
	}

	return true;
}

void GafferBindings::bindValuePlug()
{
	PlugClass<ValuePlug>()
		.def( "settable", &ValuePlug::settable )
		.def( "setFrom", &ValuePlug::setFrom )
		.def( "setToDefault", &ValuePlug::setToDefault )
		.def( "hash", (IECore::MurmurHash (ValuePlug::*)() const)&ValuePlug::hash )
		.def( "hash", (void (ValuePlug::*)( IECore::MurmurHash & ) const)&ValuePlug::hash )
		.def( "getCacheMemoryLimit", &ValuePlug::getCacheMemoryLimit )
		.staticmethod( "getCacheMemoryLimit" )
		.def( "setCacheMemoryLimit", &ValuePlug::setCacheMemoryLimit )
		.staticmethod( "setCacheMemoryLimit" )
		.def( "cacheMemoryUsage", &ValuePlug::cacheMemoryUsage )
		.staticmethod( "cacheMemoryUsage" )
		.def( "__repr__", &repr )
	;

	Serialisation::registerSerialiser( Gaffer::ValuePlug::staticTypeId(), new ValuePlugSerialiser );
}
