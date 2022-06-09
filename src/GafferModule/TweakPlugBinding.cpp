//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#include <boost/algorithm/string.hpp>
#include "boost/python.hpp"

#include "TweakPlugBinding.h"

#include "Gaffer/TweakPlug.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/ValuePlugBinding.h"
#include "GafferBindings/SerialisationBinding.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

TweakPlugPtr constructUsingData( const std::string &tweakName, IECore::ConstDataPtr tweakValue, TweakPlug::Mode mode, bool enabled )
{
	return new TweakPlug( tweakName, tweakValue.get(), mode, enabled );
}

bool applyTweak( const TweakPlug &plug, IECore::CompoundData &parameters, TweakPlug::MissingMode missingMode )
{
	IECorePython::ScopedGILRelease gilRelease;
	return plug.applyTweak( &parameters, missingMode );
}

bool applyTweaksToParameters( const TweaksPlug &tweaksPlug, IECore::CompoundData &parameters, TweakPlug::MissingMode missingMode )
{
	IECorePython::ScopedGILRelease gilRelease;
	return tweaksPlug.applyTweaks( &parameters, missingMode );
}

class TweakPlugSerialiser : public ValuePlugSerialiser
{
	bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
	{
		return false;
	}

	std::string constructor( const Gaffer::GraphComponent *graphComponent, Serialisation &serialisation ) const override
	{
		auto tweaksPlug = static_cast<const TweakPlug *>( graphComponent );

		const Serialiser *valuePlugSerialiser = Serialisation::acquireSerialiser( tweaksPlug->valuePlug() );
		std::string result = ValuePlugSerialiser::constructor( graphComponent, serialisation );

		// Pass the value plug into the constructor directly so that there's
		// never a moment in which the TweakPlug is in an invalid state.
		result = boost::algorithm::replace_first_copy(
			result,
			"TweakPlug(",
			"TweakPlug( " + valuePlugSerialiser->constructor( tweaksPlug->valuePlug(), serialisation ) + ","
		);

		return result;
	}
};

} // namespace

void GafferModule::bindTweakPlugs()
{
	PlugClass<TweakPlug> tweakPlugClass;

	{
		scope tweakPlugScope = tweakPlugClass;

		enum_<TweakPlug::Mode>( "Mode" )
			.value( "Replace", TweakPlug::Replace )
			.value( "Add", TweakPlug::Add )
			.value( "Subtract", TweakPlug::Subtract )
			.value( "Multiply", TweakPlug::Multiply )
			.value( "Remove", TweakPlug::Remove )
			.value( "Create", TweakPlug::Create )
		;

		enum_<TweakPlug::MissingMode>( "MissingMode" )
			.value( "Ignore", TweakPlug::MissingMode::Ignore )
			.value( "Error", TweakPlug::MissingMode::Error )
			.value( "IgnoreOrReplace", TweakPlug::MissingMode::IgnoreOrReplace )
		;
	}

	tweakPlugClass
		.def(
			init<ValuePlug *, const char *, Plug::Direction, unsigned>(
				(
					boost::python::arg_( "valuePlug" ),
					boost::python::arg_( "name" )=GraphComponent::defaultName<TweakPlug>(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "flags" )=Plug::Default
				)
			)
		)
		.def(
			"__init__",
			make_constructor(
				constructUsingData,
				default_call_policies(),
				(
					boost::python::arg_( "tweakName" ),
					boost::python::arg_( "valuePlug" ),
					arg( "mode" ) = TweakPlug::Replace,
					boost::python::arg_( "enabled" )=true
				)
			)
		)
		.def(
			init<const std::string &, const ValuePlugPtr, TweakPlug::Mode, bool>(
				(
					boost::python::arg_( "tweakName" ),
					boost::python::arg_( "value" ),
					arg( "mode" ) = TweakPlug::Replace,
					boost::python::arg_( "enabled" )=true
				)
			)
		)
		.def( "applyTweak", &applyTweak, ( arg( "parameters" ), arg( "missingMode" ) = TweakPlug::MissingMode::Error ) )
	;

	Serialisation::registerSerialiser( TweakPlug::staticTypeId(), new TweakPlugSerialiser );

	PlugClass<TweaksPlug>()
		.def(
			init<const std::string &, Plug::Direction, unsigned>(
				(
					boost::python::arg_( "name" )=GraphComponent::defaultName<TweaksPlug>(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "flags" )=Plug::Default
				)
			)
		)
		.def( "applyTweaks", &applyTweaksToParameters, ( arg( "parameters" ), arg( "missingMode" ) = TweakPlug::MissingMode::Error ) )
	;

}
