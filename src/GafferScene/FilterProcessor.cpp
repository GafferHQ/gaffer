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

#include "GafferScene/FilterProcessor.h"

#include "GafferScene/ScenePlug.h"

#include "Gaffer/ArrayPlug.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( FilterProcessor );

size_t FilterProcessor::g_firstPlugIndex = 0;

FilterProcessor::FilterProcessor( const std::string &name )
	:	Filter( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( outPlug()->createCounterpart( "in", Plug::In ) );
}

FilterProcessor::FilterProcessor( const std::string &name, size_t minInputs, size_t maxInputs )
	:	Filter( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild(
		new ArrayPlug( "in", Gaffer::Plug::In, outPlug()->createCounterpart( "in0", Plug::In ), minInputs, maxInputs )
	);
}

FilterProcessor::~FilterProcessor()
{
}

FilterPlug *FilterProcessor::inPlug()
{
	GraphComponent *p = getChild( g_firstPlugIndex );
	if( FilterPlug *s = IECore::runTimeCast<FilterPlug>( p ) )
	{
		return s;
	}
	else
	{
		return static_cast<ArrayPlug *>( p )->getChild<FilterPlug>( 0 );
	}
}

const FilterPlug *FilterProcessor::inPlug() const
{
	const GraphComponent *p = getChild( g_firstPlugIndex );
	if( const FilterPlug *s = IECore::runTimeCast<const FilterPlug>( p ) )
	{
		return s;
	}
	else
	{
		return static_cast<const ArrayPlug *>( p )->getChild<FilterPlug>( 0 );
	}
}

Gaffer::ArrayPlug *FilterProcessor::inPlugs()
{
	return getChild<Gaffer::ArrayPlug>( g_firstPlugIndex );
}

const Gaffer::ArrayPlug *FilterProcessor::inPlugs() const
{
	return getChild<Gaffer::ArrayPlug>( g_firstPlugIndex );
}

void FilterProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	Filter::affects( input, outputs );

	if( input->parent<ScenePlug>() )
	{
		if( const ArrayPlug *arrayIn = this->inPlugs() )
		{
			for( FilterPlug::InputIterator it( arrayIn ); !it.done(); ++it )
			{
				(*it)->sceneAffects( input, outputs );
			}
		}
		else
		{
			inPlug()->sceneAffects( input, outputs );
		}
	}
}

Gaffer::Plug *FilterProcessor::correspondingInput( const Gaffer::Plug *output )
{
	if( output == outPlug() )
	{
		return inPlug();
	}
	return Filter::correspondingInput( output );
}

const Gaffer::Plug *FilterProcessor::correspondingInput( const Gaffer::Plug *output ) const
{
	if( output == outPlug() )
	{
		return inPlug();
	}
	return Filter::correspondingInput( output );
}

void FilterProcessor::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == outPlug() && !enabledPlug()->getValue() )
	{
		h = inPlug()->hash();
	}
	else
	{
		Filter::hash( output, context, h );
	}
}

void FilterProcessor::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == outPlug() && !enabledPlug()->getValue() )
	{
		output->setFrom( inPlug() );
	}
	else
	{
		Filter::compute( output, context );
	}
}
