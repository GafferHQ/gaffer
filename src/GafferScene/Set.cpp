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
#include "GafferScene/SceneAlgo.h"

using namespace std;
using namespace IECore;
using namespace GafferScene;

static InternedString g_ellipsis( "..." );

IE_CORE_DEFINERUNTIMETYPED( Set );

size_t Set::g_firstPlugIndex = 0;

Set::Set( const std::string &name )
	:	FilteredSceneProcessor( name, Filter::NoMatch )
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
	FilteredSceneProcessor::affects( input, outputs );

	if( pathsPlug() == input || filterPlug() == input )
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

bool Set::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
{
	if( !FilteredSceneProcessor::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( plug == filterPlug() )
	{
		if( const Filter *filter = runTimeCast<const Filter>( inputPlug->source<Gaffer::Plug>()->node() ) )
		{
			if(
				filter->sceneAffectsMatch( inPlug(), inPlug()->boundPlug() ) ||
				filter->sceneAffectsMatch( inPlug(), inPlug()->transformPlug() ) ||
				filter->sceneAffectsMatch( inPlug(), inPlug()->attributesPlug() ) ||
				filter->sceneAffectsMatch( inPlug(), inPlug()->objectPlug() ) ||
				filter->sceneAffectsMatch( inPlug(), inPlug()->childNamesPlug() )
			)
			{
				// We use the filter to compute our set, so the filter can not dependent
				// on the locations within the scene - see equivalent comments in Prune
				// for more details.
				return false;
			}
		}
	}

	return true;
}

void Set::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hash( output, context, h );

	if( output == pathMatcherPlug() )
	{
		pathsPlug()->hash( h );
		if( filterPlug()->getInput<Gaffer::Plug>() )
		{
			// We remove the scene path variable to cause
			// the filter to give us a "global" hash. See
			// equivalent comments in Prune::hashSet() for
			// more details.
			Gaffer::ContextPtr c = filterContext( context );
			c->remove( ScenePlug::scenePathContextName );
			Gaffer::Context::Scope s( c.get() );
			filterPlug()->hash( h );
		}
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
			if( it->empty() )
			{
				continue;
			}
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

		if( filterPlug()->getInput<Gaffer::Plug>() )
		{
			matchingPaths( filterPlug(), inPlug(), pathMatcher );
		}

		static_cast<Gaffer::ObjectPlug *>( output )->setValue( pathMatcherData );
		return;
	}

	FilteredSceneProcessor::compute( output, context );
}

void Set::hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashSetNames( context, parent, h );
	inPlug()->setNamesPlug()->hash( h );
	modePlug()->hash( h );
	namePlug()->hash( h );
}

IECore::ConstInternedStringVectorDataPtr Set::computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstInternedStringVectorDataPtr inNamesData = inPlug()->setNamesPlug()->getValue();

	const std::string &names = namePlug()->getValue();
	if( !names.size() )
	{
		return inNamesData;
	}

	if( modePlug()->getValue() == Remove )
	{
		return inNamesData;
	}

	vector<InternedString> tokenizedNames;
	Gaffer::tokenize( names, ' ', tokenizedNames );

	// specific logic if we have only one item, to avoid the more complex logic of adding two lists together
	if( tokenizedNames.size() == 1 ) {
		const std::vector<InternedString> &inNames = inNamesData->readable();
		if( std::find( inNames.begin(), inNames.end(), tokenizedNames[0] ) != inNames.end() )
		{
			return inNamesData;
		}

		InternedStringVectorDataPtr resultData = inNamesData->copy();
		resultData->writable().push_back( tokenizedNames[0] );
		return resultData;
	}

	// inserting the new names into the vector
	// while making sure we don't have duplicates
	InternedStringVectorDataPtr resultData = inNamesData->copy();

	std::vector<InternedString> &result = resultData->writable();
	result.reserve( result.size() + tokenizedNames.size() );
	std::copy( tokenizedNames.begin(), tokenizedNames.end(), std::back_inserter( result ) );
	std::sort( result.begin(), result.end() );
	std::vector<InternedString>::iterator it;
	it = std::unique( result.begin(), result.end() );
	result.resize( std::distance( result.begin(), it ) );

	return resultData;
}

void Set::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	const std::string allSets = " " + namePlug()->getValue() + " ";
	const std::string setNameToFind = " " + setName.string() + " ";
	if( allSets.find( setNameToFind ) == std::string::npos )
	{
		h = inPlug()->setPlug()->hash();
		return;
	}

	FilteredSceneProcessor::hashSet( setName, context, parent, h );
	inPlug()->setPlug()->hash( h );
	modePlug()->hash( h );
	pathMatcherPlug()->hash( h );
}

GafferScene::ConstPathMatcherDataPtr Set::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	const std::string allSets = " " + namePlug()->getValue() + " ";
	const std::string setNameToFind = " " + setName.string() + " ";
	if( allSets.find( setNameToFind ) == std::string::npos )
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
