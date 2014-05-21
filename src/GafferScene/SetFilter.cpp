//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Context.h"

#include "GafferScene/ScenePlug.h"
#include "GafferScene/PathMatcherData.h"
#include "GafferScene/SetFilter.h"

using namespace GafferScene;
using namespace Gaffer;
using namespace IECore;
using namespace std;

IE_CORE_DEFINERUNTIMETYPED( SetFilter );

size_t SetFilter::g_firstPlugIndex = 0;

SetFilter::SetFilter( const std::string &name )
	:	Filter( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	
	addChild( new StringPlug( "set" ) );	
}

SetFilter::~SetFilter()
{
}

Gaffer::StringPlug *SetFilter::setPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *SetFilter::setPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

void SetFilter::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	Filter::affects( input, outputs );
	
	if( input == setPlug() )
	{
		outputs.push_back( matchPlug() );
	}
}

bool SetFilter::sceneAffectsMatch( const ScenePlug *scene, const Gaffer::ValuePlug *child ) const
{
	if( Filter::sceneAffectsMatch( scene, child ) )
	{
		return true;
	}
	
	return child == scene->globalsPlug();
}

void SetFilter::hashMatch( const ScenePlug *scene, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( !scene )
	{
		return;
	}

	scene->globalsPlug()->hash( h );
	setPlug()->hash( h );
	const ScenePlug::ScenePath &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	h.append( &(path[0]), path.size() );
}

unsigned SetFilter::computeMatch( const ScenePlug *scene, const Gaffer::Context *context ) const
{
	if( !scene )
	{
		return NoMatch;
	}
	
	ConstCompoundObjectPtr globals = scene->globalsPlug()->getValue();
	const CompoundData *sets = globals->member<CompoundData>( "gaffer:sets" );
	if( !sets )
	{
		return NoMatch;
	}

	const PathMatcherData *set = sets->member<PathMatcherData>( setPlug()->getValue() );
	if( !set )
	{
		return NoMatch;
	}
	
	const ScenePlug::ScenePath &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	return set->readable().match( path );
}
