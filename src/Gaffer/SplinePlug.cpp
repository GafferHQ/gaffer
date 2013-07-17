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

#include "boost/format.hpp"

using namespace Gaffer;

template<typename T>
const IECore::RunTimeTyped::TypeDescription<SplinePlug<T> > SplinePlug<T>::g_typeDescription;

template<typename T>
SplinePlug<T>::SplinePlug( const std::string &name, Direction direction, const T &defaultValue, unsigned flags )
	:	CompoundPlug( name, direction, flags ), m_defaultValue( defaultValue )
{
	CompoundPlugPtr basis = new CompoundPlug( "basis", direction );
	M44fPlugPtr basisMatrix = new M44fPlug( "matrix", direction, defaultValue.basis.matrix );
	IntPlugPtr basisStep = new IntPlug( "step", direction, defaultValue.basis.step );
	basis->addChild( basisMatrix );
	basis->addChild( basisStep );
	addChild( basis );

	addChild( new IntPlug( "endPointMultiplicity", direction, endPointMultiplicity( defaultValue ), 1 ) );

	setValue( defaultValue );
}

template<typename T>
SplinePlug<T>::~SplinePlug()
{
}

template<typename T>
bool SplinePlug<T>::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( children().size() < 2 )
	{
		// to let the basis and endPointMultiplicity plugs through during construction
		return true;
	}

	ConstCompoundPlugPtr c = IECore::runTimeCast<const CompoundPlug>( potentialChild );
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
	Ptr result = new SplinePlug<T>( name, direction, defaultValue(), getFlags() );
	result->setValue( getValue() );
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
}

template<typename T>
void SplinePlug<T>::setValue( const T &value )
{
	basisMatrixPlug()->setValue( value.basis.matrix );
	basisStepPlug()->setValue( value.basis.step );
	
	const int multiplicity = endPointMultiplicity( value );
	endPointMultiplicityPlug()->setValue( multiplicity );
	
	typename T::PointContainer::const_iterator it = value.points.begin();
	typename T::PointContainer::const_iterator eIt = value.points.end();
	if( multiplicity )
	{
		advance( it, multiplicity - 1 );
		advance( eIt, - (multiplicity - 1) );
	}
	
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
	result.basis.matrix = basisMatrixPlug()->getValue();
	result.basis.step = basisStepPlug()->getValue();
	
	unsigned n = numPoints();
	for( unsigned i=0; i<n; i++ )
	{
		result.points.insert( typename T::PointContainer::value_type( pointXPlug( i )->getValue(), pointYPlug( i )->getValue() ) );
	}
	
	const size_t multiplicity = endPointMultiplicityPlug()->getValue();
	if( multiplicity && n )
	{
		for( size_t i = 0; i < multiplicity - 1; ++i )
		{
			result.points.insert( *result.points.begin() );
			result.points.insert( *result.points.rbegin() );
		}
	}
		
	return result;
}

template<typename T>
CompoundPlug *SplinePlug<T>::basisPlug()
{
	return getChild<CompoundPlug>( "basis" );
}

template<typename T>
const CompoundPlug *SplinePlug<T>::basisPlug() const
{	
	return getChild<CompoundPlug>( "basis" );
}

template<typename T>
M44fPlug *SplinePlug<T>::basisMatrixPlug()
{
	return basisPlug()->getChild<M44fPlug>( "matrix" );
}

template<typename T>
const M44fPlug *SplinePlug<T>::basisMatrixPlug() const
{
	return basisPlug()->getChild<M44fPlug>( "matrix" );
}

template<typename T>
IntPlug *SplinePlug<T>::basisStepPlug()
{
	return basisPlug()->getChild<IntPlug>( "step" );
}

template<typename T>
const IntPlug *SplinePlug<T>::basisStepPlug() const
{
	return basisPlug()->getChild<IntPlug>( "step" );
}

