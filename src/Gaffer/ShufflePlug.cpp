//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/ShufflePlug.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// ShufflePlug
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( ShufflePlug );

ShufflePlug::ShufflePlug( const std::string &source, const std::string &destination, bool deleteSource, bool enabled )
	: ShufflePlug( "shuffle", In, Default | Dynamic )
{
	sourcePlug()->setValue( source );
	destinationPlug()->setValue( destination );
	deleteSourcePlug()->setValue( deleteSource );
	enabledPlug()->setValue( enabled );
}

/// Primarily used for serialisation.
ShufflePlug::ShufflePlug( const std::string &name, Direction direction, unsigned flags )
	: ValuePlug( name, direction, flags )
{
	addChild( new StringPlug( "source", direction ) );
	addChild( new BoolPlug( "enabled", direction, true ) );
	// Disable substitutions on the destination since we'll be performing our own substitution
	// during `ShufflesPlug::shuffle()`, in order to account for the ${source} variable.
	addChild( new StringPlug( "destination", direction, "", Plug::Default, IECore::StringAlgo::NoSubstitutions ) );
	addChild( new BoolPlug( "deleteSource", direction ) );
	addChild( new BoolPlug( "replaceDestination", direction, true ) );
}

Gaffer::StringPlug *ShufflePlug::sourcePlug()
{
	return getChild<StringPlug>( 0 );
}

const Gaffer::StringPlug *ShufflePlug::sourcePlug() const
{
	return getChild<StringPlug>( 0 );
}

Gaffer::BoolPlug *ShufflePlug::enabledPlug()
{
	return getChild<BoolPlug>( 1 );
}

const Gaffer::BoolPlug *ShufflePlug::enabledPlug() const
{
	return getChild<BoolPlug>( 1 );
}

Gaffer::StringPlug *ShufflePlug::destinationPlug()
{
	return getChild<StringPlug>( 2 );
}

const Gaffer::StringPlug *ShufflePlug::destinationPlug() const
{
	return getChild<StringPlug>( 2 );
}

Gaffer::BoolPlug *ShufflePlug::deleteSourcePlug()
{
	return getChild<BoolPlug>( 3 );
}

const Gaffer::BoolPlug *ShufflePlug::deleteSourcePlug() const
{
	return getChild<BoolPlug>( 3 );
}

Gaffer::BoolPlug *ShufflePlug::replaceDestinationPlug()
{
	return getChild<BoolPlug>( 4 );
}

const Gaffer::BoolPlug *ShufflePlug::replaceDestinationPlug() const
{
	return getChild<BoolPlug>( 4 );
}

bool ShufflePlug::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	if( !Plug::acceptsChild( potentialChild ) )
	{
		return false;
	}

	if(
		potentialChild->isInstanceOf( StringPlug::staticTypeId() ) &&
		potentialChild->getName() == "source" &&
		!getChild<Plug>( "source" )
	)
	{
		return true;
	}
	else if(
		potentialChild->isInstanceOf( BoolPlug::staticTypeId() ) &&
		potentialChild->getName() == "enabled" &&
		!getChild<Plug>( "enabled" )
	)
	{
		return true;
	}
	else if(
		potentialChild->isInstanceOf( StringPlug::staticTypeId() ) &&
		potentialChild->getName() == "destination" &&
		!getChild<Plug>( "destination" )
	)
	{
		return true;
	}
	else if(
		potentialChild->isInstanceOf( BoolPlug::staticTypeId() ) &&
		potentialChild->getName() == "deleteSource" &&
		!getChild<Plug>( "deleteSource" )
	)
	{
		return true;
	}
	else if(
		potentialChild->isInstanceOf( BoolPlug::staticTypeId() ) &&
		potentialChild->getName() == "replaceDestination" &&
		!getChild<Plug>( "replaceDestination" )
	)
	{
		return true;
	}

	return false;
}

Gaffer::PlugPtr ShufflePlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new ShufflePlug( name, direction, getFlags() );
}

//////////////////////////////////////////////////////////////////////////
// ShufflesPlug
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( ShufflesPlug );

ShufflesPlug::ShufflesPlug( const std::string &name, Direction direction, unsigned flags ) : ValuePlug( name, direction, flags )
{
}

bool ShufflesPlug::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	if( !ValuePlug::acceptsChild( potentialChild ) )
	{
		return false;
	}

	return runTimeCast<const ShufflePlug>( potentialChild );
}

bool ShufflesPlug::acceptsInput( const Plug *input ) const
{
	if( !ValuePlug::acceptsChild( input ) )
	{
		return false;
	}

	if( !input )
	{
		return true;
	}

	return runTimeCast<const ShufflesPlug>( input );
}

Gaffer::PlugPtr ShufflesPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	PlugPtr result = new ShufflesPlug( name, direction, getFlags() );
	for( Plug::Iterator it( this ); !it.done(); ++it )
	{
		result->addChild( (*it)->createCounterpart( (*it)->getName(), direction ) );
	}
	return result;
}
