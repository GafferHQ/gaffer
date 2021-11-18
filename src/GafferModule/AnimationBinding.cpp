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

#include <cmath>

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

Animation::CurvePlugPtr acquire( ValuePlug* const plug )
{
	ScopedGILRelease gilRelease;
	return Animation::acquire( plug );
}

Animation::KeyPtr setTime( Animation::Key &k, const float time )
{
	ScopedGILRelease gilRelease;
	return k.setTime( time );
}

void setValue( Animation::Key &k, const float value )
{
	ScopedGILRelease gilRelease;
	k.setValue( value );
}

void setInterpolation( Animation::Key &k, const Animation::Interpolation interpolation )
{
	ScopedGILRelease gilRelease;
	k.setInterpolation( interpolation );
}

Animation::Key* getKey( Animation::Tangent &t )
{
	return &( t.key() );
}

void setSlope( Animation::Tangent &t, const double slope )
{
	ScopedGILRelease gilRelease;
	t.setSlope( slope );
}

void setSlopeFromPosition( Animation::Tangent &t, const Imath::V2d& position, const bool relative )
{
	ScopedGILRelease gilRelease;
	t.setSlopeFromPosition( position, relative );
}

void setSlopeAndScale( Animation::Tangent &t, const double slope, const double scale )
{
	ScopedGILRelease gilRelease;
	t.setSlopeAndScale( slope, scale );
}

void setScale( Animation::Tangent &t, const double scale )
{
	ScopedGILRelease gilRelease;
	t.setScale( scale );
}

void setScaleFromPosition( Animation::Tangent &t, const Imath::V2d& position, const bool relative )
{
	ScopedGILRelease gilRelease;
	t.setScaleFromPosition( position, relative );
}

Imath::V2d getPosition( Animation::Tangent &t, const bool relative )
{
	return t.getPosition( relative );
}

void setPosition( Animation::Tangent &t, const Imath::V2d& position, const bool relative )
{
	ScopedGILRelease gilRelease;
	t.setPosition( position, relative );
}

std::string slopeRepr( const double slope )
{
	return boost::str( boost::format( ( ( std::isinf( slope ) ) ? "float( '%.9g' )" : "%.9g" ) ) % slope );
}

void setTieMode( Animation::Key &k, const Animation::TieMode mode )
{
	ScopedGILRelease gilRelease;
	k.setTieMode( mode );
}

