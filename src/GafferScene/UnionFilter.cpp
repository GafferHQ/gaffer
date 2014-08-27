//////////////////////////////////////////////////////////////////////////
//
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

#include "Gaffer/ArrayPlug.h"

#include "GafferScene/UnionFilter.h"

using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( UnionFilter );

size_t UnionFilter::g_firstPlugIndex = 0;

UnionFilter::UnionFilter( const std::string &name )
	:	Filter( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ArrayPlug(
		"in",
		Plug::In,
		matchPlug()->createCounterpart( "in", Plug::In )
	) );
}

UnionFilter::~UnionFilter()
{
}

Gaffer::ArrayPlug *UnionFilter::inPlug()
{
	return getChild<Gaffer::ArrayPlug>( g_firstPlugIndex );
}

const Gaffer::ArrayPlug *UnionFilter::inPlug() const
{
	return getChild<Gaffer::ArrayPlug>( g_firstPlugIndex );
}

void UnionFilter::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	Filter::affects( input, outputs );

	if( input->parent<ArrayPlug>() == inPlug() )
	{
		outputs.push_back( matchPlug() );
	}
}

bool UnionFilter::sceneAffectsMatch( const ScenePlug *scene, const Gaffer::ValuePlug *child ) const
{
	for( InputIntPlugIterator it( inPlug() ); it != it.end(); ++it )
	{
		const Filter *filter = IECore::runTimeCast<const Filter>( (*it)->source<Plug>()->node() );
		if( filter && filter != this && filter->sceneAffectsMatch( scene, child ) )
		{
			return true;
		}
	}
	return false;
}

bool UnionFilter::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
{
	if( !Filter::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( plug->parent<ArrayPlug>() == inPlug() && inputPlug )
	{
		const Plug *sourcePlug = inputPlug->source<Plug>();
		const Node* sourceNode = sourcePlug->node();
		return sourceNode && sourceNode->isInstanceOf( Filter::staticTypeId() );
	}

	return true;
}

void UnionFilter::hashMatch( const ScenePlug *scene, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	for( InputIntPlugIterator it( inPlug() ); it != it.end(); ++it )
	{
		(*it)->hash( h );
	}
}

unsigned UnionFilter::computeMatch( const ScenePlug *scene, const Gaffer::Context *context ) const
{
	unsigned result = NoMatch;
	for( InputIntPlugIterator it( inPlug() ); it != it.end(); ++it )
	{
		result |= (*it)->getValue();
	}
	return result;
}

