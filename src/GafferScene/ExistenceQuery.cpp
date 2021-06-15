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

#include "GafferScene/ExistenceQuery.h"

#include <cassert>

namespace GafferScene
{

size_t ExistenceQuery::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( ExistenceQuery );

ExistenceQuery::ExistenceQuery( const std::string& name )
: Gaffer::ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "scene" ) );
	addChild( new Gaffer::StringPlug( "location" ) );
	addChild( new Gaffer::BoolPlug( "exists", Gaffer::Plug::Out, false ) );
	addChild( new Gaffer::StringPlug( "closestAncestor", Gaffer::Plug::Out ) );
}

ExistenceQuery::~ExistenceQuery()
{}

ScenePlug* ExistenceQuery::scenePlug()
{
	return const_cast< ScenePlug* >(
		static_cast< const ExistenceQuery* >( this )->scenePlug() );
}

const ScenePlug* ExistenceQuery::scenePlug() const
{
	return getChild< ScenePlug >( g_firstPlugIndex );
}

Gaffer::StringPlug* ExistenceQuery::locationPlug()
{
	return const_cast< Gaffer::StringPlug* >(
		static_cast< const ExistenceQuery* >( this )->locationPlug() );
}

const Gaffer::StringPlug* ExistenceQuery::locationPlug() const
{
	return getChild< Gaffer::StringPlug >( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug* ExistenceQuery::existsPlug()
{
	return const_cast< Gaffer::BoolPlug* >(
		static_cast< const ExistenceQuery* >( this )->existsPlug() );
}

const Gaffer::BoolPlug* ExistenceQuery::existsPlug() const
{
	return getChild< Gaffer::BoolPlug >( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug* ExistenceQuery::closestAncestorPlug()
{
	return const_cast< Gaffer::StringPlug* >(
		static_cast< const ExistenceQuery* >( this )->closestAncestorPlug() );
}

const Gaffer::StringPlug* ExistenceQuery::closestAncestorPlug() const
{
	return getChild< Gaffer::StringPlug >( g_firstPlugIndex + 3 );
}

void ExistenceQuery::affects( const Gaffer::Plug* const input, AffectedPlugsContainer& outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		( input == locationPlug() ) ||
		( input == scenePlug()->existsPlug() ) )
	{
		outputs.push_back( existsPlug() );
		outputs.push_back( closestAncestorPlug() );
	}
}

void ExistenceQuery::hash( const Gaffer::ValuePlug* const output, const Gaffer::Context* const context, IECore::MurmurHash& h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == existsPlug() )
	{
		const std::string loc = locationPlug()->getValue();

		if( ! loc.empty() )
		{
			const Gaffer::BoolPlug* const eplug = scenePlug()->existsPlug();

			// NOTE : scene exists plug returns true by default when there is no input scene. See issue #4245

			if( eplug->getInput() )
			{
				const ScenePlug::ScenePath path = ScenePlug::stringToPath( loc );
				const ScenePlug::PathScope scope( context, & path );
				h = eplug->hash();
			}
		}
	}
	else if( output == closestAncestorPlug() )
	{
		const std::string loc = locationPlug()->getValue();

		if( ! loc.empty() )
		{
			const Gaffer::BoolPlug* const eplug = scenePlug()->existsPlug();

			// NOTE : scene exists plug returns true by default when there is no input scene. See issue #4245

			if( eplug->getInput() )
			{
				ScenePlug::ScenePath path = ScenePlug::stringToPath( loc );
				ScenePlug::PathScope scope( context );

				while ( ! path.empty() )
				{
					scope.setPath( & path );

					if( eplug->getValue() )
					{
						break;
					}

					path.pop_back();
				}

				h.append( path.data(), path.size() );
				// `append( path )` is a no-op if path is empty, so we must append
				// `size` to distinguish between this and the `loc.empty()` case.
				h.append( (uint64_t)path.size() );
			}
			else
			{
				h.append( "/" );
			}
		}
	}
}

void ExistenceQuery::compute( Gaffer::ValuePlug* const output, const Gaffer::Context* const context ) const
{
	if( output == existsPlug() )
	{
		bool exists = false;

		const std::string loc = locationPlug()->getValue();

		if( ! loc.empty() )
		{
			const Gaffer::BoolPlug* const eplug = scenePlug()->existsPlug();

			// NOTE : scene exists plug returns true by default when there is no input scene. See issue #4245

			if( eplug->getInput() )
			{
				const ScenePlug::ScenePath path = ScenePlug::stringToPath( loc );
				ScenePlug::PathScope scope( context, & path );
				exists = eplug->getValue();
			}
		}

		IECore::assertedStaticCast< Gaffer::BoolPlug >( output )->setValue( exists );
	}
	else if( output == closestAncestorPlug() )
	{
		std::string loc = locationPlug()->getValue();

		if( ! loc.empty() )
		{
			const Gaffer::BoolPlug* const eplug = scenePlug()->existsPlug();

			// NOTE : scene exists plug returns true by default when there is no input scene. See issue #4245

			if( eplug->getInput() )
			{
				ScenePlug::ScenePath path = ScenePlug::stringToPath( loc );
				ScenePlug::PathScope scope( context );

				while( ! path.empty() )
				{
					scope.setPath( & path );

					if( eplug->getValue() )
					{
						break;
					}

					path.pop_back();
				}

				ScenePlug::pathToString( path, loc );
			}
			else
			{
				loc = "/";
			}
		}

		IECore::assertedStaticCast< Gaffer::StringPlug >( output )->setValue( loc );
	}

	ComputeNode::compute( output, context );
}

} // GafferScene
