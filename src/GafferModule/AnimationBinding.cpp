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

void setFloatTime( Animation::Key &k, float time )
{
	ScopedGILRelease gilRelease;
	k.setTime( time );
}

void setTime( Animation::Key &k, const Animation::Time& time )
{
	ScopedGILRelease gilRelease;
	k.setTime( time );
}

void setValue( Animation::Key &k, float value )
{
	ScopedGILRelease gilRelease;
	k.setValue( value );
}

void setType( Animation::Key &k, Animation::Type type )
{
	ScopedGILRelease gilRelease;
	k.setType( type );
}

void setInterpolator( Animation::Key &k, const std::string& name )
{
	ScopedGILRelease gilRelease;
	k.setInterpolator( name );
}

Animation::Key* getKey( Animation::Tangent &t )
{
	return &( t.getKey() );
}

void setPosition( Animation::Tangent &t, const Imath::V2d& position, Animation::Tangent::Space space, bool relative )
{
	ScopedGILRelease gilRelease;
	t.setPosition( position, space, relative );
}

void setPositionWithSlope( Animation::Tangent &t, const Imath::V2d& position, double slope, Animation::Tangent::Space space, bool relative )
{
	ScopedGILRelease gilRelease;
	t.setPositionWithSlope( position, slope, space, relative );
}

void setPositionWithAccel( Animation::Tangent &t, const Imath::V2d& position, double accel, Animation::Tangent::Space space, bool relative )
{
	ScopedGILRelease gilRelease;
	t.setPositionWithAccel( position, accel, space, relative );
}

void setSlope( Animation::Tangent &t, double slope, Animation::Tangent::Space space )
{
	ScopedGILRelease gilRelease;
	t.setSlope( slope, space );
}

void setSlopeWithAccel( Animation::Tangent &t, double slope, double accel, Animation::Tangent::Space space )
{
	ScopedGILRelease gilRelease;
	t.setSlopeWithAccel( slope, accel, space );
}

void setAccel( Animation::Tangent &t, double accel, Animation::Tangent::Space space )
{
	ScopedGILRelease gilRelease;
	t.setAccel( accel, space );
}

void setTieMode( Animation::Key &k, Animation::Tangent::TieMode mode )
{
	ScopedGILRelease gilRelease;
	k.setTieMode( mode );
}

Animation::Interpolator::Factory* getInterpolatorFactory()
{
	return &( Animation::Interpolator::getFactory() );
}

boost::python::list getInterpolatorNames( Animation::Interpolator::Factory& factory )
{
	boost::python::list names;
	for( std::uint32_t i = 0; i < factory.count(); ++i )
	{
		names.append( factory.get( i )->getName() );
	}
	return names;
}

std::string keyRepr( const Animation::Key &k )
{
	// NOTE : slope may be (+/-) infinity which is represented in python as float( 'inf' ) or float( '-inf' )

	const Animation::Tangent::Space space = Animation::Tangent::Space::Key;

	return boost::str(
		boost::format( "Gaffer.Animation.Key( Gaffer.Animation.Time( %d ), %.9g, \"%s\", "
			"float( '%.9g' ), Gaffer.Animation.Tangent.Space.%s, %.9g, Gaffer.Animation.Tangent.Space.%s, "
			"float( '%.9g' ), Gaffer.Animation.Tangent.Space.%s, %.9g, Gaffer.Animation.Tangent.Space.%s, "
			"Gaffer.Animation.Tangent.TieMode.%s )" )
			% k.getTime().getTicks()
			% k.getValue()
			% k.getInterpolator()->getName()
			% k.getTangent( Animation::Tangent::Direction::Into ).getSlope( space )
			% Animation::toString( space )
			% k.getTangent( Animation::Tangent::Direction::Into ).getAccel( space )
			% Animation::toString( space )
			% k.getTangent( Animation::Tangent::Direction::From ).getSlope( space )
			% Animation::toString( space )
			% k.getTangent( Animation::Tangent::Direction::From ).getAccel( space )
			% Animation::toString( space )
			% Animation::toString( k.getTieMode() )
	);
};

