//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/SplinePlug.h"

#include "Gaffer/Action.h"

using namespace Gaffer;

namespace {

template<typename Y, typename X>
inline Y monotoneSlopeCompute( const Y& deltaY1, const Y& deltaY2, const X& deltaX1, const X& deltaX2 )
{
	// Using this weighted harmonic mean to compute slopes ensures a monotone curve.
	// This is apparently a result by Fritsch and Carlson, from here:
	//
	// F. N. Fritsch and R. E. Carlson
	// SIAM Journal on Numerical Analysis
	// Vol. 17, No. 2 (Apr., 1980), pp. 238-246
	//
	// Haven't actually gotten ahold of this paper, but stackexchange says that it says this,
	// and it seems to work quite well.
	if( deltaY1 * deltaY2 > 0.0f )
	{
		return 3.0f * ( deltaX1 + deltaX2 ) / (
			( 2.0f * deltaX2 + deltaX1 ) / deltaY1 +
			( deltaX2 + 2.0f * deltaX1 ) / deltaY2 );
	}
	else
	{
		return 0;
	}
}

template<>
inline Imath::Color3f monotoneSlopeCompute<>(
	const Imath::Color3f& deltaY1, const Imath::Color3f& deltaY2,
	const float& deltaX1, const float& deltaX2 )
{
	return Imath::Color3f(
		monotoneSlopeCompute( deltaY1[0], deltaY2[0], deltaX1, deltaX2 ),
		monotoneSlopeCompute( deltaY1[1], deltaY2[1], deltaX1, deltaX2 ),
		monotoneSlopeCompute( deltaY1[2], deltaY2[2], deltaX1, deltaX2 )
	);
}

template<>
inline Imath::Color4f monotoneSlopeCompute<>(
	const Imath::Color4f& deltaY1, const Imath::Color4f& deltaY2,
	const float& deltaX1, const float& deltaX2 )
{
	return Imath::Color4f(
		monotoneSlopeCompute( deltaY1[0], deltaY2[0], deltaX1, deltaX2 ),
		monotoneSlopeCompute( deltaY1[1], deltaY2[1], deltaX1, deltaX2 ),
		monotoneSlopeCompute( deltaY1[2], deltaY2[2], deltaX1, deltaX2 ),
		monotoneSlopeCompute( deltaY1[3], deltaY2[3], deltaX1, deltaX2 )
	);
}

// This function translates a set of control points for a MonotoneCubic curve into a set of
// bezier control points.  The X values are set up to make each segment linear in X, which
// makes the control point behaviour a bit more predictable when used as a color ramp.
// The Y tangents are adjusted to compensate for the discontinuity in the slope of the
// parameterization across control points, which mean that the X/Y tangent is continuous across
// control points.  This curve type seems to work quite well in practice for color ramps.
//
// Note that the way we are evaluating this type of curve by using a spline solver on the X
// axis is ridiculously inefficient - the bezier control points are arranged so it's actually
// always linear, and could be quickly solved analyticly.  But because we need to store these
// curves in IECore::Spline, we don't have any way to specify different interpolations for
// X and Y. So we just use bezier curve with appropriately set handles to store our linear X
// curve.
template<typename T>
void monotoneCubicCVsToBezierCurve( const typename T::PointContainer &cvs, typename T::PointContainer &result )
{
	// NOTE : It would seem more reasonable to use the slope of the first and last segment for the
	// endpoints, instead of clamping to 0.  The current argument for clamping to zero is consistency
	// with the Htoa ramp
	typename T::YType prevSlope = typename T::YType(0);

	typename T::PointContainer::const_iterator i = cvs.begin();
	const typename T::Point *p1 = &*i;
	i++;
	const typename T::Point *p2 = &*i;
	i++;

	for(;;)
	{
		typename T::YType nextSlope;


		const typename T::Point *pNext;
		if( i == cvs.end() )
		{
			nextSlope = typename T::YType( 0 );
		}
		else
		{
			pNext = &*i;

			typename T::XType xDelta1 = p2->first - p1->first;
			typename T::XType xDelta2 = pNext->first - p2->first;
			typename T::YType yDelta1 = p2->second - p1->second;
			typename T::YType yDelta2 = pNext->second - p2->second;

			nextSlope = monotoneSlopeCompute( yDelta1 / xDelta1, yDelta2 / xDelta2, xDelta1, xDelta2);

			// NOTE : If we copied everything else about this function, but instead just used:
			// 	   0.5 * ( yDelta1 / xDelta1 + yDelta2 / xDelta2 )
			// for the slope here, this would produce a CatmullRom sort of spline, but with the simpler linear
			// behaviour of the knot values.  This is what Htoa uses for a CatmullRom ramp, and might be a pretty
			// useful curve type ( quite possibly more useful than our current CatmullRom, though it would no
			// longer correspond to a CatmullRom basis in OSL ).
		}

		typename T::XType xDelta = p2->first - p1->first;

		result.insert( *p1 );
		result.insert( typename T::Point(
			p1->first + ( 1.0f/3.0f ) * xDelta,
			p1->second + (1.0f/3.0f) * prevSlope * xDelta ) );
		result.insert( typename T::Point(
			p1->first + ( 2.0f/3.0f ) * xDelta,
			p2->second - (1.0f/3.0f) * nextSlope * xDelta ) );

		if( i == cvs.end() )
		{
			break;
		}
		else
		{
			p1 = p2;
			p2 = pNext;
			prevSlope = nextSlope;
			i++;
		}
	}

	result.insert( *p2 );
}

}

