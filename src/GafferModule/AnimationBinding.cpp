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

#include "AnimationBinding.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/ValuePlugBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Animation.h"

#include "boost/lexical_cast.hpp"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

Animation::CurvePlugPtr acquire( ValuePlug *plug )
{
	ScopedGILRelease gilRelease;
	return Animation::acquire( plug );
}

Animation::KeyPtr setTime( Animation::Key &k, float time )
{
	ScopedGILRelease gilRelease;
	return k.setTime( time );
}

void setValue( Animation::Key &k, float value )
{
	ScopedGILRelease gilRelease;
	k.setValue( value );
}

void setInterpolation( Animation::Key &k, Animation::Interpolation interpolation )
{
	ScopedGILRelease gilRelease;
	k.setInterpolation( interpolation );
}

const char *interpolationRepr( const Animation::Interpolation &t )
{
	switch( t )
	{
		case Animation::Interpolation::Step :
			return "Gaffer.Animation.Interpolation.Step";
		case Animation::Interpolation::Linear :
			return "Gaffer.Animation.Interpolation.Linear";
	}

	throw IECore::Exception( "Unknown Animation::Interpolation" );
}

std::string keyRepr( const Animation::Key &k )
{
	return boost::str(
		boost::format( "Gaffer.Animation.Key( %.9g, %.9g, %s )" ) % k.getTime() % k.getValue() % interpolationRepr( k.getInterpolation() )
	);
};

Animation::KeyPtr addKey( Animation::CurvePlug &p, const Animation::KeyPtr &k, const bool removeActiveClashing )
{
	ScopedGILRelease gilRelease;
	return p.addKey( k, removeActiveClashing );
}

Animation::KeyPtr insertKey( Animation::CurvePlug &p, const float time )
{
	ScopedGILRelease gilRelease;
	return p.insertKey( time );
}

Animation::KeyPtr insertKeyValue( Animation::CurvePlug &p, const float time, const float value )
{
	ScopedGILRelease gilRelease;
	return p.insertKey( time, value );
}

void removeKey( Animation::CurvePlug &p, const Animation::KeyPtr &k )
{
	ScopedGILRelease gilRelease;
	p.removeKey( k );
}

void removeInactiveKeys( Animation::CurvePlug &p )
{
	ScopedGILRelease gilRelease;
	p.removeInactiveKeys();
}

struct CurvePlugKeySlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot,
		const Animation::CurvePlugPtr c, const Animation::KeyPtr k )
	{
		try
		{
			slot( c, k );
		}
		catch( const boost::python::error_already_set &e )
		{
			ExceptionAlgo::translatePythonException();
		}
		return boost::signals::detail::unusable();
	}
};

class CurvePlugSerialiser : public ValuePlugSerialiser
{

	public :

		std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const override
		{
			std::string result = ValuePlugSerialiser::postConstructor( graphComponent, identifier, serialisation );
			const Animation::CurvePlug *curve = static_cast<const Animation::CurvePlug *>( graphComponent );
			for( const auto &key : *curve )
			{
				result += identifier + ".addKey( " + keyRepr( key ) + " )\n";
			}
			return result;
		}

};

} // namespace

void GafferModule::bindAnimation()
{

	scope s = DependencyNodeClass<Animation>()
		.def( "canAnimate", &Animation::canAnimate )
		.staticmethod( "canAnimate" )
		.def( "isAnimated", &Animation::isAnimated )
		.staticmethod( "isAnimated" )
		.def( "acquire", &acquire )
		.staticmethod( "acquire" )
		.def( "defaultInterpolation", &Animation::defaultInterpolation )
		.staticmethod( "defaultInterpolation" )
	;

	enum_<Animation::Interpolation>( "Interpolation" )
		.value( Animation::toString( Animation::Interpolation::Step ), Animation::Interpolation::Step )
		.value( Animation::toString( Animation::Interpolation::Linear ), Animation::Interpolation::Linear )
	;

	IECorePython::RunTimeTypedClass< Animation::Key >( "Key" )
		.def( init<float, float, Animation::Interpolation>(
				(
					arg( "time" ) = 0.0f,
					arg( "value" ) = 0.0f,
					arg( "interpolation" ) = Animation::defaultInterpolation()
				)
			)
		)
		.def( "getTime", &Animation::Key::getTime )
		.def( "setTime", &setTime )
		.def( "getValue", &Animation::Key::getValue )
		.def( "setValue", &setValue )
		.def( "getInterpolation", &Animation::Key::getInterpolation )
		.def( "setInterpolation", &setInterpolation )
		.def( "isActive", &Animation::Key::isActive )
		.def( "__repr__", &keyRepr )
		.def( self == self )
		.def( self != self )
		.def(
			"parent",
			(Animation::CurvePlug *(Animation::Key::*)())&Animation::Key::parent,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
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
		.def( "keyAddedSignal", &Animation::CurvePlug::keyAddedSignal, return_internal_reference< 1 >() )
		.def( "keyRemovedSignal", &Animation::CurvePlug::keyRemovedSignal, return_internal_reference< 1 >() )
		.def( "addKey", &addKey, arg( "removeActiveClashing" ) = true )
		.def( "insertKey", &insertKey )
		.def( "insertKey", &insertKeyValue )
		.def( "hasKey", &Animation::CurvePlug::hasKey )
		.def(
			"getKey",
			(Animation::Key *(Animation::CurvePlug::*)( float ))&Animation::CurvePlug::getKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def( "removeKey", &removeKey )
		.def( "removeInactiveKeys", &removeInactiveKeys )
		.def(
			"closestKey",
			(Animation::Key *(Animation::CurvePlug::*)( float ))&Animation::CurvePlug::closestKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def(
			"closestKey",
			(Animation::Key *(Animation::CurvePlug::*)( float, float ))&Animation::CurvePlug::closestKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def(
			"previousKey",
			(Animation::Key *(Animation::CurvePlug::*)( float ))&Animation::CurvePlug::previousKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def(
			"nextKey",
			(Animation::Key *(Animation::CurvePlug::*)( float ))&Animation::CurvePlug::nextKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def( "evaluate", &Animation::CurvePlug::evaluate )
		.attr( "__qualname__" ) = "Animation.CurvePlug"
	;

	SignalClass< Animation::CurvePlug::CurvePlugKeySignal,
		DefaultSignalCaller< Animation::CurvePlug::CurvePlugKeySignal >, CurvePlugKeySlotCaller >( "CurvePlugKeySignal" );

	Serialisation::registerSerialiser( Gaffer::Animation::CurvePlug::staticTypeId(), new CurvePlugSerialiser );

}
