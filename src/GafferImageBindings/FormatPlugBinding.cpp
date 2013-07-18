//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

#include "IECore/RunTimeTyped.h"
#include "IECorePython/RunTimeTypedBinding.h"
#include "GafferImage/FormatPlug.h"
#include "GafferImageBindings/FormatBinding.h"
#include "GafferImageBindings/FormatPlugBinding.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferImage;
using namespace GafferImageBindings;

std::string FormatPlugSerialiser::constructor( const Gaffer::GraphComponent *graphComponent ) const
{
	object o( GraphComponentPtr( const_cast<GraphComponent *>( graphComponent ) ) );
	std::string r = extract<std::string>( o.attr( "__repr__" )() );
	return r;
}

void FormatPlugSerialiser::moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules ) const
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

std::string FormatPlugSerialiser::postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
{
	const Plug *plug = static_cast<const Plug *>( graphComponent );
	
	if( plug->direction() == Plug::In && plug->getFlags( Plug::Serialisable ) )
	{
		if( !serialisation.identifier( plug->getInput<Plug>() ).size() )
		{
			object pythonPlug( PlugPtr( const_cast<Plug *>( plug ) ) );
			
			if( PyObject_HasAttrString( pythonPlug.ptr(), "getValue" ) )
			{
				object pythonValue = pythonPlug.attr( "getValue" )();
				std::string value = extract<std::string>( pythonValue.attr( "__repr__" )() );
				
				if ( plug->node()->typeId() == static_cast<IECore::TypeId>(ScriptNodeTypeId) )
				{
					// If this is the default format plug then write out all of the formats.
					std::stringstream addformats;
					std::vector< std::string > names;
					GafferImage::Format::formatNames( names );
					
					for ( std::vector< std::string >::iterator it( names.begin() ); it != names.end(); it++)
					{
						Format f( Format::getFormat(*it) );
						std::string frepr( GafferImageBindings::FormatBindings::formatRepr( &f ) );
						
						addformats << "GafferImage.Format.registerFormat( " << frepr << ", \"" << *it << "\" )" << std::endl;
					}
					
					// Set the default format plug value by calling setDefaultFormat(). This ensures that the plug is created on the context.
					// If we only call setValue() here then any format knob that references the default format which is viewed before the
					// defaultFormat is set will complain of empty display windows when drawing their output. This is becuase an empty Format()
					// will be returned from the context().get() call within the getValue() method of the FormatPlug if the defaultFormat plug
					// doesn't exist on the context.
					return addformats.str() + identifier + ".setValue( " + value + " )\n";
				}
				return identifier + ".setValue( " + value + " )\n";
			}
		}
	}
	return "";
}

void GafferImageBindings::bindFormatPlug()
{
	IECorePython::RunTimeTypedClass<FormatPlug>()
		.def( init<const std::string &, Plug::Direction, const Format &, unsigned>(
				(
					boost::python::arg_( "name" )=GraphComponent::defaultName<FormatPlug>(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "defaultValue" )=Format(),
					boost::python::arg_( "flags" )=Plug::Default
				)
			)
		)
		.GAFFERBINDINGS_DEFPLUGWRAPPERFNS( FormatPlug )
		.def( "defaultValue", &FormatPlug::defaultValue, return_value_policy<copy_const_reference>() )
		.def( "setValue", &FormatPlug::setValue )
		.def( "getValue", &FormatPlug::getValue )
	;
	
	Serialisation::registerSerialiser( static_cast<IECore::TypeId>(FormatPlugTypeId), new FormatPlugSerialiser );
}
