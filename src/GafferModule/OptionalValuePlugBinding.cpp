//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "OptionalValuePlugBinding.h"

#include "GafferBindings/ValuePlugBinding.h"
#include "Gaffer/OptionalValuePlug.h"

#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/ScopedGILRelease.h"

#include "fmt/format.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

class OptionalValuePlugSerialiser : public ValuePlugSerialiser
{

	public :

		bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
		{
			// The children will be created by the constructor
			return false;
		}

		std::string constructor( const Gaffer::GraphComponent *graphComponent, Serialisation &serialisation ) const override
		{
			return repr( static_cast<const OptionalValuePlug *>( graphComponent ), &serialisation );
		}

		static std::string repr( const Gaffer::OptionalValuePlug *plug, Serialisation *serialisation )
		{
			return fmt::format(
				"Gaffer.OptionalValuePlug( \"{}\", {}, {}, {}, {} )",
				plug->getName().string(),
				Serialisation::acquireSerialiser( plug->valuePlug() )->constructor( plug->valuePlug(), *serialisation ),
				plug->enabledPlug()->defaultValue() ? "True" : "False",
				directionRepr( plug->direction() ),
				flagsRepr( plug->getFlags() )
			);
		}

};

std::string repr( const OptionalValuePlug *plug )
{
	Serialisation tempSerialisation( plug );
	return OptionalValuePlugSerialiser::repr( plug, &tempSerialisation );
}

} // namespace

void GafferModule::bindOptionalValuePlug()
{

	PlugClass<OptionalValuePlug>()
		.def( init<IECore::InternedString, const Gaffer::ValuePlugPtr &, bool, Plug::Direction, unsigned>(
				(
					arg( "name" ) = GraphComponent::defaultName<OptionalValuePlug>(),
					arg( "valuePlug"),
					arg( "enabledPlugDefaultValue" ) = false,
					arg( "direction" ) = Plug::In,
					arg( "flags" ) = Plug::Default
				)
			)
		)
		.def( "__repr__", &repr )
	;

	Serialisation::registerSerialiser( Gaffer::OptionalValuePlug::staticTypeId(), new OptionalValuePlugSerialiser );

}
