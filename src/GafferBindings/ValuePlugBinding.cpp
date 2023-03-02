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

#include "GafferBindings/ValuePlugBinding.h"

#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/Serialisation.h"

#include "Gaffer/Context.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/Node.h"
#include "Gaffer/Reference.h"
#include "Gaffer/Spreadsheet.h"
#include "Gaffer/ValuePlug.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/algorithm/string/replace.hpp"

#include "fmt/format.h"

#include <unordered_map>

using namespace std;
using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

const IECore::InternedString g_omitParentNodePlugValues( "valuePlugSerialiser:omitParentNodePlugValues" );

std::string valueSerialisationWalk( const Gaffer::ValuePlug *plug, const std::string &identifier, Serialisation &serialisation, bool &canCondense )
{
	// There's nothing to do if the plug isn't serialisable.
	if( !plug->getFlags( Plug::Serialisable ) )
	{
		canCondense = false;
		return "";
	}

	// Otherwise we need to get the individual value serialisations
	// for each child.

	string childSerialisations;
	bool canCondenseChildren = true;
	for( ValuePlug::Iterator childIt( plug ); !childIt.done(); ++childIt )
	{
		const std::string childIdentifier = serialisation.childIdentifier( identifier, childIt.base() );
		childSerialisations += valueSerialisationWalk( childIt->get(), childIdentifier, serialisation, canCondenseChildren );
	}

	// The child results alone are sufficient for a complete
	// serialisation, but we'd prefer to condense them into
	// a single `setValue()` call at this level if we can, for
	// greater readability. Return now if that's not possible.
	if( !canCondenseChildren )
	{
		canCondense = false;
		return childSerialisations;
	}

	object pythonPlug( ValuePlugPtr( const_cast<ValuePlug *>( plug ) ) );
	if( !PyObject_HasAttrString( pythonPlug.ptr(), "getValue" ) )
	{
		// Can't condense, because can't get value at this level.
		// We also disable condensing at outer levels in this case,
		// because otherwise we hit problems trying to serialise
		// SplinePlugs.
		canCondense = false;
		return childSerialisations;
	}

	// Alternatively, there may have been no children because we're
	// visiting a leaf plug. In this case we may want to omit the
	// value, in which case we should also return now.
	if( plug->children().empty() )
	{
		if( plug->getInput() || plug->direction() == Plug::Out )
		{
			canCondense = false;
			return "";
		}
	}

	// Emit the `setValue()` call for this plug.

	if( plug->isSetToDefault() )
	{
		return "";
	}

	object pythonValue = pythonPlug.attr( "getValue" )();
	return identifier + ".setValue( " + ValuePlugSerialiser::valueRepr( pythonValue, &serialisation ) + " )\n";
}

std::string compoundObjectRepr( const IECore::CompoundObject &o, Serialisation *serialisation )
{
	std::string items;
	for( const auto &e : o.members() )
	{
		if( items.size() )
		{
			items += ", ";
		}
		items += "'" + e.first.string() + "' : " + ValuePlugSerialiser::valueRepr( object( e.second ), serialisation );
	}

	if( serialisation )
	{
		serialisation->addModule( "IECore" );
	}

	if( items.empty() )
	{
		return "IECore.CompoundObject()";
	}
	else
	{
		return "IECore.CompoundObject( { " + items + "} )";
	}
}

} // namespace

std::string ValuePlugSerialiser::repr( const Gaffer::ValuePlug *plug, const std::string &extraArguments, Serialisation *serialisation )
{
	std::string result = Serialisation::classPath( plug ) + "( \"" + plug->getName().string() + "\", ";

	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + PlugSerialiser::directionRepr( plug->direction() ) + ", ";
	}

	object pythonPlug( PlugPtr( const_cast<ValuePlug *>( plug ) ) );
	if( PyObject_HasAttrString( pythonPlug.ptr(), "defaultValue" ) )
	{
		object pythonDefaultValue = pythonPlug.attr( "defaultValue" )();
		const std::string defaultValue = valueRepr( pythonDefaultValue, serialisation );
		if( defaultValue.size() )
		{
			result += "defaultValue = " + defaultValue + ", ";
		}
		else
		{
			throw IECore::Exception(
				fmt::format( "Default value for plug \"{}\" cannot be serialised", plug->fullName() )
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

	const unsigned flags = plug->getFlags();
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

std::string ValuePlugSerialiser::constructor( const Gaffer::GraphComponent *graphComponent, Serialisation &serialisation ) const
{
	return repr( static_cast<const ValuePlug *>( graphComponent ), "", &serialisation );
}

std::string ValuePlugSerialiser::postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const
{
	std::string result = PlugSerialiser::postHierarchy( graphComponent, identifier, serialisation );

	const ValuePlug *plug = static_cast<const ValuePlug *>( graphComponent );
	if( plug == serialisation.parent() || !plug->parent<ValuePlug>() )
	{
		// Top level ValuePlug. We are responsible for emitting the
		// appropriate `setValue()` calls for this and all descendants.
		if( plug->node() != serialisation.parent() || !Context::current()->get<bool>( g_omitParentNodePlugValues, false ) )
		{
			bool unused;
			result = valueSerialisationWalk( plug, identifier, serialisation, unused ) + result;
		}
	}

	return result;
}

std::string ValuePlugSerialiser::valueRepr( const boost::python::object &value, Serialisation *serialisation )
{
	// CompoundObject may contain objects which can only be serialised
	// via `objectToBase64()`, so we need to override the standard Cortex
	// serialiser.

	boost::python::extract<const IECore::CompoundObject &> compoundObjectExtractor( value );
	if( compoundObjectExtractor.check() )
	{
		return compoundObjectRepr( compoundObjectExtractor(), serialisation );
	}

	// We use IECore.repr() because it correctly prefixes the imath
	// types with the module name, and also works around problems
	// when round-tripping empty Box2fs. Accessing it via `import`
	// is slow so we do it only once and store in `g_repr`. We
	// deliberately "leak" this value as otherwise it will be cleaned
	// up during static destruction, _after_ Python has already shut
	// down.
	static object *g_repr = new boost::python::object( boost::python::import( "IECore" ).attr( "repr" ) );
	std::string result = extract<std::string>( (*g_repr)( value ) );
	if( result.size() && result[0] != '<' )
	{
		if( serialisation )
		{
			const std::string module = Serialisation::modulePath( value );
			if( module.size() )
			{
				serialisation->addModule( module );
			}
		}
		return result;
	}

	extract<IECore::ConstObjectPtr> objectExtractor( value );
	if( objectExtractor.check() )
	{
		// Fall back to base64 encoding
		IECore::ConstObjectPtr object = objectExtractor();
		return
			"Gaffer.Serialisation.objectFromBase64( \"" +
			Serialisation::objectToBase64( object.get() ) +
			"\" )"
		;
	}

	return "";
}
