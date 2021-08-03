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

#include "Gaffer/Animation.h"

#include "Gaffer/Action.h"
#include "Gaffer/Context.h"
#include "Gaffer/Private/ScopedValue.h"

#include "OpenEXR/ImathFun.h"

#include "boost/bind.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <cassert>
#include <limits>
#include <vector>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;

namespace
{

	double maxAccel( const double slope )
	{
		// NOTE : s = y/x
		//        a = sqrt(x^2 + y^2)
		//
		//        When acceleration at maximum, x = 1, therefore,
		//
		//        y = s
		//        a = sqrt(1 + s^2)

		return std::sqrt( 1.0 + slope * slope );
	}

	double slopeFromPosition( const Imath::V2d& position, const Gaffer::Animation::Tangent::Direction direction )
	{
		static_assert( std::numeric_limits< double >::is_iec559, "IEEE 754 required to represent negative infinity" );

		// NOTE : when x and y are both 0 then slope is 0, otherwise if x is 0 slope is (+/-) infinity

		if( position.x == 0.0 )
		{
			if( position.y == 0.0 )
			{
				return 0.0;
			}

			return std::copysign( std::numeric_limits< double >::infinity(),
				position.y * ( direction == Gaffer::Animation::Tangent::Direction::Into ? -1.0 : 1.0 ) );
		}
		else
		{
			return position.y / position.x;
		}
	}

	double slopeToKeySpace( const double slope, const double dt )
	{
		if( dt == 0.0 )
		{
			return 0.0;
		}

		return slope / dt;
	}

	double slopeFromKeySpace( const double slope, const double dt )
	{
		// NOTE : (+/-) infinity * 0.0 == nan

		if( dt == 0.0 )
		{
			return 0.0;
		}

		return slope * dt;
	}

	double accelToKeySpace( const double accel, const double slope, const double dt )
	{
		if( dt == 0.0 )
		{
			return 0.0;
		}

		// NOTE : As s tends to (+/-) infinity, ((1 + s(k)^2) / (1 + s(c)^2)) tends to
		//        (infinity / infinity) which is meaningless, So,
		//
		//        when |s| <  1 : a(k) = a(c) * dt * sqrt((1 + s(k)^2) / (1 + s(c)^2))
		//        when |s| >= 1 : a(k) = a(c) * sqrt(1 + (1/s(k))^2) / (1 + (1/s(c))^2)

		if( std::abs( slope ) < 1.0 )
		{
			const double sc = slope;
			const double sk = sc / dt;
			return accel * dt * std::sqrt( ( 1.0 + sk * sk ) / ( 1.0 + sc * sc ) );
		}
		else
		{
			const double sc = 1.0 / slope;
			const double sk = sc * dt;
			return accel * std::sqrt( ( 1.0 + sk * sk ) / ( 1.0 + sc * sc ) );
		}
	}

	double accelFromKeySpace( const double accel, const double slope, const double dt )
	{
		if( dt == 0.0 )
		{
			return 0.0;
		}

		// NOTE : As s tends to (+/-) infinity, ((1 + s(c)^2) / (1 + s(k)^2)) tends to
		//        (infinity / infinity) which is meaningless, So,
		//
		//        when |s| <  1 : a(c) = a(k) * std::sqrt((1 + s(c)^2) / (1 + s(k)^2)) / dt
		//        when |s| >= 1 : a(c) = a(k) * sqrt((1 + (1/s(c))^2) / (1 + (1/s(k))^2))

		if( std::abs( slope ) < 1.0 )
		{
			const double sc = slope;
			const double sk = sc / dt;
			return accel * std::sqrt( ( 1.0 + sc * sc ) / ( 1.0 + sk * sk ) ) / dt;
		}
		else
		{
			const double sc = 1.0 / slope;
			const double sk = sc * dt;
			return accel * std::sqrt( ( 1.0 + sc * sc ) / ( 1.0 + sk * sk ) );
		}
	}

	// step interpolator

	struct InterpolatorStep
	: public Gaffer::Animation::Interpolator
	{
		InterpolatorStep()
		: Gaffer::Animation::Interpolator( "Step", Gaffer::Animation::Interpolator::Hints() )
		{}

		double evaluate(
			const double valueLo, const double /*valueHi*/,
			const Gaffer::Animation::Tangent& /*tangentLo*/, const Gaffer::Animation::Tangent& /*tangentHi*/,
			const double /*time*/ ) const override
		{
			return valueLo;
		}
	};

	// step next interpolator

	struct InterpolatorStepNext
	: public Gaffer::Animation::Interpolator
	{
		InterpolatorStepNext()
		: Gaffer::Animation::Interpolator( "StepNext", Gaffer::Animation::Interpolator::Hints() )
		{}

		double evaluate(
			const double /*valueLo*/, const double valueHi,
			const Gaffer::Animation::Tangent& /*tangentLo*/, const Gaffer::Animation::Tangent& /*tangentHi*/,
			const double /*time*/ ) const override
		{
			return valueHi;
		}
	};

	// linear interpolator

	struct InterpolatorLinear
	: public Gaffer::Animation::Interpolator
	{
		InterpolatorLinear()
		: Gaffer::Animation::Interpolator( "Linear", Gaffer::Animation::Interpolator::Hints() )
		{}

		double evaluate(
			const double valueLo, const double valueHi,
			const Gaffer::Animation::Tangent& /*tangentLo*/, const Gaffer::Animation::Tangent& /*tangentHi*/,
			const double time ) const override
		{
			return valueLo * ( 1.0 - time ) + valueHi * ( time );
		}
	};

	// smooth step interpolator

	struct InterpolatorSmoothStep
	: public Gaffer::Animation::Interpolator
	{
		InterpolatorSmoothStep()
		: Gaffer::Animation::Interpolator( "SmoothStep", Gaffer::Animation::Interpolator::Hints() )
		{}

		double evaluate(
			const double valueLo, const double valueHi,
			const Gaffer::Animation::Tangent& /*tangentLo*/, const Gaffer::Animation::Tangent& /*tangentHi*/,
			const double time ) const override
		{
			// NOTE : s = 3t^2 - 2t^3
			//        v = l(1-s) + hs
			//        v = (h-l)3t^2 - (h-l)2t^3 + l

			return ( valueHi - valueLo ) * time * time * ( 3.0 - time - time ) + valueLo;
		}
	};

	// cubic interpolator

	struct InterpolatorCubic
	: public Gaffer::Animation::Interpolator
	{
		InterpolatorCubic()
		: Gaffer::Animation::Interpolator( "Cubic", Gaffer::Animation::Interpolator::Hints(
			Gaffer::Animation::Interpolator::Hint::UseSlopeLo ) |
			Gaffer::Animation::Interpolator::Hint::UseSlopeHi )
		{}

		double evaluate(
			const double valueLo, const double valueHi,
			const Gaffer::Animation::Tangent& tangentLo, const Gaffer::Animation::Tangent& tangentHi,
			const double time ) const override
		{
			double a, b, c, d;
			computeCoeffs( valueLo, valueHi, tangentLo, tangentHi, a, b, c, d );

			// NOTE : v  = at^3 + bt^2 + ct + d

			return ( time * ( time * ( time * a + b ) + c ) + d );
		}

		void bisect(
			const double valueLo, const double valueHi,
			const Gaffer::Animation::Tangent& tangentLo, const Gaffer::Animation::Tangent& tangentHi,
			const double time, Gaffer::Animation::Key& newKey,
			Gaffer::Animation::Tangent& newTangentLo, Gaffer::Animation::Tangent& newTangentHi ) const override
		{
			double a, b, c, d;
			computeCoeffs( valueLo, valueHi, tangentLo, tangentHi, a, b, c, d );

			// NOTE : v  =  at^3 +  bt^2 + ct + d
			//        v' = 3at^2 + 2bt   + c

			const double v = ( time * ( time * ( time *           a       + b ) + c ) + d );
			const double s =          ( time * ( time * ( a + a + a ) + b + b ) + c );
			const double x = Gaffer::Animation::Tangent::defaultAccel();

			const Gaffer::Animation::Tangent::Space space = Gaffer::Animation::Tangent::Space::Span;

			const double sl = (       time ) * tangentLo.getSlope( space );
			const double si = (       time ) * s;
			const double sf = ( 1.0 - time ) * s;
			const double sh = ( 1.0 - time ) * tangentHi.getSlope( space );

			newKey.setValue( v );
			newKey.getTangent( Gaffer::Animation::Tangent::Direction::Into ).setSlope( si, space );
			newKey.getTangent( Gaffer::Animation::Tangent::Direction::Into ).setAccel( x, space );
			newKey.getTangent( Gaffer::Animation::Tangent::Direction::From ).setSlope( sf, space );
			newKey.getTangent( Gaffer::Animation::Tangent::Direction::From ).setAccel( x, space );
			newTangentLo.setSlope( sl, space );
			newTangentLo.setAccel( x, space );
			newTangentHi.setSlope( sh, space );
			newTangentHi.setAccel( x, space );
		}

	private:

		void computeCoeffs(
			const double valueLo, const double valueHi,
			const Gaffer::Animation::Tangent& tangentLo, const Gaffer::Animation::Tangent& tangentHi,
			double& a, double& b, double& c, double& d ) const
		{
			// NOTE : clamp slope to prevent infs and nans in interpolated values

			const double maxSlope = 1.e9;

			const Gaffer::Animation::Tangent::Space space = Gaffer::Animation::Tangent::Space::Span;

			const double sl = std::min( std::max( tangentLo.getSlope( space ), -maxSlope ), maxSlope );
			const double sh = std::min( std::max( tangentHi.getSlope( space ), -maxSlope ), maxSlope );
			const double dv = valueHi - valueLo;

			a = sl + sh - dv - dv;
			b = dv + dv + dv - sl - sl - sh;
			c = sl;
			d = valueLo;
		}
	};