std::string keyRepr( const Animation::Key &k )
{
	return boost::str( boost::format(
		"Gaffer.Animation.Key( %.9g, %.9g, Gaffer.Animation.Interpolation.%s, %s, %.9g, %s, %.9g, Gaffer.Animation.TieMode.%s )" )
			% k.getTime()
			% k.getValue()
			% Animation::toString( k.getInterpolation() )
			% slopeRepr( k.tangentIn().getSlope() )
			% k.tangentIn().getScale()
			% slopeRepr( k.tangentOut().getSlope() )
			% k.tangentOut().getScale()
			% Animation::toString( k.getTieMode() )
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

void setExtrapolationIn( Animation::CurvePlug &p, const Animation::Extrapolation extrapolation )
{
	ScopedGILRelease gilRelease;
	p.setExtrapolationIn( extrapolation );
}

void setExtrapolationOut( Animation::CurvePlug &p, const Animation::Extrapolation extrapolation )
{
	ScopedGILRelease gilRelease;
	p.setExtrapolationOut( extrapolation );
}

void setExtrapolation( Animation::CurvePlug &p, const Animation::Direction direction, const Animation::Extrapolation extrapolation )
{
	ScopedGILRelease gilRelease;
	p.setExtrapolation( direction, extrapolation );
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

struct CurvePlugDirectionSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot,
		const Animation::CurvePlugPtr c, const Animation::Direction d )
	{
		try
		{
			slot( c, d );
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
			const Animation::CurvePlug* const curve = static_cast<const Animation::CurvePlug *>( graphComponent );
			result += identifier + ".setExtrapolationIn( Gaffer.Animation.Extrapolation." + Animation::toString( curve->getExtrapolationIn() ) + " )\n";
			result += identifier + ".setExtrapolationOut( Gaffer.Animation.Extrapolation." + Animation::toString( curve->getExtrapolationOut() ) + " )\n";
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

	scope s = DependencyNodeClass< Animation >()
		.def( "canAnimate", &Animation::canAnimate )
		.staticmethod( "canAnimate" )
		.def( "isAnimated", &Animation::isAnimated )
		.staticmethod( "isAnimated" )
		.def( "acquire", &acquire )
		.staticmethod( "acquire" )
		.def( "defaultInterpolation", &Animation::defaultInterpolation )
		.staticmethod( "defaultInterpolation" )
		.def( "defaultExtrapolation", &Animation::defaultExtrapolation )
		.staticmethod( "defaultExtrapolation" )
		.def( "defaultTieMode", &Animation::defaultTieMode )
		.staticmethod( "defaultTieMode" )
		.def( "defaultSlope", &Animation::defaultSlope )
		.staticmethod( "defaultSlope" )
		.def( "defaultScale", &Animation::defaultScale )
		.staticmethod( "defaultScale" )
		.def( "opposite", &Animation::opposite )
		.staticmethod( "opposite" )
	;

	enum_< Animation::Interpolation >( "Interpolation" )
		.value( Animation::toString( Animation::Interpolation::Constant ), Animation::Interpolation::Constant )
		.value( Animation::toString( Animation::Interpolation::ConstantNext ), Animation::Interpolation::ConstantNext )
		.value( Animation::toString( Animation::Interpolation::Linear ), Animation::Interpolation::Linear )
		.value( Animation::toString( Animation::Interpolation::Cubic ), Animation::Interpolation::Cubic )
		.value( Animation::toString( Animation::Interpolation::Bezier ), Animation::Interpolation::Bezier )
	;

	enum_< Animation::Extrapolation >( "Extrapolation" )
		.value( Animation::toString( Animation::Extrapolation::Constant ), Animation::Extrapolation::Constant )
	;

	enum_< Animation::Direction >( "Direction" )
		.value( Animation::toString( Animation::Direction::In ), Animation::Direction::In )
		.value( Animation::toString( Animation::Direction::Out ), Animation::Direction::Out )
	;

	enum_< Animation::TieMode >( "TieMode" )
		.value( Animation::toString( Animation::TieMode::Manual ), Animation::TieMode::Manual )
		.value( Animation::toString( Animation::TieMode::Slope ), Animation::TieMode::Slope )
		.value( Animation::toString( Animation::TieMode::Scale ), Animation::TieMode::Scale )
	;

	class_< Animation::Tangent, boost::noncopyable >( "Tangent", no_init )
		.def( "key", &getKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def( "direction", &Animation::Tangent::direction )
		.def( "setSlope", &setSlope )
		.def( "setSlopeFromPosition", setSlopeFromPosition, ( arg( "position" ), arg( "relative" ) = false ) )
		.def( "getSlope", (double (Animation::Tangent::*)() const)&Animation::Tangent::getSlope )
		.def( "setScale", &setScale )
		.def( "setScaleFromPosition", setScaleFromPosition, ( arg( "position" ), arg( "relative" ) = false ) )
		.def( "getScale", (double (Animation::Tangent::*)() const)&Animation::Tangent::getScale )
		.def( "setSlopeAndScale", &setSlopeAndScale )
		.def( "setPosition", &setPosition, ( arg( "position" ), arg( "relative" ) = false ) )
		.def( "getPosition", &getPosition, arg( "relative" ) = false )
		.def( "slopeIsConstrained", &Animation::Tangent::slopeIsConstrained )
		.def( "scaleIsConstrained", &Animation::Tangent::scaleIsConstrained )
		;

	IECorePython::RunTimeTypedClass< Animation::Key >( "Key" )
		.def( init< float, float, Animation::Interpolation, double, double, double, double, Animation::TieMode >(
				(
					arg( "time" ) = 0.0f,
					arg( "value" ) = 0.0f,
					arg( "interpolation" ) = Animation::defaultInterpolation(),
					arg( "inSlope" ) = Animation::defaultSlope(),
					arg( "inScale" ) = Animation::defaultScale(),
					arg( "outSlope" ) = Animation::defaultSlope(),
					arg( "outScale" ) = Animation::defaultScale(),
					arg( "tieMode" ) = Animation::defaultTieMode()
				)
			)
		)
		.def( "getTime", &Animation::Key::getTime )
		.def( "setTime", &setTime )
		.def( "getValue", &Animation::Key::getValue )
		.def( "setValue", &setValue )
		.def( "getInterpolation", &Animation::Key::getInterpolation )
		.def( "setInterpolation", &setInterpolation )
		.def( "tangentIn",
			(Animation::Tangent& (Animation::Key::*)())&Animation::Key::tangentIn,
			return_internal_reference<>() )
		.def( "tangentOut",
			(Animation::Tangent& (Animation::Key::*)())&Animation::Key::tangentOut,
			return_internal_reference<>() )
		.def( "tangent",
			(Animation::Tangent& (Animation::Key::*)( Animation::Direction ))&Animation::Key::tangent,
			return_internal_reference<>() )
		.def( "setTieMode", &setTieMode )
		.def( "getTieMode", &Animation::Key::getTieMode )
		.def( "isActive", &Animation::Key::isActive )
		.def( "__repr__", &keyRepr )
		.def(
			"parent",
			(Animation::CurvePlug *(Animation::Key::*)())&Animation::Key::parent,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
	;

	PlugClass< Animation::CurvePlug >()
		.def( init< const char *, Plug::Direction, unsigned >(
				(
					boost::python::arg_( "name" )=GraphComponent::defaultName<Animation::CurvePlug>(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "flags" )=Plug::Default
				)
			)
		)
		.def( "keyAddedSignal", &Animation::CurvePlug::keyAddedSignal, return_internal_reference< 1 >() )
		.def( "keyRemovedSignal", &Animation::CurvePlug::keyRemovedSignal, return_internal_reference< 1 >() )
		.def( "keyTimeChangedSignal", &Animation::CurvePlug::keyTimeChangedSignal, return_internal_reference< 1 >() )
		.def( "keyValueChangedSignal", &Animation::CurvePlug::keyValueChangedSignal, return_internal_reference< 1 >() )
		.def( "keyInterpolationChangedSignal", &Animation::CurvePlug::keyInterpolationChangedSignal, return_internal_reference< 1 >() )
		.def( "keyTieModeChangedSignal", &Animation::CurvePlug::keyTieModeChangedSignal, return_internal_reference< 1 >() )
		.def( "extrapolationChangedSignal", &Animation::CurvePlug::extrapolationChangedSignal, return_internal_reference< 1 >() )
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
		.def( "getExtrapolationIn", &Animation::CurvePlug::getExtrapolationIn )
		.def( "setExtrapolationIn", &setExtrapolationIn )
		.def( "getExtrapolationOut", &Animation::CurvePlug::getExtrapolationOut )
		.def( "setExtrapolationOut", &setExtrapolationOut )
		.def( "getExtrapolation", &Animation::CurvePlug::getExtrapolation )
		.def( "setExtrapolation", &setExtrapolation )
		.def( "evaluate", &Animation::CurvePlug::evaluate )
		.attr( "__qualname__" ) = "Animation.CurvePlug"
	;

	SignalClass< Animation::CurvePlug::CurvePlugKeySignal,
		DefaultSignalCaller< Animation::CurvePlug::CurvePlugKeySignal >, CurvePlugKeySlotCaller >( "CurvePlugKeySignal" );

	SignalClass< Animation::CurvePlug::CurvePlugDirectionSignal,
		DefaultSignalCaller< Animation::CurvePlug::CurvePlugDirectionSignal >, CurvePlugDirectionSlotCaller >( "CurvePlugDirectionSignal" );

	Serialisation::registerSerialiser( Gaffer::Animation::CurvePlug::staticTypeId(), new CurvePlugSerialiser );

}
