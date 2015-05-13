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

#include "Gaffer/StringPlug.h"
#include "Gaffer/StringAlgo.h"

#include "GafferScene/Set.h"
#include "GafferScene/PathMatcherData.h"

using namespace std;
using namespace IECore;
using namespace GafferScene;

static InternedString g_ellipsis( "..." );

IE_CORE_DEFINERUNTIMETYPED( Set );

size_t Set::g_firstPlugIndex = 0;

Set::Set( const std::string &name )
	:	SceneProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new Gaffer::IntPlug( "mode", Gaffer::Plug::In, Create, Create, Remove ) );
	addChild( new Gaffer::StringPlug( "name", Gaffer::Plug::In, "set" ) );
	addChild( new Gaffer::StringVectorDataPlug( "paths", Gaffer::Plug::In, new StringVectorData ) );
	addChild( new PathMatcherDataPlug( "__pathMatcher", Gaffer::Plug::Out, new PathMatcherData ) );

	// Direct pass-throughs for the things we don't process
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->objectPlug()->setInput( inPlug()->objectPlug() );
	outPlug()->childNamesPlug()->setInput( inPlug()->childNamesPlug() );
	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
}

Set::~Set()
{
}

Gaffer::IntPlug *Set::modePlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Set::modePlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *Set::namePlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *Set::namePlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringVectorDataPlug *Set::pathsPlug()
{
	return getChild<Gaffer::StringVectorDataPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringVectorDataPlug *Set::pathsPlug() const
{
	return getChild<Gaffer::StringVectorDataPlug>( g_firstPlugIndex + 2 );
}

PathMatcherDataPlug *Set::pathMatcherPlug()
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 3 );
}

const PathMatcherDataPlug *Set::pathMatcherPlug() const
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 3 );
}

void Set::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );

	if( pathsPlug() == input )
	{
		outputs.push_back( pathMatcherPlug() );
	}
	else if( namePlug() == input )
	{
		outputs.push_back( outPlug()->setNamesPlug() );
		outputs.push_back( outPlug()->setPlug() );
	}
	else if(
		modePlug() == input ||
		pathMatcherPlug() == input
	)
	{
		outputs.push_back( outPlug()->setPlug() );
	}
}

void Set::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneProcessor::hash( output, context, h );

	if( output == pathMatcherPlug() )
	{
		pathsPlug()->hash( h );
	}
}

void Set::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == pathMatcherPlug() )
	{
		ConstStringVectorDataPtr pathsData = pathsPlug()->getValue();
		const vector<string> &paths = pathsData->readable();

		PathMatcherDataPtr pathMatcherData = new PathMatcherData;
		PathMatcher &pathMatcher = pathMatcherData->writable();

		vector<InternedString> tokenizedPath;
		for( vector<string>::const_iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
		{
			tokenizedPath.clear();
			Gaffer::tokenize( *it, '/', tokenizedPath );
			for( vector<InternedString>::const_iterator nIt = tokenizedPath.begin(), neIt = tokenizedPath.end(); nIt != neIt; ++nIt )
			{
				if( Gaffer::hasWildcards( nIt->c_str() ) || *nIt == g_ellipsis )
				{
					throw IECore::Exception( "Path \"" + *it + "\" contains wildcards." );
				}
			}
			pathMatcher.addPath( tokenizedPath );
		}

		static_cast<Gaffer::ObjectPlug *>( output )->setValue( pathMatcherData );
		return;
	}

	SceneProcessor::compute( output, context );
}

void Set::hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashSetNames( context, parent, h );
	inPlug()->setNamesPlug()->hash( h );
	modePlug()->hash( h );
	namePlug()->hash( h );
}

IECore::ConstInternedStringVectorDataPtr Set::computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstInternedStringVectorDataPtr inNamesData = inPlug()->setNamesPlug()->getValue();

	InternedString name = namePlug()->getValue();
	if( !name.string().size() )
	{
		return inNamesData;
	}

	const std::vector<InternedString> &inNames = inNamesData->readable();
	if( std::find( inNames.begin(), inNames.end(), name ) != inNames.end() )
	{
		return inNamesData;
	}

	if( modePlug()->getValue() == Remove )
	{
		return inNamesData;
	}

	InternedStringVectorDataPtr result = inNamesData->copy();
	result->writable().push_back( name );
	return result;
}

void Set::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( setName != namePlug()->getValue() )
	{
		h = inPlug()->setPlug()->hash();
		return;
	}

	SceneProcessor::hashSet( setName, context, parent, h );
	inPlug()->setPlug()->hash( h );
	modePlug()->hash( h );
	pathMatcherPlug()->hash( h );
}

GafferScene::ConstPathMatcherDataPtr Set::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( InternedString( namePlug()->getValue() ) != setName )
	{
		return inPlug()->setPlug()->getValue();
	}

	ConstPathMatcherDataPtr pathMatcher = pathMatcherPlug()->getValue();
	switch( modePlug()->getValue() )
	{
		case Add : {
			ConstPathMatcherDataPtr inputSet = inPlug()->setPlug()->getValue();
			if( !inputSet->readable().isEmpty() )
			{
				PathMatcherDataPtr result = inputSet->copy();
				result->writable().addPaths( pathMatcher->readable() );
				return result;
			}
			// Input set empty - fall through to create mode.
		}
		case Create : {
			return pathMatcher;
		}
		case Remove :
		default : {
			ConstPathMatcherDataPtr inputSet = inPlug()->setPlug()->getValue();
			if( inputSet->readable().isEmpty() )
			{
				return inputSet;
			}
			PathMatcherDataPtr result = inputSet->copy();
			result->writable().removePaths( pathMatcher->readable() );
			return result;
		}
	}
}