	// bezier interpolator

	struct InterpolatorBezier
	: public Gaffer::Animation::Interpolator
	{
		InterpolatorBezier()
		: Gaffer::Animation::Interpolator( "Bezier", Gaffer::Animation::Interpolator::Hints(
			Gaffer::Animation::Interpolator::Hint::UseSlopeLo ) |
			Gaffer::Animation::Interpolator::Hint::UseSlopeHi   |
			Gaffer::Animation::Interpolator::Hint::UseAccelLo   |
			Gaffer::Animation::Interpolator::Hint::UseAccelHi )
		{}

		double evaluate(
			const double valueLo, const double valueHi,
			const Gaffer::Animation::Tangent& tangentLo, const Gaffer::Animation::Tangent& tangentHi,
			const double time ) const override
		{
			const Gaffer::Animation::Tangent::Space space = Gaffer::Animation::Tangent::Space::Span;

			const Imath::V2d tl = tangentLo.getPosition( space, false );
			const Imath::V2d th = tangentHi.getPosition( space, false );

			// NOTE : Curve is determined by two polynomials parameterised by s,
			//
			//        v = a(v)s^3 +  b(v)s^2 + c(v)s + d(v)
			//        t = a(t)s^3 +  b(t)s^2 + c(t)s + d(t)
			//
			//        where t is normalised time in seconds, v is value, to evaluate v at the
			//        specified t, first need to solve the second polynomial to determine s.

			const double s = solveForTime( tl.x, th.x, time );

			// compute coefficients of value polynomial

			const double tl3 = tl.y + tl.y + tl.y;
			const double th3 = th.y + th.y + th.y;
			const double vl3 = valueLo + valueLo + valueLo;
			const double av = tl3 - th3 + valueHi - valueLo;
			const double bv = th3 + vl3 - tl3 - tl3;
			const double cv = tl3 - vl3;
			const double dv = valueLo;

			// evaluate value polynomial

			return ( s * ( s * ( s * av + bv ) + cv ) + dv );
		}

		void bisect(
			const double valueLo, const double valueHi,
			const Gaffer::Animation::Tangent& tangentLo, const Gaffer::Animation::Tangent& tangentHi,
			const double time, Gaffer::Animation::Key& newKey,
			Gaffer::Animation::Tangent& newTangentLo, Gaffer::Animation::Tangent& newTangentHi ) const override
		{
			const Gaffer::Animation::Tangent::Space space = Gaffer::Animation::Tangent::Space::Span;

			const Imath::V2d p1( 0.0, valueLo );
			const Imath::V2d p2 = tangentLo.getPosition( space, false );
			const Imath::V2d p3 = tangentHi.getPosition( space, false );
			const Imath::V2d p4( 1.0, valueHi );

			const double s = solveForTime( p2.x, p3.x, time );

			// NOTE : simple geometric bisection

			const Imath::V2d h  = Imath::lerp( p2, p3, s );
			const Imath::V2d l2 = Imath::lerp( p1, p2, s );
			const Imath::V2d l3 = Imath::lerp( l2, h,  s );
			const Imath::V2d r3 = Imath::lerp( p3, p4, s );
			const Imath::V2d r2 = Imath::lerp( h,  r3, s );
			const Imath::V2d l4 = Imath::lerp( l3, r2, s );

			const Imath::V2d lf(   l2.x          / (       time ), l2.y );
			const Imath::V2d mi(   l3.x          / (       time ), l3.y );
			const Imath::V2d mf( ( r2.x - time ) / ( 1.0 - time ), r2.y );
			const Imath::V2d hi( ( r3.x - time ) / ( 1.0 - time ), r3.y );

			newKey.setValue( l4.y );
			newKey.getTangent( Gaffer::Animation::Tangent::Direction::Into ).setPosition( mi, space, false );
			newKey.getTangent( Gaffer::Animation::Tangent::Direction::From ).setPosition( mf, space, false );
			newTangentLo.setPosition( lf, space, false );
			newTangentHi.setPosition( hi, space, false );
		}

	private:

		double solveForTime( const double tl, const double th, const double time ) const
		{
			if( time <= 0.0 ) return 0.0;
			if( time >= 1.0 ) return 1.0;

			// compute coeffs

			const double th3 = th + th + th;
			const double ct = tl + tl + tl;
			const double at = ct - th3 + 1.0;
			const double bt = th3 - ct - ct;
			const double bt2 = bt + bt;

			// root bracketed in interval [0,1]

			double sl = 0.0;
			double sh = 1.0;

			// time is a reasonable first guess

			double s = time;

			// max of 10 newton-raphson iterations

			for( int i = 0; i < 10; ++i )
			{
				// evaluate function and derivative
				//
				// NOTE : f   =  a(t)s^3 +  b(t)s^2 + c(t)s + d(t) - t
				//        f'  = 3a(t)s^2 + 2b(t)s   + c(t)

				const double  f = ( s * ( s * ( s *             at   + bt  ) + ct ) - time );
				const double df =       ( s * ( s * ( at + at + at ) + bt2 ) + ct );

				// maintain bounds

				if( std::abs( f ) < std::numeric_limits< double >::epsilon() )
				{
					break;
				}
				else if( f < 0.0 )
				{
					sl = s;
				}
				else
				{
					sh = s;
				}

				// NOTE : when derivative is zero or newton-raphson step would escape bounds use bisection step instead.

				double ds;

				if( df == 0.0 )
				{
					ds = 0.5 * ( sh - sl );
					s = sl + ds;
				}
				else
				{
					ds = f / df;

					if( ( ( s - ds ) <= sl ) || ( ( s - ds ) >= sh ) )
					{
						ds = 0.5 * ( sh - sl );
						s = sl + ds;
					}
					else
					{
						s -= ds;
					}
				}

				assert( s >= sl );
				assert( s <= sh );

				// check for convergence

				if( std::abs( ds ) < std::numeric_limits< double >::epsilon() )
				{
					break;
				}
			}

			return s;
		}
	};

	// get the interpolator to use for specified type

	Gaffer::Animation::Interpolator* getInterpolatorForType( const Gaffer::Animation::Type type )
	{
		Gaffer::Animation::Interpolator::Factory& factory =
			Gaffer::Animation::Interpolator::getFactory();

		switch( type )
		{
			case Gaffer::Animation::Step:
				return factory.get( "Step" );
			case Gaffer::Animation::Linear:
				return factory.get( "Linear" );
			default:
				return factory.getDefault();
		}
	}

} // namespace

