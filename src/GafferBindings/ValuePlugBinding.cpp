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
#include "boost/algorithm/string/predicate.hpp"
#include "boost/algorithm/string/replace.hpp"

#include "Gaffer/ValuePlug.h"
#include "Gaffer/Node.h"
#include "Gaffer/Context.h"
#include "Gaffer/Reference.h"
#include "Gaffer/Metadata.h"

#include "GafferBindings/ValuePlugBinding.h"
#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/Serialisation.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

GAFFERBINDINGS_API bool shouldResetPlugDefault( const Gaffer::Plug *plug, const Serialisation *serialisation )
{
	if( !serialisation )
	{
		return false;
	}

	if( plug->node() != serialisation->parent() || plug->getInput() )
	{
		return false;
	}

	return Context::current()->get<bool>( "valuePlugSerialiser:resetParentPlugDefaults", false );
}

GAFFERBINDINGS_API std::string valueRepr( boost::python::object &o )
{
	// We use IECore.repr() because it correctly prefixes the imath
	// types with the module name, and also works around problems
	// when round-tripping empty Box2fs.
	object repr = boost::python::import( "IECore" ).attr( "repr" );
	return extract<std::string>( repr( o ) );
}

} // namespace

std::string ValuePlugSerialiser::repr( const Gaffer::ValuePlug *plug, unsigned flagsMask, const std::string &extraArguments, const Serialisation *serialisation )
{
	std::string result = Serialisation::classPath( plug ) + "( \"" + plug->getName().string() + "\", ";

	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + PlugSerialiser::directionRepr( plug->direction() ) + ", ";
	}

	object pythonPlug( PlugPtr( const_cast<ValuePlug *>( plug ) ) );
	if( PyObject_HasAttrString( pythonPlug.ptr(), "defaultValue" ) )
	{
		object pythonDefaultValue;
		if( shouldResetPlugDefault( plug, serialisation ) )
		{
			pythonDefaultValue = pythonPlug.attr( "getValue" )();
		}
		else
		{
			pythonDefaultValue = pythonPlug.attr( "defaultValue" )();
		}

		const std::string defaultValue = valueRepr( pythonDefaultValue );
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

	if( PyObject_HasAttrString( pythonPlug.ptr(), "hasMinValue" ) )
	{
		const bool hasMinValue = pythonPlug.attr( "hasMinValue" )();
		if( hasMinValue )
		{
			object pythonMinValue = pythonPlug.attr( "minValue" )();
			result += "minValue = " + valueRepr( pythonMinValue ) + ", ";
		}
	}

	if( PyObject_HasAttrString( pythonPlug.ptr(), "hasMaxValue" ) )
	{
		const bool hasMinValue = pythonPlug.attr( "hasMaxValue" )();
		if( hasMinValue )
		{
			object pythonMaxValue = pythonPlug.attr( "maxValue" )();
			result += "maxValue = " + valueRepr( pythonMaxValue ) + ", ";
		}
	}

	const unsigned flags = plug->getFlags() & flagsMask;
	if( flags != Plug::Default )
	{
		result += "flags = " + PlugSerialiser::flagsRepr( flags ) + ", ";
	}

	if( extraArguments.size() )
	{
		result += extraArguments + " ";
	}

	result += ")";

	return result;

}

void ValuePlugSerialiser::moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const
{
	PlugSerialiser::moduleDependencies( graphComponent, modules, serialisation );

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

std::string ValuePlugSerialiser::constructor( const Gaffer::GraphComponent *graphComponent, const Serialisation &serialisation ) const
{
	return repr( static_cast<const ValuePlug *>( graphComponent ), Plug::All & ~Plug::ReadOnly, "", &serialisation );
}

std::string ValuePlugSerialiser::postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
{
	const ValuePlug *plug = static_cast<const ValuePlug *>( graphComponent );
	if( !valueNeedsSerialisation( plug, serialisation ) )
	{
		return "";
	}

	object pythonPlug( ValuePlugPtr( const_cast<ValuePlug *>( plug ) ) );
	object pythonValue = pythonPlug.attr( "getValue" )();

	bool omitDefaultValue = true;
	if( const Reference *reference = IECore::runTimeCast<const Reference>( plug->node() ) )
	{
		// Prior to version 0.9.0.0, `.grf` files created with `Box::exportForReference()`
		// could contain setValue() calls for promoted plugs like this one. When such
		// files have been loaded on a Reference node, we must always serialise the plug values
		// from the Reference node, lest they should get clobbered by the setValue() calls
		// in the `.grf` file.
		int milestoneVersion = 0;
		int majorVersion = 0;
		if( IECore::ConstIntDataPtr v = Metadata::value<IECore::IntData>( reference, "serialiser:milestoneVersion" ) )
		{
			milestoneVersion = v->readable();
		}
		if( IECore::ConstIntDataPtr v = Metadata::value<IECore::IntData>( reference, "serialiser:majorVersion" ) )
		{
			majorVersion = v->readable();
		}
		omitDefaultValue = milestoneVersion > 0 || majorVersion > 8;
		/// \todo Consider whether or not we might like to have a plug flag
		/// to control this behaviour, so that ValuePlugSerialiser doesn't
		/// need explicit knowledge of Reference Nodes. On the one hand, reducing
		/// coupling between this and the Reference node seems good, but on the other,
		/// it'd be nice to keep the plug flags as simple as possible, and we don't have
		/// another worthwhile use case.
	}

	if( omitDefaultValue && PyObject_HasAttrString( pythonPlug.ptr(), "defaultValue" ) )
	{
		object pythonDefaultValue = pythonPlug.attr( "defaultValue" )();
		if( pythonValue == pythonDefaultValue )
		{
			return "";
		}
	}

	return identifier + ".setValue( " + valueRepr( pythonValue ) + " )\n";
}

bool ValuePlugSerialiser::valueNeedsSerialisation( const Gaffer::ValuePlug *plug, const Serialisation &serialisation ) const
{
	if(
		plug->direction() != Plug::In ||
		!plug->getFlags( Plug::Serialisable ) ||
		plug->getInput()
	)
	{
		return false;
	}

	if( shouldResetPlugDefault( plug, &serialisation ) )
	{
		// There's no point in serialising the value if we're
		// turning it into the default value anyway.
		return false;
	}

	object pythonPlug( ValuePlugPtr( const_cast<ValuePlug *>( plug ) ) );
	if( !PyObject_HasAttrString( pythonPlug.ptr(), "getValue" ) )
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
