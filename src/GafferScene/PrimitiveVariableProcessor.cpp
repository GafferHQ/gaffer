//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferScene/PrimitiveVariableProcessor.h"

#include "Gaffer/StringPlug.h"

#include "IECore/StringAlgo.h"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( PrimitiveVariableProcessor );

size_t PrimitiveVariableProcessor::g_firstPlugIndex = 0;

PrimitiveVariableProcessor::PrimitiveVariableProcessor( const std::string &name, IECore::PathMatcher::Result filterDefault )
	:	SceneElementProcessor( name, filterDefault )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "names" ) );
	addChild( new BoolPlug( "invertNames" ) );

	// Fast pass-throughs for things we don't modify
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
}

PrimitiveVariableProcessor::~PrimitiveVariableProcessor()
{
}

Gaffer::StringPlug *PrimitiveVariableProcessor::namesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *PrimitiveVariableProcessor::namesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *PrimitiveVariableProcessor::invertNamesPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *PrimitiveVariableProcessor::invertNamesPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

void PrimitiveVariableProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( input == namesPlug() || input == invertNamesPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

bool PrimitiveVariableProcessor::processesObject() const
{
	bool invert = invertNamesPlug()->getValue();
	if( invert )
	{
		// we don't know if we're modifying the object till we find out what
		// variables it has.
		return true;
	}
	else
	{
		// if there are no names, then we know we're not modifying the object.
		std::string names = namesPlug()->getValue();
		return names.size();
	}
}

void PrimitiveVariableProcessor::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	namesPlug()->hash( h );
	invertNamesPlug()->hash( h );
}

IECore::ConstObjectPtr PrimitiveVariableProcessor::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	ConstPrimitivePtr inputGeometry = runTimeCast<const Primitive>( inputObject );
	if( !inputGeometry )
	{
		return inputObject;
	}

	const std::string names = namesPlug()->getValue();

	bool invert = invertNamesPlug()->getValue();
	IECoreScene::PrimitivePtr result = inputGeometry->copy();
	IECoreScene::PrimitiveVariableMap::iterator next;
	for( IECoreScene::PrimitiveVariableMap::iterator it = result->variables.begin(); it != result->variables.end(); it = next )
	{
		next = it;
		next++;
		if( StringAlgo::matchMultiple( it->first, names ) != invert )
		{
			processPrimitiveVariable( path, context, inputGeometry, it->second );
			if( it->second.interpolation == IECoreScene::PrimitiveVariable::Invalid || !it->second.data )
			{
				result->variables.erase( it );
			}
		}
	}

	return result;
}
