//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
#include "boost/lexical_cast.hpp"

#include "Gaffer/Animation.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/ValuePlugBinding.h"
#include "GafferBindings/AnimationBinding.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

const char *typeRepr( const Animation::Type &t )
{
	switch( t )
	{
		case Animation::Step :
			return "Gaffer.Animation.Type.Step";
		case Animation::Linear :
			return "Gaffer.Animation.Type.Linear";
		default :
			return "Gaffer.Animation.Type.Invalid";
	}
}

std::string keyRepr( const Animation::Key &k )
{
	if( !k )
	{
		return "Gaffer.Animation.Key()";
	}
	return boost::str(
		boost::format( "Gaffer.Animation.Key( %f, %f, %s )" ) % k.time % k.value % typeRepr( k.type )
	);
};

class CurvePlugSerialiser : public ValuePlugSerialiser
{

	public :

		virtual std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
		{
			std::string result = ValuePlugSerialiser::postConstructor( graphComponent, identifier, serialisation );
			const Animation::CurvePlug *curve = static_cast<const Animation::CurvePlug *>( graphComponent );

			for( std::set<Animation::Key>::const_iterator it = curve->keys().begin(), eIt = curve->keys().end(); it != eIt; ++it )
			{
				result += identifier + ".addKey( " + keyRepr( *it ) + " )\n";
			}

			return result;
		}

};

} // namespace

void GafferBindings::bindAnimation()
{

	scope s = DependencyNodeClass<Animation>()
		.def( "canAnimate", &Animation::canAnimate )
		.staticmethod( "canAnimate" )
		.def( "isAnimated", &Animation::isAnimated )
		.staticmethod( "isAnimated" )
		.def( "acquire", &Animation::acquire, return_value_policy<CastToIntrusivePtr>() )
		.staticmethod( "acquire" )
	;

	enum_<Animation::Type>( "Type" )
		.value( "Invalid", Animation::Invalid )
		.value( "Step", Animation::Step )
		.value( "Linear", Animation::Linear )
	;

	class_<Animation::Key>( "Key" )
		.def( init<const Animation::Key &>() )
		.def( init<float, float, Animation::Type>(
				(
					arg( "time" ),
					arg( "value" ) = 0.0f,
					arg( "type" ) = Animation::Linear
				)
			)
		)
		.def_readwrite( "time", &Animation::Key::time )
		.def_readwrite( "value", &Animation::Key::value )
		.def_readwrite( "type", &Animation::Key::type )
		.def( "__repr__", &keyRepr )
		.def( self == self )
		.def( self != self )
		.def( !self )
	;

	PlugClass<Animation::CurvePlug>()
		.def( init<const char *, Plug::Direction, unsigned>(
				(
					boost::python::arg_( "name" )=GraphComponent::defaultName<Animation::CurvePlug>(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "flags" )=Plug::Default
				)
			)
		)
		.def( "addKey", &Animation::CurvePlug::addKey )
		.def( "hasKey", &Animation::CurvePlug::hasKey )
		.def( "getKey", &Animation::CurvePlug::getKey )
		.def( "removeKey", &Animation::CurvePlug::removeKey )
		.def( "closestKey", &Animation::CurvePlug::closestKey )
		.def( "previousKey", &Animation::CurvePlug::previousKey )
		.def( "nextKey", &Animation::CurvePlug::nextKey )
		.def( "evaluate", &Animation::CurvePlug::evaluate )
		// Adjusting the name so that it correctly reflects
		// the nesting, and can be used by the PlugSerialiser.
		.attr( "__name__" ) = "Animation.CurvePlug"
	;

	Serialisation::registerSerialiser( Gaffer::Animation::CurvePlug::staticTypeId(), new CurvePlugSerialiser );

}