void addKey( Animation::CurvePlug &p, const Animation::KeyPtr &k )
{
	ScopedGILRelease gilRelease;
	p.addKey( k );
}

void addKeyInherit( Animation::CurvePlug &p, const Animation::KeyPtr &k, const bool inherit )
{
	ScopedGILRelease gilRelease;
	p.addKey( k, inherit );
}

Animation::Key* insertKey( Animation::CurvePlug &p, const Animation::Time& time )
{
	ScopedGILRelease gilRelease;
	return p.insertKey( time );
}

void removeKey( Animation::CurvePlug &p, const Animation::KeyPtr &k )
{
	ScopedGILRelease gilRelease;
	p.removeKey( k );
}

struct CurvePlugSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot,
		const Animation::CurvePlugPtr c )
	{
		try
		{
			slot( c );
		}
		catch( const error_already_set &e )
		{
			ExceptionAlgo::translatePythonException();
		}
		return boost::signals::detail::unusable();
	}
};

struct CurvePlugDirectionSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot,
		const Animation::CurvePlugPtr c, const Animation::Tangent::Direction d )
	{
		try
		{
			slot( c, d );
		}
		catch( const error_already_set &e )
		{
			ExceptionAlgo::translatePythonException();
		}
		return boost::signals::detail::unusable();
	}
};

struct CurvePlugKeySlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot,
		const Animation::CurvePlugPtr c, const Animation::KeyPtr k )
	{
		try
		{
			slot( c, k );
		}
		catch( const error_already_set &e )
		{
			ExceptionAlgo::translatePythonException();
		}
		return boost::signals::detail::unusable();
	}
};

struct CurvePlugKeyDirectionSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot,
		const Animation::CurvePlugPtr c, const Animation::KeyPtr k, const Animation::Tangent::Direction d )
	{
		try
		{
			slot( c, k, d );
		}
		catch( const error_already_set &e )
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

	scope s = DependencyNodeClass< Animation >()
		.def( "canAnimate", &Animation::canAnimate )
		.staticmethod( "canAnimate" )
		.def( "isAnimated", &Animation::isAnimated )
		.staticmethod( "isAnimated" )
		.def( "acquire", &acquire )
		.staticmethod( "acquire" )
		.def( "equivalentValues", &Animation::equivalentValues )
		.staticmethod( "equivalentValues" )
	;

	enum_<Animation::Type>( "Type" )
		.value( Animation::toString( Animation::Step ), Animation::Step )
		.value( Animation::toString( Animation::Linear ), Animation::Linear )
		.value( Animation::toString( Animation::Unknown ), Animation::Unknown )
	;

	{
		scope s = class_< Animation::Time >( "Time", init<>() )
			.def( init< std::int64_t >() )
			.def( init< double, Animation::Time::Units >() )
			.def( init< double, double >() )
			.def( "getSeconds", &Animation::Time::getSeconds )
			.def( "getReal", &Animation::Time::getReal )
			.def( "getTicks", &Animation::Time::getTicks )
			.def( "snap", &Animation::Time::snap )
			// NOTE : https://bugs.llvm.org/show_bug.cgi?id=43124
#			ifdef __clang__
#			pragma GCC diagnostic push
#			pragma GCC diagnostic ignored "-Wself-assign-overloaded"
#			endif
			.def( self += self )
			.def( self -= self )
			.def( self /= self )
			.def( self %= self )
			.def( self <= self )
			.def( self >= self )
#			ifdef __clang__
#			pragma GCC diagnostic pop
#			endif
			.def( self +  self )
			.def( self -  self )
			.def( self /  self )
			.def( self %  self )
			.def( self == self )
			.def( self != self )
			.def( self <  self )
			.def( self >  self )
			;

		enum_< Animation::Time::Units >( "Units" )
			.value( Animation::toString( Animation::Time::Units::Seconds ), Animation::Time::Units::Seconds )
			.value( Animation::toString( Animation::Time::Units::Fps24 ), Animation::Time::Units::Fps24 )
			.value( Animation::toString( Animation::Time::Units::Fps25 ), Animation::Time::Units::Fps25 )
			.value( Animation::toString( Animation::Time::Units::Fps48 ), Animation::Time::Units::Fps48 )
			.value( Animation::toString( Animation::Time::Units::Fps60 ), Animation::Time::Units::Fps60 )
			.value( Animation::toString( Animation::Time::Units::Fps90 ), Animation::Time::Units::Fps90 )
			.value( Animation::toString( Animation::Time::Units::Fps120 ), Animation::Time::Units::Fps120 )
			.value( Animation::toString( Animation::Time::Units::Milli ), Animation::Time::Units::Milli )
			.value( Animation::toString( Animation::Time::Units::Ticks ), Animation::Time::Units::Ticks );
	}

	{
		scope s = IECorePython::RefCountedClass< Animation::Interpolator, IECore::RefCounted >( "Interpolator" )
			.def( "getName", &Animation::Interpolator::getName,
				return_value_policy<copy_const_reference>() )
			.def( "getHints", &Animation::Interpolator::getHints )
			.def( "getFactory", &getInterpolatorFactory,
				return_value_policy<IECorePython::CastToIntrusivePtr>() )
			.staticmethod( "getFactory" )
			;

		enum_< Animation::Interpolator::Hint >( "Hint" )
			.value( "UseSlopeLo", Animation::Interpolator::Hint::UseSlopeLo )
			.value( "UseSlopeHi", Animation::Interpolator::Hint::UseSlopeHi )
			.value( "UseAccelLo", Animation::Interpolator::Hint::UseAccelLo )
			.value( "UseAccelHi", Animation::Interpolator::Hint::UseAccelHi );

		class_< Animation::Interpolator::Hints >( "Hints", no_init )
			.def( "test", &Animation::Interpolator::Hints::test )
			;

		IECorePython::RefCountedClass< Animation::Interpolator::Factory, IECore::RefCounted >( "Factory" )
			.def( "getNames", &getInterpolatorNames )
			.def( "get",
				(Animation::Interpolator* (Animation::Interpolator::Factory::*)( std::uint32_t )) &Animation::Interpolator::Factory::get,
				return_value_policy<IECorePython::CastToIntrusivePtr>() )
			.def( "get",
				(Animation::Interpolator* (Animation::Interpolator::Factory::*)( const std::string& )) &Animation::Interpolator::Factory::get,
				return_value_policy<IECorePython::CastToIntrusivePtr>() )
			.def( "getDefault", &Animation::Interpolator::Factory::getDefault,
				return_value_policy<IECorePython::CastToIntrusivePtr>() )
			;
	}

	{
		scope s = class_< Animation::Tangent, boost::noncopyable >( "Tangent", no_init )
			.def( "getKey", &getKey,
				return_value_policy<IECorePython::CastToIntrusivePtr>()
			)
			.def( "getDirection", &Animation::Tangent::getDirection )
			.def( "setPosition", &setPosition )
			.def( "setPositionWithSlope", &setPositionWithSlope )
			.def( "setPositionWithAccel", &setPositionWithAccel )
			.def( "getPosition", &Animation::Tangent::getPosition )
			.def( "setSlope", &setSlope )
			.def( "setSlopeWithAccel", &setSlopeWithAccel )
			.def( "getSlope", &Animation::Tangent::getSlope )
			.def( "slopeIsUsed", &Animation::Tangent::slopeIsUsed )
			.def( "setAccel", &setAccel )
			.def( "getAccel", &Animation::Tangent::getAccel )
			.def( "accelIsUsed", &Animation::Tangent::accelIsUsed )
			.def( "opposite", &Animation::Tangent::opposite )
			.staticmethod( "opposite" )
			;

		enum_< Animation::Tangent::Direction >( "Direction" )
			.value( Animation::toString( Animation::Tangent::Direction::Into ), Animation::Tangent::Direction::Into )
			.value( Animation::toString( Animation::Tangent::Direction::From ), Animation::Tangent::Direction::From );

		enum_< Animation::Tangent::Space >( "Space" )
			.value( Animation::toString( Animation::Tangent::Space::Key ), Animation::Tangent::Space::Key )
			.value( Animation::toString( Animation::Tangent::Space::Span ), Animation::Tangent::Space::Span );
		
		enum_< Animation::Tangent::TieMode >( "TieMode" )
			.value( Animation::toString( Animation::Tangent::TieMode::Manual ), Animation::Tangent::TieMode::Manual )
			.value( Animation::toString( Animation::Tangent::TieMode::Slope ), Animation::Tangent::TieMode::Slope )
			.value( Animation::toString( Animation::Tangent::TieMode::SlopeAndAccel ), Animation::Tangent::TieMode::SlopeAndAccel );
	}

	IECorePython::RefCountedClass< Animation::Key, IECore::RefCounted >( "Key" )
		.def( init< float, float, Animation::Type >(
				(
					arg( "time" ) = 0.0f,
					arg( "value" ) = 0.0f,
					arg( "type" ) = Animation::Linear
				)
			)
		)
		.def( init< const Animation::Time&, float, const std::string& >(
				(
					arg( "time" ) = Animation::Time(),
					arg( "value" ) = 0.0f,
					arg( "interpolator" ) = Animation::Interpolator::getFactory().getDefault()->getName()
				)
			)
		)
		.def( init< const Animation::Time&, float, const std::string&,
			double, Animation::Tangent::Space, double, Animation::Tangent::Space,
			double, Animation::Tangent::Space, double, Animation::Tangent::Space,
			Animation::Tangent::TieMode >() )
		.def( "getFloatTime", &Animation::Key::getFloatTime )
		.def( "getTime",
			(Animation::Time (Animation::Key::*)() const)&Animation::Key::getTime ) // TODO : this now returns an Animation.Time ...
		.def( "setTime", &setFloatTime )
		.def( "setTime", &setTime )
		.def( "getValue", &Animation::Key::getValue )
		.def( "setValue", &setValue )
		.def( "getType", &Animation::Key::getType )
		.def( "setType", &setType )
		.def( "getInterpolator",
			(Animation::Interpolator* (Animation::Key::*)())&Animation::Key::getInterpolator,
			return_value_policy<IECorePython::CastToIntrusivePtr>() )
		.def( "setInterpolator", &setInterpolator )
		.def( "getTangent",
			(Animation::Tangent& (Animation::Key::*)( Animation::Tangent::Direction ))&Animation::Key::getTangent,
			return_internal_reference<>() )
		.def( "setTieMode", &setTieMode )
		.def( "getTieMode", &Animation::Key::getTieMode )
		.def( "__repr__", &keyRepr )
		.def( self == self )
		.def( self != self )
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
		.def( "colorChangedSignal", &Animation::CurvePlug::colorChangedSignal, return_internal_reference< 1 >() )
		.def( "extrapolatorChangedSignal", &Animation::CurvePlug::extrapolatorChangedSignal, return_internal_reference< 1 >() )
		.def( "keyAddedSignal", &Animation::CurvePlug::keyAddedSignal, return_internal_reference< 1 >() )
		.def( "keyRemovedSignal", &Animation::CurvePlug::keyRemovedSignal, return_internal_reference< 1 >() )
		.def( "keyTimeChangedSignal", &Animation::CurvePlug::keyTimeChangedSignal, return_internal_reference< 1 >() )
		.def( "keyValueChangedSignal", &Animation::CurvePlug::keyValueChangedSignal, return_internal_reference< 1 >() )
		.def( "keyTieModeChangedSignal", &Animation::CurvePlug::keyTieModeChangedSignal, return_internal_reference< 1 >() )
		.def( "keyInterpolatorChangedSignal", &Animation::CurvePlug::keyInterpolatorChangedSignal, return_internal_reference< 1 >() )
		.def( "keyTangentSlopeChangedSignal", &Animation::CurvePlug::keyTangentSlopeChangedSignal, return_internal_reference< 1 >() )
		.def( "keyTangentAccelChangedSignal", &Animation::CurvePlug::keyTangentAccelChangedSignal, return_internal_reference< 1 >() )
		.def( "keyTangentAutoModeChangedSignal", &Animation::CurvePlug::keyTangentAutoModeChangedSignal, return_internal_reference< 1 >() )
		.def( "addKey", &addKey )
		.def( "addKey", &addKeyInherit )
		.def( "insertKey", &insertKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>() )
		.def( "hasKey",
			(bool (Animation::CurvePlug::*)( float ) const)&Animation::CurvePlug::hasKey )
		.def( "hasKey",
			(bool (Animation::CurvePlug::*)( const Animation::Time& ) const)&Animation::CurvePlug::hasKey )
		.def(
			"getKey",
			(Animation::Key *(Animation::CurvePlug::*)( float ))&Animation::CurvePlug::getKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def(
			"getKey",
			(Animation::Key *(Animation::CurvePlug::*)( const Animation::Time& ))&Animation::CurvePlug::getKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def( "removeKey", &removeKey )
		.def(
			"closestKey",
			(Animation::Key *(Animation::CurvePlug::*)( float ))&Animation::CurvePlug::closestKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def(
			"closestKey",
			(Animation::Key *(Animation::CurvePlug::*)( const Animation::Time& ))&Animation::CurvePlug::closestKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def(
			"closestKey",
			(Animation::Key *(Animation::CurvePlug::*)( float, float ))&Animation::CurvePlug::closestKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def(
			"closestKey",
			(Animation::Key *(Animation::CurvePlug::*)( const Animation::Time&, float ))&Animation::CurvePlug::closestKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def(
			"previousKey",
			(Animation::Key *(Animation::CurvePlug::*)( float ))&Animation::CurvePlug::previousKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def(
			"previousKey",
			(Animation::Key *(Animation::CurvePlug::*)( const Animation::Time& ))&Animation::CurvePlug::previousKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def(
			"nextKey",
			(Animation::Key *(Animation::CurvePlug::*)( float ))&Animation::CurvePlug::nextKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def(
			"nextKey",
			(Animation::Key *(Animation::CurvePlug::*)( const Animation::Time& ))&Animation::CurvePlug::nextKey,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def( "evaluate",
			(float (Animation::CurvePlug::*)( float ) const)&Animation::CurvePlug::evaluate )
		.def( "evaluate",
			(float (Animation::CurvePlug::*)( const Animation::Time& ) const)&Animation::CurvePlug::evaluate )
		.attr( "__qualname__" ) = "Animation.CurvePlug"
	;

	SignalClass< Animation::CurvePlug::CurvePlugSignal,
		DefaultSignalCaller< Animation::CurvePlug::CurvePlugSignal >, CurvePlugSlotCaller >( "CurvePlugSignal" );

	SignalClass< Animation::CurvePlug::CurvePlugDirectionSignal,
		DefaultSignalCaller< Animation::CurvePlug::CurvePlugDirectionSignal >, CurvePlugDirectionSlotCaller >( "CurvePlugDirectionSignal" );

	SignalClass< Animation::CurvePlug::CurvePlugKeySignal,
		DefaultSignalCaller< Animation::CurvePlug::CurvePlugKeySignal >, CurvePlugKeySlotCaller >( "CurvePlugKeySignal" );

	SignalClass< Animation::CurvePlug::CurvePlugKeyDirectionSignal,
		DefaultSignalCaller< Animation::CurvePlug::CurvePlugKeyDirectionSignal >, CurvePlugKeyDirectionSlotCaller >( "CurvePlugKeyDirectionSignal" );

	Serialisation::registerSerialiser( Gaffer::Animation::CurvePlug::staticTypeId(), new CurvePlugSerialiser );

}