namespace Gaffer
{

//////////////////////////////////////////////////////////////////////////
// Time implementation
//////////////////////////////////////////////////////////////////////////

Animation::Time::Time()
: m_ticks( static_cast< std::int64_t >( 0 ) )
{}

Animation::Time::Time( const std::int64_t ticks )
: m_ticks( ticks )
{}

Animation::Time::Time( const double value, const Animation::Time::Units units )
: m_ticks( static_cast< std::int64_t >( std::round( value * (
	static_cast< double >( static_cast< int >( Units::Ticks ) ) /
	static_cast< double >( units ) ) ) ) )
{}

Animation::Time::Time( const double value, const double units )
: m_ticks( ( units > 0.0 )
	? static_cast< std::int64_t >( std::round( value * (
		static_cast< double >( static_cast< int >( Units::Ticks ) ) /
		std::min( units, static_cast< double >( static_cast< int >( Units::Ticks ) ) ) ) ) )
	: static_cast< std::int64_t >( 0 ) )
{}

Animation::Time::Time( Animation::Time const& rhs )
: m_ticks( rhs.m_ticks )
{}

Animation::Time::~Time()
{}

Animation::Time& Animation::Time::operator  = ( const Animation::Time& rhs )
{
	m_ticks = rhs.m_ticks;
	return *this;
}

Animation::Time& Animation::Time::operator += ( const Animation::Time& rhs )
{
	m_ticks += rhs.m_ticks;
	return *this;
}

Animation::Time& Animation::Time::operator -= ( const Animation::Time& rhs )
{
	m_ticks -= rhs.m_ticks;
	return *this;
}

Animation::Time& Animation::Time::operator /= ( const Animation::Time& rhs )
{
	m_ticks /= rhs.m_ticks;
	return *this;
}

Animation::Time& Animation::Time::operator %= ( const Animation::Time& rhs )
{
	m_ticks = std::labs( m_ticks % rhs.m_ticks );
	return *this;
}

std::int64_t Animation::Time::getTicks() const
{
	return m_ticks;
}

double Animation::Time::getReal( const double units ) const
{
	return ( units > 0.0 )
		? ( static_cast< double >( m_ticks ) / (
			static_cast< double >( static_cast< int >( Units::Ticks ) ) / units ) )
		: static_cast< double >( 0 );
}

double Animation::Time::getSeconds() const
{
	return getReal( static_cast< double >( Units::Seconds ) );
}

void Animation::Time::snap( const double units )
{
	if( units > 0.0 )
	{
		// NOTE : round to nearest unit then convert back to ticks and round to nearest tick

		const double s = static_cast< double >( static_cast< int >( Units::Ticks ) ) /
			std::min( units, static_cast< double >( static_cast< int >( Units::Ticks ) ) );

		m_ticks = static_cast< std::int64_t >( std::round( std::round( static_cast< double >( m_ticks ) / s ) * s ) );
	}
	else
	{
		m_ticks = static_cast< std::int64_t >( 0 );
	}
}

Animation::Time operator +  ( const Animation::Time& lhs, const Animation::Time& rhs )
{
	return Animation::Time( lhs ) += rhs;
}

Animation::Time operator -  ( const Animation::Time& lhs, const Animation::Time& rhs )
{
	return Animation::Time( lhs ) -= rhs;
}

Animation::Time operator /  ( const Animation::Time& lhs, const Animation::Time& rhs )
{
	return Animation::Time( lhs ) /= rhs;
}

Animation::Time operator %  ( const Animation::Time& lhs, const Animation::Time& rhs )
{
	return Animation::Time( lhs ) %= rhs;
}

bool operator == ( const Animation::Time& lhs, const Animation::Time& rhs )
{
	return lhs.m_ticks == rhs.m_ticks;
}

bool operator != ( const Animation::Time& lhs, const Animation::Time& rhs )
{
	return !( lhs == rhs );
}

bool operator <  ( const Animation::Time& lhs, const Animation::Time& rhs )
{
	return lhs.m_ticks < rhs.m_ticks;
}

bool operator >  ( const Animation::Time& lhs, const Animation::Time& rhs )
{
	return lhs.m_ticks > rhs.m_ticks;
}

bool operator <= ( const Animation::Time& lhs, const Animation::Time& rhs )
{
	return lhs.m_ticks <= rhs.m_ticks;
}

bool operator >= ( const Animation::Time& lhs, const Animation::Time& rhs )
{
	return lhs.m_ticks >= rhs.m_ticks;
}

Animation::Time abs( const Animation::Time& rhs )
{
	Animation::Time t;
	t.m_ticks = std::labs( rhs.m_ticks );
	return t;
}

//////////////////////////////////////////////////////////////////////////
// Interpolator implementation
//////////////////////////////////////////////////////////////////////////

Animation::Interpolator::Hints::Hints()
: m_bits( 0 )
{}

Animation::Interpolator::Hints::Hints( const Animation::Interpolator::Hint hint )
: m_bits( static_cast< std::uint32_t >( 1 ) << static_cast< std::uint32_t >( hint ) )
{}

Animation::Interpolator::Hints::Hints( const Animation::Interpolator::Hints& rhs )
: m_bits( rhs.m_bits )
{}

Animation::Interpolator::Hints& Animation::Interpolator::Hints::operator = ( const Animation::Interpolator::Hints& rhs )
{
	m_bits = rhs.m_bits;
	return *this;
}

bool Animation::Interpolator::Hints::test( const Animation::Interpolator::Hint hint ) const
{
	return static_cast< bool >( m_bits & ( static_cast< std::uint32_t >( 1 ) << static_cast< std::uint32_t >( hint ) ) );
}

Animation::Interpolator::Hints operator | ( const Animation::Interpolator::Hints& lhs, const Animation::Interpolator::Hints& rhs )
{
	Animation::Interpolator::Hints result( lhs );
	result.m_bits |= rhs.m_bits;
	return result;
}

Animation::Interpolator::Factory::Factory()
: m_container()
, m_default()
{
	add( new InterpolatorBezier() );
	add( new InterpolatorCubic() );
	add( new InterpolatorLinear() );
	add( new InterpolatorSmoothStep() );
	add( new InterpolatorStepNext() );
	add( new InterpolatorStep() );

	m_default = get( 0 );
}

Animation::Interpolator::Factory::~Factory()
{}

bool Animation::Interpolator::Factory::add( Animation::Interpolator::Ptr interpolator )
{
	// NOTE : check for null pointer

	if( ! interpolator )
	{
		return false;
	}

	// NOTE : check for interpolator with same name

	for( Container::const_iterator it = m_container.begin(), itEnd = m_container.end(); it != itEnd; ++it )
	{
		if( ( *it )->getName() == interpolator->getName() )
		{
			return false;
		}
	}

	m_container.push_back( interpolator );

	return true;
}

std::uint32_t Animation::Interpolator::Factory::count()
{
	return static_cast< std::uint32_t >( m_container.size() );
}

Animation::Interpolator* Animation::Interpolator::Factory::get( const std::string& name )
{
	for( Container::iterator it = m_container.begin(), itEnd = m_container.end(); it != itEnd; ++it )
	{
		if( ( *it )->getName() == name )
		{
			return ( *it ).get();
		}
	}

	return m_default.get();
}

Animation::Interpolator* Animation::Interpolator::Factory::get( const std::uint32_t index )
{
	const Container::size_type i = static_cast< Container::size_type >( index );
	return ( i < m_container.size() ) ? m_container[ i ].get() : m_default.get();
}

Animation::Interpolator* Animation::Interpolator::Factory::getDefault()
{
	return m_default.get();
}

Animation::Interpolator::Factory& Animation::Interpolator::getFactory()
{
	static Factory::Ptr factory( new Factory() );
	return *factory;
}

Animation::Interpolator::Interpolator( const std::string& name, const Hints hints )
: m_name( name )
, m_hints( hints )
{}

Animation::Interpolator::~Interpolator()
{}

const std::string& Animation::Interpolator::getName() const
{
	return m_name;
}

Animation::Interpolator::Hints Animation::Interpolator::getHints() const
{
	return m_hints;
}

double Animation::Interpolator::evaluate(
	const double /*valueLo*/, const double /*valueHi*/,
	const Animation::Tangent& /*tangentLo*/, const Animation::Tangent& /*tangentHi*/,
	const double /*time*/ ) const
{
	return 0.0;
}

void Animation::Interpolator::bisect(
	const double valueLo, const double valueHi,
	const Tangent& tangentLo, const Tangent& tangentHi,
	const double time, Key& newKey, Tangent& newTangentLo, Tangent& newTangentHi ) const
{
	newKey.setValue( evaluate( valueLo, valueHi, tangentLo, tangentHi, time ) );
}

//////////////////////////////////////////////////////////////////////////
// Tangent implementation
//////////////////////////////////////////////////////////////////////////

double Animation::Tangent::defaultSlope()
{
	// NOTE : flat slope

	return 0.0;
}

double Animation::Tangent::defaultAccel()
{
	// NOTE : one third is the tangent length that corresponds to linear interpolation

	return ( 1.0 / 3.0 );
}

Animation::Tangent::Direction Animation::Tangent::opposite( const Animation::Tangent::Direction direction )
{
	return static_cast< Direction >( ( static_cast< int >( direction ) + 1 ) % 2 );
}

Animation::Tangent::Tangent( Animation::Key& key, const Animation::Tangent::Direction direction, const double slope, const double accel )
: m_key( & key )
, m_direction( direction )
, m_slope( slope )
, m_accel( std::min( accel, maxAccel( m_slope ) ) )
, m_dt( 0.0 )
{}

Animation::Tangent::~Tangent()
{}

Animation::Key& Animation::Tangent::getKey()
{
	return const_cast< Key& >(
		static_cast< const Tangent* >( this )->getKey() );
}

const Animation::Key& Animation::Tangent::getKey() const
{
	assert( m_key );
	return *m_key;
}

Animation::Tangent::Direction Animation::Tangent::getDirection() const
{
	return m_direction;
}

void Animation::Tangent::convertPosition( Imath::V2d& position, const Animation::Tangent::Space space, const bool relative ) const
{
	// convert from absolute position

	if( ! relative )
	{
		if( space == Space::Key )
		{
			position.x -= m_key->m_time.getSeconds();
		}
		else if( m_direction == Direction::Into )
		{
			position.x -= 1.0;
		}

		position.y -= m_key->m_value;
	}

	// convert from key space

	if( space == Space::Key )
	{
		position.x = ( m_dt == 0.0 ) ? 0.0 : ( position.x / m_dt );
	}

	// constrain direction of tangent

	position.x = ( m_direction == Direction::Into )
		? std::min( position.x, 0.0 )
		: std::max( position.x, 0.0 );
}

void Animation::Tangent::setPosition( Imath::V2d position, const Animation::Tangent::Space space, const bool relative )
{
	// convert position to relative span space

	convertPosition( position, space, relative );

	// set slope and acceleration

	setSlope( slopeFromPosition( position, m_direction ), Space::Span );
	setAccel( position.length(), Space::Span );
}

void Animation::Tangent::setPositionWithSlope( Imath::V2d position, const double slope, const Animation::Tangent::Space space, const bool relative )
{
	// convert position to relative span space

	convertPosition( position, space, relative );

	// constrain position to quadrant based on slope and direction

	position.y = ( m_direction == Direction::Into )
		? ( ( slope > 0.0 )
			? std::min( position.y, 0.0 )
			: std::max( position.y, 0.0 ) )
		: ( ( slope < 0.0 )
			? std::min( position.y, 0.0 )
			: std::max( position.y, 0.0 ) );

	// set slope and acceleration

	setSlope( slope, Space::Span );
	setAccel( position.length(), Space::Span );
}

void Animation::Tangent::setPositionWithAccel( Imath::V2d position, const double accel, const Animation::Tangent::Space space, const bool relative )
{
	// convert position to relative span space

	convertPosition( position, space, relative );

	// set slope and acceleration

	setSlope( slopeFromPosition( position, m_direction ), Space::Span );
	setAccel( accel, Space::Span );
}

Imath::V2d Animation::Tangent::getPosition( const Animation::Tangent::Space space, const bool relative ) const
{
	if( ( space == Space::Key ) && ( m_dt == 0.0 ) )
	{
		return Imath::V2d( 0.0, 0.0 );
	}

	// compute relative position in span space
	//
	// NOTE : s   = y/x
	//            = tan(angle)
	//        x   = a * cos(angle)
	//            = a / sqrt(1 + tan^2(angle))
	//            = a / sqrt(1 + s^2)
	//        y   = x * s
	//
	//        1/s = x/y
	//            = tan(PI/2-angle)
	//        y   = a * cos(PI/2-angle)
	//            = a / sqrt(1 + tan^2(PI/2-angle))
	//            = a / sqrt(1 + (1/s)^2)
	//        x   = y * (1/s)
	//
	//        As s tends to 0, sqrt(1 + s^2) tends to 1, so x tends to a and y tends to 0, but
	//        as s tends to (+/-) infinity, sqrt(1 + s^2) tends to infinity, so x tends to 0
	//        and y becomes meaningless. However as s tends to (+/-) infinity, 1/s tends to 0
	//        so sqrt(1 + (1/s)^2) tends to 1, so y tends to a and x tends to 0. So,
	//
	//            when |s| <  1 : x = a / sqrt(1 + s^2)
	//                            y = x * s
	//            when |s| >= 1 : y = a / sqrt(1 + (1/s)^2)
	//                            x = y * (1/s)

	Imath::V2d p;

	if( std::abs( m_slope ) < 1.0 )
	{
		const double s = m_slope;
		p.x = std::min( m_accel / std::sqrt( 1.0 + s * s ), 1.0 );
		p.y = p.x * s;
	}
	else
	{
		const double s = 1.0 / m_slope;
		p.y = std::copysign( m_accel / std::sqrt( 1.0 + s * s ), s );
		p.x = std::min( p.y * s, 1.0 );
	}

	if( m_direction == Direction::Into )
	{
		if( p.x != 0.0 ) { p.x = -p.x; }
		if( p.y != 0.0 ) { p.y = -p.y; }
	}

	if( space == Space::Key )
	{
		p.x *= m_dt;
	}

	// convert to absolute position

	if( ! relative )
	{
		if( space == Space::Key )
		{
			p.x += m_key->m_time.getSeconds();
		}
		else if( m_direction == Direction::Into )
		{
			p.x += 1.0;
		}

		p.y += m_key->m_value;
	}

	return p;
}

void Animation::Tangent::setSlope( double slope, const Animation::Tangent::Space space )
{
	// convert to span space

	if( space == Space::Key )
	{
		slope = slopeFromKeySpace( slope, m_dt );
	}

	// check for no change

	if( Animation::equivalentValues( m_slope, slope ) )
	{
		return;
	}

	// clamp accel based on new slope

	const double accel = std::min( m_accel, maxAccel( slope ) );

	// make change via action

	if( m_key->m_parent )
	{
		KeyPtr key = m_key;
		const double ps = m_slope;
		const double pa = m_accel;
		Action::enact(
			key->m_parent,
			// Do
			[ this, key, slope, accel ] {
				m_slope = slope;
				m_accel = accel;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
				key->m_parent->m_keyTangentSlopeChangedSignal( key->m_parent, key.get(), m_direction );
			},
			// Undo
			[ this, key, ps, pa ] {
				m_slope = ps;
				m_accel = pa;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
				key->m_parent->m_keyTangentSlopeChangedSignal( key->m_parent, key.get(), m_direction );
			}
		);
	}
	else
	{
		m_slope = slope;
		m_accel = accel;
	}

	// tie slope of sibling

	if( m_key->tieSlopeActive( opposite( m_direction ) ) )
	{
		const Space space = m_key->tieSlopeSpace();
		Private::ScopedValue< bool > guard( m_key->m_tieSlope, false );
		m_key->getTangent( opposite( m_direction ) ).setSlope( getSlope( space ), space );
	}
}

void Animation::Tangent::setSlopeWithAccel( const double slope, const double accel, const Animation::Tangent::Space space )
{
	setSlope( slope, space );
	setAccel( accel, Space::Span );
}

double Animation::Tangent::getSlope( const Animation::Tangent::Space space ) const
{
	return ( space == Space::Key ) ? slopeToKeySpace( m_slope, m_dt ) : m_slope;
}

void Animation::Tangent::setAccel( double accel, const Animation::Tangent::Space space )
{
	// convert to span space

	if( space == Space::Key )
	{
		accel = accelFromKeySpace( accel, m_slope, m_dt );
	}

	// clamp acceleration

	accel = std::min( accel, maxAccel( m_slope ) );

	// check for no change

	if( Animation::equivalentValues( m_accel, accel ) )
	{
		return;
	}

	// tie acceleration of sibling
	//
	// NOTE : scale sibling by same amount, unless scale is infinite then add instead.

	if( m_key->tieAccelActive( opposite( m_direction ) ) )
	{
		Tangent& sibling = m_key->getTangent( opposite( m_direction ) );
		Private::ScopedValue< bool > guard( m_key->m_tieAccel, false );
		sibling.setAccel( ( m_accel == 0.0 )
				? ( sibling.m_accel + accel )
				: ( sibling.m_accel * ( accel / m_accel ) ),
			Space::Span );
	}

	// make change via action

	if( m_key->m_parent )
	{
		KeyPtr key = m_key;
		const double pa = m_accel;
		Action::enact(
			key->m_parent,
			// Do
			[ this, key, accel ] {
				m_accel = accel;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
				key->m_parent->m_keyTangentAccelChangedSignal( key->m_parent, key.get(), m_direction );
			},
			// Undo
			[ this, key, pa ] {
				m_accel = pa;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
				key->m_parent->m_keyTangentAccelChangedSignal( key->m_parent, key.get(), m_direction );
			}
		);
	}
	else
	{
		m_accel = accel;
	}
}

void Animation::Tangent::setAccelWithSlope( const double accel, const double slope, const Animation::Tangent::Space space )
{
	setSlope( slope, Space::Span );
	setAccel( accel, space );
}

double Animation::Tangent::getAccel( const Space space ) const
{
	return ( space == Space::Key ) ? accelToKeySpace( m_accel, m_slope, m_dt ) : m_accel;
}

void Animation::Tangent::update()
{
	// update span time difference

	const double dt = m_key->getTime( m_direction ).getSeconds();

	if( dt != m_dt )
	{
		if( dt == 0.0 )
		{
			// NOTE : when key is removed from curve (dt == 0) we do not update m_dt so that we know
			//        the previous span dt if the key is added back to a curve. dt may also be zero
			//        when the parent key is the only key in its parent curve.
		}
		else if( m_dt == 0.0 )
		{
			// NOTE : when a new key is added to curve (m_dt == 0) we set m_dt but do not adjust
			//        slope and accel as the values are explicitly given in span space. This case
			//        occurs when a key is newly contructed (including deserialisation)

			m_dt = dt;
		}
		else
		{
			// NOTE : when both dt and m_dt are non zero then either the key has been removed from
			//        the curve, then added back, or its time or one of its adjacent keys' time has
			//        changed, in which case we adjust the slope and accel to maintain key space slope.

			// TODO : the slope is changed here without being signaled ...

			m_slope *= ( dt / m_dt );
			m_dt = dt;
		}
	}
}

} // Gaffer

