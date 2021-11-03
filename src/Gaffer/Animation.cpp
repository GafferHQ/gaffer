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
#include "Gaffer/Private/ScopedAssignment.h"

#include "OpenEXR/ImathFun.h"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <limits>
#include <vector>

namespace Gaffer
{

class Animation::Interpolator : public IECore::RefCounted
{

	public:

		IE_CORE_DECLAREMEMBERPTR( Interpolator )

		enum class Hint
		{
			UseSlopeLo = 0,
			UseSlopeHi = 1,
			UseScaleLo = 2,
			UseScaleHi = 3
		};

		struct Hints
		{
			Hints();
			Hints( Hint hint );
			Hints( const Hints& rhs );
			Hints& operator = ( const Hints& rhs );
			bool test( Hint hint ) const;

			GAFFER_API friend Hints operator | ( const Hints& lhs, const Hints& rhs );

		private:

			std::uint32_t m_bits;
		};

		struct Factory : public IECore::RefCounted
		{
			~Factory();

			bool add( Interpolator::Ptr interpolator );
			Interpolator* get( Animation::Interpolation interpolation );
			Interpolator* getDefault();

			IE_CORE_DECLAREMEMBERPTR( Factory )

		private:

			friend class Interpolator;
			Factory();

			typedef std::vector< Interpolator::Ptr > Container;
			Container m_container;
			Interpolator::Ptr m_default;
		};

	static Factory& getFactory();

	~Interpolator();

	Animation::Interpolation getInterpolation() const;
	Hints getHints() const;

protected:

	/// construct with specified interpolation and hints
	Interpolator( const Animation::Interpolation interpolation, Hints hints );

private:

	friend class CurvePlug;
	friend class Tangent;

	/// Implement to return interpolated value at specified normalised time
	virtual double evaluate( const Key& keyLo, const Key& keyHi, double time, double dt ) const = 0;

	/// Implement to bisect the span at the specified time, should set new key's value and slope and scale of new tangents
	virtual void bisect( const Key& keyLo, const Key& keyHi, double time, double dt,
		Key& newKey, Tangent& newTangentLo, Tangent& newTangentHi ) const;

	/// Implement to compute the effective slope of the specified tangent
	virtual double effectiveSlope( const Tangent& tangent, double dt, double dv ) const;

	/// Implement to compute the effective scale of the specified tangent
	virtual double effectiveScale( const Tangent& tangent, double dt, double dv ) const;

	Animation::Interpolation m_interpolation;
	Hints m_hints;
};

} // Gaffer

namespace
{

double maxScale( const double slope )
{
	// NOTE : s = y/x
	//        l = sqrt(x^2 + y^2)
	//
	//        When scale at maximum, x = 1, therefore,
	//
	//        y = s
	//        l = sqrt(1 + s^2)

	return std::sqrt( std::fma( slope, slope, 1.0 ) );
}

double slopeFromPosition( const Imath::V2d& position, const Gaffer::Animation::Direction direction )
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
			position.y * ( direction == Gaffer::Animation::Direction::In ? -1.0 : 1.0 ) );
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

double tieScaleRatio( const double inScale, const double outScale )
{
	return ( inScale == outScale ) ? 1.0 : ( ( outScale == 0.0 ) ? 0.0 : ( inScale / outScale ) );
}

// constant interpolator

struct InterpolatorConstant
: public Gaffer::Animation::Interpolator
{
	InterpolatorConstant()
	: Gaffer::Animation::Interpolator( Gaffer::Animation::Interpolation::Constant, Gaffer::Animation::Interpolator::Hints() )
	{}

	double evaluate( const Gaffer::Animation::Key& keyLo, const Gaffer::Animation::Key& /*keyHi*/,
		const double /*time*/, const double /*dt*/ ) const override
	{
		return keyLo.getValue();
	}
};

// constant next interpolator

struct InterpolatorConstantNext
: public Gaffer::Animation::Interpolator
{
	InterpolatorConstantNext()
	: Gaffer::Animation::Interpolator( Gaffer::Animation::Interpolation::ConstantNext, Gaffer::Animation::Interpolator::Hints() )
	{}

	double evaluate( const Gaffer::Animation::Key& /*keyLo*/, const Gaffer::Animation::Key& keyHi,
		const double /*time*/, const double /*dt*/ ) const override
	{
		return keyHi.getValue();
	}
};

// linear interpolator

struct InterpolatorLinear
: public Gaffer::Animation::Interpolator
{
	InterpolatorLinear()
	: Gaffer::Animation::Interpolator( Gaffer::Animation::Interpolation::Linear, Gaffer::Animation::Interpolator::Hints() )
	{}

	double evaluate( const Gaffer::Animation::Key& keyLo, const Gaffer::Animation::Key& keyHi,
		const double time, const double /*dt*/ ) const override
	{
		return keyLo.getValue() * ( 1.0 - time ) + keyHi.getValue() * ( time );
	}

	double effectiveSlope( const Gaffer::Animation::Tangent& /*tangent*/, const double dt, const double dv ) const override
	{
		return ( dv / dt );
	}
};

// cubic interpolator

struct InterpolatorCubic
: public Gaffer::Animation::Interpolator
{
	InterpolatorCubic()
	: Gaffer::Animation::Interpolator( Gaffer::Animation::Interpolation::Cubic, Gaffer::Animation::Interpolator::Hints(
		Gaffer::Animation::Interpolator::Hint::UseSlopeLo ) |
		Gaffer::Animation::Interpolator::Hint::UseSlopeHi )
	{}

	double evaluate( const Gaffer::Animation::Key& keyLo, const Gaffer::Animation::Key& keyHi,
		const double time, const double dt ) const override
	{
		double a, b, c, d;
		computeCoeffs( keyLo, keyHi, a, b, c, d, dt );

		// NOTE : v  = at^3 + bt^2 + ct + d

		return std::fma( time, std::fma( time, std::fma( time, a, b ), c ), d );
	}

	void bisect( const Gaffer::Animation::Key& keyLo, const Gaffer::Animation::Key& keyHi,
		const double time, const double dt, Gaffer::Animation::Key& newKey,
		Gaffer::Animation::Tangent& newTangentLo, Gaffer::Animation::Tangent& newTangentHi ) const override
	{
		double a, b, c, d;
		computeCoeffs( keyLo, keyHi, a, b, c, d, dt );

		// NOTE : v  =  at^3 +  bt^2 + ct + d
		//        v' = 3at^2 + 2bt   + c

		const double v = std::fma( time, std::fma( time, std::fma( time,         a,     b ), c ), d );
		const double s =                 std::fma( time, std::fma( time, a + a + a, b + b ), c );

		newKey.setValue( v );
		const double slope = slopeToKeySpace( s, dt );
		newKey.tangentIn().setSlope( slope );
		newKey.tangentOut().setSlope( slope );
		newTangentLo.setSlope( keyLo.tangentOut().getSlope() );
		newTangentHi.setSlope( keyHi.tangentIn().getSlope() );
	}

	double effectiveScale( const Gaffer::Animation::Tangent& tangent, const double /*dt*/, const double /*dv*/ ) const override
	{
		return ( 1.0 / 3.0 ) * maxScale( tangent.getSlope() );
	}

private:

	void computeCoeffs(
		const Gaffer::Animation::Key& keyLo, const Gaffer::Animation::Key& keyHi,
		double& a, double& b, double& c, double& d, const double dt ) const
	{
		// NOTE : clamp slope to prevent infs and nans in interpolated values

		const double maxSlope = 1.e9;

		const double dv = keyHi.getValue() - keyLo.getValue();
		const double sl = Imath::clamp( slopeFromKeySpace( keyLo.tangentOut().getSlope(), dt ), -maxSlope, maxSlope );
		const double sh = Imath::clamp( slopeFromKeySpace( keyHi.tangentIn().getSlope(), dt ), -maxSlope, maxSlope );

		a = sl + sh - dv - dv;
		b = dv + dv + dv - sl - sl - sh;
		c = sl;
		d = keyLo.getValue();
	}
};

// bezier interpolator