template<typename T>
const IECore::RunTimeTyped::TypeDescription<SplinePlug<T> > SplinePlug<T>::g_typeDescription;

template<typename T>
T SplineDefinition<T>::spline() const
{
	T result;

	result.points = points;

	if( interpolation == SplineDefinitionInterpolationLinear )
	{
		result.basis = T::Basis::linear();
	}
	else if( interpolation == SplineDefinitionInterpolationCatmullRom )
	{
		result.basis = T::Basis::catmullRom();
	}
	else if( interpolation == SplineDefinitionInterpolationBSpline )
	{
		result.basis = T::Basis::bSpline();
	}
	else if( interpolation == SplineDefinitionInterpolationMonotoneCubic )
	{
		result.basis = T::Basis::bezier();
		if( points.size() > 1 )
		{
			result.points.clear();
			monotoneCubicCVsToBezierCurve<T>( points, result.points );
		}
	}

	int multiplicity = endPointMultiplicity();

	if( multiplicity && result.points.size() )
	{
		for( int i = 0; i < multiplicity - 1; ++i )
		{
			result.points.insert( *result.points.begin() );
			result.points.insert( *result.points.rbegin() );
		}
	}

	return result;
}

template<typename T>
bool SplineDefinition<T>::trimEndPoints()
{
	int multiplicity = endPointMultiplicity();

	if( (int)points.size() < multiplicity * 2 )
	{
		// Not enough points to make a curve once we account for endpoint multiplicity
		return false;
	}

	if( multiplicity > 1 )
	{
		typename PointContainer::const_iterator it = points.begin();
		for( int i = 1; i < multiplicity; i++ )
		{
			++it;
			if( *it != *points.begin() )
			{
				// We don't have enough matching points to equal the endPointMultiplicity
				return false;
			}
		}

		typename PointContainer::const_reverse_iterator rit = points.rbegin();
		for( int i = 1; i < multiplicity; i++ )
		{
			++rit;
			if( *rit != *points.rbegin() )
			{
				// We don't have enough matching points to equal the endPointMultiplicity
				return false;
			}
		}

		// We have an appropriate amount of duplication of the end points.  This will be added automatically
		// when converting to a Cortex spline, so we trim it off of the source points here

		typename PointContainer::reverse_iterator endMultiplicity = points.rbegin();
		advance( endMultiplicity, multiplicity - 1 );
		points.erase( endMultiplicity.base(), points.rbegin().base() );

		typename PointContainer::iterator startMultiplicity = points.begin();
		advance( startMultiplicity, multiplicity - 1 );
		points.erase( points.begin(), startMultiplicity );
	}

	return true;
}