//////////////////////////////////////////////////////////////////////////
// Key implementation
//////////////////////////////////////////////////////////////////////////

Animation::Key::Key( float time, float value, Type type )
: m_parent( nullptr )
, m_interpolator( getInterpolatorForType( type ) )
, m_into( *this, Animation::Tangent::Direction::Into, Animation::Tangent::defaultSlope(), Animation::Tangent::defaultAccel() )
, m_from( *this, Animation::Tangent::Direction::From, Animation::Tangent::defaultSlope(), Animation::Tangent::defaultAccel() )
, m_time( time, Animation::Time::Units::Seconds )
, m_value( value )
, m_tieSlope( true )
, m_tieAccel( true )
{}

Animation::Key::Key( const Animation::Time& time, float value, const std::string& interpolatorName, double slopeInto, double slopeFrom, double accelInto, double accelFrom, bool tieSlope, bool tieAccel )
: m_parent( nullptr )
, m_interpolator( Interpolator::getFactory().get( interpolatorName ) )
, m_into( *this, Animation::Tangent::Direction::Into, slopeInto, accelInto )
, m_from( *this, Animation::Tangent::Direction::From, slopeFrom, accelFrom )
, m_time( time )
, m_value( value )
, m_tieSlope( tieAccel )
, m_tieAccel( tieSlope )
{}

Animation::Tangent& Animation::Key::getTangent( const Animation::Tangent::Direction direction )
{
	return const_cast< Animation::Tangent& >(
		static_cast< const Animation::Key* >( this )->getTangent( direction ) );
}

const Animation::Tangent& Animation::Key::getTangent( const Animation::Tangent::Direction direction ) const
{
	return ( direction == Animation::Tangent::Direction::Into ) ? m_into : m_from;
}

bool Animation::Key::getTieSlope() const
{
	return m_tieSlope;
}

void Animation::Key::setTieSlope( const bool tie )
{
	// check for no change

	if( tie == m_tieSlope )
	{
		return;
	}

	// make change via action

	if( m_parent )
	{
		KeyPtr key = this;
		Action::enact(
			m_parent,
			// Do
			[ key, tie ] {
				key->m_tieSlope = tie;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
				key->m_parent->m_keyTieSlopeChangedSignal( key->m_parent, key.get() );
			},
			// Undo
			[ key, tie ] {
				key->m_tieSlope = ! tie;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
				key->m_parent->m_keyTieSlopeChangedSignal( key->m_parent, key.get() );
			}
		);
	}
	else
	{
		m_tieSlope = tie;
	}

	// tie slope

	tieSlopeAverage( tieSlopeSpace() );
}

