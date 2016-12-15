//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "IECore/SimpleTypedData.h"

#include "Gaffer/GraphComponent.h"
#include "Gaffer/Plug.h"
#include "Gaffer/Node.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"

using namespace std;
using namespace IECore;

namespace
{

InternedString g_readOnlyName( "readOnly" );

size_t findNth( const std::string &s, char c, int n )
{
	size_t result = 0;
	while( n-- && result != string::npos )
	{
		result = s.find( c, result );
	}

	return result;
}

} // namespace

namespace Gaffer
{

namespace MetadataAlgo
{

void setReadOnly( GraphComponent *graphComponent, bool readOnly, bool persistent )
{
	Metadata::registerValue( graphComponent, g_readOnlyName, new BoolData( readOnly ), persistent );
}

bool getReadOnly( const GraphComponent *graphComponent )
{
	ConstBoolDataPtr d = Metadata::value<BoolData>( graphComponent, g_readOnlyName );
	return d ? d->readable() : false;
}

bool readOnly( const GraphComponent *graphComponent )
{
	while( graphComponent )
	{
		if( getReadOnly( graphComponent ) )
		{
			return true;
		}
		graphComponent = graphComponent->parent<GraphComponent>();
	}
	return false;
}

bool affectedByChange( const Plug *plug, IECore::TypeId changedNodeTypeId, const StringAlgo::MatchPattern &changedPlugPath, const Gaffer::Plug *changedPlug )
{
	if( changedPlug )
	{
		return plug == changedPlug;
	}

	const Node *node = plug->node();
	if( !node || !node->isInstanceOf( changedNodeTypeId ) )
	{
		return false;
	}

	if( StringAlgo::match( plug->relativeName( node ), changedPlugPath ) )
	{
		return true;
	}

	return false;
}

bool childAffectedByChange( const GraphComponent *parent, IECore::TypeId changedNodeTypeId, const StringAlgo::MatchPattern &changedPlugPath, const Gaffer::Plug *changedPlug )
{
	if( changedPlug )
	{
		return parent == changedPlug->parent<GraphComponent>();
	}

	const Node *node = runTimeCast<const Node>( parent );
	if( !node )
	{
		node = parent->ancestor<Node>();
	}

	if( !node || !node->isInstanceOf( changedNodeTypeId ) )
	{
		return false;
	}

	if( parent == node )
	{
		return changedPlugPath.find( '.' ) == string::npos;
	}

	const string parentName = parent->relativeName( node );
	const size_t n = count( parentName.begin(), parentName.end(), '.' ) + 1;
	const size_t parentMatchPatternEnd = findNth( changedPlugPath, '.', n );

	if( parentMatchPatternEnd == string::npos )
	{
		return false;
	}

	return StringAlgo::match( parentName, changedPlugPath.substr( 0, parentMatchPatternEnd ) );
}

bool ancestorAffectedByChange( const Plug *plug, IECore::TypeId changedNodeTypeId, const StringAlgo::MatchPattern &changedPlugPath, const Gaffer::Plug *changedPlug )
{
	if( changedPlug )
	{
		return changedPlug->isAncestorOf( plug );
	}

	while( ( plug = plug->parent<Plug>() ) )
	{
		if( affectedByChange( plug, changedNodeTypeId, changedPlugPath, changedPlug ) )
		{
			return true;
		}
	}

	return false;
}

bool affectedByChange( const Node *node, IECore::TypeId changedNodeTypeId, const Gaffer::Node *changedNode )
{
	if( changedNode )
	{
		return node == changedNode;
	}

	return node->isInstanceOf( changedNodeTypeId );
}

} // namespace MetadataAlgo

} // namespace Gaffer