template<typename T>
int SplineDefinition<T>::endPointMultiplicity() const
{
	int multiplicity = 1;
	if( interpolation == SplineDefinitionInterpolationCatmullRom )
	{
		multiplicity = 2;
	}
	else if( interpolation == SplineDefinitionInterpolationBSpline )
	{
		multiplicity = 3;
	}
	return multiplicity;
}


template<typename T>
SplinePlug<T>::SplinePlug( const std::string &name, Direction direction, const ValueType &defaultValue, unsigned flags )
	:	ValuePlug( name, direction, flags ), m_defaultValue( defaultValue )
{
	addChild( new IntPlug( "interpolation", direction, SplineDefinitionInterpolationCatmullRom,
		SplineDefinitionInterpolationLinear, SplineDefinitionInterpolationMonotoneCubic ) );

	setToDefault();
}

template<typename T>
SplinePlug<T>::~SplinePlug()
{
}

template<typename T>
bool SplinePlug<T>::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( children().size() < 1 )
	{
		// to let the interpolation plug through during construction
		return true;
	}

	const ValuePlug *c = IECore::runTimeCast<const ValuePlug>( potentialChild );
	if( !c )
	{
		return false;
	}

	if( c->children().size()==0 )
	{
		// when we're getting loaded from a serialisation, the point plugs are
		// added before the point.x and point.y plugs are added, so we have to
		// make this concession.
		return true;
	}

	if( c->children().size()!=2 )
	{
		return false;
	}
	if( !c->getChild<XPlugType>( "x" ) )
	{
		return false;
	}
	if( !c->getChild<YPlugType>( "y" ) )
	{
		return false;
	}
	return true;
}

template<typename T>
PlugPtr SplinePlug<T>::createCounterpart( const std::string &name, Direction direction ) const
{
	Ptr result = new SplinePlug<T>( name, direction, m_defaultValue, getFlags() );
	result->clearPoints();
	for( unsigned i = 0; i < numPoints(); ++i )
	{
		const ValuePlug *p = pointPlug( i );
		result->addChild( p->createCounterpart( p->getName(), direction ) );
	}
	return result;
}

template<typename T>
const T &SplinePlug<T>::defaultValue() const
{
	return m_defaultValue;
}

template<typename T>
void SplinePlug<T>::setToDefault()
{
	setValue( m_defaultValue );
	for( const auto &p : ValuePlug::Range( *this ) )
	{
		p->resetDefault();
	}
}

template<typename T>
void SplinePlug<T>::resetDefault()
{
	ValuePlug::resetDefault();

	const T newDefault = getValue();
	const T oldDefault = m_defaultValue;
	Action::enact(
		this,
		[this, newDefault] () {
			this->m_defaultValue = newDefault;
		},
		[this, oldDefault] () {
			this->m_defaultValue = oldDefault;
		}
	);
}

template<typename T>
bool SplinePlug<T>::isSetToDefault() const
{
	return getValue() == m_defaultValue;
}

template<typename T>
void SplinePlug<T>::setValue( const T &value )
{
	interpolationPlug()->setValue( value.interpolation );

	typename T::PointContainer::const_iterator it = value.points.begin();
	typename T::PointContainer::const_iterator eIt = value.points.end();

	unsigned existingPoints = numPoints();
	unsigned i = 0;
	for( ; it!=eIt; ++it )
	{
		if( i >= existingPoints )
		{
			addPoint();
		}
		pointXPlug( i )->setValue( it->first );
		pointYPlug( i )->setValue( it->second );
		i++;
	}

	// remove unneeded preexisting points
	while( numPoints() > i )
	{
		removeChild( pointPlug( i ) );
	}
}

template<typename T>
T SplinePlug<T>::getValue() const
{
	T result;
	result.interpolation = (SplineDefinitionInterpolation)interpolationPlug()->getValue();

	unsigned n = numPoints();
	for( unsigned i=0; i<n; i++ )
	{
		result.points.insert( typename T::Point( pointXPlug( i )->getValue(), pointYPlug( i )->getValue() ) );
	}

	return result;
}


