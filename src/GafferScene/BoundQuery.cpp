//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/BoundQuery.h"

#include "Imath/ImathBoxAlgo.h"

#include <cassert>
#include <cmath>

namespace
{

float ensurePositiveZero( float const value )
{
	return ( value == 0.0f ) ? std::fabs( value ) : value;
}

void
setV3fPlugComponentValue( Gaffer::V3fPlug const& parent, Gaffer::NumericPlug< float >& child, Imath::V3f const& value )
{
	float cv;

	if( & child == parent.getChild( 0 ) )
	{
		cv = value.x;
	}
	else if( & child == parent.getChild( 1 ) )
	{
		cv = value.y;
	}
	else if( & child == parent.getChild( 2 ) )
	{
		cv = value.z;
	}
	else
	{
		assert( 0 ); // NOTE : Unknown child plug
		cv = 0.f;
	}

	child.setValue( ensurePositiveZero( cv ) );
}

Imath::Box3f const g_singularBox( Imath::V3f( 0.f, 0.f, 0.f ), Imath::V3f( 0.f, 0.f, 0.f ) );

} // namespace

namespace GafferScene
{

size_t BoundQuery::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( BoundQuery );

BoundQuery::BoundQuery( std::string const& name )
: Gaffer::ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "scene" ) );
	addChild( new Gaffer::StringPlug( "location" ) );
	addChild( new Gaffer::IntPlug( "space", Gaffer::Plug::In,
		static_cast< int >( Space::World ),
		0, static_cast< int >( Space::Relative ) ) );
	addChild( new Gaffer::StringPlug( "relativeLocation" ) );
	addChild( new Gaffer::Box3fPlug( "bound", Gaffer::Plug::Out ) );
	addChild( new Gaffer::AtomicBox3fPlug( "__internalBound", Gaffer::Plug::Out ) );
	addChild( new Gaffer::V3fPlug( "center", Gaffer::Plug::Out ) );
	addChild( new Gaffer::V3fPlug( "size", Gaffer::Plug::Out ) );
}

BoundQuery::~BoundQuery()
{}

ScenePlug* BoundQuery::scenePlug()
{
	return const_cast< ScenePlug* >(
		static_cast< BoundQuery const* >( this )->scenePlug() );
}

ScenePlug const* BoundQuery::scenePlug() const
{
	return getChild< ScenePlug >( g_firstPlugIndex );
}

Gaffer::StringPlug* BoundQuery::locationPlug()
{
	return const_cast< Gaffer::StringPlug* >(
		static_cast< BoundQuery const* >( this )->locationPlug() );
}

