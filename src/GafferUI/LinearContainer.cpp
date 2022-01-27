//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2014, John Haddon. All rights reserved.
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/LinearContainer.h"

#include "GafferUI/Style.h"

#include "IECore/Exception.h"

#include "boost/bind/bind.hpp"

using namespace std;
using namespace Imath;
using namespace GafferUI;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( LinearContainer );

LinearContainer::LinearContainer( const std::string &name, Orientation orientation,
	Alignment alignment, float spacing, Direction direction )
	:	ContainerGadget( name ), m_orientation( orientation ), m_alignment( alignment ), m_spacing( spacing ), m_direction( direction )
{
	// We already initialised these values above, but that didn't perform any range checking,
	// so we set them here as well. The reason we initialize them at all is so that the set
	// methods will determine that the values are not changing, and therefore not call
	// `dirty()` unecessarily.
	setOrientation( orientation );
	setAlignment( alignment );
	setSpacing( spacing );
	setDirection( direction );
}

LinearContainer::~LinearContainer()
{
}

void LinearContainer::setOrientation( Orientation orientation )
{
	if( orientation < X || orientation > Y )
	{
		throw IECore::InvalidArgumentException( "Invalid orientation" );
	}
	if( orientation != m_orientation )
	{
		m_orientation = orientation;
		dirty( DirtyType::Layout );
	}
}

LinearContainer::Orientation LinearContainer::getOrientation() const
{
	return m_orientation;
}

void LinearContainer::setAlignment( Alignment alignment )
{
	if( alignment < Min || alignment > Max )
	{
		throw IECore::InvalidArgumentException( "Invalid alignment" );
	}
	if( alignment != m_alignment )
	{
		m_alignment = alignment;
		dirty( DirtyType::Layout );
	}
}

LinearContainer::Alignment LinearContainer::getAlignment() const
{
	return m_alignment;
}

void LinearContainer::setSpacing( float spacing )
{
	if( spacing < 0.0f )
	{
		throw IECore::InvalidArgumentException( "Invalid spacing" );
	}
	if( spacing!=m_spacing )
	{
		m_spacing = spacing;
		dirty( DirtyType::Layout );
	}
}

float LinearContainer::getSpacing() const
{
	return m_spacing;
}

void LinearContainer::setDirection( Direction direction )
{
	if( direction != Increasing && direction != Decreasing )
	{
		throw IECore::InvalidArgumentException( "Invalid alignment" );
	}
	if( direction != m_direction )
	{
		m_direction = direction;
		dirty( DirtyType::Layout );
	}
}

LinearContainer::Direction LinearContainer::getDirection() const
{
	return m_direction;
}

void LinearContainer::updateLayout() const
{
	int axis = m_orientation - 1;
	V3f size( 0 );
	vector<Box3f> bounds;
	for( ChildContainer::const_iterator it=children().begin(); it!=children().end(); it++ )
	{
		const Gadget *child = static_cast<const Gadget *>( it->get() );
		if( !child->getVisible() )
		{
			continue;
		}

		Box3f b = child->bound();
		if( !b.isEmpty() )
		{
			for( int a=0; a<3; a++ )
			{
				if( a==axis )
				{
					size[a] += b.size()[a];
				}
				else
				{
					size[a] = max( size[a], b.size()[a] );
				}
			}
		}
		bounds.push_back( b );
	}
	size[axis] += (bounds.size() - 1) * m_spacing;

	float offset = size[axis] / 2.0f  * ( m_direction==Increasing ? -1.0f : 1.0f );

	int i = 0;
	for( ChildContainer::const_iterator it=children().begin(); it!=children().end(); it++ )
	{
		Gadget *child = static_cast<Gadget *>( it->get() );
		if( !child->getVisible() )
		{
			continue;
		}

		const Box3f &b = bounds[i++];

		V3f childOffset( 0 );
		if( !b.isEmpty() )
		{
			for( int a=0; a<3; a++ )
			{
				if( a==axis )
				{
					childOffset[a] = offset - ( m_direction==Increasing ? b.min[a] : b.max[a] );
				}
				else
				{
					switch( m_alignment )
					{
						case Min :
							childOffset[a] = -size[a]/2.0f - b.min[a];
							break;
						case Centre :
							childOffset[a] = -b.center()[a];
							break;
						default :
							// max
							childOffset[a] = size[a]/2.0f - b.max[a];
					}
				}
			}
			offset += b.size()[axis] * ( m_direction==Increasing ? 1.0f : -1.0f );
		}
		offset += m_spacing * ( m_direction==Increasing ? 1.0f : -1.0f );

		M44f m; m.translate( childOffset );
		child->setTransform( m );
	}
}