bool Animation::Key::getTieAccel() const
{
	return m_tieAccel;
}

void Animation::Key::setTieAccel( const bool tie )
{
	// check for no change

	if( tie == m_tieAccel )
	{
		return;
	}

	// make change via action

	if( m_parent )
	{
		KeyPtr key = this;
		Action::enact(
			m_parent,
			// Do
			[ key, tie ] {
				key->m_tieAccel = tie;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
				key->m_parent->m_keyTieAccelChangedSignal( key->m_parent, key.get() );
			},
			// Undo
			[ key, tie ] {
				key->m_tieAccel = ! tie;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
				key->m_parent->m_keyTieAccelChangedSignal( key->m_parent, key.get() );
			}
		);
	}
	else
	{
		m_tieAccel = tie;
	}
}

float Animation::Key::getFloatTime() const
{
	return m_time.getSeconds();
}

Animation::Time Animation::Key::getTime() const
{
	return m_time;
}

Animation::Time Animation::Key::getTime( const Animation::Tangent::Direction direction ) const
{
	// NOTE : At first key in into direction and at last key in from direction time is zero.
	//        When key is the only key, time is zero is both directions.

	const Key* k = 0;

	if( m_parent )
	{
		if( direction == Animation::Tangent::Direction::Into )
		{
			k = prevKey();
		}
		else
		{
			k = nextKey();
		}
	}

	return ( k == 0 ) ? Animation::Time() : abs( m_time - k->getTime() );
}

void Animation::Key::setTime( float time )
{
	setTime( Animation::Time( time, Animation::Time::Units::Seconds ) );
}

void Animation::Key::setTime( const Animation::Time& time )
{
	if( time == m_time )
	{
		return;
	}

	if( m_parent )
	{
		if( KeyPtr existingKey = m_parent->getKey( time ) )
		{
			m_parent->removeKey( existingKey );
		}

		KeyPtr key = this;
		const Animation::Time previousTime = m_time;
		CurvePlug *curve = m_parent;
		Action::enact(
			m_parent,
			// Do
			[ curve, previousTime, time, key ] {
				Key* const kpn = key->nextKey();
				Key* const kpp = key->prevKey();
				curve->m_keys.modify(
					curve->m_keys.find( previousTime ),
					[ time ] ( KeyPtr &k ) {
						k->m_time = time;
					}
				);
				Key* const kn = key->nextKey();
				Key* const kp = key->prevKey();
				if( kpn ){ kpn->m_into.update(); }
				if( kpp ){ kpp->m_from.update(); }
				if( kn && kn != kpn ){ kn->m_into.update(); }
				if( kp && kp != kpp ){ kp->m_from.update(); }
				key->m_from.update();
				key->m_into.update();
				curve->propagateDirtiness( curve->outPlug() );
				curve->m_keyTimeChangedSignal( key->m_parent, key.get() );
			},
			// Undo
			[ curve, previousTime, time, key ] {
				Key* const kpn = key->nextKey();
				Key* const kpp = key->prevKey();
				curve->m_keys.modify(
					curve->m_keys.find( time ),
					[ previousTime ] ( KeyPtr &k ) {
						k->m_time = previousTime;
					}
				);
				Key* const kn = key->nextKey();
				Key* const kp = key->prevKey();
				if( kpn ){ kpn->m_into.update(); }
				if( kpp ){ kpp->m_from.update(); }
				if( kn && kn != kpn ){ kn->m_into.update(); }
				if( kp && kp != kpp ){ kp->m_from.update(); }
				key->m_into.update();
				key->m_from.update();
				curve->propagateDirtiness( curve->outPlug() );
				curve->m_keyTimeChangedSignal( key->m_parent, key.get() );
			}
		);

		// NOTE : time change may result in the into tangent of the key being affected by
		//        a different interpolator, and the interpolator of this key affecting the
		//        into tangent of the next key.

		if( Key* const kp = prevKey() )
		{
			const Interpolator::Hints hints = kp->m_interpolator->getHints();

			if( ! hints.test( Interpolator::Hint::UseSlopeLo ) )
			{
				m_into.setSlope( Tangent::defaultSlope(), Tangent::Space::Span );
			}

			if( ! hints.test( Interpolator::Hint::UseAccelLo ) )
			{
				m_into.setAccel( Tangent::defaultAccel(), Tangent::Space::Span );
			}

			// NOTE : update previous final key tie slope as final key from tangent not valid
			//        due to zero time dt. the into tangent may have been manipulated assume
			//        user wants to keep into tangent as is so just copy its slope to from tangent

			if( key.get() == m_parent->finalKey() && kp->tieSlopeActive( Tangent::Direction::From ) )
			{
				Private::ScopedValue< bool > guard( kp->m_tieSlope, false );
				kp->m_from.setSlope( kp->m_into.getSlope( Tangent::Space::Key ), Tangent::Space::Key );
			}
		}

		if( Key* const kn = nextKey() )
		{
			const Interpolator::Hints hints = m_interpolator->getHints();

			if( ! hints.test( Interpolator::Hint::UseSlopeHi ) )
			{
				kn->m_into.setSlope( Tangent::defaultSlope(), Tangent::Space::Span );
			}

			if( ! hints.test( Interpolator::Hint::UseAccelHi ) )
			{
				kn->m_into.setAccel( Tangent::defaultAccel(), Tangent::Space::Span );
			}

			// NOTE : update previous first key tie slope as first key from tangent not valid
			//        due to zero time dt. the from tangent may have been manipulated assume
			//        user wants to keep from tangent as is so just copy its slope to into tangent

			if( key.get() == m_parent->firstKey() && kn->tieSlopeActive( Tangent::Direction::Into ) )
			{
				Private::ScopedValue< bool > guard( kn->m_tieSlope, false );
				kn->m_into.setSlope( kn->m_from.getSlope( Tangent::Space::Key ), Tangent::Space::Key );
			}
		}
	}
	else
	{
		m_time = time;
	}
}

float Animation::Key::getValue() const
{
	return m_value;
}

void Animation::Key::setValue( float value )
{
	if( Animation::equivalentValues( value, m_value ) )
	{
		return;
	}

	if( m_parent )
	{
		KeyPtr key = this;
		const float previousValue = m_value;
		Action::enact(
			m_parent,
			// Do
			[ key, value ] {
				key->m_value = value;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
				key->m_parent->m_keyValueChangedSignal( key->m_parent, key.get() );
			},
			// Undo
			[ key, previousValue ] {
				key->m_value = previousValue;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
				key->m_parent->m_keyValueChangedSignal( key->m_parent, key.get() );
			}
		);
	}
	else
	{
		m_value = value;
	}
}

Animation::Type Animation::Key::getType() const
{
	if( m_interpolator->getName() == "Step" )
	{
		return Animation::Type::Step;
	}
	else if( m_interpolator->getName() == "Linear" )
	{
		return Animation::Type::Linear;
	}
	else
	{
		return Animation::Type::Unknown;
	}
}

void Animation::Key::setType( const Animation::Type type )
{
	setInterpolator( getInterpolatorForType( type )->getName() );
}

Animation::Interpolator* Animation::Key::getInterpolator()
{
	return const_cast< Interpolator* >( static_cast< const Animation::Key* >( this )->getInterpolator() );
}

const Animation::Interpolator* Animation::Key::getInterpolator() const
{
	return m_interpolator;
}

void Animation::Key::setInterpolator( const std::string& name )
{
	Interpolator* const interpolator = Interpolator::getFactory().get( name );

	if( ! interpolator || ( interpolator == m_interpolator ) )
	{
		return;
	}

	Interpolator* const pi = m_interpolator;

	// change interpolator via action

	if( m_parent )
	{
		KeyPtr key = this;
		Action::enact(
			m_parent,
			// Do
			[ key, interpolator ] {
				key->m_interpolator = interpolator;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
				key->m_parent->m_keyInterpolatorChangedSignal( key->m_parent, key.get() );
			},
			// Undo
			[ key, pi ] {
				key->m_interpolator = pi;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
				key->m_parent->m_keyInterpolatorChangedSignal( key->m_parent, key.get() );
			}
		);

		// NOTE : check if new interpolator uses slope/accel of next key's into tangent, if not set default values
		//        if not check if previous interpolator used slope of into tangent, if not and tie slope
		//        active copy slope from next key's from tangent so slopes remain tied after interpolator change.

		if( Key* const kn = nextKey() )
		{
			const Interpolator::Hints hints = m_interpolator->getHints();

			if( ! hints.test( Interpolator::Hint::UseSlopeHi ) )
			{
				kn->m_into.setSlope( Tangent::defaultSlope(), Tangent::Space::Span );
			}
			else if( ! pi->getHints().test( Interpolator::Hint::UseSlopeHi ) && kn->tieSlopeActive( Tangent::Direction::Into ) )
			{
				Private::ScopedValue< bool > guard( kn->m_tieSlope, false );
				kn->m_into.setSlope( kn->m_from.getSlope( Tangent::Space::Key ), Tangent::Space::Key );
			}

			if( ! hints.test( Interpolator::Hint::UseAccelHi ) )
			{
				kn->m_into.setAccel( Tangent::defaultAccel(), Tangent::Space::Span );
			}
		}
	}
	else
	{
		m_interpolator = interpolator;
	}

	// NOTE : check if new interpolator uses slope/accel of from tangent, if not set default values
	//        if not check if previous interpolator used slope of from tangent, if not and tie slope
	//        active copy slope from into tangent so slopes remain tied after interpolator change.

	const Interpolator::Hints hints = m_interpolator->getHints();

	if( ! hints.test( Interpolator::Hint::UseSlopeLo ) )
	{
		m_from.setSlope( Tangent::defaultSlope(), Tangent::Space::Span );
	}
	else if( ! pi->getHints().test( Interpolator::Hint::UseSlopeLo ) && tieSlopeActive( Tangent::Direction::From ) )
	{
		Private::ScopedValue< bool > guard( m_tieSlope, false );
		m_from.setSlope( m_into.getSlope( Tangent::Space::Key ), Tangent::Space::Key );
	}

	if( ! hints.test( Interpolator::Hint::UseAccelLo ) )
	{
		m_from.setAccel( Tangent::defaultAccel(), Tangent::Space::Span );
	}
}

