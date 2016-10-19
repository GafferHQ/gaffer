//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/PlugBinding.h"

#include "GafferScene/LightTweaks.h"

#include "GafferSceneBindings/LightTweaksBinding.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;

namespace
{

LightTweaks::TweakPlugPtr constructUsingData( const std::string &tweakName, IECore::ConstDataPtr tweakValue, bool enabled )
{
	return new LightTweaks::TweakPlug( tweakName, tweakValue.get(), enabled );
}

std::string maskedTweakPlugRepr( const LightTweaks::TweakPlug *plug, unsigned flagsMask )
{
	// The only reason we have a different __repr__ implementation than Gaffer::Plug is
	// because we can't determine the nested class name from a PyObject.
	std::string result = "GafferScene.LightTweaks.TweakPlug( \"" + plug->getName().string() + "\", ";

	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + PlugSerialiser::directionRepr( plug->direction() ) + ", ";
	}

	const unsigned flags = plug->getFlags() & flagsMask;
	if( flags != Plug::Default )
	{
		result += "flags = " + PlugSerialiser::flagsRepr( flags ) + ", ";
	}

	result += ")";

	return result;
}

std::string tweakPlugRepr( const LightTweaks::TweakPlug *plug )
{
	return maskedTweakPlugRepr( plug, Plug::All );
}

class TweakPlugSerialiser : public PlugSerialiser
{

	public :

		virtual std::string constructor( const Gaffer::GraphComponent *graphComponent, const Serialisation &serialisation ) const
		{
			return maskedTweakPlugRepr( static_cast<const LightTweaks::TweakPlug *>( graphComponent ), Plug::All & ~Plug::ReadOnly );
		}

		virtual bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const
		{
			// If the parent is dynamic then all the children will need construction.
			const Plug *parent = child->parent<Plug>();
			return parent->getFlags( Gaffer::Plug::Dynamic );
		}

};

} // namespace

void GafferSceneBindings::bindLightTweaks()
{
	scope lightTweaksScope = DependencyNodeClass<LightTweaks>();

	scope tweakPlugScope = PlugClass<LightTweaks::TweakPlug>()
		.def(
			init<const char *, Plug::Direction, unsigned>(
				(
					boost::python::arg_( "name" )=GraphComponent::defaultName<LightTweaks::TweakPlug>(),
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
					boost::python::arg_( "tweakValuePlug" ),
					boost::python::arg_( "enabled" )=true
				)
			)
		)
		.def(
			init<const std::string &, const ValuePlugPtr, bool>(
				(
					boost::python::arg_( "tweakName" ),
					boost::python::arg_( "tweakValue" ),
					boost::python::arg_( "enabled" )=true
				)
			)
		)
		.def( "__repr__", tweakPlugRepr )
	;

	enum_<LightTweaks::TweakPlug::Mode>( "Mode" )
		.value( "Replace", LightTweaks::TweakPlug::Replace )
		.value( "Add", LightTweaks::TweakPlug::Add )
		.value( "Subtract", LightTweaks::TweakPlug::Subtract )
		.value( "Multiply", LightTweaks::TweakPlug::Multiply )
	;

	Serialisation::registerSerialiser( LightTweaks::TweakPlug::staticTypeId(), new TweakPlugSerialiser );

}