struct InterpolatorBezier
: public Gaffer::Animation::Interpolator
{
	InterpolatorBezier()
	: Gaffer::Animation::Interpolator( Gaffer::Animation::Interpolation::Bezier, Gaffer::Animation::Interpolator::Hints(
		Gaffer::Animation::Interpolator::Hint::UseSlopeLo ) |
		Gaffer::Animation::Interpolator::Hint::UseSlopeHi   |
		Gaffer::Animation::Interpolator::Hint::UseScaleLo   |
		Gaffer::Animation::Interpolator::Hint::UseScaleHi )
	{}

	double evaluate( const Gaffer::Animation::Key& keyLo, const Gaffer::Animation::Key& keyHi,
		const double time, const double dt ) const override
	{
		const Imath::V2d tl = keyLo.tangentOut().getPosition( false );
		const Imath::V2d th = keyHi.tangentIn().getPosition( false );

		// NOTE : Curve is determined by two polynomials parameterised by s,
		//
		//        v = a(v)s^3 +  b(v)s^2 + c(v)s + d(v)
		//        t = a(t)s^3 +  b(t)s^2 + c(t)s + d(t)
		//
		//        where t is normalised time in seconds, v is value, to evaluate v at the
		//        specified t, first need to solve the second polynomial to determine s.

		const double s = solveForTime(
			( tl.x - keyLo.getTime() ) / dt,
			( th.x - keyHi.getTime() ) / dt + 1.0, time );

		// compute coefficients of value polynomial

		const double valueLo = keyLo.getValue();
		const double valueHi = keyHi.getValue();
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

	void bisect( const Gaffer::Animation::Key& keyLo, const Gaffer::Animation::Key& keyHi,
		const double time, const double dt, Gaffer::Animation::Key& newKey,
		Gaffer::Animation::Tangent& newTangentLo, Gaffer::Animation::Tangent& newTangentHi ) const override
	{
		const Imath::V2d p1( keyLo.getTime(), keyLo.getValue() );
		const Imath::V2d p2 = keyLo.tangentOut().getPosition( false );
		const Imath::V2d p3 = keyHi.tangentIn().getPosition( false );
		const Imath::V2d p4( keyHi.getTime(), keyHi.getValue() );

		const double s = solveForTime(
			( p2.x - keyLo.getTime() ) / dt,
			( p3.x - keyHi.getTime() ) / dt + 1.0, time );

		// NOTE : simple geometric bisection

		const Imath::V2d h  = Imath::lerp( p2, p3, s );
		const Imath::V2d l2 = Imath::lerp( p1, p2, s );
		const Imath::V2d l3 = Imath::lerp( l2, h,  s );
		const Imath::V2d r3 = Imath::lerp( p3, p4, s );
		const Imath::V2d r2 = Imath::lerp( h,  r3, s );
		const Imath::V2d l4 = Imath::lerp( l3, r2, s );

		newKey.setValue( l4.y );
		newTangentLo.setPosition( l2, false );
		newKey.tangentIn().setPosition( l3, false );
		newKey.tangentOut().setPosition( r2, false );
		newTangentHi.setPosition( r3, false );
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

} // namespace

namespace Gaffer
{

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
	add( new InterpolatorConstantNext() );
	add( new InterpolatorConstant() );

	m_default = m_container.front();
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

	// NOTE : check for interpolator with same interpolation

	for( Container::const_iterator it = m_container.begin(), itEnd = m_container.end(); it != itEnd; ++it )
	{
		if( ( *it )->getInterpolation() == interpolator->getInterpolation() )
		{
			return false;
		}
	}

	m_container.push_back( interpolator );

	return true;
}

Animation::Interpolator* Animation::Interpolator::Factory::get( const Animation::Interpolation interpolation )
{
	for( Container::iterator it = m_container.begin(), itEnd = m_container.end(); it != itEnd; ++it )
	{
		if( ( *it )->getInterpolation() == interpolation )
		{
			return ( *it ).get();
		}
	}

	return m_default.get();
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

Animation::Interpolator::Interpolator( const Animation::Interpolation interpolation, const Animation::Interpolator::Hints hints )
: m_interpolation( interpolation )
, m_hints( hints )
{}

Animation::Interpolator::~Interpolator()
{}

Animation::Interpolation Animation::Interpolator::getInterpolation() const
{
	return m_interpolation;
}

Animation::Interpolator::Hints Animation::Interpolator::getHints() const
{
	return m_hints;
}

double Animation::Interpolator::evaluate(
	const Animation::Key& /*keyLo*/, const Animation::Key& /*keyHi*/,
	const double /*time*/, const double /*dt*/ ) const
{
	return 0.0;
}

void Animation::Interpolator::bisect(
	const Animation::Key& keyLo, const Animation::Key& keyHi,
	const double time, const double dt, Animation::Key& newKey,
	Animation::Tangent& /*newTangentLo*/, Animation::Tangent& /*newTangentHi*/ ) const
{
	newKey.setValue( evaluate( keyLo, keyHi, time, dt ) );
}

double Animation::Interpolator::effectiveSlope(
	const Animation::Tangent& tangent, const double dt, const double dv ) const
{
	return 0.0;
}

double Animation::Interpolator::effectiveScale(
	const Animation::Tangent& tangent, const double dt, const double dv ) const
{
	return 0.0;
}

//////////////////////////////////////////////////////////////////////////
// Tangent implementation
//////////////////////////////////////////////////////////////////////////

Animation::Tangent::Tangent( Animation::Key& key, const Animation::Direction direction, const double slope, const double scale )
: m_key( & key )
, m_direction( direction )
, m_dt( 0.0 )
, m_dv( 0.0 )
, m_slope( slope )
, m_scale( Imath::clamp( scale, 0.0, maxScale( m_slope ) ) )
{}

Animation::Tangent::~Tangent()
{}

Animation::Key& Animation::Tangent::key()
{
	return const_cast< Key& >(
		static_cast< const Tangent* >( this )->key() );
}

const Animation::Key& Animation::Tangent::key() const
{
	assert( m_key );
	return *m_key;
}

Animation::Direction Animation::Tangent::direction() const
{
	return m_direction;
}

void Animation::Tangent::positionToRelative( Imath::V2d& position, const bool relative ) const
{
	assert( m_dt != 0.0 );

	// convert from absolute position

	if( ! relative )
	{
		position.x -= m_key->m_time;
		position.y -= m_key->m_value;
	}

	// constrain direction of tangent

	position.x = ( m_direction == Direction::In )
		? std::min( position.x, 0.0 )
		: std::max( position.x, 0.0 );
}

void Animation::Tangent::setPosition( const Imath::V2d& pos, const bool relative )
{
	// when span width is zero position is constrained to parent key

	if( m_dt == 0.0 )
	{
		return;
	}

	// convert relative position

	Imath::V2d position( pos );
	positionToRelative( position, relative );

	// set slope and scale

	setSlopeWithScale( slopeFromPosition( position, m_direction ), position.length() / m_dt );
}

void Animation::Tangent::setPositionWithSlope( const Imath::V2d& pos, const bool relative, const double slope )
{
	// when span width is zero position is constrained to parent key

	if( m_dt == 0.0 )
	{
		return;
	}

	// convert relative position

	Imath::V2d position( pos );
	positionToRelative( position, relative );

	// constrain position to quadrant based on slope and direction

	position.y = ( m_direction == Direction::In )
		? ( ( slope > 0.0 )
			? std::min( position.y, 0.0 )
			: std::max( position.y, 0.0 ) )
		: ( ( slope < 0.0 )
			? std::min( position.y, 0.0 )
			: std::max( position.y, 0.0 ) );

	// set slope and scale

	setSlopeWithScale( slope, position.length() / m_dt );
}

void Animation::Tangent::setPositionWithScale( const Imath::V2d& pos, const bool relative, const double scale )
{
	// when span width is zero position is constrained to parent key

	if( m_dt == 0.0 )
	{
		return;
	}

	// convert relative position

	Imath::V2d position( pos );
	positionToRelative( position, relative );

	// set slope and scale

	setSlopeWithScale( slopeFromPosition( position, m_direction ), scale );
}

Imath::V2d Animation::Tangent::getPosition( const bool relative ) const
{
	Imath::V2d p( 0.0, 0.0 );

	// when span width is zero position is that of parent key

	if( m_dt != 0.0 )
	{
		// compute relative position
		//
		// NOTE : s   = y/x
		//            = tan(angle)
		//        x   = l * cos(angle)
		//            = l / sqrt(1 + tan^2(angle))
		//            = l / sqrt(1 + s^2)
		//        y   = x * s
		//
		//        1/s = x/y
		//            = tan(PI/2-angle)
		//        y   = l * cos(PI/2-angle)
		//            = l / sqrt(1 + tan^2(PI/2-angle))
		//            = l / sqrt(1 + (1/s)^2)
		//        x   = y * (1/s)
		//
		//        As s tends to 0, sqrt(1 + s^2) tends to 1, so x tends to l and y tends to 0, but
		//        as s tends to (+/-) infinity, sqrt(1 + s^2) tends to infinity, so x tends to 0
		//        and y becomes meaningless. However as s tends to (+/-) infinity, 1/s tends to 0
		//        so sqrt(1 + (1/s)^2) tends to 1, so y tends to l and x tends to 0. So,
		//
		//            when |s| <  1 : x = l / sqrt(1 + s^2)
		//                            y = x * s
		//            when |s| >= 1 : y = l / sqrt(1 + (1/s)^2)
		//                            x = y * (1/s)

		const double slope = getSlope();
		const double scale = getScale();

		if( std::abs( slope ) < 1.0 )
		{
			const double s = slope;
			p.x = std::min( ( scale * m_dt ) / std::sqrt( std::fma( s, s, 1.0 ) ), m_dt );
			p.y = p.x * s;
		}
		else
		{
			const double s = 1.0 / slope;
			p.y = std::copysign( ( scale * m_dt ) / std::sqrt( std::fma( s, s, 1.0 ) ), s );
			p.x = std::min( p.y * s, m_dt );
		}

		if( m_direction == Direction::In )
		{
			if( p.x != 0.0 ) { p.x = -p.x; }
			if( p.y != 0.0 ) { p.y = -p.y; }
		}
	}

	// convert to absolute position

	if( ! relative )
	{
		p.x += m_key->m_time;
		p.y += m_key->m_value;
	}

	return p;
}

void Animation::Tangent::setSlope( const double slope )
{
	setSlope( slope, false );
}

void Animation::Tangent::setSlopeWithScale( const double slope, const double scale )
{
	setSlope( slope );
	setScale( scale );
}

void Animation::Tangent::setSlope( double slope, const bool force )
{
	// check that slope is unconstrained

	if( ! force && slopeIsConstrained() )
	{
		return;
	}

	// check for no change

	if( m_slope == slope )
	{
		return;
	}

	// clamp existing scale based on new slope

	const double scale = std::min( m_scale, maxScale( slope ) );

	// make change via action

	if( m_key->m_parent )
	{
		KeyPtr key = m_key;
		const double previousSlope = m_slope;
		const double previousScale = m_scale;
		Action::enact(
			key->m_parent,
			// Do
			[ this, key, slope, scale ] {
				m_slope = slope;
				m_scale = scale;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
			},
			// Undo
			[ this, key, previousSlope, previousScale ] {
				m_slope = previousSlope;
				m_scale = previousScale;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
			}
		);
	}
	else
	{
		m_slope = slope;
		m_scale = scale;
	}

	// tie slope of opposite tangent

	if( m_key->tieSlopeActive() )
	{
		Tangent& ot = m_key->tangent( opposite( m_direction ) );
		Private::ScopedAssignment< TieMode > tmGuard( m_key->m_tieMode, TieMode::Manual );
		ot.setSlope( m_slope, /* force = */ true );
	}
}

double Animation::Tangent::getSlope() const
{
	if( slopeIsConstrained() )
	{
		const Interpolator* const interpolator = ( m_direction == Direction::Out )
			? m_key->m_interpolator
			: m_key->prevKey()->m_interpolator;

		return interpolator->effectiveSlope( *this, m_dt, m_dv );
	}

	return m_slope;
}

bool Animation::Tangent::slopeIsConstrained() const
{
	assert( m_key );

	// when unparented or inactive slope is not constrained

	if( ! m_key->m_parent || ! m_key->m_active )
	{
		return false;
	}

	// check interpolator hints

	if(
		( ( m_direction == Direction::Out ) && ( m_key->m_parent->finalKey() != m_key ) &&
			! m_key->m_interpolator->getHints().test( Interpolator::Hint::UseSlopeLo ) ) ||
		( ( m_direction == Direction::In ) && ( m_key->m_parent->firstKey() != m_key ) &&
			! m_key->prevKey()->m_interpolator->getHints().test( Interpolator::Hint::UseSlopeHi ) ) )
	{
		return true;
	}

	return false;
}

void Animation::Tangent::setScale( double scale )
{
	setScale( scale, false );
}

void Animation::Tangent::setScale( double scale, const bool force )
{
	// check that scale is unconstrained

	if( ! force && scaleIsConstrained() )
	{
		return;
	}

	// clamp new scale based on existing slope

	scale = Imath::clamp( scale, 0.0, maxScale( m_slope ) );

	// check for no change

	if( m_scale == scale )
	{
		return;
	}

	// make change via action

	if( m_key->m_parent )
	{
		KeyPtr key = m_key;
		const double previousScale = m_scale;
		Action::enact(
			key->m_parent,
			// Do
			[ this, key, scale ] {
				m_scale = scale;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
			},
			// Undo
			[ this, key, previousScale ] {
				m_scale = previousScale;
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
			}
		);
	}
	else
	{
		m_scale = scale;
	}

	// tie scale of opposite tangent
	//
	// NOTE : maintain proportionality of opposite tangent's scale.

	if( m_key->tieScaleActive() && ( m_key->m_tieScaleRatio != 0.0 ) )
	{
		Tangent& ot = m_key->tangent( opposite( m_direction ) );
		Private::ScopedAssignment< TieMode > tmGuard( m_key->m_tieMode, TieMode::Manual );
		ot.setScale( ( m_direction == Direction::In )
				? ( scale / m_key->m_tieScaleRatio )
				: ( scale * m_key->m_tieScaleRatio ), /* force = */ true );
	}
}

double Animation::Tangent::getScale() const
{
	if( scaleIsConstrained() )
	{
		const Interpolator* const interpolator = ( m_direction == Direction::Out )
			? m_key->m_interpolator
			: m_key->prevKey()->m_interpolator;

		return interpolator->effectiveScale( *this, m_dt, m_dv );
	}

	return m_scale;
}

bool Animation::Tangent::scaleIsConstrained() const
{
	assert( m_key );

	// when unparented or inactive scale is not constrained

	if( ! m_key->m_parent || ! m_key->m_active )
	{
		return false;
	}

	// check interpolator hints

	if(
		( ( m_direction == Direction::Out ) && ( m_key->m_parent->finalKey() != m_key ) &&
			! m_key->m_interpolator->getHints().test( Interpolator::Hint::UseScaleLo ) ) ||
		( ( m_direction == Direction::In ) && ( m_key->m_parent->firstKey() != m_key ) &&
			! m_key->prevKey()->m_interpolator->getHints().test( Interpolator::Hint::UseScaleHi ) ) )
	{
		return true;
	}

	return false;
}

void Animation::Tangent::update()
{
	assert( m_key );

	// update span time and value differences

	double dt = 0.0;
	double dv = 0.0;

	if( m_key->m_parent )
	{
		switch( m_direction )
		{
			case Direction::In:
				if( const Key* const kp = m_key->prevKey() )
				{
					dt = ( m_key->m_time - kp->m_time );
					dv = ( m_key->m_value - kp->m_value );
				}
				break;
			case Direction::Out:
				if( const Key* const kn = m_key->nextKey() )
				{
					dt = ( kn->m_time - m_key->m_time );
					dv = ( kn->m_value - m_key->m_value );
				}
				break;
			default:
				break;
		}
	}

	// NOTE : when dt becomes zero either the tangent's parent key has been removed from a curve
	//        or the tangent's direction is in and its parent key is the first key in a curve
	//        or the tangent's direction is out and its parent key is the final key in a curve.
	// NOTE : when dt becomes non zero either the tangent's parent key has been added to a curve
	//        or is no longer the first or final key in a curve.

	m_dv = dv;
	m_dt = dt;
}

//////////////////////////////////////////////////////////////////////////
// Key implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Gaffer::Animation::Key )

Animation::Key::Key( const float time, const float value, const Animation::Interpolation interpolation,
	const double inSlope, const double inScale, const double outSlope, const double outScale,
	const Animation::TieMode tieMode )
: m_parent( nullptr )
, m_in( *this, Direction::In, inSlope, inScale )
, m_out( *this, Direction::Out, outSlope, outScale )
, m_time( time )
, m_value( value )
, m_interpolator( Interpolator::getFactory().get( interpolation ) )
, m_tieScaleRatio( tieScaleRatio( inScale, outScale ) )
, m_tieMode( tieMode )
, m_active( false )
{}

Animation::Key::~Key()
{
	// NOTE : parent reference should have been reset before the key is destructed

	assert( m_parent == nullptr );
}

Animation::Tangent& Animation::Key::tangentIn()
{
	return m_in;
}

const Animation::Tangent& Animation::Key::tangentIn() const
{
	return m_in;
}

Animation::Tangent& Animation::Key::tangentOut()
{
	return m_out;
}

const Animation::Tangent& Animation::Key::tangentOut() const
{
	return m_out;
}

Animation::Tangent& Animation::Key::tangent( const Animation::Direction direction )
{
	return const_cast< Tangent& >(
		static_cast< const Key* >( this )->tangent( direction ) );
}

const Animation::Tangent& Animation::Key::tangent( const Animation::Direction direction ) const
{
	return ( direction == Direction::In ) ? m_in : m_out;
}

Animation::TieMode Animation::Key::getTieMode() const
{
	return m_tieMode;
}

void Animation::Key::setTieMode( const Animation::TieMode tieMode )
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
		TieMode previousTieMode = m_tieMode;
		Action::enact(
			m_parent,
			// Do
			[ key, tieMode ] {
				key->m_tieMode = tieMode;
				key->m_parent->m_keyTieModeChangedSignal( key->m_parent, key.get() );
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
			},
			// Undo
			[ key, previousTieMode ] {
				key->m_tieMode = previousTieMode;
				key->m_parent->m_keyTieModeChangedSignal( key->m_parent, key.get() );
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
			}
		);
	}
	else
	{
		m_tieMode = tieMode;
	}

	ensureTieMode();
}

float Animation::Key::getTime() const
{
	return m_time;
}

Animation::KeyPtr Animation::Key::setTime( const float time )
{
	if( time == m_time )
	{
		return KeyPtr();
	}

	KeyPtr clashingKey;

	if( m_parent )
	{
		// find any clashing active key.
		clashingKey = m_parent->getKey( time );

		// if key is active find first clashing inactive key
		KeyPtr clashingInactiveKey;
		if( m_active )
		{
			const CurvePlug::InactiveKeys::iterator it = m_parent->m_inactiveKeys.find( m_time );
			if( it != m_parent->m_inactiveKeys.end() )
			{
				clashingInactiveKey = &( *it );
			}
		}

		// time change via action

		KeyPtr key = this;
		const float previousTime = m_time;
		const bool active = m_active;
		CurvePlug* const curve = m_parent;

#		define ASSERTCONTAINSKEY( KEY, CONTAINER, RESULT ) \
			assert( ( RESULT ) == ( std::find_if( ( CONTAINER ).begin(), ( CONTAINER ).end(), \
				[ key = &( *( KEY ) ) ]( const Key& k ) { return key == & k; } ) != ( CONTAINER ).end() ) );

		Action::enact(
			m_parent,
			// Do
			[ curve, time, previousTime, active, key, clashingKey, clashingInactiveKey ] {
				// check state is as expected
				key->throwIfStateNotAsExpected( curve, active, previousTime );
				if( clashingInactiveKey )
					clashingInactiveKey->throwIfStateNotAsExpected( curve, false, previousTime );
				if( clashingKey )
					clashingKey->throwIfStateNotAsExpected( curve, true, time );
				// NOTE : If key is inactive,
				//          remove key from inactive keys container
				//        else if there is a clashing inactive key
				//          remove the clashing inactive key from inactive keys container
				//          replace key with clashing inactive key in active keys container
				//        else
				//          remove key from active keys container
				//        set time of key
				//        If there is a clashing active key,
				//          replace clashing active key with key in active container
				//          insert clashing key into inactive keys container
				//        else insert key into active keys container
				// NOTE : It is critical to the following code that the key comparison NEVER throws.
				Key* const kpn = key->nextKey();
				Key* const kpp = key->prevKey();
				assert( key->m_hook.is_linked() );
				if( ! active )
				{
					ASSERTCONTAINSKEY( key, curve->m_inactiveKeys, true )
					curve->m_inactiveKeys.erase( curve->m_inactiveKeys.iterator_to( *key ) );
					ASSERTCONTAINSKEY( key, curve->m_inactiveKeys, false )
				}
				else if( clashingInactiveKey )
				{
					assert( clashingInactiveKey->m_hook.is_linked() );
					ASSERTCONTAINSKEY( clashingInactiveKey, curve->m_inactiveKeys, true )
					curve->m_inactiveKeys.erase( curve->m_inactiveKeys.iterator_to( *clashingInactiveKey ) );
					ASSERTCONTAINSKEY( clashingInactiveKey, curve->m_inactiveKeys, false )
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
					curve->m_keys.replace_node( curve->m_keys.iterator_to( *key ), *clashingInactiveKey );
					ASSERTCONTAINSKEY( clashingInactiveKey, curve->m_keys, true )
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
					clashingInactiveKey->m_active = true;
				}
				else
				{
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
					curve->m_keys.erase( curve->m_keys.iterator_to( *key ) );
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
				}
				assert( ! key->m_hook.is_linked() );
				key->m_time = time;
				key->m_active = true;
				if( clashingKey )
				{
					assert( clashingKey->m_hook.is_linked() );
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
					ASSERTCONTAINSKEY( key, curve->m_inactiveKeys, false )
					ASSERTCONTAINSKEY( clashingKey, curve->m_keys, true )
					curve->m_keys.replace_node( curve->m_keys.iterator_to( *clashingKey ), *key );
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
					ASSERTCONTAINSKEY( clashingKey, curve->m_keys, false )
					assert( ! clashingKey->m_hook.is_linked() );
					curve->m_inactiveKeys.insert_before( curve->m_inactiveKeys.lower_bound( key->m_time ), *clashingKey );
					ASSERTCONTAINSKEY( clashingKey, curve->m_inactiveKeys, true )
					clashingKey->m_active = false;
				}
				else
				{
					assert( curve->m_keys.count( key->m_time ) == static_cast< CurvePlug::Keys::size_type >( 0 ) );
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
					curve->m_keys.insert( *key );
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
				}

				assert( ! key || ( key->m_active == true ) );
				assert( ! clashingKey || ( clashingKey->m_active == false ) );
				assert( ! clashingInactiveKey || ( clashingInactiveKey->m_active == true ) );

				// update keys
				//
				// NOTE : only update next/prev keys at old time when there is no clashing inactive
				//        key as any clashing inactive key will replace the key whose time is being
				//        set. only update the next/prev keys at the new time when there is no active
				//        clashing key as the key whose time is being set will replace any active
				//        clashing key. The key and any clashing inactive key are always updated.
				key->m_out.update();
				key->m_in.update();
				if( clashingInactiveKey )
				{
					clashingInactiveKey->m_in.update();
					clashingInactiveKey->m_out.update();
				}
				else
				{
					if( kpn ){ kpn->m_in.update(); }
					if( kpp ){ kpp->m_out.update(); }
				}
				if( ! clashingKey )
				{
					Key* const kn = key->nextKey();
					if( kn && ( kn != kpn || clashingInactiveKey ) ){ kn->m_in.update(); }
					Key* const kp = key->prevKey();
					if( kp && ( kp != kpp || clashingInactiveKey ) ){ kp->m_out.update(); }
				}

				curve->m_keyTimeChangedSignal( key->m_parent, key.get() );
				curve->propagateDirtiness( curve->outPlug() );
			},
			// Undo
			[ curve, time, previousTime, active, key, clashingKey, clashingInactiveKey ] {
				// check state is as expected
				key->throwIfStateNotAsExpected( curve, true, time );
				if( clashingKey )
					clashingKey->throwIfStateNotAsExpected( curve, false, time );
				if( clashingInactiveKey )
					clashingInactiveKey->throwIfStateNotAsExpected( curve, true, previousTime );
				// NOTE : If there was a clashing active key
				//          remove the clashing active key from inactive keys container
				//          replace key with clashing active key in active keys container
				//        else
				//          remove key from active keys container
				//        reset time of key
				//        If key was inactive reinsert key into inactive container
				//        else if there was a clashing inactive key
				//          replace clashing inactive key with key in active container
				//          reinsert clashing inactive key into inactive keys container
				//        else reinsert key into active keys container
				// NOTE : It is critical to the following code that the key comparison NEVER throws.
				Key* const kpn = key->nextKey();
				Key* const kpp = key->prevKey();
				assert( key->m_hook.is_linked() );
				if( clashingKey )
				{
					assert( clashingKey->m_hook.is_linked() );
					ASSERTCONTAINSKEY( clashingKey, curve->m_inactiveKeys, true )
					curve->m_inactiveKeys.erase( curve->m_inactiveKeys.iterator_to( *clashingKey ) );
					ASSERTCONTAINSKEY( clashingKey, curve->m_inactiveKeys, false )
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
					curve->m_keys.replace_node( curve->m_keys.iterator_to( *key ), *clashingKey );
					ASSERTCONTAINSKEY( clashingKey, curve->m_keys, true )
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
					clashingKey->m_active = true;
				}
				else
				{
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
					curve->m_keys.erase( curve->m_keys.iterator_to( *key ) );
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
				}
				assert( ! key->m_hook.is_linked() );
				key->m_time = previousTime;
				key->m_active = active;
				if( ! key->m_active )
				{
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
					ASSERTCONTAINSKEY( key, curve->m_inactiveKeys, false )
					curve->m_inactiveKeys.insert_before( curve->m_inactiveKeys.lower_bound( key->m_time ), *key );
					ASSERTCONTAINSKEY( key, curve->m_inactiveKeys, true )
				}
				else if( clashingInactiveKey )
				{
					assert( clashingInactiveKey->m_hook.is_linked() );
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
					ASSERTCONTAINSKEY( key, curve->m_inactiveKeys, false )
					ASSERTCONTAINSKEY( clashingInactiveKey, curve->m_keys, true )
					curve->m_keys.replace_node( curve->m_keys.iterator_to( *clashingInactiveKey ), *key );
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
					ASSERTCONTAINSKEY( clashingInactiveKey, curve->m_keys, false )
					ASSERTCONTAINSKEY( clashingInactiveKey, curve->m_inactiveKeys, false )
					curve->m_inactiveKeys.insert_before( curve->m_inactiveKeys.lower_bound( key->m_time ), *clashingInactiveKey );
					ASSERTCONTAINSKEY( clashingInactiveKey, curve->m_inactiveKeys, true )
					clashingInactiveKey->m_active = false;
				}
				else
				{
					assert( curve->m_keys.count( key->m_time ) == static_cast< CurvePlug::Keys::size_type >( 0 ) );
					ASSERTCONTAINSKEY( key, curve->m_keys, false )
					curve->m_keys.insert( *key );
					ASSERTCONTAINSKEY( key, curve->m_keys, true )
				}

				assert( ! key || ( key->m_active == active ) );
				assert( ! clashingKey || ( clashingKey->m_active == true ) );
				assert( ! clashingInactiveKey || ( clashingInactiveKey->m_active == false ) );

				// update keys
				//
				// NOTE : only update next/prev keys at old time when there is no clashing inactive
				//        key as key whose time is being set replaces any clashing inactive key.
				//        only update the next/prev keys at the new time when there is no active
				//        clashing key as any active clashing key will replace the key whose time
				//        is being set. The active clashing key is updated as it becomes active.
				//        The key whose time was set is updated if it was active.
				if( active )
				{
					key->m_in.update();
					key->m_out.update();
				}
				if( clashingKey )
				{
					clashingKey->m_in.update();
					clashingKey->m_out.update();
				}
				else
				{
					if( kpn ){ kpn->m_in.update(); }
					if( kpp ){ kpp->m_out.update(); }
				}
				if( ! clashingInactiveKey )
				{
					Key* const kn = key->nextKey();
					if( kn && ( kn != kpn || clashingKey ) ){ kn->m_in.update(); }
					Key* const kp = key->prevKey();
					if( kp && ( kp != kpp || clashingKey ) ){ kp->m_out.update(); }
				}

				curve->m_keyTimeChangedSignal( key->m_parent, key.get() );
				curve->propagateDirtiness( curve->outPlug() );
			}
		);

#		undef ASSERTCONTAINSKEY
	}
	else
	{
		m_time = time;
	}

	return clashingKey;
}

float Animation::Key::getValue() const
{
	return m_value;
}

void Animation::Key::setValue( const float value )
{
	if( value == m_value )
	{
		return;
	}

	// NOTE : inactive keys remain parented and participate in undo/redo and signalling

	if( m_parent )
	{
		KeyPtr key = this;
		const float previousValue = m_value;
		Action::enact(
			m_parent,
			// Do
			[ key, value ] {
				key->m_value = value;
				key->m_out.update();
				key->m_in.update();
				if( Key* const kn = key->nextKey() ){ kn->m_in.update(); }
				if( Key* const kp = key->prevKey() ){ kp->m_out.update(); }
				key->m_parent->m_keyValueChangedSignal( key->m_parent, key.get() );
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
			},
			// Undo
			[ key, previousValue ] {
				key->m_value = previousValue;
				key->m_out.update();
				key->m_in.update();
				if( Key* const kn = key->nextKey() ){ kn->m_in.update(); }
				if( Key* const kp = key->prevKey() ){ kp->m_out.update(); }
				key->m_parent->m_keyValueChangedSignal( key->m_parent, key.get() );
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
			}
		);
	}
	else
	{
		m_value = value;
	}
}

Animation::Interpolation Animation::Key::getInterpolation() const
{
	return m_interpolator->getInterpolation();
}

void Animation::Key::setInterpolation( const Animation::Interpolation interpolation )
{
	Interpolator* const interpolator = Interpolator::getFactory().get( interpolation );

	if( ! interpolator || ( interpolator == m_interpolator ) )
	{
		return;
	}

	// NOTE : inactive keys remain parented and participate in undo/redo and signalling

	if( m_parent )
	{
		KeyPtr key = this;
		Interpolator* const previousInterpolator = m_interpolator;
		Action::enact(
			m_parent,
			// Do
			[ key, interpolator ] {
				key->m_interpolator = interpolator;
				key->m_parent->m_keyInterpolationChangedSignal( key->m_parent, key.get() );
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
			},
			// Undo
			[ key, previousInterpolator ] {
				key->m_interpolator = previousInterpolator;
				key->m_parent->m_keyInterpolationChangedSignal( key->m_parent, key.get() );
				key->m_parent->propagateDirtiness( key->m_parent->outPlug() );
			}
		);
	}
	else
	{
		m_interpolator = interpolator;
	}
}

bool Animation::Key::isActive() const
{
	return m_active;
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

	if( m_parent && m_active )
	{
		assert( m_hook.is_linked() );

		CurvePlug::Keys::const_iterator it = m_parent->m_keys.iterator_to( *this );

		if( ++it != m_parent->m_keys.end() )
		{
			k = &( *it );
		}
	}

	return k;
}

const Animation::Key *Animation::Key::prevKey() const
{
	const Key* k = 0;

	if( m_parent && m_active )
	{
		CurvePlug::Keys::const_iterator it = m_parent->m_keys.iterator_to( *this );

		if( it-- != m_parent->m_keys.begin() )
		{
			k = &( *it );
		}
	}

	return k;
}

Animation::CurvePlug *Animation::Key::parent()
{
	return m_parent;
}

const Animation::CurvePlug *Animation::Key::parent() const
{
	return m_parent;
}

void Animation::Key::ensureTieMode()
{
	if( tieSlopeActive() )
	{
		const double si = m_in.m_slope;
		const double so = m_out.m_slope;

		if( si != so )
		{
			// ensure that tangent slopes are equivalent.
			//
			// NOTE : If only one tangent's slope is constrained or the tangent protrudes beyond the
			//        start/end of the curve, preserve the opposite slope, otherwise take average.

			const bool inConstrainedOrProtrudes = m_in.slopeIsConstrained() || ( prevKey() == nullptr );
			const bool outConstrainedOrProtrudes = m_out.slopeIsConstrained() || ( nextKey() == nullptr );

			const double s = ( inConstrainedOrProtrudes == outConstrainedOrProtrudes )
				? std::tan(
					std::atan( si ) * 0.5 +
					std::atan( so ) * 0.5 )
				: ( ( outConstrainedOrProtrudes ) ? si : so );

			Private::ScopedAssignment< TieMode > tmGuard( m_tieMode, TieMode::Manual );
			m_in.setSlope( s, /* force = */ true );
			m_out.setSlope( s, /* force = */ true );
		}
	}

	if( tieScaleActive() )
	{
		// capture scale ratio when scale is tied.

		m_tieScaleRatio = tieScaleRatio( m_in.m_scale, m_out.m_scale );
	}
}

bool Animation::Key::tieScaleActive() const
{
	switch( m_tieMode )
	{
		case TieMode::Manual:
			return false;
		case TieMode::Slope:
			return false;
		case TieMode::Scale:
			break;
		default:
			return false;
	}

	return true;
}

bool Animation::Key::tieSlopeActive() const
{
	switch( m_tieMode )
	{
		case TieMode::Manual:
			return false;
		case TieMode::Slope:
			break;
		case TieMode::Scale:
			break;
		default:
			return false;
	}

	return true;
}

void Animation::Key::throwIfStateNotAsExpected( const Animation::CurvePlug* const curve, const bool active, const float time ) const
{
	// check that state is as expected
	//
	// NOTE : state may be changed outside the undo system and therefore not be as expected in
	//        which case throw an appropriate exception so user is informed of invalid api usage.

	if( m_parent != curve )
	{
		throw IECore::Exception( "Key parent changed outside undo system." );
	}

	if( m_active != active )
	{
		throw IECore::Exception( "Key active changed outside undo system." );
	}

	if( m_time != time )
	{
		throw IECore::Exception( "Key time changed outside undo system." );
	}
}

void Animation::Key::Dispose::operator()( Animation::Key* const key ) const
{
	assert( key != nullptr );

	key->m_parent = nullptr;
	key->m_active = false;
	key->removeRef();
}

//////////////////////////////////////////////////////////////////////////
// CurvePlug implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( Animation::CurvePlug );

Animation::CurvePlug::CurvePlug( const std::string &name, const Plug::Direction direction, const unsigned flags )
: ValuePlug( name, direction, flags & ~Plug::AcceptsInputs )
, m_keys()
, m_inactiveKeys()
, m_keyAddedSignal()
, m_keyRemovedSignal()
, m_keyTimeChangedSignal()
, m_keyValueChangedSignal()
, m_keyInterpolationChangedSignal()
, m_keyTieModeChangedSignal()
{
	addChild( new FloatPlug( "out", Plug::Out ) );
}

Animation::CurvePlug::~CurvePlug()
{
	m_keys.clear_and_dispose( Key::Dispose() );
	m_inactiveKeys.clear_and_dispose( Key::Dispose() );
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

Animation::CurvePlug::CurvePlugKeySignal& Animation::CurvePlug::keyInterpolationChangedSignal()
{
	return m_keyInterpolationChangedSignal;
}

Animation::CurvePlug::CurvePlugKeySignal& Animation::CurvePlug::keyTieModeChangedSignal()
{
	return m_keyTieModeChangedSignal;
}

Animation::KeyPtr Animation::CurvePlug::addKey( const Animation::KeyPtr &key, const bool removeActiveClashing )
{
	const KeyPtr clashingKey = getKey( key->m_time );

	if( clashingKey )
	{
		if( key == clashingKey )
		{
			return KeyPtr();
		}
	}

	if( key->m_parent )
	{
		key->m_parent->removeKey( key.get() );
	}

	// save the time of the key at the point it is added in case it was previously
	// removed from the curve and changes have been made whilst the key was outside
	// the curve (these changes will not have been recorded in the undo/redo system)
	// when redo is called we can then check for any change and throw an exception
	// if time is not as we expect it to be. principle here is that the user should
	// not make changes outside the undo system so if they have then let them know.

	const float time = key->m_time;

#	define ASSERTCONTAINSKEY( KEY, CONTAINER, RESULT ) \
		assert( ( RESULT ) == ( std::find_if( ( CONTAINER ).begin(), ( CONTAINER ).end(), \
			[ key = &( *( KEY ) ) ]( const Key& k ) { return key == & k; } ) != ( CONTAINER ).end() ) );

	Action::enact(
		this,
		// Do
		[ this, key, clashingKey, time ] {
			// check state is as expected
			key->throwIfStateNotAsExpected( nullptr, false, time );
			if( clashingKey )
				clashingKey->throwIfStateNotAsExpected( this, true, time );
			// NOTE : If there is a clashing key,
			//          replace clashing key with key in active container
			//          insert clashing key into inactive keys container
			//        else insert key into active keys container
			// NOTE : It is critical to the following code that the key comparison NEVER throws.
			assert( ! key->m_hook.is_linked() );
			if( clashingKey )
			{
				assert( clashingKey->m_hook.is_linked() );
				ASSERTCONTAINSKEY( key, m_keys, false )
				ASSERTCONTAINSKEY( key, m_inactiveKeys, false )
				ASSERTCONTAINSKEY( clashingKey, m_keys, true )
				m_keys.replace_node( m_keys.iterator_to( *clashingKey ), *key );
				ASSERTCONTAINSKEY( key, m_keys, true )
				ASSERTCONTAINSKEY( clashingKey, m_keys, false )
				m_inactiveKeys.insert_before( m_inactiveKeys.lower_bound( time ), *clashingKey );
				ASSERTCONTAINSKEY( clashingKey, m_inactiveKeys, true )
				clashingKey->m_active = false;
			}
			else
			{
				assert( m_keys.count( key->m_time ) == static_cast< Keys::size_type >( 0 ) );
				ASSERTCONTAINSKEY( key, m_keys, false )
				m_keys.insert( *key );
				ASSERTCONTAINSKEY( key, m_keys, true )
			}
			key->m_parent = this; // NOTE : never throws or fails
			key->addRef();        // NOTE : take ownership
			key->m_active = true;

			// update keys
			//
			// NOTE : only update the new next/prev keys when there is no active clashing key as
			//        the key being added will replace any inactive clashing key. Always update
			//        the key being added.
			key->m_in.update();
			key->m_out.update();
			if( ! clashingKey )
			{
				if( Key* const kn = key->nextKey() ){ kn->m_in.update(); }
				if( Key* const kp = key->prevKey() ){ kp->m_out.update(); }
			}

			m_keyAddedSignal( this, key.get() );
			propagateDirtiness( outPlug() );
		},
		// Undo
		[ this, key, clashingKey, time ] {
			// check state is as expected
			key->throwIfStateNotAsExpected( this, true, time );
			if( clashingKey )
				clashingKey->throwIfStateNotAsExpected( this, false, time );
			// NOTE : If there was a clashing key
			//          remove the clashing key from inactive keys container
			//          replace key with clashing key in active keys container
			//        else
			//          remove key from active keys container
			// NOTE : It is critical to the following code that the key comparison NEVER throws.
			Key* const kn = key->nextKey();
			Key* const kp = key->prevKey();

			assert( key->m_hook.is_linked() );
			if( clashingKey )
			{
				assert( clashingKey->m_hook.is_linked() );
				ASSERTCONTAINSKEY( clashingKey, m_inactiveKeys, true )
				m_inactiveKeys.erase( m_inactiveKeys.iterator_to( *clashingKey ) );
				ASSERTCONTAINSKEY( clashingKey, m_inactiveKeys, false )
				ASSERTCONTAINSKEY( key, m_keys, true )
				m_keys.replace_node( m_keys.iterator_to( *key ), *clashingKey );
				Key::Dispose()( key.get() );
				ASSERTCONTAINSKEY( clashingKey, m_keys, true )
				ASSERTCONTAINSKEY( key, m_keys, false )
				clashingKey->m_active = true;
			}
			else
			{
				assert( key->m_active == true );
				ASSERTCONTAINSKEY( key, m_keys, true )
				m_keys.erase_and_dispose( m_keys.iterator_to( *key ), Key::Dispose() );
				ASSERTCONTAINSKEY( key, m_keys, false )
			}

			// update keys
			//
			// NOTE : only update the old next/prev keys when there is no inactive clashing key as
			//        any inactive clashing key will replace the key being removed. Always update
			//        the key being removed and the inactive clashing key as it becomes active.
			key->m_in.update();
			key->m_out.update();
			if( clashingKey )
			{
				clashingKey->m_in.update();
				clashingKey->m_out.update();
			}
			else
			{
				if( kn ){ kn->m_in.update(); }
				if( kp ){ kp->m_out.update(); }
			}

			m_keyRemovedSignal( this, key.get() );
			propagateDirtiness( outPlug() );
		}
	);

#	undef ASSERTCONTAINSKEY

	// remove the clashing key
	if( clashingKey && removeActiveClashing )
	{
		removeKey( clashingKey );
	}

	return clashingKey;
}

Animation::KeyPtr Animation::CurvePlug::insertKey( const float time )
{
	return insertKeyInternal( time, nullptr );
}

Animation::KeyPtr Animation::CurvePlug::insertKey( const float time, const float value )
{
	return insertKeyInternal( time, & value );
}

Animation::KeyPtr Animation::CurvePlug::insertKeyInternal( const float time, const float* const value )
{
	// find span keys for time

	KeyPtr key;
	Key* lo = nullptr;
	Key* hi = nullptr;

	Keys::iterator hiIt = m_keys.lower_bound( time );
	if( hiIt != m_keys.end() )
	{
		hi = &( *( hiIt ) );

		if( hi->m_time == time )
		{
			key = hi;
		}
		else if( hiIt != m_keys.begin() )
		{
			lo = &( *( --hiIt ) );

			if( lo->m_time == time )
			{
				key = lo;
			}
		}
	}
	else
	{
		lo = finalKey();
	}

	// if key already exists at time then return it with updated value, otherwise if time is
	// outside existing range of keys, there is no way currently to extrapolate a value so
	// if no value has been provided then return KeyPtr().

	if( key )
	{
		if( value != nullptr )
		{
			key->setValue( *value );
		}

		return key;
	}
	else if( !( lo && hi ) && ( value == nullptr ) )
	{
		return key;
	}

	// get interpolator and tie mode

	const Interpolator* interpolator = Interpolator::getFactory().getDefault();
	TieMode tieMode = defaultTieMode();

	if( lo )
	{
		interpolator = lo->m_interpolator;
		tieMode = lo->m_tieMode;
	}
	else if( const Key* const kf = firstKey() )
	{
		interpolator = kf->m_interpolator;
		tieMode = kf->m_tieMode;
	}

	assert( interpolator );

	// create key with tie mode set to manual so we can adjust slope and scale

	key.reset( new Key( time, ( ( value != nullptr ) ? ( *value ) : 0.f ), interpolator->getInterpolation() ) );
	key->m_tieMode = TieMode::Manual;

	// if specified value is the same as the evaluated value of the curve then bisect span.

	if( ( lo && hi ) && ( ( value == nullptr ) || ( evaluate( time ) == ( *value ) ) ) )
	{
		// normalise time to lo, hi key time range

		const double lt = ( time - lo->m_time );
		const double ht = ( hi->m_time - time );
		const double nt = std::min( std::max( lt / lo->m_out.m_dt, 0.0 ), 1.0 );

		// create dummmy hi/lo keys. use dummy keys to prevent unwanted side effects from
		// badly behaved interpolators.

		KeyPtr kl( new Key( lo->m_time, lo->getValue(), interpolator->getInterpolation() ) );
		KeyPtr kh( new Key( hi->m_time, hi->getValue(), interpolator->getInterpolation() ) );

		kl->m_in.m_slope = lo->m_in.m_slope;
		kl->m_in.m_scale = lo->m_in.m_scale;
		kl->m_out.m_slope = lo->m_out.m_slope;
		kl->m_out.m_scale = lo->m_out.m_scale;
		kl->m_tieMode = TieMode::Manual;

		kh->m_in.m_slope = hi->m_in.m_slope;
		kh->m_in.m_scale = hi->m_in.m_scale;
		kh->m_out.m_slope = hi->m_out.m_slope;
		kh->m_out.m_scale = hi->m_out.m_scale;
		kh->m_tieMode = TieMode::Manual;

		// new tangents are in space of new spans (post-bisection)

		kl->m_out.m_dt = lt;
		key->m_in.m_dt = lt;
		key->m_out.m_dt = ht;
		kh->m_in.m_dt = ht;

		// bisect span

		interpolator->bisect( *lo, *hi, nt, lo->m_out.m_dt, *key, kl->m_out, kh->m_in );

		// retrieve new tangent slope and scale

		const double lfsl = kl->m_out.getSlope();
		const double lfsc = kl->m_out.getScale();
		const double hisl = kh->m_in.getSlope();
		const double hisc = kh->m_in.getScale();

		// add new key to curve

		addKey( key );

		// set new tangent slope and scale for lo and hi keys

		Private::ScopedAssignment< TieMode > ltm( lo->m_tieMode, TieMode::Manual );
		Private::ScopedAssignment< TieMode > htm( hi->m_tieMode, TieMode::Manual );

		lo->m_out.setSlopeWithScale( lfsl, lfsc );
		hi->m_in.setSlopeWithScale( hisl, hisc );
	}
	else
	{
		// only compute auto slope when we have a valid span

		if( lo && hi )
		{
			// normalise time to lo, hi key time range

			const double nt = Imath::clamp( ( time - lo->m_time ) / lo->m_out.m_dt, 0.0, 1.0 );

			// auto adjust slope of key (perpendicular to the bisector of the angle between lo-key and hi-key)
			//
			// NOTE : when setting the slope we set force to false so that the slope is only set if it is used

			const Imath::V2d kp( nt, key->m_value );
			const Imath::V2d lp( 0.0, lo->m_value );
			const Imath::V2d hp( 1.0, hi->m_value );
			const double s = slopeToKeySpace(
				slopeFromPosition( ( kp - lp ).normalized() + ( hp - kp ).normalized(), Animation::Direction::Out ),
				lo->m_out.m_dt );

			key->m_out.setSlope( s );
			key->m_in.setSlope( s );
		}

		// add new key to curve

		addKey( key );
	}

	key->setTieMode( tieMode );

	return key;
}

bool Animation::CurvePlug::hasKey( const float time ) const
{
	return m_keys.find( time ) != m_keys.end();
}

Animation::Key *Animation::CurvePlug::getKey( const float time )
{
	return const_cast< Key* >( static_cast< const CurvePlug* >( this )->getKey( time ) );
}

const Animation::Key *Animation::CurvePlug::getKey( const float time ) const
{
	Keys::const_iterator it = m_keys.find( time );
	return ( it != m_keys.end() )
		? &( *it )
		: nullptr;
}

void Animation::CurvePlug::removeKey( const Animation::KeyPtr &key )
{
	if( key->m_parent != this )
	{
		throw IECore::Exception( "Key is not a child" );
	}

	// save the time of the key at the point it is removed in case it is subsequently
	// added back to the curve and changes are made whilst the key is outside
	// the curve (these changes will not be recorded in the undo/redo system)
	// when undo is called we can then check for any change and throw an exception
	// if time is not as we expect it to be. principle here is that the user should
	// not make changes outside the undo system so if they have then let them know.

	const float time = key->m_time;

	// if key is active find first clashing inactive key
	KeyPtr clashingKey;
	if( key->m_active )
	{
		const InactiveKeys::iterator it = m_inactiveKeys.find( key->m_time );
		if( it != m_inactiveKeys.end() )
		{
			clashingKey = &( *it );
		}
	}

	const bool active = key->m_active;

#	define ASSERTCONTAINSKEY( KEY, CONTAINER, RESULT ) \
		assert( ( RESULT ) == ( std::find_if( ( CONTAINER ).begin(), ( CONTAINER ).end(), \
			[ key = &( *( KEY ) ) ]( const Key& k ) { return key == & k; } ) != ( CONTAINER ).end() ) );

	Action::enact(
		this,
		// Do
		[ this, key, clashingKey, active, time ] {
			// check state is as expected
			key->throwIfStateNotAsExpected( this, active, time );
			if( clashingKey )
				clashingKey->throwIfStateNotAsExpected( this, false, time );
			// NOTE : If key is inactive,
			//          remove key from inactive keys container
			//        else if there is a clashing key
			//          remove the clashing key from inactive keys container
			//          replace key with clashing key in active keys container
			//        else
			//          remove key from active keys container
			// NOTE : It is critical to the following code that the key comparison NEVER throws.
			Key* const kn = key->nextKey();
			Key* const kp = key->prevKey();
			assert( key->m_hook.is_linked() );
			if( ! active )
			{
				ASSERTCONTAINSKEY( key, m_inactiveKeys, true )
				m_inactiveKeys.erase_and_dispose( m_inactiveKeys.iterator_to( *key ), Key::Dispose() );
				ASSERTCONTAINSKEY( key, m_inactiveKeys, false )
			}
			else if( clashingKey )
			{
				assert( clashingKey->m_hook.is_linked() );
				ASSERTCONTAINSKEY( clashingKey, m_inactiveKeys, true )
				m_inactiveKeys.erase( m_inactiveKeys.iterator_to( *clashingKey ) );
				ASSERTCONTAINSKEY( clashingKey, m_inactiveKeys, false )
				ASSERTCONTAINSKEY( key, m_keys, true )
				m_keys.replace_node( m_keys.iterator_to( *key ), *clashingKey );
				Key::Dispose()( key.get() );
				ASSERTCONTAINSKEY( key, m_keys, false )
				ASSERTCONTAINSKEY( clashingKey, m_keys, true )
				clashingKey->m_active = true;
			}
			else
			{
				ASSERTCONTAINSKEY( key, m_keys, true )
				m_keys.erase_and_dispose( m_keys.iterator_to( *key ), Key::Dispose() );
				ASSERTCONTAINSKEY( key, m_keys, false )
			}

			// update keys
			//
			// NOTE : only update the old next/prev keys when there is no inactive clashing key as
			//        any inactive clashing key will replace the key being removed. Always update
			//        the key being removed and the inactive clashing key as it becomes active.
			key->m_in.update();
			key->m_out.update();
			if( clashingKey )
			{
				clashingKey->m_in.update();
				clashingKey->m_out.update();
			}
			else
			{
				if( kn ){ kn->m_in.update(); }
				if( kp ){ kp->m_out.update(); }
			}

			m_keyRemovedSignal( this, key.get() );
			propagateDirtiness( outPlug() );
		},
		// Undo
		[ this, key, clashingKey, active, time ] {
			// check state is as expected
			key->throwIfStateNotAsExpected( nullptr, false, time );
			if( clashingKey )
				clashingKey->throwIfStateNotAsExpected( this, true, time );
			// NOTE : If key was inactive reinsert key into inactive container
			//        else if there was a clashing key
			//          replace clashing key with key in active container
			//          reinsert clashing key into inactive keys container
			//        else reinsert key into active keys container
			// NOTE : It is critical to the following code that the key comparison NEVER throws.
			assert( ! key->m_hook.is_linked() );
			if( ! active )
			{
				ASSERTCONTAINSKEY( key, m_keys, false )
				ASSERTCONTAINSKEY( key, m_inactiveKeys, false )
				m_inactiveKeys.insert_before( m_inactiveKeys.lower_bound( time ), *key );
				ASSERTCONTAINSKEY( key, m_inactiveKeys, true )
			}
			else if( clashingKey )
			{
				assert( clashingKey->m_hook.is_linked() );
				ASSERTCONTAINSKEY( key, m_keys, false )
				ASSERTCONTAINSKEY( key, m_inactiveKeys, false )
				ASSERTCONTAINSKEY( clashingKey, m_keys, true )
				m_keys.replace_node( m_keys.iterator_to( *clashingKey ), *key );
				ASSERTCONTAINSKEY( key, m_keys, true )
				ASSERTCONTAINSKEY( clashingKey, m_keys, false )
				m_inactiveKeys.insert_before( m_inactiveKeys.lower_bound( time ), *clashingKey );
				ASSERTCONTAINSKEY( clashingKey, m_inactiveKeys, true )
				clashingKey->m_active = false;
			}
			else
			{
				assert( m_keys.count( key->m_time ) == static_cast< Keys::size_type >( 0 ) );
				ASSERTCONTAINSKEY( key, m_keys, false )
				m_keys.insert( *key );
				ASSERTCONTAINSKEY( key, m_keys, true )
			}
			key->m_parent = this; // NOTE : never throws or fails
			key->addRef();        // NOTE : take ownership
			key->m_active = active;

			// update keys
			//
			// NOTE : only update the new next/prev keys when there is no active clashing key as
			//        the key being added will replace any active clashing key. only update the key
			//        being added when it becomes active.
			if( active )
			{
				key->m_in.update();
				key->m_out.update();
			}
			if( ! clashingKey )
			{
				if( Key* const k = key->nextKey() ){ k->m_in.update(); }
				if( Key* const k = key->prevKey() ){ k->m_out.update(); }
			}

			m_keyAddedSignal( this, key.get() );
			propagateDirtiness( outPlug() );
		}
	);

#	undef ASSERTCONTAINSKEY
}

void Animation::CurvePlug::removeInactiveKeys()
{
	for( InactiveKeys::iterator it = m_inactiveKeys.begin(), itEnd = m_inactiveKeys.end(); it != itEnd; )
	{
		removeKey( &( *it++ ) );
	}
}

Animation::Key *Animation::CurvePlug::closestKey( const float time )
{
	return const_cast< Key* >( static_cast< const CurvePlug* >( this )->closestKey( time ) );
}

const Animation::Key *Animation::CurvePlug::closestKey( const float time ) const
{
	if( m_keys.empty() )
	{
		return nullptr;
	}

	Keys::const_iterator rightIt = m_keys.lower_bound( time );
	if( rightIt == m_keys.end() )
	{
		return &( *( m_keys.rbegin() ) );
	}
	else if( rightIt->m_time == time || rightIt == m_keys.begin() )
	{
		return &( *( rightIt ) );
	}
	else
	{
		Keys::const_iterator leftIt = std::prev( rightIt );
		return &( *( std::fabs( time - leftIt->m_time ) < std::fabs( time - rightIt->m_time ) ? leftIt : rightIt ) );
	}
}

Animation::Key *Animation::CurvePlug::closestKey( const float time, const float maxDistance )
{
	return const_cast< Key* >( static_cast< const CurvePlug* >( this )->closestKey( time, maxDistance ) );
}

const Animation::Key *Animation::CurvePlug::closestKey( const float time, const float maxDistance ) const
{
	const Key* const candidate = closestKey( time );

	if( !candidate || ( std::fabs( candidate->m_time - time ) > maxDistance ) )
	{
		return nullptr;
	}

	return candidate;
}

Animation::Key *Animation::CurvePlug::previousKey( const float time )
{
	return const_cast< Key* >( static_cast< const CurvePlug* >( this )->previousKey( time ) );
}

const Animation::Key *Animation::CurvePlug::previousKey( const float time ) const
{
	Keys::const_iterator rightIt = m_keys.lower_bound( time );
	return ( rightIt != m_keys.begin() )
		? &( *( std::prev( rightIt ) ) )
		: nullptr;
}

Animation::Key *Animation::CurvePlug::nextKey( const float time )
{
	return const_cast< Key* >( static_cast< const CurvePlug* >( this )->nextKey( time ) );
}

const Animation::Key *Animation::CurvePlug::nextKey( const float time ) const
{
	Keys::const_iterator rightIt = m_keys.upper_bound( time );
	return ( rightIt != m_keys.end() )
		? &( *( rightIt ) )
		: nullptr;
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
		k = &( *( m_keys.cbegin() ) );
	}

	return k;
}

const Animation::Key *Animation::CurvePlug::finalKey() const
{
	const Key* k = 0;

	if( ! m_keys.empty() )
	{
		k = &( *( m_keys.crbegin() ) );
	}

	return k;
}

Animation::CurvePlug::TimeKey::type Animation::CurvePlug::TimeKey::operator()( const Animation::Key& key ) const
{
	return key.getTime();
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

float Animation::CurvePlug::evaluate( const float time ) const
{
	// NOTE : no keys return 0

	if( m_keys.empty() )
	{
		return 0.f;
	}

	// NOTE : each key determines value at a specific time therefore only
	//        interpolate for times which are between the keys.

	Keys::const_iterator hiIt = m_keys.lower_bound( time );
	if( hiIt == m_keys.end() )
	{
		return ( m_keys.rbegin() )->getValue();
	}

	const Key &hi = *( hiIt );

	if( hi.m_time == time || hiIt == m_keys.begin() )
	{
		return hi.getValue();
	}

	const Key &lo = *( std::prev( hiIt ) );

	// normalise time to lo, hi key time range

	const double dt = lo.m_out.m_dt;
	const double nt = Imath::clamp( ( time - lo.m_time ) / dt, 0.0, 1.0 );

	// evaluate interpolator

	return lo.m_interpolator->evaluate( lo, hi, nt, dt );
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

bool Animation::canAnimate( const ValuePlug* const plug )
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
		IECore::runTimeCast<const FloatPlug>( plug ) ||
		IECore::runTimeCast<const IntPlug>( plug ) ||
		IECore::runTimeCast<const BoolPlug>( plug );
}

bool Animation::isAnimated( const ValuePlug* const plug )
{
	return inputCurve( plug );
}

Animation::CurvePlug *Animation::acquire( ValuePlug* const plug )
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
		ValuePlug *valuePlug = IECore::runTimeCast<ValuePlug>( it->get() );
		if( !valuePlug )
		{
			continue;
		}

		if( CurvePlug *curve = inputCurve( valuePlug ) )
		{
			animation = IECore::runTimeCast<Animation>( curve->node() );
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

Animation::CurvePlug *Animation::inputCurve( ValuePlug* const plug )
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

const Animation::CurvePlug *Animation::inputCurve( const ValuePlug* const plug )
{
	// preferring cast over maintaining two near-identical methods.
	return inputCurve( const_cast<ValuePlug *>( plug ) );
}

void Animation::affects( const Plug* const input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );
}

void Animation::hash( const ValuePlug* const output, const Context* const context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( const CurvePlug *parent = output->parent<CurvePlug>() )
	{
		h.append( parent->evaluate( context->getTime() ) );
	}
}

void Animation::compute( ValuePlug* const output, const Context* const context ) const
{
	if( const CurvePlug *parent = output->parent<CurvePlug>() )
	{
		static_cast<FloatPlug *>( output )->setValue( parent->evaluate( context->getTime() ) );
		return;
	}

	ComputeNode::compute( output, context );
}

ValuePlug::CachePolicy Animation::computeCachePolicy( const Gaffer::ValuePlug* const output ) const
{
	if( output->parent<CurvePlug>() )
	{
		return ValuePlug::CachePolicy::Uncached;
	}

	return ComputeNode::computeCachePolicy( output );
}

Animation::Interpolation Animation::defaultInterpolation()
{
	return Interpolator::getFactory().getDefault()->getInterpolation();
}

Animation::TieMode Animation::defaultTieMode()
{
	return TieMode::Scale;
}

Animation::Direction Animation::opposite( const Animation::Direction direction )
{
	return static_cast< Direction >( ( static_cast< int >( direction ) + 1 ) % 2 );
}

double Animation::defaultSlope()
{
	return 0.0;
}

double Animation::defaultScale()
{
	return ( 1.0 / 3.0 );
}

const char* Animation::toString( const Animation::Interpolation interpolation )
{
	switch( interpolation )
	{
		case Interpolation::Constant:
			return "Constant";
		case Interpolation::ConstantNext:
			return "ConstantNext";
		case Interpolation::Linear:
			return "Linear";
		case Interpolation::Cubic:
			return "Cubic";
		case Interpolation::Bezier:
			return "Bezier";
		default:
			assert( 0 );
			return 0;
	}
}

const char* Animation::toString( const Animation::Direction direction )
{
	switch( direction )
	{
		case Direction::In:
			return "In";
		case Direction::Out:
			return "Out";
		default:
			assert( 0 );
			return 0;
	}
}

const char* Animation::toString( const Animation::TieMode mode )
{
	switch( mode )
	{
		case TieMode::Manual:
			return "Manual";
		case TieMode::Slope:
			return "Slope";
		case TieMode::Scale:
			return "Scale";
		default:
			assert( 0 );
			return 0;
	}
}

} // Gaffer