template<typename T>
unsigned SplinePlug<T>::numPoints() const
{
	return children().size() - 2;
}

template<typename T>
unsigned SplinePlug<T>::addPoint()
{
	const unsigned n = numPoints();
	CompoundPlugPtr p = new CompoundPlug( "p0", direction() );
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
CompoundPlug *SplinePlug<T>::pointPlug( unsigned pointIndex )
{
	if( pointIndex >= numPoints() )
	{
		throw IECore::Exception( "Point index out of range." );
	}
	return getChild<CompoundPlug>( pointIndex + 2 ); // plus two is to skip basis and endPointMultiplicity plugs
}

template<typename T>
const CompoundPlug *SplinePlug<T>::pointPlug( unsigned pointIndex ) const
{
	if( pointIndex >= numPoints() )
	{
		throw IECore::Exception( "Point index out of range." );
	}
	return getChild<CompoundPlug>( pointIndex + 2 ); // plus two is to skip basis and endPointMultiplicity plugs
}

template<typename T>
typename SplinePlug<T>::XPlugType *SplinePlug<T>::pointXPlug( unsigned pointIndex )
{
	typename XPlugType::Ptr p = pointPlug( pointIndex )->getChild<XPlugType>( "x" );
	if( !p )
	{
		throw IECore::Exception( "Child Plug for x point position has been removed." );
	}
	return p;
}

template<typename T>
const typename SplinePlug<T>::XPlugType *SplinePlug<T>::pointXPlug( unsigned pointIndex ) const
{
	typename XPlugType::ConstPtr p = pointPlug( pointIndex )->getChild<XPlugType>( "x" );
	if( !p )
	{
		throw IECore::Exception( "Child Plug for x point position has been removed." );
	}
	return p;
}

template<typename T>
typename SplinePlug<T>::YPlugType *SplinePlug<T>::pointYPlug( unsigned pointIndex )
{
	typename YPlugType::Ptr p = pointPlug( pointIndex )->getChild<YPlugType>( "y" );
	if( !p )
	{
		throw IECore::Exception( "Child Plug for y point position has been removed." );
	}
	return p;
}

template<typename T>
const typename SplinePlug<T>::YPlugType *SplinePlug<T>::pointYPlug( unsigned pointIndex ) const
{
	typename YPlugType::ConstPtr p = pointPlug( pointIndex )->getChild<YPlugType>( "y" );
	if( !p )
	{
		throw IECore::Exception( "Child Plug for y point position has been removed." );
	}
	return p;
}

template<typename T>
IntPlug *SplinePlug<T>::endPointMultiplicityPlug()
{
	return getChild<IntPlug>( "endPointMultiplicity" );
}

template<typename T>
const IntPlug *SplinePlug<T>::endPointMultiplicityPlug() const
{
	return getChild<IntPlug>( "endPointMultiplicity" );
}

template<typename T>
size_t SplinePlug<T>::endPointMultiplicity( const T &value ) const
{
	size_t startMultiplicity = 0;
	for( typename T::PointContainer::const_iterator it=value.points.begin(); it!=value.points.end(); ++it )
	{
		if( *it != *value.points.begin() )
		{
			break;
		}
		startMultiplicity++;
	}
	
	size_t endMultiplicity = 0;
	for( typename T::PointContainer::const_reverse_iterator it=value.points.rbegin(); it!=value.points.rend(); ++it )
	{
		if( *it != *value.points.rbegin() )
		{
			break;
		}
		endMultiplicity++;
	}
	
	if( startMultiplicity == endMultiplicity )
	{
		return startMultiplicity;
	}
	else
	{
		return 1;
	}
}

namespace Gaffer
{

// RunTimeTyped specialisation
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::SplineffPlug, SplineffPlugTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::SplinefColor3fPlug, SplinefColor3fPlugTypeId )

}

// explicit instantiation
template class SplinePlug<IECore::Splineff>;
template class SplinePlug<IECore::SplinefColor3f>;
