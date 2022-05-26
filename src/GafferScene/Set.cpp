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

#include "GafferScene/Set.h"

#include "GafferScene/FilterResults.h"

#include "Gaffer/DeleteContextVariables.h"
#include "Gaffer/StringPlug.h"

#include "IECore/StringAlgo.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

struct PathMatcherScope : public ScenePlug::GlobalScope
{

	PathMatcherScope( const Context *context, const string &setVariable, const InternedString &setName )
		:	ScenePlug::GlobalScope( context ), m_setName( setName )
	{
		if( !setVariable.empty() )
		{
			// Storing as `string` rather than `InternedString` to
			// avoid confusion when referring to the variable in
			// upstream expressions.
			set( setVariable, &m_setName.string() );
		}
	}

	private :

		const InternedString m_setName;

};

InternedString g_ellipsis( "..." );

} // namespace

//////////////////////////////////////////////////////////////////////////
// Set implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Set );

size_t Set::g_firstPlugIndex = 0;

Set::Set( const std::string &name )
	:	FilteredSceneProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new Gaffer::IntPlug( "mode", Gaffer::Plug::In, Create, Create, Remove ) );
	addChild( new Gaffer::StringPlug( "name", Gaffer::Plug::In, "set" ) );
	addChild( new Gaffer::StringPlug( "setVariable" ) );
	addChild( new Gaffer::StringVectorDataPlug( "paths", Gaffer::Plug::In, new StringVectorData ) );

	addChild( new PathMatcherDataPlug( "__filterResults", Gaffer::Plug::In, new PathMatcherData, Plug::Default & ~Plug::Serialisable ) );
	addChild( new PathMatcherDataPlug( "__pathMatcher", Gaffer::Plug::Out, new PathMatcherData ) );

	// Internal nodes to drive `filterResultsPlug()`, without leaking `setVariable` to
	// the upstream scene.

	Gaffer::DeleteContextVariablesPtr deleteContextVariables = new Gaffer::DeleteContextVariables( "__DeleteContextVariables" );
	deleteContextVariables->setup( inPlug() );
	deleteContextVariables->inPlug()->setInput( inPlug() );
	deleteContextVariables->enabledPlug()->setInput( setVariablePlug() );
	deleteContextVariables->variablesPlug()->setInput( setVariablePlug() );
	addChild( deleteContextVariables );

	FilterResultsPtr filterResults = new FilterResults( "__FilterResults" );
	addChild( filterResults );

	filterResults->scenePlug()->setInput( deleteContextVariables->outPlug() );
	filterResults->filterPlug()->setInput( filterPlug() );
	filterResultsPlug()->setInput( filterResults->outPlug() );

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

Gaffer::StringPlug *Set::setVariablePlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *Set::setVariablePlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringVectorDataPlug *Set::pathsPlug()
{
	return getChild<Gaffer::StringVectorDataPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringVectorDataPlug *Set::pathsPlug() const
{
	return getChild<Gaffer::StringVectorDataPlug>( g_firstPlugIndex + 3 );
}

Gaffer::PathMatcherDataPlug *Set::filterResultsPlug()
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::PathMatcherDataPlug *Set::filterResultsPlug() const
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 4 );
}

Gaffer::PathMatcherDataPlug *Set::pathMatcherPlug()
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::PathMatcherDataPlug *Set::pathMatcherPlug() const
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 5 );
}

void Set::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	if(
		input == inPlug()->setNamesPlug() ||
		input == modePlug() ||
		input == namePlug()
	)
	{
		outputs.push_back( outPlug()->setNamesPlug() );
	}

	if(
		input == namePlug() ||
		input == setVariablePlug() ||
		input == inPlug()->setPlug() ||
		input == modePlug() ||
		input == pathMatcherPlug()
	)
	{
		outputs.push_back( outPlug()->setPlug() );
	}

	if(
		input == pathsPlug() ||
		input == filterResultsPlug()
	)
	{
		outputs.push_back( pathMatcherPlug() );
	}
}

void Set::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hash( output, context, h );

	if( output == pathMatcherPlug() )
	{
		pathsPlug()->hash( h );
		filterResultsPlug()->hash( h );
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
			StringAlgo::tokenize( *it, '/', tokenizedPath );
			for( vector<InternedString>::const_iterator nIt = tokenizedPath.begin(), neIt = tokenizedPath.end(); nIt != neIt; ++nIt )
			{
				if( StringAlgo::hasWildcards( nIt->c_str() ) || *nIt == g_ellipsis )
				{
					throw IECore::Exception( "Path \"" + *it + "\" contains wildcards." );
				}
			}
			pathMatcher.addPath( tokenizedPath );
		}

		pathMatcher.addPaths( filterResultsPlug()->getValue()->readable() );

		static_cast<PathMatcherDataPlug *>( output )->setValue( pathMatcherData );
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

	const std::string names = namePlug()->getValue();
	if( !names.size() )
	{
		return inNamesData;
	}

	if( modePlug()->getValue() == Remove )
	{
		return inNamesData;
	}

	// Fast path for the common case of a single name.
	const std::vector<InternedString> &inNames = inNamesData->readable();
	if( names.find( ' ' ) == string::npos )
	{
		if( StringAlgo::hasWildcards( names ) || find( inNames.begin(), inNames.end(), names ) != inNames.end() )
		{
			return inNamesData;
		}
		InternedStringVectorDataPtr resultData = inNamesData->copy();
		resultData->writable().push_back( names );
		return resultData;
	}

	// Slow path. Merge names ignoring duplicates and wildcards.

	vector<InternedString> tokenizedNames;
	StringAlgo::tokenize( names, ' ', tokenizedNames );

	InternedStringVectorDataPtr resultData = inNamesData->copy();
	std::vector<InternedString> &result = resultData->writable();
	result.reserve( result.size() + tokenizedNames.size() );
	std::copy_if(
		tokenizedNames.begin(), tokenizedNames.end(), std::back_inserter( result ),
		[] ( const InternedString &s ) {
			return !StringAlgo::hasWildcards( s.string() );
		}
	);

	std::sort( result.begin(), result.end() );
	result.erase( std::unique( result.begin(), result.end() ), result.end() );

	return resultData;
}

void Set::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( !StringAlgo::matchMultiple( setName.string(), namePlug()->getValue() ) )
	{
		h = inPlug()->setPlug()->hash();
		return;
	}

	FilteredSceneProcessor::hashSet( setName, context, parent, h );
	inPlug()->setPlug()->hash( h );

	PathMatcherScope scope( context, setVariablePlug()->getValue(), setName );
	modePlug()->hash( h );
	pathMatcherPlug()->hash( h );
}

IECore::ConstPathMatcherDataPtr Set::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( !StringAlgo::matchMultiple( setName.string(), namePlug()->getValue() ) )
	{
		return inPlug()->setPlug()->getValue();
	}

	Mode mode;
	ConstPathMatcherDataPtr pathMatcher;
	{
		PathMatcherScope scope( context, setVariablePlug()->getValue(), setName );
		mode = static_cast<Mode>( modePlug()->getValue() );
		pathMatcher = pathMatcherPlug()->getValue();
	}

	switch( mode )
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
			[[fallthrough]];
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
