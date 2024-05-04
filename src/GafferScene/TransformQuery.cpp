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

#include "GafferScene/TransformQuery.h"

#include "Imath/ImathMatrixAlgo.h"
#include "Imath/ImathEuler.h"

#include <cassert>
#include <cmath>
#include <cmath> // NOTE : M_PI

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

} // namespace

namespace GafferScene
{

size_t TransformQuery::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( TransformQuery );

TransformQuery::TransformQuery( std::string const& name )
: Gaffer::ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "scene" ) );
	addChild( new Gaffer::StringPlug( "location" ) );
	addChild( new Gaffer::IntPlug( "space", Gaffer::Plug::In,
		static_cast< int >( Space::World ),
		0, static_cast< int >( Space::Relative ) ) );
	addChild( new Gaffer::StringPlug( "relativeLocation" ) );
	addChild( new Gaffer::BoolPlug( "invert" ) );
	addChild( new Gaffer::M44fPlug( "matrix", Gaffer::Plug::Out ) );
	addChild( new Gaffer::V3fPlug( "translate", Gaffer::Plug::Out ) );
	addChild( new Gaffer::V3fPlug( "rotate", Gaffer::Plug::Out ) );
	addChild( new Gaffer::V3fPlug( "scale", Gaffer::Plug::Out ) );
}

TransformQuery::~TransformQuery()
{}

ScenePlug* TransformQuery::scenePlug()
{
	return const_cast< ScenePlug* >(
		static_cast< TransformQuery const* >( this )->scenePlug() );
}

ScenePlug const* TransformQuery::scenePlug() const
{
	return getChild< ScenePlug >( g_firstPlugIndex );
}

Gaffer::StringPlug* TransformQuery::locationPlug()
{
	return const_cast< Gaffer::StringPlug* >(
		static_cast< TransformQuery const* >( this )->locationPlug() );
}

