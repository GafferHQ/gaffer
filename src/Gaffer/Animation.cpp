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

		return std::sqrt( std::fma( slope, slope, 1.0 ) );
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
		assert( dt != 0.0 );

		return slope / dt;
	}

	double slopeFromKeySpace( const double slope, const double dt )
	{
		assert( dt != 0.0 );

		return slope * dt;
	}

	double accelToKeySpace( const double accel, const double slope, const double dt )
	{
		assert( dt != 0.0 );

		// NOTE : As s tends to (+/-) infinity, ((1 + s(k)^2) / (1 + s(c)^2)) tends to
		//        (infinity / infinity) which is meaningless, So,
		//
		//        when |s| <  1 : a(k) = a(c) * dt * sqrt((1 + s(k)^2) / (1 + s(c)^2))
		//        when |s| >= 1 : a(k) = a(c) * sqrt(1 + (1/s(k))^2) / (1 + (1/s(c))^2)

		if( std::abs( slope ) < 1.0 )
		{
			const double sc = slope;
			const double sk = sc / dt;
			return accel * std::sqrt( std::fma( sk, sk, 1.0 ) / std::fma( sc, sc, 1.0 ) ) * dt;
		}
		else
		{
			const double sc = 1.0 / slope;
			const double sk = sc * dt;
			return accel * std::sqrt( std::fma( sk, sk, 1.0 ) / std::fma( sc, sc, 1.0 ) );
		}
	}

	double accelFromKeySpace( const double accel, const double slope, const double dt )
	{
		assert( dt != 0.0 );

		// NOTE : As s tends to (+/-) infinity, ((1 + s(c)^2) / (1 + s(k)^2)) tends to
		//        (infinity / infinity) which is meaningless, So,
		//
		//        when |s| <  1 : a(c) = a(k) * std::sqrt((1 + s(c)^2) / (1 + s(k)^2)) / dt
		//        when |s| >= 1 : a(c) = a(k) * sqrt((1 + (1/s(c))^2) / (1 + (1/s(k))^2))

		if( std::abs( slope ) < 1.0 )
		{
			const double sc = slope;
			const double sk = sc / dt;
			return accel * std::sqrt( std::fma( sc, sc, 1.0 ) / std::fma( sk, sk, 1.0 ) ) / dt;
		}
		else
		{
			const double sc = 1.0 / slope;
			const double sk = sc * dt;
			return accel * std::sqrt( std::fma( sc, sc, 1.0 ) / std::fma( sk, sk, 1.0 ) );
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

			return std::fma( time, std::fma( time, std::fma( time, a, b ), c ), d );
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

			const double v = std::fma( time, std::fma( time, std::fma( time,         a,     b ), c ), d );
			const double s =                 std::fma( time, std::fma( time, a + a + a, b + b ), c );
			const double x = defaultAccel();

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

			return std::fma( s, std::fma( s, std::fma( s, av, bv ), cv ), dv );
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
			const double at3 = at + at + at;

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

				const double  f = std::fma( s, std::fma( s, std::fma( s, at,  bt  ), ct ), -time );
				const double df =              std::fma( s, std::fma( s, at3, bt2 ), ct );

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

Animation::Interpolator::Interpolator( const std::string& name, const Hints hints,
	const double defaultSlope, const double defaultAccel )
: m_name( name )
, m_hints( hints )
, m_defaultSlope( defaultSlope )
, m_defaultAccel( defaultAccel )
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

double Animation::Interpolator::defaultSlope() const
{
	return m_defaultSlope;
}

double Animation::Interpolator::defaultAccel() const
{
	return m_defaultAccel;
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

Animation::Tangent::Direction Animation::Tangent::opposite( const Animation::Tangent::Direction direction )
{
	return static_cast< Direction >( ( static_cast< int >( direction ) + 1 ) % 2 );
}

double Animation::Tangent::defaultSlope()
{
	return 0.0;
}

double Animation::Tangent::defaultAccel()
{
	return ( 1.0 / 3.0 );
}

Animation::Tangent::Tangent( Animation::Key& key, const Animation::Tangent::Direction direction,
	const double slope, const Animation::Tangent::Space slopeSpace, const double accel, const Animation::Tangent::Space accelSpace )
: m_key( & key )
, m_slope( slope )
, m_accel( std::min( accel, maxAccel( m_slope ) ) )
, m_dt( 0.0 )
, m_vt( 0.0 )
, m_direction( direction )
, m_slopeSpace( slopeSpace )
, m_accelSpace( accelSpace )
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
	//
	// NOTE : see comment in update() regards treating m_dt == 0.0 as 1.0

	if( space == Space::Key && ( m_dt != 0.0 ) )
	{
		position.x /= m_dt;
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
	//
	// NOTE : use guards to prevent update of slope/accel space.

	{
		Private::ScopedValue< Space > ssGuard( m_slopeSpace, Space::Span );
		Private::ScopedValue< Space > asGuard( m_accelSpace, Space::Span );
		setSlope( slopeFromPosition( position, m_direction ), Space::Span );
		setAccel( position.length(), Space::Span );
	}

	setSlopeSpace( space );
	setAccelSpace( space );
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
	//
	// NOTE : use guards to prevent update of slope/accel space.

	{
		Private::ScopedValue< Space > ssGuard( m_slopeSpace, Space::Span );
		Private::ScopedValue< Space > asGuard( m_accelSpace, Space::Span );
		setSlope( slope, Space::Span );
		setAccel( position.length(), Space::Span );
	}

	setAccelSpace( space );
}

void Animation::Tangent::setPositionWithAccel( Imath::V2d position, const double accel, const Animation::Tangent::Space space, const bool relative )
{
	// convert position to relative span space

	convertPosition( position, space, relative );

	// set slope and acceleration
	//
	// NOTE : use guards to prevent update of slope/accel space.

	{
		Private::ScopedValue< Space > ssGuard( m_slopeSpace, Space::Span );
		Private::ScopedValue< Space > asGuard( m_accelSpace, Space::Span );
		setSlope( slopeFromPosition( position, m_direction ), Space::Span );
		setAccel( accel, Space::Span );
	}

	setSlopeSpace( space );
}

Imath::V2d Animation::Tangent::getPosition( const Animation::Tangent::Space space, const bool relative ) const
{
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
		p.x = std::min( m_accel / std::sqrt( std::fma( s, s, 1.0 ) ), 1.0 );
		p.y = p.x * s;
	}
	else
	{
		const double s = 1.0 / m_slope;
		p.y = std::copysign( m_accel / std::sqrt( std::fma( s, s, 1.0 ) ), s );
		p.x = std::min( p.y * s, 1.0 );
	}

	if( m_direction == Direction::Into )
	{
		if( p.x != 0.0 ) { p.x = -p.x; }
		if( p.y != 0.0 ) { p.y = -p.y; }
	}

	// NOTE : see comment in update() regards treating m_dt == 0.0 as 1.0

	if( ( space == Space::Key ) && ( m_dt != 0.0 ) )
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

void Animation::Tangent::setSlopeSpace( const Animation::Tangent::Space space )
{
	// check for no change

	if( ( m_dt != 0.0 ) || ( m_slopeSpace == space ) )
	{
		return;
	}

	// make change via action

	if( m_key->m_parent )
	{
		KeyPtr key = m_key;
		const Space ss = m_slopeSpace;
		Action::enact(
			key->m_parent,
			// Do
			[ this, key, space ] {
				m_slopeSpace = space;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
			},
			// Undo
			[ this, key, ss ] {
				m_slopeSpace = ss;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
			}
		);
	}
	else
	{
		m_slopeSpace = space;
	}
}

void Animation::Tangent::setSlope( double slope, const Animation::Tangent::Space space )
{
	// convert to span space
	//
	// NOTE : see comment in update() regards treating m_dt == 0.0 as 1.0

	if( ( space == Space::Key ) && ( m_dt != 0.0 ) )
	{
		slope = slopeFromKeySpace( slope, m_dt );
	}

	// set slope space

	setSlopeSpace( space );

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

	// tie slope of opposite tangent

	if( m_key->tieSlopeActive( opposite( m_direction ) ) )
	{
		Tangent& ot = m_key->getTangent( opposite( m_direction ) );
		Private::ScopedValue< TieMode > tmGuard( m_key->m_tieMode, TieMode::Manual );
		Private::ScopedValue< Space > ssGuard( ot.m_slopeSpace, Space::Key );
		ot.setSlope( getSlope( Space::Key ), Space::Key );
	}
}

void Animation::Tangent::setSlopeWithAccel( const double slope, const double accel, const Animation::Tangent::Space space )
{
	Private::ScopedValue< Space > asGuard( m_accelSpace, Space::Span );
	setSlope( slope, space );
	setAccel( accel, Space::Span );
}

double Animation::Tangent::getSlope( const Animation::Tangent::Space space ) const
{
	// NOTE : see comment in update() regards treating m_dt == 0.0 as 1.0

	return ( ( space == Space::Key ) && ( m_dt != 0.0 ) ) ? slopeToKeySpace( m_slope, m_dt ) : m_slope;
}

bool Animation::Tangent::slopeIsUsed() const
{
	assert( m_key );

	// check key added to curve

	if( m_key->m_parent == 0 )
	{
		return false;
	}

	// check whether key is first or final key then interpolator hints

	if(
		( ( m_direction == Direction::From ) && (
			( m_key->m_parent->finalKey() == m_key ) ||
			( m_key->m_interpolator->getHints().test( Interpolator::Hint::UseSlopeLo ) == false ) ) ) ||
		( ( m_direction == Direction::Into ) && (
			( m_key->m_parent->firstKey() == m_key ) ||
			( m_key->prevKey()->m_interpolator->getHints().test( Interpolator::Hint::UseSlopeHi ) == false ) ) ) )
	{
		return false;
	}

	return true;
}

void Animation::Tangent::setAccelSpace( const Animation::Tangent::Space space )
{
	// check for no change

	if( ( m_dt != 0.0 ) || ( m_accelSpace == space ) )
	{
		return;
	}

	// make change via action

	if( m_key->m_parent )
	{
		KeyPtr key = m_key;
		const Space as = m_accelSpace;
		Action::enact(
			key->m_parent,
			// Do
			[ this, key, space ] {
				m_accelSpace = space;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
			},
			// Undo
			[ this, key, as ] {
				m_accelSpace = as;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
			}
		);
	}
	else
	{
		m_accelSpace = space;
	}
}

void Animation::Tangent::setAccel( double accel, const Animation::Tangent::Space space )
{
	// convert to span space
	//
	// NOTE : see comment in update() regards treating m_dt == 0.0 as 1.0

	if( ( space == Space::Key ) && ( m_dt != 0.0 ) )
	{
		accel = accelFromKeySpace( accel, m_slope, m_dt );
	}

	// set accel space

	setAccelSpace( space );

	// clamp acceleration

	accel = std::min( accel, maxAccel( m_slope ) );

	// check for no change

	if( Animation::equivalentValues( m_accel, accel ) )
	{
		return;
	}

	// tie acceleration of opposite tangent
	//
	// NOTE : scale opposite by same amount, unless scale is infinite then add instead.

	if( m_key->tieAccelActive( opposite( m_direction ) ) )
	{
		Tangent& ot = m_key->getTangent( opposite( m_direction ) );
		Private::ScopedValue< TieMode > tmGuard( m_key->m_tieMode, TieMode::Manual );
		Private::ScopedValue< Space > asGuard( ot.m_accelSpace, Space::Span );
		ot.setAccel( ( m_accel == 0.0 )
				? ( ot.m_accel + accel )
				: ( ot.m_accel * ( accel / m_accel ) ),
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

double Animation::Tangent::getAccel( const Space space ) const
{
	// NOTE : see comment in update() regards treating m_dt == 0.0 as 1.0

	return ( ( space == Space::Key ) && ( m_dt != 0.0 ) ) ? accelToKeySpace( m_accel, m_slope, m_dt ) : m_accel;
}

bool Animation::Tangent::accelIsUsed() const
{
	assert( m_key );

	// check key added to curve

	if( m_key->m_parent == 0 )
	{
		return false;
	}

	// check whether key is first or final key then interpolator hints

	if(
		( ( m_direction == Direction::From ) && (
			( m_key->m_parent->finalKey() == m_key ) ||
			( m_key->m_interpolator->getHints().test( Interpolator::Hint::UseAccelLo ) == false ) ) ) ||
		( ( m_direction == Direction::Into ) && (
			( m_key->m_parent->firstKey() == m_key ) ||
			( m_key->prevKey()->m_interpolator->getHints().test( Interpolator::Hint::UseAccelHi ) == false ) ) ) )
	{
		return false;
	}

	return true;
}

void Animation::Tangent::update()
{
	// update span time and value differences
	//
	// NOTE : when dt is zero the tangent's parent key has not been added to a curve or
	//        the tangent's direction is into and its parent key is the first key in a
	//        curve or the tangent's direction is from and its parent key is the final
	//        key in a curve. In all these cases treat dt as one, this makes span space
	//        and key space equivalent. However if dt was 1.0 in the above cases it
	//        would not be possible to differentiate from the case where the time
	//        difference to next/prev key is actually one second.

	double dt = 0.0;
	double vt = 0.0;

	if( m_key->m_parent )
	{
		switch( m_direction )
		{
			case Direction::Into:
				if( const Key* const kp = m_key->prevKey() )
				{
					dt = ( m_key->m_time - kp->m_time ).getSeconds();
					vt = ( m_key->m_value - kp->m_value );
				}
				break;
			case Direction::From:
				if( const Key* const kn = m_key->nextKey() )
				{
					dt = ( kn->m_time - m_key->m_time ).getSeconds();
					vt = ( kn->m_value - m_key->m_value );
				}
				break;
			default:
				break;
		}
	}

	// NOTE : when dt becomes zero either the tangent's parent key has been removed from a curve
	//        or the tangent's direction is into and its parent key is the first key in a curve
	//        or the tangent's direction is from and its parent key is the final key in a curve.
	//        In all the above cases do not update m_dt so that if the parent key is added back
	//        to a curve or is no longer the first or final key in a curve, it is possible to
	//        correctly adjust the slope and accel to a new span dt. this is not possible by
	//        converting the slope and accel to key space.
	// NOTE : when dt becomes non zero either the tangent's parent key has been added to a curve
	//        or is no longer the first or final key in a curve (and above note does not apply)
	//        so convert the slope and accel to span space based on new span dt.
	// NOTE : when dt changes from non zero to a different non zero value, adjust slope and accel
	//        based on new span dt as determined by tangent auto mode.

	if( dt != m_dt )
	{
		if( m_dt == 0.0 )
		{
			// NOTE : convert slope and accel to span space

			if( m_slopeSpace == Space::Key )
			{
				m_slope = slopeFromKeySpace( m_slope, dt );
				m_slopeSpace = Space::Span;
			}

			if( m_accelSpace == Space::Key )
			{
				m_accel = accelFromKeySpace( m_accel, m_slope, dt );
				m_accelSpace = Space::Span;
			}

			m_dt = dt;
		}
		else if( dt != 0.0 )
		{
			// TODO : this should be done (or not) by tangent auto mode

#			define AUTO_MODE_MANUAL 1
#			define AUTO_MODE_MANUAL_SLOPE 2
#			define AUTO_MODE_SIMPLE 3
#			define AUTO_MODE AUTO_MODE_MANUAL_SLOPE

#			if   AUTO_MODE == AUTO_MODE_MANUAL
			const double ss = m_slope;
			const double st = m_slope * ( dt / m_dt );
			// TODO : signal change to accel as it is changing in span space. however no action neeeded
			m_accel = accelFromKeySpace( accelToKeySpace( m_accel, ss, m_dt ), st, dt );
			// NOTE : no need to signal slope change as it is not changing in key space
			m_slope = st;
#			elif AUTO_MODE == AUTO_MODE_MANUAL_SLOPE
			// NOTE : no need to signal accel change as it is not changing in span space
			// NOTE : no need to signal slope change as it is not changing in key space
			m_slope *= ( dt / m_dt );
#			elif AUTO_MODE == AUTO_MODE_SIMPLE
			// TODO : average slopes in key space if tie slope enabled
#			endif
			m_dt = dt;
		}
	}

	m_vt = vt;
}

} // Gaffer

//////////////////////////////////////////////////////////////////////////
// Key implementation
//////////////////////////////////////////////////////////////////////////

Animation::Key::Key( const float time, const float value, const Animation::Type type )
: m_parent( nullptr )
, m_interpolator( getInterpolatorForType( type ) )
, m_into( *this, Tangent::Direction::Into,
	Tangent::defaultSlope(), Tangent::Space::Span, Tangent::defaultAccel(), Tangent::Space::Span )
, m_from( *this, Tangent::Direction::From,
	Tangent::defaultSlope(), Tangent::Space::Span, Tangent::defaultAccel(), Tangent::Space::Span )
, m_time( time, Time::Units::Seconds )
, m_value( value )
, m_tieMode( Tangent::TieMode::SlopeAndAccel )
{}

Animation::Key::Key( const Animation::Time& time, const float value, const std::string& interpolatorName )
: m_parent( nullptr )
, m_interpolator( Interpolator::getFactory().get( interpolatorName ) )
, m_into( *this, Tangent::Direction::Into,
	Tangent::defaultSlope(), Tangent::Space::Span, Tangent::defaultAccel(), Tangent::Space::Span )
, m_from( *this, Tangent::Direction::From,
	Tangent::defaultSlope(), Tangent::Space::Span, Tangent::defaultAccel(), Tangent::Space::Span )
, m_time( time )
, m_value( value )
, m_tieMode( Tangent::TieMode::SlopeAndAccel )
{}

Animation::Key::Key( const Animation::Time& time, const float value, const std::string& interpolatorName,
	const double intoSlope, const Animation::Tangent::Space intoSlopeSpace, const double intoAccel, const Animation::Tangent::Space intoAccelSpace,
	const double fromSlope, const Animation::Tangent::Space fromSlopeSpace, const double fromAccel, const Animation::Tangent::Space fromAccelSpace,
	const Animation::Tangent::TieMode tieMode )
: m_parent( nullptr )
, m_interpolator( Interpolator::getFactory().get( interpolatorName ) )
, m_into( *this, Tangent::Direction::Into, intoSlope, intoSlopeSpace, intoAccel, intoAccelSpace )
, m_from( *this, Tangent::Direction::From, fromSlope, fromSlopeSpace, fromAccel, fromAccelSpace )
, m_time( time )
, m_value( value )
, m_tieMode( tieMode )
{}

Animation::Tangent& Animation::Key::getTangent( const Animation::Tangent::Direction direction )
{
	return const_cast< Tangent& >(
		static_cast< const Key* >( this )->getTangent( direction ) );
}

const Animation::Tangent& Animation::Key::getTangent( const Animation::Tangent::Direction direction ) const
{
	return ( direction == Tangent::Direction::Into ) ? m_into : m_from;
}

Animation::Tangent::TieMode Animation::Key::getTieMode() const
{
	return m_tieMode;
}

void Animation::Key::setTieMode( const Animation::Tangent::TieMode tieMode )
{
	// check for no change

	if( tieMode == m_tieMode )
	{
		return;
	}

	// make change via action

	if( m_parent )
	{
		KeyPtr key = this;
		Tangent::TieMode pm = m_tieMode;
		Action::enact(
			m_parent,
			// Do
			[ key, tieMode ] {
				key->m_tieMode = tieMode;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
				key->m_parent->m_keyTieModeChangedSignal( key->m_parent, key.get() );
			},
			// Undo
			[ key, pm ] {
				key->m_tieMode = pm;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
				key->m_parent->m_keyTieModeChangedSignal( key->m_parent, key.get() );
			}
		);
	}
	else
	{
		m_tieMode = tieMode;
	}

	tieSlopeAverage();
}

float Animation::Key::getFloatTime() const
{
	return m_time.getSeconds();
}

Animation::Time Animation::Key::getTime() const
{
	return m_time;
}

void Animation::Key::setTime( float time )
{
	setTime( Animation::Time( time, Time::Units::Seconds ) );
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
		const Time previousTime = m_time;
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
				m_into.setSlope( kp->m_interpolator->defaultSlope(), Tangent::Space::Span );
			}

			if( ! hints.test( Interpolator::Hint::UseAccelLo ) )
			{
				m_into.setAccel( kp->m_interpolator->defaultAccel(), Tangent::Space::Span );
			}

			// NOTE : update previous final key tie slope as final key from tangent not valid
			//        due to zero time dt. the into tangent may have been manipulated assume
			//        user wants to keep into tangent as is so just copy its slope to from tangent

			if( key.get() == m_parent->finalKey() && kp->tieSlopeActive( Tangent::Direction::From ) )
			{
				Private::ScopedValue< Tangent::TieMode > guard( kp->m_tieMode, Tangent::TieMode::Manual );
				kp->m_from.setSlope( kp->m_into.getSlope( Tangent::Space::Key ), Tangent::Space::Key );
			}
		}

		if( Key* const kn = nextKey() )
		{
			const Interpolator::Hints hints = m_interpolator->getHints();

			if( ! hints.test( Interpolator::Hint::UseSlopeHi ) )
			{
				kn->m_into.setSlope( kn->m_interpolator->defaultSlope(), Tangent::Space::Span );
			}

			if( ! hints.test( Interpolator::Hint::UseAccelHi ) )
			{
				kn->m_into.setAccel( kn->m_interpolator->defaultAccel(), Tangent::Space::Span );
			}

			// NOTE : update previous first key tie slope as first key from tangent not valid
			//        due to zero time dt. the from tangent may have been manipulated assume
			//        user wants to keep from tangent as is so just copy its slope to into tangent

			if( key.get() == m_parent->firstKey() && kn->tieSlopeActive( Tangent::Direction::Into ) )
			{
				Private::ScopedValue< Tangent::TieMode > guard( kn->m_tieMode, Tangent::TieMode::Manual );
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
				key->m_from.update();
				key->m_into.update();
				if( Key* const kn = key->nextKey() ){ kn->m_into.update(); }
				if( Key* const kp = key->prevKey() ){ kp->m_from.update(); }
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
				key->m_parent->m_keyValueChangedSignal( key->m_parent, key.get() );
			},
			// Undo
			[ key, previousValue ] {
				key->m_value = previousValue;
				key->m_from.update();
				key->m_into.update();
				if( Key* const kn = key->nextKey() ){ kn->m_into.update(); }
				if( Key* const kp = key->prevKey() ){ kp->m_from.update(); }
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
		return Type::Step;
	}
	else if( m_interpolator->getName() == "Linear" )
	{
		return Type::Linear;
	}
	else
	{
		return Type::Unknown;
	}
}

void Animation::Key::setType( const Animation::Type type )
{
	setInterpolator( getInterpolatorForType( type )->getName() );
}

Animation::Interpolator* Animation::Key::getInterpolator()
{
	return const_cast< Interpolator* >( static_cast< const Key* >( this )->getInterpolator() );
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
				kn->m_into.setSlope( m_interpolator->defaultSlope(), Tangent::Space::Span );
			}
			else if( ! pi->getHints().test( Interpolator::Hint::UseSlopeHi ) && kn->tieSlopeActive( Tangent::Direction::Into ) )
			{
				Private::ScopedValue< Tangent::TieMode > tmGuard( kn->m_tieMode, Tangent::TieMode::Manual );
				Private::ScopedValue< Tangent::Space > issGuard( kn->m_into.m_slopeSpace, Tangent::Space::Key );
				kn->m_into.setSlope( kn->m_from.getSlope( Tangent::Space::Key ), Tangent::Space::Key );
			}

			if( ! hints.test( Interpolator::Hint::UseAccelHi ) )
			{
				kn->m_into.setAccel( m_interpolator->defaultAccel(), Tangent::Space::Span );
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
		m_from.setSlope( m_interpolator->defaultSlope(), Tangent::Space::Span );
	}
	else if( ! pi->getHints().test( Interpolator::Hint::UseSlopeLo ) && tieSlopeActive( Tangent::Direction::From ) )
	{
		Private::ScopedValue< Tangent::TieMode > tmGuard( m_tieMode, Tangent::TieMode::Manual );
		Private::ScopedValue< Tangent::Space > issGuard( m_from.m_slopeSpace, Tangent::Space::Key );
		m_from.setSlope( m_into.getSlope( Tangent::Space::Key ), Tangent::Space::Key );
	}

	if( ! hints.test( Interpolator::Hint::UseAccelLo ) )
	{
		m_from.setAccel( m_interpolator->defaultAccel(), Tangent::Space::Span );
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

void Animation::Key::tieSlopeAverage()
{
	if(
		tieSlopeActive( Tangent::Direction::Into ) &&
		tieSlopeActive( Tangent::Direction::From ) )
	{
		const Tangent::Space space = Tangent::Space::Key;
		const double si = m_into.getSlope( space );
		const double sf = m_from.getSlope( space );

		if( ! Animation::equivalentValues( si, sf ) )
		{
			// NOTE : average slope angles

			const double s = std::tan(
				std::atan( si ) * 0.5 +
				std::atan( sf ) * 0.5 );

			Private::ScopedValue< Tangent::TieMode > tmGuard( m_tieMode, Tangent::TieMode::Manual );
			Private::ScopedValue< Tangent::Space > issGuard( m_into.m_slopeSpace, space );
			Private::ScopedValue< Tangent::Space > fssGuard( m_from.m_slopeSpace, space );
			m_into.setSlope( s, space );
			m_from.setSlope( s, space );
		}
	}
}

bool Animation::Key::tieAccelActive( const Tangent::Direction direction ) const
{
	switch( m_tieMode )
	{
		case Tangent::TieMode::Manual:
			return false;
		case Tangent::TieMode::Slope:
			return false;
		case Tangent::TieMode::SlopeAndAccel:
			break;
		default:
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
	switch( m_tieMode )
	{
		case Tangent::TieMode::Manual:
			return false;
		case Tangent::TieMode::Slope:
			break;
		case Tangent::TieMode::SlopeAndAccel:
			break;
		default:
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
, m_keyTieModeChangedSignal()
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

Animation::CurvePlug::CurvePlugKeySignal& Animation::CurvePlug::keyTieModeChangedSignal()
{
	return m_keyTieModeChangedSignal;
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
			if( Key* const kn = key->nextKey() ){ kn->m_into.update(); }
			if( Key* const kp = key->prevKey() ){ kp->m_from.update(); }
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
			key->m_into.setSlope( kp->m_interpolator->defaultSlope(), Tangent::Space::Span );
		}

		if( ! hints.test( Interpolator::Hint::UseAccelLo ) )
		{
			key->m_into.setAccel( kp->m_interpolator->defaultAccel(), Tangent::Space::Span );
		}

		// NOTE : update previous final key tie slope as final key from tangent not valid
		//        due to zero time dt. the into tangent may have been manipulated assume
		//        user wants to keep into tangent as is so just copy its slope to from tangent

		if( key.get() == finalKey() && kp->tieSlopeActive( Tangent::Direction::From ) )
		{
			Private::ScopedValue< Tangent::TieMode > guard( kp->m_tieMode, Tangent::TieMode::Manual );
			kp->m_from.setSlope( kp->m_into.getSlope( Tangent::Space::Key ), Tangent::Space::Key );
		}
	}

	if( Key* const kn = key->nextKey() )
	{
		const Interpolator::Hints hints = key->m_interpolator->getHints();

		if( ! hints.test( Interpolator::Hint::UseSlopeHi ) )
		{
			kn->m_into.setSlope( key->m_interpolator->defaultSlope(), Tangent::Space::Span );
		}

		if( ! hints.test( Interpolator::Hint::UseAccelHi ) )
		{
			kn->m_into.setAccel( key->m_interpolator->defaultAccel(), Tangent::Space::Span );
		}

		// NOTE : update previous first key tie slope as first key from tangent not valid
		//        due to zero time dt. the from tangent may have been manipulated assume
		//        user wants to keep from tangent as is so just copy its slope to into tangent

		if( key.get() == firstKey() && kn->tieSlopeActive( Tangent::Direction::Into ) )
		{
			Private::ScopedValue< Tangent::TieMode > guard( kn->m_tieMode, Tangent::TieMode::Manual );
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

	KeyPtr km( new Key( time, 0.0, interpolator->getName(),
		interpolator->defaultSlope(), Tangent::Space::Span,
		interpolator->defaultAccel(), Tangent::Space::Span,
		interpolator->defaultSlope(), Tangent::Space::Span,
		interpolator->defaultAccel(), Tangent::Space::Span, Tangent::TieMode::Manual ) );
	KeyPtr kl( new Key( lo.getTime(), lo.getValue(), interpolator->getName(),
		lo.m_into.m_slope, lo.m_into.m_slopeSpace,
		lo.m_into.m_accel, lo.m_into.m_accelSpace,
		lo.m_from.m_slope, lo.m_from.m_slopeSpace,
		lo.m_from.m_accel, lo.m_from.m_accelSpace, Tangent::TieMode::Manual ) );
	KeyPtr kh( new Key( hi.getTime(), hi.getValue(), interpolator->getName(),
		hi.m_into.m_slope, hi.m_into.m_slopeSpace,
		hi.m_into.m_accel, hi.m_into.m_accelSpace,
		hi.m_from.m_slope, hi.m_from.m_slopeSpace,
		hi.m_from.m_accel, hi.m_from.m_accelSpace, Tangent::TieMode::Manual ) );

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

	Private::ScopedValue< Tangent::TieMode > ltm( lo.m_tieMode, Tangent::TieMode::Manual );
	Private::ScopedValue< Tangent::TieMode > htm( hi.m_tieMode, Tangent::TieMode::Manual );

	// add new key to curve

	addKey( km );

	// check add key succeeded

	const bool success = ( km->m_parent == this ) && ( getKey( time ) == km.get() );

	if( ! success )
	{
		return 0;
	}

	// set new tangent positions and tie mode of new key

	lo.m_from.setPosition( lfp, Tangent::Space::Span, false );
	hi.m_into.setPosition( hip, Tangent::Space::Span, false );

	km->setTieMode( Tangent::TieMode::SlopeAndAccel );

	return km.get();
}

bool Animation::CurvePlug::hasKey( float time ) const
{
	return hasKey( Time( time, Time::Units::Seconds ) );
}

bool Animation::CurvePlug::hasKey( const Animation::Time& time ) const
{
	return m_keys.find( time ) != m_keys.end();
}

Animation::Key *Animation::CurvePlug::getKey( float time )
{
	return getKey( Time( time, Time::Units::Seconds ) );
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
	return getKey( Time( time, Time::Units::Seconds ) );
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
				kn->m_into.setSlope( kp->m_interpolator->defaultSlope(), Tangent::Space::Span );
			}

			if( ! hints.test( Interpolator::Hint::UseAccelHi ) )
			{
				kn->m_into.setAccel( kp->m_interpolator->defaultAccel(), Tangent::Space::Span );
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
	return closestKey( Time( time, Time::Units::Seconds ) );
}

Animation::Key *Animation::CurvePlug::closestKey( const Animation::Time& time )
{
	return const_cast< Key* >( const_cast< const CurvePlug* >( this )->closestKey( time ) );
}

const Animation::Key *Animation::CurvePlug::closestKey( float time ) const
{
	return closestKey( Time( time, Time::Units::Seconds ) );
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
	return closestKey( Time( time, Time::Units::Seconds ), maxDistance );
}

Animation::Key *Animation::CurvePlug::closestKey( const Animation::Time& time, float maxDistance )
{
	return const_cast< Key* >( const_cast< const CurvePlug* >( this )->closestKey( time, maxDistance ) );
}

const Animation::Key *Animation::CurvePlug::closestKey( float time, float maxDistance ) const
{
	return closestKey( Time( time, Time::Units::Seconds ), maxDistance );
}

const Animation::Key *Animation::CurvePlug::closestKey( const Animation::Time& time, float maxDistance ) const
{
	const Key *candidate = closestKey( time );

	if( !candidate || ( abs( candidate->getTime() - time ) ).getSeconds() > static_cast< double >( maxDistance ) )
	{
		return nullptr;
	}

	return candidate;
}

Animation::Key *Animation::CurvePlug::previousKey( float time )
{
	return previousKey( Time( time, Time::Units::Seconds ) );
}

Animation::Key *Animation::CurvePlug::previousKey( const Animation::Time& time )
{
	return const_cast< Key* >( const_cast< const CurvePlug* >( this )->previousKey( time ) );
}

const Animation::Key *Animation::CurvePlug::previousKey( float time ) const
{
	return previousKey( Time( time, Time::Units::Seconds ) );
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
	return nextKey( Time( time, Time::Units::Seconds ) );
}

Animation::Key *Animation::CurvePlug::nextKey( const Animation::Time& time )
{
	return const_cast< Key* >( const_cast< const CurvePlug* >( this )->nextKey( time ) );
}

const Animation::Key *Animation::CurvePlug::nextKey( float time ) const
{
	return nextKey( Time( time, Time::Units::Seconds ) );
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
	return evaluate( Animation::Time( time, Time::Units::Seconds ) );
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
		lo.getTangent( Tangent::Direction::From ),
		hi.getTangent( Tangent::Direction::Into ), nt );
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
		h.append( parent->evaluate( Time( context->getTime(), Time::Units::Seconds ) ) );
	}
}

void Animation::compute( ValuePlug *output, const Context *context ) const
{
	if( const CurvePlug *parent = output->parent<CurvePlug>() )
	{
		static_cast<FloatPlug *>( output )->setValue( parent->evaluate(
			Time( context->getTime(), Time::Units::Seconds ) ) );
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

const char* Animation::toString( const Animation::Type type )
{
	switch( type )
	{
		case Type::Step:
			return "Step";
		case Type::Linear:
			return "Linear";
		case Type::Unknown:
			return "Unknown";
		default:
			assert( 0 );
			return 0;
	}
}

const char* Animation::toString( const Animation::Time::Units time )
{
	switch( time )
	{
		case Time::Units::Seconds:
			return "Seconds";
		case Time::Units::Fps24:
			return "Fps24";
		case Time::Units::Fps25:
			return "Fps25";
		case Time::Units::Fps48:
			return "Fps48";
		case Time::Units::Fps60:
			return "Fps60";
		case Time::Units::Fps90:
			return "Fps90";
		case Time::Units::Fps120:
			return "Fps120";
		case Time::Units::Milli:
			return "Milli";
		case Time::Units::Ticks:
			return "Ticks";
		default:
			assert( 0 );
			return 0;
	}
}

const char* Animation::toString( const Animation::Tangent::Space space )
{
	switch( space )
	{
		case Tangent::Space::Span:
			return "Span";
		case Tangent::Space::Key:
			return "Key";
		default:
			assert( 0 );
			return 0;
	}
}

const char* Animation::toString( const Animation::Tangent::Direction direction )
{
	switch( direction )
	{
		case Tangent::Direction::Into:
			return "Into";
		case Tangent::Direction::From:
			return "From";
		default:
			assert( 0 );
			return 0;
	}
}

const char* Animation::toString( const Animation::Tangent::TieMode mode )
{
	switch( mode )
	{
		case Tangent::TieMode::Manual:
			return "Manual";
		case Tangent::TieMode::Slope:
			return "Slope";
		case Tangent::TieMode::SlopeAndAccel:
			return "SlopeAndAccel";
		default:
			assert( 0 );
			return 0;
	}
}
