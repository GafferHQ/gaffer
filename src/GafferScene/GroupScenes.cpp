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

#include "GafferScene/GroupScenes.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( GroupScenes );

GroupScenes::GroupScenes( const std::string &name )
	:	SceneHierarchyProcessor( name )
{
	addChild( new StringPlug( "name", Plug::In, "group" ) );
}

GroupScenes::~GroupScenes()
{
}

Gaffer::StringPlug *GroupScenes::namePlug()
{
	return getChild<StringPlug>( "name" );
}

const Gaffer::StringPlug *GroupScenes::namePlug() const
{
	return getChild<StringPlug>( "name" );
}

void GroupScenes::affects( const ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	SceneHierarchyProcessor::affects( input, outputs );
	
	if( input == namePlug() || input == inPlug()->childNamesPlug() )
	{
		outputs.push_back( mappingPlug() );
	}
}

void GroupScenes::computeMapping( const Gaffer::Context *context, Mapping &result ) const
{	
	string groupName = namePlug()->getValue();
	if( groupName == "" )
	{
		return;
	}
	
	MappingChildContainer &rootChildren = result["/"];
	rootChildren[groupName] = Child( "", "" );
	
	ConstStringVectorDataPtr childNamesData = inPlug()->childNames( "/" );
	if( !childNamesData )
	{
		return;
	}
	
	const vector<string> &childNames = childNamesData->readable();
	MappingChildContainer &groupChildren = result["/" + groupName];
	for( vector<string>::const_iterator it = childNames.begin(), end = childNames.end(); it != end; it++ )
	{
		groupChildren[*it] = Child( "in", "/" + *it );
	}
	
}