Animation::Key *Animation::Key::nextKey()
{
	return const_cast< Key* >( static_cast< const Key* >( this )->nextKey() );
}

Animation::Key *Animation::Key::prevKey()
{
	return const_cast< Key* >( static_cast< const Key* >( this )->prevKey() );
}

const Animation::Key *Animation::Key::nextKey() const
{
	const Key* k = 0;

	if( m_parent )
	{
		CurvePlug::Keys::const_iterator it = m_parent->m_keys.find( m_time );

		if( ++it != m_parent->m_keys.end() )
		{
			k = ( *it ).get();
		}
	}

	return k;
}

const Animation::Key *Animation::Key::prevKey() const
{
	const Key* k = 0;

	if( m_parent )
	{
		CurvePlug::Keys::const_iterator it = m_parent->m_keys.find( m_time );

		if( it-- != m_parent->m_keys.begin() )
		{
			k = ( *it ).get();
		}
	}

	return k;
}

bool Animation::Key::operator == ( const Key &rhs ) const
{
	// TODO : why are keys compared for deep equality ??
	//        compare tangents equal as well ??

	return
		m_time == rhs.m_time &&
		m_value == rhs.m_value &&
		m_interpolator == rhs.m_interpolator;
}

bool Animation::Key::operator != ( const Key &rhs ) const
{
	return !(*this == rhs);
}

Animation::CurvePlug *Animation::Key::parent()
{
	return m_parent;
}

const Animation::CurvePlug *Animation::Key::parent() const
{
	return m_parent;
}

Animation::Tangent::Space Animation::Key::tieSlopeSpace() const
{
	// NOTE : dt is zero when key is not in curve or key is only key in curve or
	//        key is first or last key in curve.
	//        when dt is zero for key space is meaningless so tie slope in span space

	return ( ( m_into.m_dt != 0.0 ) && ( m_from.m_dt != 0.0 ) )
		? Animation::Tangent::Space::Key
		: Animation::Tangent::Space::Span;
}

void Animation::Key::tieSlopeAverage( const Animation::Tangent::Space space )
{
	if(
		tieSlopeActive( Tangent::Direction::Into ) &&
		tieSlopeActive( Tangent::Direction::From ) )
	{
		const double si = m_into.getSlope( space );
		const double sf = m_from.getSlope( space );

		if( Animation::equivalentValues( si, sf ) )
		{
			// NOTE : average slope angles

			const double s = std::tan(
				std::atan( si ) * 0.5 +
				std::atan( sf ) * 0.5 );

			Private::ScopedValue< bool > guard( m_tieSlope, false );
			m_into.setSlope( s, space );
			m_from.setSlope( s, space );
		}
	}
}

bool Animation::Key::tieAccelActive( const Tangent::Direction direction ) const
{
	if( ! m_tieAccel )
	{
		return false;
	}

	// NOTE : when key not added to curve tie accel is active

	if( m_parent )
	{
		// check that interpolator of previous key uses accel

		const Key* const kp = prevKey();

		if( ! kp ||
			( ( direction == Tangent::Direction::Into ) &&
				( ! kp->m_interpolator->getHints().test( Interpolator::Hint::UseAccelHi ) ) ) ||
			( ( direction == Tangent::Direction::From ) &&
				( !     m_interpolator->getHints().test( Interpolator::Hint::UseAccelLo ) || ( m_parent->finalKey() == this ) ) ) )
		{
			return false;
		}
	}

	return true;
}

bool Animation::Key::tieSlopeActive( const Tangent::Direction direction ) const
{
	if( ! m_tieSlope )
	{
		return false;
	}

	// NOTE : when key not added to curve tie slope is active

	if( m_parent )
	{
		// check that interpolator of previous key uses slope

		const Key* const kp = prevKey();

		if( ! kp ||
			( ( direction == Tangent::Direction::Into ) &&
				( ! kp->m_interpolator->getHints().test( Interpolator::Hint::UseSlopeHi ) ) ) ||
			( ( direction == Tangent::Direction::From ) &&
				( !     m_interpolator->getHints().test( Interpolator::Hint::UseSlopeLo ) || ( m_parent->finalKey() == this ) ) ) )
		{
			return false;
		}
	}

	return true;
}

//////////////////////////////////////////////////////////////////////////
// CurvePlug implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( Animation::CurvePlug );

Animation::CurvePlug::CurvePlug( const std::string &name, Direction direction, unsigned flags )
: ValuePlug( name, direction, flags & ~Plug::AcceptsInputs )
, m_keys()
, m_colorChangedSignal()
, m_extrapolatorChangedSignal()
, m_keyAddedSignal()
, m_keyRemovedSignal()
, m_keyTimeChangedSignal()
, m_keyValueChangedSignal()
, m_keyTieSlopeChangedSignal()
, m_keyTieAccelChangedSignal()
, m_keyInterpolatorChangedSignal()
, m_keyTangentSlopeChangedSignal()
, m_keyTangentAccelChangedSignal()
, m_keyTangentAutoModeChangedSignal()
{
	addChild( new FloatPlug( "out", Plug::Out ) );
}

Animation::CurvePlug::CurvePlugSignal& Animation::CurvePlug::colorChangedSignal()
{
	return m_colorChangedSignal;
}

Animation::CurvePlug::CurvePlugDirectionSignal& Animation::CurvePlug::extrapolatorChangedSignal()
{
	return m_extrapolatorChangedSignal;
}

Animation::CurvePlug::CurvePlugKeySignal& Animation::CurvePlug::keyAddedSignal()
{
	return m_keyAddedSignal;
}

Animation::CurvePlug::CurvePlugKeySignal& Animation::CurvePlug::keyRemovedSignal()
{
	return m_keyRemovedSignal;
}

Animation::CurvePlug::CurvePlugKeySignal& Animation::CurvePlug::keyTimeChangedSignal()
{
	return m_keyTimeChangedSignal;
}

Animation::CurvePlug::CurvePlugKeySignal& Animation::CurvePlug::keyValueChangedSignal()
{
	return m_keyValueChangedSignal;
}

Animation::CurvePlug::CurvePlugKeySignal& Animation::CurvePlug::keyTieSlopeChangedSignal()
{
	return m_keyTieSlopeChangedSignal;
}

Animation::CurvePlug::CurvePlugKeySignal& Animation::CurvePlug::keyTieAccelChangedSignal()
{
	return m_keyTieAccelChangedSignal;
}

Animation::CurvePlug::CurvePlugKeySignal& Animation::CurvePlug::keyInterpolatorChangedSignal()
{
	return m_keyInterpolatorChangedSignal;
}

Animation::CurvePlug::CurvePlugKeyDirectionSignal& Animation::CurvePlug::keyTangentSlopeChangedSignal()
{
	return m_keyTangentSlopeChangedSignal;
}

Animation::CurvePlug::CurvePlugKeyDirectionSignal& Animation::CurvePlug::keyTangentAccelChangedSignal()
{
	return m_keyTangentAccelChangedSignal;
}

Animation::CurvePlug::CurvePlugKeyDirectionSignal& Animation::CurvePlug::keyTangentAutoModeChangedSignal()
{
	return m_keyTangentAutoModeChangedSignal;
}

