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

#include "GafferScene/DeleteAttributes.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( DeleteAttributes );

size_t DeleteAttributes::g_firstPlugIndex = 0;

DeleteAttributes::DeleteAttributes( const std::string &name )
	:	FilteredSceneProcessor( name, IECore::PathMatcher::EveryMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "names" ) );
	addChild( new BoolPlug( "invertNames" ) );

	// Fast pass-throughs for things we don't modify
	for( auto &p : Plug::Range( *outPlug() ) )
	{
		if( p != outPlug()->attributesPlug() )
		{
			p->setInput( inPlug()->getChild<Plug>( p->getName() ) );
		}
	}
}

DeleteAttributes::~DeleteAttributes()
{
}

Gaffer::StringPlug *DeleteAttributes::namesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *DeleteAttributes::namesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *DeleteAttributes::invertNamesPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *DeleteAttributes::invertNamesPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

void DeleteAttributes::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	if(
		input == filterPlug() ||
		input == namesPlug() ||
		input == invertNamesPlug() ||
		input == inPlug()->attributesPlug()
	)
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

DeleteAttributes::Operation DeleteAttributes::operation( const Gaffer::Context *context, std::string &names, bool &invertNames ) const
{
	if( !(filterValue( context ) & PathMatcher::ExactMatch) )
	{
		return Operation::PassThrough;
	}

	names = namesPlug()->getValue();
	invertNames = invertNamesPlug()->getValue();

	if( !invertNames && names.empty() )
	{
		return Operation::PassThrough;
	}
	else if(
		( !invertNames && names == "*" ) ||
		( invertNames && names == "" )
	)
	{
		return Operation::Clear;
	}

	return Operation::Delete;
}

void DeleteAttributes::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	string names;
	bool invertNames;
	switch( operation( context, names, invertNames ) )
	{
		case Operation::PassThrough :
			h = inPlug()->attributesPlug()->hash();
			return;
		case Operation::Clear :
			h = inPlug()->attributesPlug()->defaultHash();
			return;
		case Operation::Delete :
		default :
			FilteredSceneProcessor::hashAttributes( path, context, parent, h );
			h.append( names );
			h.append( invertNames );
			inPlug()->attributesPlug()->hash( h );
			return;
	}
}

IECore::ConstCompoundObjectPtr DeleteAttributes::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	string names;
	bool invertNames;
	switch( operation( context, names, invertNames ) )
	{
		case Operation::PassThrough :
			return inPlug()->attributesPlug()->getValue();
		case Operation::Clear :
			return inPlug()->attributesPlug()->defaultValue();
		case Operation::Delete :
		default : {
			ConstCompoundObjectPtr inputAttributes = inPlug()->attributesPlug()->getValue();
			CompoundObjectPtr result = new CompoundObject;
			for( const auto &a : inputAttributes->members() )
			{
				if( StringAlgo::matchMultiple( a.first, names ) == invertNames )
				{
					result->members().insert( a );
				}
			}
			return result;
		}
	}
}