Gaffer::StringPlug const* BoundQuery::locationPlug() const
{
	return getChild< Gaffer::StringPlug >( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug* BoundQuery::spacePlug()
{
	return const_cast< Gaffer::IntPlug* >(
		static_cast< BoundQuery const* >( this )->spacePlug() );
}

Gaffer::IntPlug const* BoundQuery::spacePlug() const
{
	return getChild< Gaffer::IntPlug >( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug* BoundQuery::relativeLocationPlug()
{
	return const_cast< Gaffer::StringPlug* >(
		static_cast< BoundQuery const* >( this )->relativeLocationPlug() );
}

Gaffer::StringPlug const* BoundQuery::relativeLocationPlug() const
{
	return getChild< Gaffer::StringPlug >( g_firstPlugIndex + 3 );
}

Gaffer::Box3fPlug* BoundQuery::boundPlug()
{
	return const_cast< Gaffer::Box3fPlug* >(
		static_cast< BoundQuery const* >( this )->boundPlug() );
}

Gaffer::Box3fPlug const* BoundQuery::boundPlug() const
{
	return getChild< Gaffer::Box3fPlug >( g_firstPlugIndex + 4 );
}

Gaffer::AtomicBox3fPlug* BoundQuery::internalBoundPlug()
{
	return const_cast< Gaffer::AtomicBox3fPlug* >(
		static_cast< BoundQuery const* >( this )->internalBoundPlug() );
}

Gaffer::AtomicBox3fPlug const* BoundQuery::internalBoundPlug() const
{
	return getChild< Gaffer::AtomicBox3fPlug >( g_firstPlugIndex + 5 );
}

Gaffer::V3fPlug* BoundQuery::centerPlug()
{
	return const_cast< Gaffer::V3fPlug* >(
		static_cast< BoundQuery const* >( this )->centerPlug() );
}

Gaffer::V3fPlug const* BoundQuery::centerPlug() const
{
	return getChild< Gaffer::V3fPlug >( g_firstPlugIndex + 6 );
}

Gaffer::V3fPlug* BoundQuery::sizePlug()
{
	return const_cast< Gaffer::V3fPlug* >(
		static_cast< BoundQuery const* >( this )->sizePlug() );
}

Gaffer::V3fPlug const* BoundQuery::sizePlug() const
{
	return getChild< Gaffer::V3fPlug >( g_firstPlugIndex + 7 );
}

void BoundQuery::affects( Gaffer::Plug const* const input, AffectedPlugsContainer& outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == internalBoundPlug() )
	{
		outputs.push_back( boundPlug()->minPlug()->getChild( 0 ) );
		outputs.push_back( boundPlug()->minPlug()->getChild( 1 ) );
		outputs.push_back( boundPlug()->minPlug()->getChild( 2 ) );
		outputs.push_back( boundPlug()->maxPlug()->getChild( 0 ) );
		outputs.push_back( boundPlug()->maxPlug()->getChild( 1 ) );
		outputs.push_back( boundPlug()->maxPlug()->getChild( 2 ) );
		outputs.push_back( centerPlug()->getChild( 0 ) );
		outputs.push_back( centerPlug()->getChild( 1 ) );
		outputs.push_back( centerPlug()->getChild( 2 ) );
		outputs.push_back( sizePlug()->getChild( 0 ) );
		outputs.push_back( sizePlug()->getChild( 1 ) );
		outputs.push_back( sizePlug()->getChild( 2 ) );
	}
	else if(
		( input == spacePlug() ) ||
		( input == locationPlug() ) ||
		( input == relativeLocationPlug() ) ||
		( input == scenePlug()->boundPlug() ) ||
		( input == scenePlug()->existsPlug() ) ||
		( input == scenePlug()->transformPlug() ) )
	{
		outputs.push_back( internalBoundPlug() );
	}
}

void BoundQuery::hash( Gaffer::ValuePlug const* const output, Gaffer::Context const* const context, IECore::MurmurHash& h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == internalBoundPlug() )
	{
		std::string const loc = locationPlug()->getValue();
		if( ! loc.empty() )
		{
			ScenePlug const* const splug = scenePlug();
			assert( splug != 0 );

			ScenePlug::ScenePath const path = ScenePlug::stringToPath( loc );

			if( splug->exists( path ) )
			{
				switch( static_cast< Space >( spacePlug()->getValue() ) )
				{
					case Space::Local:
						h = splug->boundHash( path );
						break;
					case Space::World:
						h.append( splug->fullTransformHash( path ) );
						h.append( splug->boundHash( path ) );
						break;
					case Space::Relative:
					{
						std::string const rloc = relativeLocationPlug()->getValue();

						if( ! rloc.empty() )
						{
							if( loc == rloc )
							{
								h = splug->boundHash( path );
							}
							else
							{
								ScenePlug::ScenePath const rpath = ScenePlug::stringToPath( rloc );

								if( splug->exists( rpath ) )
								{
									h.append( splug->fullTransformHash( path ) );
									h.append( splug->fullTransformHash( rpath ) );
									h.append( splug->boundHash( path ) );
								}
							}
						}
						break;
					}
					default:
						break;
				}
			}
		}
	}
	else
	{
		Gaffer::GraphComponent const* const parent = output->parent();

		if(
			( parent == boundPlug()->minPlug() ) ||
			( parent == boundPlug()->maxPlug() ) ||
			( parent == centerPlug() ) ||
			( parent == sizePlug() ) )
		{
			internalBoundPlug()->hash( h );
		}
	}
}

void BoundQuery::compute( Gaffer::ValuePlug* const output, Gaffer::Context const* const context ) const
{
	if( output == internalBoundPlug() )
	{
		Imath::Box3f b;

		std::string const loc = locationPlug()->getValue();
		if( ! loc.empty() )
		{
			ScenePlug const* const splug = scenePlug();
			assert( splug != 0 );

			ScenePlug::ScenePath const path = ScenePlug::stringToPath( loc );

			if( splug->exists( path ) )
			{
				switch( static_cast< Space >( spacePlug()->getValue() ) )
				{
					case Space::Local:
						b = splug->bound( path );
						break;
					case Space::World:
						b = Imath::transform( splug->bound( path ), splug->fullTransform( path ) );
						break;
					case Space::Relative:
					{
						std::string const rloc = relativeLocationPlug()->getValue();

						if( ! rloc.empty() )
						{
							if( loc == rloc )
							{
								b = splug->bound( path );
							}
							else
							{
								ScenePlug::ScenePath const rpath = ScenePlug::stringToPath( rloc );

								if( splug->exists( rpath ) )
								{
									b = Imath::transform( splug->bound( path ),
										splug->fullTransform( path ) * splug->fullTransform( rpath ).inverse() );
								}
							}
						}
						break;
					}
					default:
						break;
				}
			}
		}

		IECore::assertedStaticCast< Gaffer::AtomicBox3fPlug >( output )->setValue( b.isEmpty() ? g_singularBox : b );
	}
	else
	{
		Gaffer::GraphComponent* const parent = output->parent();

		if( parent == boundPlug()->minPlug() )
		{
			Imath::Box3f const b = internalBoundPlug()->getValue();
			setV3fPlugComponentValue(
				*( IECore::assertedStaticCast< Gaffer::V3fPlug >( parent ) ),
				*( IECore::assertedStaticCast< Gaffer::NumericPlug< float > >( output ) ), b.min );
		}
		else if( parent == boundPlug()->maxPlug() )
		{
			Imath::Box3f const b = internalBoundPlug()->getValue();
			setV3fPlugComponentValue(
				*( IECore::assertedStaticCast< Gaffer::V3fPlug >( parent ) ),
				*( IECore::assertedStaticCast< Gaffer::NumericPlug< float > >( output ) ), b.max );
		}
		else if( parent == centerPlug() )
		{
			Imath::Box3f const b = internalBoundPlug()->getValue();
			setV3fPlugComponentValue(
				*( IECore::assertedStaticCast< Gaffer::V3fPlug >( parent ) ),
				*( IECore::assertedStaticCast< Gaffer::NumericPlug< float > >( output ) ), b.center() );
		}
		else if( parent == sizePlug() )
		{
			Imath::Box3f const b = internalBoundPlug()->getValue();
			setV3fPlugComponentValue(
				*( IECore::assertedStaticCast< Gaffer::V3fPlug >( parent ) ),
				*( IECore::assertedStaticCast< Gaffer::NumericPlug< float > >( output ) ), b.size() );
		}
	}

	ComputeNode::compute( output, context );
}

} // GafferScene