void Animation::CurvePlug::addKey( const KeyPtr &key, const bool inherit )
{
	if( Key* const previousKey = getKey( key->getTime() ) )
	{
		if( key == previousKey )
		{
			return;
		}

		removeKey( previousKey );
	}

	if( key->m_parent )
	{
		key->m_parent->removeKey( key.get() );
	}

	// inherit interpolation from existing span or first key

	if( inherit )
	{
		if( Key* const kp = previousKey( key->getTime() ) )
		{
			key->setInterpolator( kp->getInterpolator()->getName() );
		}
		else if( Key* const kf = firstKey() )
		{
			key->setInterpolator( kf->getInterpolator()->getName() );
		}
	}

	Action::enact(
		this,
		// Do
		[ this, key ] {
			m_keys.insert( key );
			key->m_parent = this;
			key->m_into.update();
			key->m_from.update();
			if( Key* const k = key->nextKey() ){ k->m_into.update(); }
			if( Key* const k = key->prevKey() ){ k->m_from.update(); }
			propagateDirtiness( outPlug() );
			m_keyAddedSignal( this, key.get() );
		},
		// Undo
		[ this, key ] {
			Key* const kn = key->nextKey();
			Key* const kp = key->prevKey();
			m_keys.erase( key->getTime() );
			if( kn ){ kn->m_into.update(); }
			if( kp ){ kp->m_from.update(); }
			key->m_parent = nullptr;
			key->m_into.update();
			key->m_from.update();
			propagateDirtiness( outPlug() );
			m_keyRemovedSignal( this, key.get() );
		}
	);

	// NOTE : adding key may result in the into tangent of the key being affected by
	//        a different interpolator, and the interpolator of this key affecting the
	//        into tangent of the next key.

	if( Key* const kp = key->prevKey() )
	{
		const Interpolator::Hints hints = kp->m_interpolator->getHints();

		if( ! hints.test( Interpolator::Hint::UseSlopeLo ) )
		{
			key->m_into.setSlope( Tangent::defaultSlope(), Tangent::Space::Span );
		}

		if( ! hints.test( Interpolator::Hint::UseAccelLo ) )
		{
			key->m_from.setAccel( Tangent::defaultAccel(), Tangent::Space::Span );
		}

		// NOTE : update previous final key tie slope as final key from tangent not valid
		//        due to zero time dt. the into tangent may have been manipulated assume
		//        user wants to keep into tangent as is so just copy its slope to from tangent

		if( key.get() == finalKey() && kp->tieSlopeActive( Tangent::Direction::From ) )
		{
			Private::ScopedValue< bool > guard( kp->m_tieSlope, false );
			kp->m_from.setSlope( kp->m_into.getSlope( Tangent::Space::Key ), Tangent::Space::Key );
		}
	}

	if( Key* const kn = key->nextKey() )
	{
		const Interpolator::Hints hints = key->m_interpolator->getHints();

		if( ! hints.test( Interpolator::Hint::UseSlopeHi ) )
		{
			kn->m_into.setSlope( Tangent::defaultSlope(), Tangent::Space::Span );
		}

		if( ! hints.test( Interpolator::Hint::UseAccelHi ) )
		{
			kn->m_into.setAccel( Tangent::defaultAccel(), Tangent::Space::Span );
		}

		// NOTE : update previous first key tie slope as first key from tangent not valid
		//        due to zero time dt. the from tangent may have been manipulated assume
		//        user wants to keep from tangent as is so just copy its slope to into tangent

		if( key.get() == firstKey() && kn->tieSlopeActive( Tangent::Direction::Into ) )
		{
			Private::ScopedValue< bool > guard( kn->m_tieSlope, false );
			kn->m_into.setSlope( kn->m_from.getSlope( Tangent::Space::Key ), Tangent::Space::Key );
		}
	}
}

Animation::Key *Animation::CurvePlug::insertKey( const Animation::Time& time )
{
	// find span for key

	Keys::const_iterator hiIt = m_keys.lower_bound( time );
	if( hiIt == m_keys.end() )
	{
		return 0;
	}

	Key &hi = **hiIt;

	if( hi.getTime() == time || hiIt == m_keys.begin() )
	{
		return 0;
	}

	Key &lo = **std::prev( hiIt );

	// get interpolator for span

	const Interpolator* const interpolator = lo.getInterpolator();

	if( ! interpolator )
	{
		return 0;
	}

	// normalise time to lo, hi key time range

	const double lt = ( time - lo.getTime() ).getSeconds();
	const double ht = ( hi.getTime() - time ).getSeconds();
	const double nt = std::min( std::max( lt / lo.m_from.m_dt, 0.0 ), 1.0 );

	// create new key and dummmy hi/lo keys. use dummy keys to prevent unwanted side effects from
	// badly behaved interpolators.

	KeyPtr km( new Animation::Key( time, 0.0, interpolator->getName(),
		Tangent::defaultSlope(), Tangent::defaultSlope(), Tangent::defaultAccel(), Tangent::defaultAccel(), false, false ) );
	KeyPtr kl( new Animation::Key( lo.getTime(), lo.getValue(), interpolator->getName(),
		lo.m_into.m_slope, lo.m_from.m_slope, lo.m_into.m_accel, lo.m_from.m_accel, false, false ) );
	KeyPtr kh( new Animation::Key( hi.getTime(), hi.getValue(), interpolator->getName(),
		hi.m_into.m_slope, hi.m_from.m_slope, hi.m_into.m_accel, hi.m_from.m_accel, false, false ) );

	// new tangents are in space of new spans (post-bisection)

	kl->m_from.m_dt = lt;
	km->m_into.m_dt = lt;
	km->m_from.m_dt = ht;
	kh->m_into.m_dt = ht;

	// bisect span

	interpolator->bisect( lo.m_value, hi.m_value, lo.m_from, hi.m_into, nt, *km, kl->m_from, kh->m_into );

	// retrieve new tangent positions

	const Imath::V2d lfp = kl->m_from.getPosition( Tangent::Space::Span, false );
	const Imath::V2d hip = kh->m_into.getPosition( Tangent::Space::Span, false );

	// ensure slope/accel untied for lo and hi keys

	Private::ScopedValue< bool > lts( lo.m_tieSlope, false );
	Private::ScopedValue< bool > lta( lo.m_tieAccel, false );
	Private::ScopedValue< bool > hts( hi.m_tieSlope, false );
	Private::ScopedValue< bool > hta( hi.m_tieAccel, false );

	// add new key to curve

	addKey( km );

	// check add key succeeded

	const bool success = ( km->m_parent == this ) && ( getKey( time ) == km.get() );

	if( ! success )
	{
		return 0;
	}

	// set new tangent positions and tie slope/accel of new key

	lo.m_from.setPosition( lfp, Tangent::Space::Span, false );
	hi.m_into.setPosition( hip, Tangent::Space::Span, false );

	km->setTieSlope( true );
	km->setTieAccel( true );

	return km.get();
}

bool Animation::CurvePlug::hasKey( float time ) const
{
	return hasKey( Animation::Time( time, Animation::Time::Units::Seconds ) );
}

bool Animation::CurvePlug::hasKey( const Animation::Time& time ) const
{
	return m_keys.find( time ) != m_keys.end();
}

Animation::Key *Animation::CurvePlug::getKey( float time )
{
	return getKey( Animation::Time( time, Animation::Time::Units::Seconds ) );
}

Animation::Key *Animation::CurvePlug::getKey( const Animation::Time& time )
{
	auto it = m_keys.find( time );
	if( it != m_keys.end() )
	{
		return it->get();
	}
	return nullptr;
}

const Animation::Key *Animation::CurvePlug::getKey( float time ) const
{
	return getKey( Animation::Time( time, Animation::Time::Units::Seconds ) );
}

const Animation::Key *Animation::CurvePlug::getKey( const Animation::Time& time ) const
{
	auto it = m_keys.find( time );
	if( it != m_keys.end() )
	{
		return it->get();
	}
	return nullptr;
}

void Animation::CurvePlug::removeKey( const KeyPtr &key )
{
	if( key->m_parent != this )
	{
		throw IECore::Exception( "Key is not a child" );
	}

	// NOTE : removing key may result in the into tangent of the next key being affected
	//        by a different interpolator

	if( Key* const kp = key->prevKey() )
	{
		if( Key* const kn = key->nextKey() )
		{
			const Interpolator::Hints hints = kp->m_interpolator->getHints();

			if( ! hints.test( Interpolator::Hint::UseSlopeHi ) )
			{
				kn->m_into.setSlope( Tangent::defaultSlope(), Tangent::Space::Span );
			}

			if( ! hints.test( Interpolator::Hint::UseAccelHi ) )
			{
				kn->m_into.setAccel( Tangent::defaultAccel(), Tangent::Space::Span );
			}
		}
	}

	Action::enact(
		this,
		// Do
		[ this, key ] {
			Key* const kn = key->nextKey();
			Key* const kp = key->prevKey();
			m_keys.erase( key->getTime() );
			if( kn ){ kn->m_into.update(); }
			if( kp ){ kp->m_from.update(); }
			key->m_parent = nullptr;
			key->m_into.update();
			key->m_from.update();
			propagateDirtiness( outPlug() );
			m_keyRemovedSignal( this, key.get() );
		},
		// Undo
		[ this, key ] {
			m_keys.insert( key );
			key->m_parent = this;
			key->m_into.update();
			key->m_from.update();
			if( Key* const k = key->nextKey() ){ k->m_into.update(); }
			if( Key* const k = key->prevKey() ){ k->m_from.update(); }
			propagateDirtiness( outPlug() );
			m_keyAddedSignal( this, key.get() );
		}
	);
}

Animation::Key *Animation::CurvePlug::closestKey( float time )
{
	return closestKey( Animation::Time( time, Animation::Time::Units::Seconds ) );
}

Animation::Key *Animation::CurvePlug::closestKey( const Animation::Time& time )
{
	return const_cast<Animation::Key *>( const_cast<const CurvePlug *>( this )->closestKey( time ) );
}

const Animation::Key *Animation::CurvePlug::closestKey( float time ) const
{
	return closestKey( Animation::Time( time, Animation::Time::Units::Seconds ) );
}

const Animation::Key *Animation::CurvePlug::closestKey( const Animation::Time& time ) const
{
	if( m_keys.empty() )
	{
		return nullptr;
	}

	Keys::const_iterator rightIt = m_keys.lower_bound( time );
	if( rightIt == m_keys.end() )
	{
		return m_keys.rbegin()->get();
	}
	else if( (*rightIt)->getTime() == time || rightIt == m_keys.begin() )
	{
		return rightIt->get();
	}
	else
	{
		Keys::const_iterator leftIt = std::prev( rightIt );
		return abs( time - (*leftIt)->getTime() ) < abs( time - (*rightIt)->getTime() ) ? leftIt->get() : rightIt->get();
	}
}

Animation::Key *Animation::CurvePlug::closestKey( float time, float maxDistance )
{
	return closestKey( Animation::Time( time, Animation::Time::Units::Seconds ), maxDistance );
}

Animation::Key *Animation::CurvePlug::closestKey( const Animation::Time& time, float maxDistance )
{
	return const_cast<Animation::Key *>( const_cast<const CurvePlug *>( this )->closestKey( time, maxDistance ) );
}