Gaffer::StringPlug const* TransformQuery::locationPlug() const
{
	return getChild< Gaffer::StringPlug >( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug* TransformQuery::spacePlug()
{
	return const_cast< Gaffer::IntPlug* >(
		static_cast< TransformQuery const* >( this )->spacePlug() );
}

Gaffer::IntPlug const* TransformQuery::spacePlug() const
{
	return getChild< Gaffer::IntPlug >( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug* TransformQuery::relativeLocationPlug()
{
	return const_cast< Gaffer::StringPlug* >(
		static_cast< TransformQuery const* >( this )->relativeLocationPlug() );
}

Gaffer::StringPlug const* TransformQuery::relativeLocationPlug() const
{
	return getChild< Gaffer::StringPlug >( g_firstPlugIndex + 3 );
}

Gaffer::BoolPlug* TransformQuery::invertPlug()
{
	return const_cast< Gaffer::BoolPlug* >(
		static_cast< TransformQuery const* >( this )->invertPlug() );
}

Gaffer::BoolPlug const* TransformQuery::invertPlug() const
{
	return getChild< Gaffer::BoolPlug >( g_firstPlugIndex + 4 );
}

Gaffer::M44fPlug* TransformQuery::matrixPlug()
{
	return const_cast< Gaffer::M44fPlug* >(
		static_cast< TransformQuery const* >( this )->matrixPlug() );
}

Gaffer::M44fPlug const* TransformQuery::matrixPlug() const
{
	return getChild< Gaffer::M44fPlug >( g_firstPlugIndex + 5 );
}

Gaffer::V3fPlug* TransformQuery::translatePlug()
{
	return const_cast< Gaffer::V3fPlug* >(
		static_cast< TransformQuery const* >( this )->translatePlug() );
}

Gaffer::V3fPlug const* TransformQuery::translatePlug() const
{
	return getChild< Gaffer::V3fPlug >( g_firstPlugIndex + 6 );
}

Gaffer::V3fPlug* TransformQuery::rotatePlug()
{
	return const_cast< Gaffer::V3fPlug* >(
		static_cast< TransformQuery const* >( this )->rotatePlug() );
}

Gaffer::V3fPlug const* TransformQuery::rotatePlug() const
{
	return getChild< Gaffer::V3fPlug >( g_firstPlugIndex + 7 );
}

Gaffer::V3fPlug* TransformQuery::scalePlug()
{
	return const_cast< Gaffer::V3fPlug* >(
		static_cast< TransformQuery const* >( this )->scalePlug() );
}

Gaffer::V3fPlug const* TransformQuery::scalePlug() const
{
	return getChild< Gaffer::V3fPlug >( g_firstPlugIndex + 8 );
}

void TransformQuery::affects( Gaffer::Plug const* const input, AffectedPlugsContainer& outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == matrixPlug() )
	{
		outputs.push_back( translatePlug()->getChild( 0 ) );
		outputs.push_back( translatePlug()->getChild( 1 ) );
		outputs.push_back( translatePlug()->getChild( 2 ) );
		outputs.push_back( rotatePlug()->getChild( 0 ) );
		outputs.push_back( rotatePlug()->getChild( 1 ) );
		outputs.push_back( rotatePlug()->getChild( 2 ) );
		outputs.push_back( scalePlug()->getChild( 0 ) );
		outputs.push_back( scalePlug()->getChild( 1 ) );
		outputs.push_back( scalePlug()->getChild( 2 ) );
	}
	else if(
		( input == spacePlug() ) ||
		( input == invertPlug() ) ||
		( input == locationPlug() ) ||
		( input == relativeLocationPlug() ) ||
		( input == scenePlug()->existsPlug() ) ||
		( input == scenePlug()->transformPlug() ) )
	{
		outputs.push_back( matrixPlug() );
	}
}

void TransformQuery::hash( Gaffer::ValuePlug const* const output, Gaffer::Context const* const context, IECore::MurmurHash& h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == matrixPlug() )
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
					{
						if( invertPlug()->getValue() )
						{
							h.append( splug->transformHash( path ) );
						}
						else
						{
							h = splug->transformHash( path );
						}
						break;
					}
					case Space::World:
					{
						h.append( splug->fullTransformHash( path ) );
						h.append( invertPlug()->hash() );
						break;
					}
					case Space::Relative:
					{
						std::string const rloc = relativeLocationPlug()->getValue();

						if( ! rloc.empty() )
						{
							ScenePlug::ScenePath const rpath = ScenePlug::stringToPath( rloc );

							if(
								( rpath != path ) &&
								( splug->exists( rpath ) ) )
							{
								h.append( splug->fullTransformHash( path ) );
								h.append( splug->fullTransformHash( rpath ) );
								invertPlug()->hash( h );
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
			( parent == translatePlug() ) ||
			( parent == rotatePlug() ) ||
			( parent == scalePlug() ) )
		{
			matrixPlug()->hash( h );
		}
	}
}

void TransformQuery::compute( Gaffer::ValuePlug* const output, Gaffer::Context const* const context ) const
{
	if( output == matrixPlug() )
	{
		Imath::M44f m;

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
						m = splug->transform( path );
						break;
					case Space::World:
						m = splug->fullTransform( path );
						break;
					case Space::Relative:
					{
						std::string const rloc = relativeLocationPlug()->getValue();

						if( ! rloc.empty() )
						{
							ScenePlug::ScenePath const rpath = ScenePlug::stringToPath( rloc );

							if(
								( rpath != path ) &&
								( splug->exists( rpath ) ) )
							{
								m = splug->fullTransform( path ) * splug->fullTransform( rpath ).inverse();
							}
						}
						break;
					}
					default:
						break;
				}

				if( invertPlug()->getValue() )
				{
					m.invert();
				}
			}
		}

		IECore::assertedStaticCast< Gaffer::M44fPlug >( output )->setValue( m );
	}
	else
	{
		Gaffer::GraphComponent* const parent = output->parent();

		if( parent == translatePlug() )
		{
			Imath::M44f const m = matrixPlug()->getValue();
			setV3fPlugComponentValue(
				*( IECore::assertedStaticCast< Gaffer::V3fPlug >( parent ) ),
				*( IECore::assertedStaticCast< Gaffer::NumericPlug< float > >( output ) ), m.translation() );
		}
		else if( parent == rotatePlug() )
		{
			Imath::Eulerf::Order order = Imath::Eulerf::XYZ;
			Imath::M44f const m = Imath::sansScalingAndShear( matrixPlug()->getValue() );
			Imath::Eulerf euler( m, order );
			euler *= static_cast< float >( 180.0 / M_PI );
			setV3fPlugComponentValue(
				*( IECore::assertedStaticCast< Gaffer::V3fPlug >( parent ) ),
				*( IECore::assertedStaticCast< Gaffer::NumericPlug< float > >( output ) ), euler );
		}
		else if( parent == scalePlug() )
		{
			Imath::V3f scale( 0.f );
			Imath::M44f const m = matrixPlug()->getValue();
			Imath::extractScaling( m, scale );
			setV3fPlugComponentValue(
				*( IECore::assertedStaticCast< Gaffer::V3fPlug >( parent ) ),
				*( IECore::assertedStaticCast< Gaffer::NumericPlug< float > >( output ) ), scale );
		}
	}

	ComputeNode::compute( output, context );
}

} // GafferScene
