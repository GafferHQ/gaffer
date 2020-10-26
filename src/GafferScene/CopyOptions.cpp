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

#include "GafferScene/CopyOptions.h"

#include "IECore/StringAlgo.h"

#include "boost/algorithm/string/predicate.hpp"

using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( CopyOptions );

size_t CopyOptions::g_firstPlugIndex = 0;

CopyOptions::CopyOptions( const std::string &name )
	:	GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "source", Plug::In ) );
	addChild( new StringPlug( "options" , Plug::In, "" ) );

	// Fast pass-throughs for things we don't modify
	outPlug()->childNamesPlug()->setInput( inPlug()->childNamesPlug() );
	outPlug()->objectPlug()->setInput( inPlug()->objectPlug() );
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
	outPlug()->setPlug()->setInput( inPlug()->setPlug() );
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
}

CopyOptions::~CopyOptions()
{
}

GafferScene::ScenePlug *CopyOptions::sourcePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const GafferScene::ScenePlug *CopyOptions::sourcePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *CopyOptions::optionsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *CopyOptions::optionsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

void CopyOptions::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if( input == sourcePlug()->globalsPlug() || input == optionsPlug() )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void CopyOptions::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	sourcePlug()->globalsPlug()->hash( h );
	optionsPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr CopyOptions::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{

	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	// Since we're not going to modify any existing members (only add new ones),
	// and our result becomes const on returning it, we can directly reference
	// the input members in our result without copying. Be careful not to modify
	// them though!
	result->members() = inputGlobals->members();

	// copy matching options
	const std::string prefix = "option:";
	const std::string names = optionsPlug()->getValue();

	IECore::ConstCompoundObjectPtr sourceGlobals = sourcePlug()->globalsPlug()->getValue();
	for( IECore::CompoundObject::ObjectMap::const_iterator it = sourceGlobals->members().begin(), eIt = sourceGlobals->members().end(); it != eIt; ++it )
	{
		if( boost::starts_with( it->first.c_str(), prefix ) )
		{
			if( IECore::StringAlgo::matchMultiple( it->first.c_str() + prefix.size(), names.c_str() ) )
			{
				result->members()[it->first] = it->second;
			}
		}
	}

	return result;
}
