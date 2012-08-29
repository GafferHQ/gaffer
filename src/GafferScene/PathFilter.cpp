//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferScene/PathFilter.h"

using namespace GafferScene;
using namespace Gaffer;
using namespace IECore;
using namespace std;

IE_CORE_DEFINERUNTIMETYPED( PathFilter );

size_t PathFilter::g_firstPlugIndex = 0;

PathFilter::PathFilter( const std::string &name )
	:	Filter( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringVectorDataPlug( "paths", Plug::In, 0, Plug::Default ) );
}

PathFilter::~PathFilter()
{
}

Gaffer::StringVectorDataPlug *PathFilter::pathsPlug()
{
	return getChild<Gaffer::StringVectorDataPlug>( g_firstPlugIndex );
}

const Gaffer::StringVectorDataPlug *PathFilter::pathsPlug() const
{
	return getChild<Gaffer::StringVectorDataPlug>( g_firstPlugIndex );
}

void PathFilter::affects( const Gaffer::ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	if( input == pathsPlug() )
	{
		outputs.push_back( matchPlug() );
	}
}

void PathFilter::hashMatch( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( context->get<string>( "scene:path" ) );
	pathsPlug()->hash( h );
}

Filter::Result PathFilter::computeMatch( const Gaffer::Context *context ) const
{
	ConstStringVectorDataPtr paths = pathsPlug()->getValue();
	if( !paths )
	{
		return NoMatch;
	}
	
	string path = context->get<string>( "scene:path" );
	Result result = NoMatch;
	for( vector<string>::const_iterator it = paths->readable().begin(), eIt = paths->readable().end(); it != eIt; it++ )
	{
		if( it->compare( 0, path.size(), path ) == 0 )
		{
			if( it->size() == path.size() )
			{
				return Match;
			}
			else if( it->size() > path.size() && (*it)[path.size()] == '/' )
			{
				// don't return yet, because we're holding out for a full match
				result = DescendantMatch;
			}
		}
	}
	return result;
}
