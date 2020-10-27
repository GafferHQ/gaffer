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
#include "boost/format.hpp"

using namespace std;
using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

bool shouldResetPlugDefault( const Gaffer::Plug *plug, const Serialisation *serialisation )
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

bool shouldOmitDefaultValue( const Gaffer::ValuePlug *plug )
{
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
		return milestoneVersion > 0 || majorVersion > 8;
	}
	return true;
}

std::string valueRepr( boost::python::object &o )
{
	// We use IECore.repr() because it correctly prefixes the imath
	// types with the module name, and also works around problems
	// when round-tripping empty Box2fs.
	object repr = boost::python::import( "IECore" ).attr( "repr" );
	std::string result = extract<std::string>( repr( o ) );
	if( result.size() && result[0] != '<' )
	{
		return result;
	}

	extract<IECore::ConstObjectPtr> objectExtractor( o );
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

std::string valueSerialisationWalk( const Gaffer::ValuePlug *plug, const std::string &identifier, const Serialisation &serialisation, bool &canCondense )
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
	for( ValuePlugIterator childIt( plug ); !childIt.done(); ++childIt )
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

	object pythonValue = pythonPlug.attr( "getValue" )();

	if( shouldOmitDefaultValue( plug ) && PyObject_HasAttrString( pythonPlug.ptr(), "defaultValue" ) )
	{
		object pythonDefaultValue = pythonPlug.attr( "defaultValue" )();
		if( pythonValue == pythonDefaultValue )
		{
			return "";
		}
	}

	return identifier + ".setValue( " + valueRepr( pythonValue ) + " )\n";
}

} // namespace

std::string ValuePlugSerialiser::repr( const Gaffer::ValuePlug *plug, const std::string &extraArguments, const Serialisation *serialisation )
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
		if( defaultValue.size() )
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
	return repr( static_cast<const ValuePlug *>( graphComponent ), "", &serialisation );
}

std::string ValuePlugSerialiser::postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
{
	std::string result = PlugSerialiser::postHierarchy( graphComponent, identifier, serialisation );

	const ValuePlug *plug = static_cast<const ValuePlug *>( graphComponent );
	if( plug == serialisation.parent() || !plug->parent<ValuePlug>() )
	{
		// Top level ValuePlug. We are responsible for emitting the
		// appropriate `setValue()` calls for this and all descendants.

		const bool resetDefault = shouldResetPlugDefault( plug, &serialisation );
		const bool isRowsPlug = IECore::runTimeCast<const Spreadsheet::RowsPlug>( plug );

		if( !resetDefault || isRowsPlug )
		{
			bool unused;
			result = valueSerialisationWalk( plug, identifier, serialisation, unused ) + result;
		}

		if( isRowsPlug && resetDefault )
		{
			// RowsPlugs serialise their children independently via `addRow()` and `addColumn()`
			// so we don't have the opportunity to reset default values in `repr()`. Instead we
			// emit `setValue()` calls above and then call `resetDefault()` here afterwards.
			//
			/// \todo Replace the `shouldResetPlugDefault()` mechanism entirely. It only exists
			/// to allow users to author default values when exporting references and extensions.
			/// But this implicit introduction of new defaults during export is too error-prone.
			/// It's very easy to change values for testing and then forget to change them back
			/// before exporting again. Instead we should just expose `ValuePlug::resetDefault()`
			/// to the user so that they can explicitly set the default at their convenience.
			/// Then we should omit the `setValue()` calls when exporting instead, so that the
			/// user can't inadvertently replace the default they carefully authored.
			result += identifier + ".resetDefault()\n";
		}
	}

	return result;
}
