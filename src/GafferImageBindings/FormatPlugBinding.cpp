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

#include "GafferBindings/Serialisation.h"
#include "GafferBindings/ValuePlugBinding.h"

#include "GafferImage/FormatPlug.h"
#include "GafferImageBindings/FormatBinding.h"
#include "GafferImageBindings/FormatPlugBinding.h"

using namespace std;
using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferImage;
using namespace GafferImageBindings;

namespace
{

class FormatPlugSerialiser : public GafferBindings::ValuePlugSerialiser
{

	public :

		virtual void moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules ) const
		{
			ValuePlugSerialiser::moduleDependencies( graphComponent, modules );
			modules.insert( "IECore" );
		}

		virtual std::string constructor( const Gaffer::GraphComponent *graphComponent ) const
		{
			object o( GraphComponentPtr( const_cast<GraphComponent *>( graphComponent ) ) );
			std::string r = extract<std::string>( o.attr( "__repr__" )() );
			return r;
		}

		virtual std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
		{
			std::string result;

			const Plug *plug = static_cast<const Plug *>( graphComponent );
			if( plug->node()->typeId() == static_cast<IECore::TypeId>(ScriptNodeTypeId) )
			{
				// If this is the default format plug then write out all of the formats.
				/// \todo Why do we do this? Unfortunately it's very hard to tell because
				/// there are no unit tests for it. Why don't we allow the config files to
				/// just recreate the formats next time?
				vector<string> names;
				GafferImage::Format::formatNames( names );
				for( vector<string>::const_iterator it = names.begin(), eIt = names.end(); it != eIt; ++it )
				{
					result +=
						"GafferImage.Format.registerFormat( " +
						formatRepr( Format::getFormat( *it ) ) +
						", \"" + *it + "\" )\n";
				}
			}

			result += ValuePlugSerialiser::postConstructor( graphComponent, identifier, serialisation );
			return result;
		}

};

} // namespace

void GafferImageBindings::bindFormatPlug()
{
	PlugClass<FormatPlug>()
		.def( init<const std::string &, Plug::Direction, const Format &, unsigned>(
				(
					boost::python::arg_( "name" )=GraphComponent::defaultName<FormatPlug>(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "defaultValue" )=Format(),
					boost::python::arg_( "flags" )=Plug::Default
				)
			)
		)
		.def( "defaultValue", &FormatPlug::defaultValue, return_value_policy<copy_const_reference>() )
		.def( "setValue", &FormatPlug::setValue )
		.def( "getValue", &FormatPlug::getValue )
	;

	Serialisation::registerSerialiser( static_cast<IECore::TypeId>(FormatPlugTypeId), new FormatPlugSerialiser );
}