template<typename T>
IntPlug *SplinePlug<T>::interpolationPlug()
{
	return getChild<IntPlug>( "interpolation" );
}

template<typename T>
const IntPlug *SplinePlug<T>::interpolationPlug() const
{
	return getChild<IntPlug>( "interpolation" );
}

template<typename T>
unsigned SplinePlug<T>::numPoints() const
{
	return children().size() - 1;
}

template<typename T>
unsigned SplinePlug<T>::addPoint()
{
	const unsigned n = numPoints();
	ValuePlugPtr p = new ValuePlug( "p0", direction() );
	p->setFlags( Plug::Dynamic, true );

	typename XPlugType::Ptr x = new XPlugType( "x", direction(), typename T::XType( 0 ) );
	x->setFlags( Plug::Dynamic, true );
	p->addChild( x );

	typename YPlugType::Ptr y = new YPlugType( "y", direction(), typename T::YType( 0 ) );
	y->setFlags( Plug::Dynamic, true );
	p->addChild( y );

	addChild( p );

	return n;
}

template<typename T>
void SplinePlug<T>::removePoint( unsigned pointIndex )
{
	removeChild( pointPlug( pointIndex ) );
}

template<typename T>
void SplinePlug<T>::clearPoints()
{
	unsigned i = numPoints();
	if( !i )
	{
		return;
	}

	do {
		removePoint( --i );
	} while( i!=0 );
}

template<typename T>
ValuePlug *SplinePlug<T>::pointPlug( unsigned pointIndex )
{
	if( pointIndex >= numPoints() )
	{
		throw IECore::Exception( "Point index out of range." );
	}
	return getChild<ValuePlug>( pointIndex + 1 ); // plus one is to skip interpolation plug
}

template<typename T>
const ValuePlug *SplinePlug<T>::pointPlug( unsigned pointIndex ) const
{
	if( pointIndex >= numPoints() )
	{
		throw IECore::Exception( "Point index out of range." );
	}
	return getChild<ValuePlug>( pointIndex + 1 ); // plus one is to skip interpolation plug
}

template<typename T>
typename SplinePlug<T>::XPlugType *SplinePlug<T>::pointXPlug( unsigned pointIndex )
{
	XPlugType *p = pointPlug( pointIndex )->template getChild<XPlugType>( "x" );
	if( !p )
	{
		throw IECore::Exception( "Child Plug for x point position has been removed." );
	}
	return p;
}

template<typename T>
const typename SplinePlug<T>::XPlugType *SplinePlug<T>::pointXPlug( unsigned pointIndex ) const
{
	const XPlugType *p = pointPlug( pointIndex )->template getChild<XPlugType>( "x" );
	if( !p )
	{
		throw IECore::Exception( "Child Plug for x point position has been removed." );
	}
	return p;
}

template<typename T>
typename SplinePlug<T>::YPlugType *SplinePlug<T>::pointYPlug( unsigned pointIndex )
{
	YPlugType *p = pointPlug( pointIndex )->template getChild<YPlugType>( "y" );
	if( !p )
	{
		throw IECore::Exception( "Child Plug for y point position has been removed." );
	}
	return p;
}

template<typename T>
const typename SplinePlug<T>::YPlugType *SplinePlug<T>::pointYPlug( unsigned pointIndex ) const
{
	const YPlugType *p = pointPlug( pointIndex )->template getChild<YPlugType>( "y" );
	if( !p )
	{
		throw IECore::Exception( "Child Plug for y point position has been removed." );
	}
	return p;
}


namespace Gaffer
{

// RunTimeTyped specialisation
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::SplineffPlug, SplineffPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::SplinefColor3fPlug, SplinefColor3fPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::SplinefColor4fPlug, SplinefColor4fPlugTypeId )

// explicit instantiation
template struct SplineDefinition< IECore::Splineff >;
template struct SplineDefinition< IECore::SplinefColor3f >;
template struct SplineDefinition< IECore::SplinefColor4f >;
template class SplinePlug< SplineDefinitionff >;
template class SplinePlug< SplineDefinitionfColor3f >;
template class SplinePlug< SplineDefinitionfColor4f >;

}