const Animation::Key *Animation::CurvePlug::closestKey( float time, float maxDistance ) const
{
	return closestKey( Animation::Time( time, Animation::Time::Units::Seconds ), maxDistance );
}

const Animation::Key *Animation::CurvePlug::closestKey( const Animation::Time& time, float maxDistance ) const
{
	const Animation::Key *candidate = closestKey( time );

	if( !candidate || ( abs( candidate->getTime() - time ) ).getSeconds() > static_cast< double >( maxDistance ) )
	{
		return nullptr;
	}

	return candidate;
}

Animation::Key *Animation::CurvePlug::previousKey( float time )
{
	return previousKey( Animation::Time( time, Animation::Time::Units::Seconds ) );
}

Animation::Key *Animation::CurvePlug::previousKey( const Animation::Time& time )
{
	return const_cast<Animation::Key *>( const_cast<const CurvePlug *>( this )->previousKey( time ) );
}

const Animation::Key *Animation::CurvePlug::previousKey( float time ) const
{
	return previousKey( Animation::Time( time, Animation::Time::Units::Seconds ) );
}

const Animation::Key *Animation::CurvePlug::previousKey( const Animation::Time& time ) const
{
	Keys::const_iterator rightIt = m_keys.lower_bound( time );
	if( rightIt == m_keys.begin() )
	{
		return nullptr;
	}
	return std::prev( rightIt )->get();
}

Animation::Key *Animation::CurvePlug::nextKey( float time )
{
	return nextKey( Animation::Time( time, Animation::Time::Units::Seconds ) );
}

Animation::Key *Animation::CurvePlug::nextKey( const Animation::Time& time )
{
	return const_cast<Animation::Key *>( const_cast<const CurvePlug *>( this )->nextKey( time ) );
}

const Animation::Key *Animation::CurvePlug::nextKey( float time ) const
{
	return nextKey( Animation::Time( time, Animation::Time::Units::Seconds ) );
}

const Animation::Key *Animation::CurvePlug::nextKey( const Animation::Time& time ) const
{
	Keys::const_iterator rightIt = m_keys.upper_bound( time );
	if( rightIt == m_keys.end() )
	{
		return nullptr;
	}
	return rightIt->get();
}

Animation::Key *Animation::CurvePlug::firstKey()
{
	return const_cast< Key* >( static_cast< const CurvePlug* >( this )->firstKey() );
}

Animation::Key *Animation::CurvePlug::finalKey()
{
	return const_cast< Key* >( static_cast< const CurvePlug* >( this )->finalKey() );
}

const Animation::Key *Animation::CurvePlug::firstKey() const
{
	const Key* k = 0;

	if( ! m_keys.empty() )
	{
		k = ( *( m_keys.cbegin() ) ).get();
	}

	return k;
}

const Animation::Key *Animation::CurvePlug::finalKey() const
{
	const Key* k = 0;

	if( ! m_keys.empty() )
	{
		k = ( *( m_keys.crbegin() ) ).get();
	}

	return k;
}

Animation::KeyIterator Animation::CurvePlug::begin()
{
	return m_keys.begin();
}

Animation::KeyIterator Animation::CurvePlug::end()
{
	return m_keys.end();
}

Animation::ConstKeyIterator Animation::CurvePlug::begin() const
{
	return m_keys.begin();
}

Animation::ConstKeyIterator Animation::CurvePlug::end() const
{
	return m_keys.end();
}

float Animation::CurvePlug::evaluate( float time ) const
{
	return evaluate( Animation::Time( time, Animation::Time::Units::Seconds ) );
}

float Animation::CurvePlug::evaluate( const Animation::Time& time ) const
{
	// NOTE : no keys return 0

	if( m_keys.empty() )
	{
		return 0;
	}

	// NOTE : each key determines value at a specific time therefore only
	//        interpolate for times which are between the keys.

	Keys::const_iterator hiIt = m_keys.lower_bound( time );
	if( hiIt == m_keys.end() )
	{
		return (*m_keys.rbegin())->getValue();
	}

	const Key &hi = **hiIt;

	if( hi.getTime() == time || hiIt == m_keys.begin() )
	{
		return hi.getValue();
	}

	const Key &lo = **std::prev( hiIt );

	// normalise time to lo, hi key time range

	const double nt = std::min( std::max(
		( time - lo.getTime() ).getSeconds() / ( hi.getTime() - lo.getTime() ).getSeconds(), 0.0 ), 1.0 );

	// evaluate interpolator

	return lo.getInterpolator()->evaluate(
		lo.m_value, hi.m_value,
		lo.getTangent( Animation::Tangent::Direction::From ),
		hi.getTangent( Animation::Tangent::Direction::Into ), nt );
}

FloatPlug *Animation::CurvePlug::outPlug()
{
	return getChild<FloatPlug>( 0 );
}

const FloatPlug *Animation::CurvePlug::outPlug() const
{
	return getChild<FloatPlug>( 0 );
}

//////////////////////////////////////////////////////////////////////////
// Animation implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Animation );

size_t Animation::g_firstPlugIndex = 0;

Animation::Animation( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new Plug( "curves" ) );
}

Animation::~Animation()
{
}

Plug *Animation::curvesPlug()
{
	return getChild<Plug>( g_firstPlugIndex );
}

const Plug *Animation::curvesPlug() const
{
	return getChild<Plug>( g_firstPlugIndex );
}

bool Animation::canAnimate( const ValuePlug *plug )
{
	if( !plug->getFlags( Plug::AcceptsInputs ) )
	{
		return false;
	}

	if( plug->getInput() && !isAnimated( plug ) )
	{
		return false;
	}

	const Node *node = plug->node();
	if( !node || !node->parent<Node>() )
	{
		// Nowhere to parent our Animation node.
		return false;
	}

	return
		runTimeCast<const FloatPlug>( plug ) ||
		runTimeCast<const IntPlug>( plug ) ||
		runTimeCast<const BoolPlug>( plug );
}

bool Animation::isAnimated( const ValuePlug *plug )
{
	return inputCurve( plug );
}

Animation::CurvePlug *Animation::acquire( ValuePlug *plug )
{
	// If the plug is already driven by a curve, return it.
	if( CurvePlug *curve = inputCurve( plug ) )
	{
		return curve;
	}

	// Otherwise we need to make one. Try to find an
	// existing Animation driving plugs on the same node.

	AnimationPtr animation;
	if( !plug->node() )
	{
		throw IECore::Exception( "Plug does not belong to a node" );
	}

	for( Plug::RecursiveIterator it( plug->node() ); !it.done(); ++it )
	{
		ValuePlug *valuePlug = runTimeCast<ValuePlug>( it->get() );
		if( !valuePlug )
		{
			continue;
		}

		if( CurvePlug *curve = inputCurve( valuePlug ) )
		{
			animation = runTimeCast<Animation>( curve->node() );
			if( animation )
			{
				break;
			}
		}
	}

	// If we couldn't find an existing Animation, then
	// make one.
	if( !animation )
	{
		Node *parent = plug->node()->parent<Node>();
		if( !parent )
		{
			throw IECore::Exception( "Node does not have a parent" );
		}
		animation = new Animation;
		parent->addChild( animation );
	}

	// Add a curve to the animation, and hook it up to
	// the target plug.

	CurvePlugPtr curve = new CurvePlug( "curve0", Plug::In, Plug::Default | Plug::Dynamic );
	animation->curvesPlug()->addChild( curve );

	plug->setInput( curve->outPlug() );

	return curve.get();
}

Animation::CurvePlug *Animation::inputCurve( ValuePlug *plug )
{
	ValuePlug *source = plug->source<ValuePlug>();
	if( source == plug ) // no input
	{
		return nullptr;
	}

	CurvePlug *curve = source->parent<CurvePlug>();
	if( !curve )
	{
		return nullptr;
	}

	if( source == curve->outPlug() )
	{
		return curve;
	}

	return nullptr;
}

const Animation::CurvePlug *Animation::inputCurve( const ValuePlug *plug )
{
	// preferring cast over maintaining two near-identical methods.
	return inputCurve( const_cast<ValuePlug *>( plug ) );
}

void Animation::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );
}

void Animation::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( const CurvePlug *parent = output->parent<CurvePlug>() )
	{
		h.append( parent->evaluate( Animation::Time( context->getTime(), Animation::Time::Units::Seconds ) ) );
	}
}

void Animation::compute( ValuePlug *output, const Context *context ) const
{
	if( const CurvePlug *parent = output->parent<CurvePlug>() )
	{
		static_cast<FloatPlug *>( output )->setValue( parent->evaluate(
			Animation::Time( context->getTime(), Animation::Time::Units::Seconds ) ) );
		return;
	}

	ComputeNode::compute( output, context );
}

ValuePlug::CachePolicy Animation::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output->parent<CurvePlug>() )
	{
		return ValuePlug::CachePolicy::Uncached;
	}

	return ComputeNode::computeCachePolicy( output );
}

bool Animation::equivalentValues( const double a, const double b )
{
	// see python PEP 485 : https://www.python.org/dev/peps/pep-0485

	if( a == b )
	{
		return true;
	}

	if( std::isinf( a ) || std::isinf( b ) )
	{
		return false;
	}

	const double delta = std::abs( a - b );

	static const double relative = 1E-9;
	static const double absolute = std::numeric_limits< double >::epsilon();

	return
		( ( delta <= std::abs( relative * a ) ) &&
		( ( delta <= std::abs( relative * b ) ) ) ) ||
			( delta <= absolute );
}
