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

#include "Gaffer/RampPlug.h"

#include "Gaffer/Action.h"
#include "Gaffer/PlugAlgo.h"

using namespace Gaffer;

template<typename T>
const IECore::RunTimeTyped::TypeDescription<RampPlug<T> > RampPlug<T>::g_typeDescription;

template<typename T>
RampPlug<T>::RampPlug( const std::string &name, Direction direction, const ValueType &defaultValue, unsigned flags )
	:	ValuePlug( name, direction, flags ), m_defaultValue( defaultValue )
{
	addChild( new IntPlug( "interpolation", direction, (int)IECore::RampInterpolation::CatmullRom,
		(int)IECore::RampInterpolation::Linear, (int)IECore::RampInterpolation::Constant ) );
	// We'd really like to use an ArrayPlug here, but since it isn't a ValuePlug we're
	// not allowed to parent one to ourselves.
	addChild( new ValuePlug( "points", direction ) );

	setToDefault();
}

template<typename T>
RampPlug<T>::~RampPlug()
{
}

template<typename T>
bool RampPlug<T>::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( !ValuePlug::acceptsChild( potentialChild ) )
	{
		return false;
	}
	// Just accept the plugs we make during construction.
	return children().size() < 2;
}

template<typename T>
PlugPtr RampPlug<T>::createCounterpart( const std::string &name, Direction direction ) const
{
	Ptr result = new RampPlug<T>( name, direction, m_defaultValue, getFlags() );
	result->clearPoints();
	for( unsigned i = 0; i < numPoints(); ++i )
	{
		result->addPoint( pointXPlug( i )->defaultValue(), pointYPlug( i )->defaultValue() );
	}
	return result;
}

template<typename T>
const T &RampPlug<T>::defaultValue() const
{
	return m_defaultValue;
}

template<typename T>
void RampPlug<T>::setToDefault()
{
	setValue( m_defaultValue );
	interpolationPlug()->resetDefault();
	for( const auto &p : ValuePlug::Range( *pointsPlug() ) )
	{
		p->resetDefault();
	}
}

template<typename T>
void RampPlug<T>::resetDefault()
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
bool RampPlug<T>::isSetToDefault() const
{
	for( const auto &p : ValuePlug::RecursiveRange( *this ) )
	{
		if( p->children().empty() && PlugAlgo::dependsOnCompute( p.get() ) )
		{
			// Value can vary by context, so there is no single "current value",
			// and therefore no true concept of whether or not it's at the default.
			return false;
		}
	}
	return getValue() == m_defaultValue;
}

template<typename T>
IECore::MurmurHash RampPlug<T>::defaultHash() const
{
	IECore::MurmurHash result;
	result.append( typeId() );
	result.append( m_defaultValue.interpolation );
	for( auto &p : m_defaultValue.points )
	{
		result.append( p.first );
		result.append( p.second );
	}
	return result;
}

template<typename T>
void RampPlug<T>::setValue( const T &value )
{
	interpolationPlug()->setValue( (int)value.interpolation );

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
		removePoint( numPoints() - 1 );
	}
}

template<typename T>
T RampPlug<T>::getValue() const
{
	T result;
	result.interpolation = (IECore::RampInterpolation)interpolationPlug()->getValue();

	unsigned n = numPoints();
	for( unsigned i=0; i<n; i++ )
	{
		result.points.insert( typename T::Point( pointXPlug( i )->getValue(), pointYPlug( i )->getValue() ) );
	}

	return result;
}

template<typename T>
IntPlug *RampPlug<T>::interpolationPlug()
{
	return getChild<IntPlug>( 0 );
}

template<typename T>
const IntPlug *RampPlug<T>::interpolationPlug() const
{
	return getChild<IntPlug>( 0 );
}

template<typename T>
ValuePlug *RampPlug<T>::pointsPlug()
{
	return getChild<ValuePlug>( 1 );
}

template<typename T>
const ValuePlug *RampPlug<T>::pointsPlug() const
{
	return getChild<ValuePlug>( 1 );
}

template<typename T>
unsigned RampPlug<T>::numPoints() const
{
	return pointsPlug()->children().size();
}

template<typename T>
unsigned RampPlug<T>::addPoint()
{
	return addPoint( XType( 0 ), YType( 0 ) );
}

template<typename T>
unsigned RampPlug<T>::addPoint( XType xDefaultValue, const YType &yDefaultValue )
{
	const unsigned n = numPoints();
	ValuePlugPtr p = new ValuePlug( "p0", direction() );
	typename XPlugType::Ptr x = new XPlugType( "x", direction(), xDefaultValue );
	p->addChild( x );
	typename YPlugType::Ptr y = new YPlugType( "y", direction(), yDefaultValue );
	p->addChild( y );
	pointsPlug()->addChild( p );
	return n;
}

template<typename T>
void RampPlug<T>::removePoint( unsigned pointIndex )
{
	pointsPlug()->removeChild( pointPlug( pointIndex ) );
}

template<typename T>
void RampPlug<T>::clearPoints()
{
	pointsPlug()->clearChildren();
}

template<typename T>
ValuePlug *RampPlug<T>::pointPlug( unsigned pointIndex )
{
	if( pointIndex >= numPoints() )
	{
		throw IECore::Exception( "Point index out of range." );
	}
	return pointsPlug()->template getChild<ValuePlug>( pointIndex );
}

template<typename T>
const ValuePlug *RampPlug<T>::pointPlug( unsigned pointIndex ) const
{
	if( pointIndex >= numPoints() )
	{
		throw IECore::Exception( "Point index out of range." );
	}
	return pointsPlug()->template getChild<ValuePlug>( pointIndex );
}

template<typename T>
typename RampPlug<T>::XPlugType *RampPlug<T>::pointXPlug( unsigned pointIndex )
{
	XPlugType *p = pointPlug( pointIndex )->template getChild<XPlugType>( "x" );
	if( !p )
	{
		throw IECore::Exception( "Child Plug for x point position has been removed." );
	}
	return p;
}

template<typename T>
const typename RampPlug<T>::XPlugType *RampPlug<T>::pointXPlug( unsigned pointIndex ) const
{
	const XPlugType *p = pointPlug( pointIndex )->template getChild<XPlugType>( "x" );
	if( !p )
	{
		throw IECore::Exception( "Child Plug for x point position has been removed." );
	}
	return p;
}

template<typename T>
typename RampPlug<T>::YPlugType *RampPlug<T>::pointYPlug( unsigned pointIndex )
{
	YPlugType *p = pointPlug( pointIndex )->template getChild<YPlugType>( "y" );
	if( !p )
	{
		throw IECore::Exception( "Child Plug for y point position has been removed." );
	}
	return p;
}

template<typename T>
const typename RampPlug<T>::YPlugType *RampPlug<T>::pointYPlug( unsigned pointIndex ) const
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
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::RampffPlug, RampffPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::RampfColor3fPlug, RampfColor3fPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::RampfColor4fPlug, RampfColor4fPlugTypeId )

// explicit instantiation
template class RampPlug< IECore::Rampff >;
template class RampPlug< IECore::RampfColor3f >;
template class RampPlug< IECore::RampfColor4f >;

}
