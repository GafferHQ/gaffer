//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/CollectScenes.h"

#include "GafferScene/SceneAlgo.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

class SceneScope : public Context::EditableScope
{

	public :

		SceneScope( const Context *context, const InternedString &rootNameVariable )
			:	EditableScope( context ), m_rootNameVariable( rootNameVariable )
		{
		}

		SceneScope( const Context *context, const InternedString &rootNameVariable, const ScenePlug::ScenePath &downstreamPath, const StringPlug *sourceRootPlug )
			:	EditableScope( context ), m_rootNameVariable( rootNameVariable )
		{
			setScenePath( downstreamPath, sourceRootPlug );
		}

		void setRootName( const InternedString &name )
		{
			set( m_rootNameVariable, name.string() );
		}

		void setScenePath( const ScenePlug::ScenePath &downstreamPath, const StringPlug *sourceRootPlug )
		{
			setRootName( downstreamPath[0] );
			ScenePlug::ScenePath upstreamPath;
			// We evaluate the sourceRootPlug _after_ setting the root name,
			// so that users can use the root name in expressions and
			// substitutions.
			ScenePlug::stringToPath( sourceRootPlug->getValue(), upstreamPath );
			upstreamPath.insert( upstreamPath.end(), downstreamPath.begin() + 1, downstreamPath.end() );
			set( ScenePlug::scenePathContextName, upstreamPath );
		}

	private :

		InternedString m_rootNameVariable;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// CollectScenes
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( CollectScenes );

size_t CollectScenes::g_firstPlugIndex = 0;

CollectScenes::CollectScenes( const std::string &name )
	:	SceneProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringVectorDataPlug( "rootNames", Plug::In, new StringVectorData() ) );
	addChild( new StringPlug( "rootNameVariable", Plug::In, "collect:rootName" ) );
	addChild( new StringPlug( "sourceRoot", Plug::In, "/" ) );

	outPlug()->childBoundsPlug()->setFlags( Plug::AcceptsDependencyCycles, true );
}

CollectScenes::~CollectScenes()
{
}

Gaffer::StringVectorDataPlug *CollectScenes::rootNamesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 0 );
}

const Gaffer::StringVectorDataPlug *CollectScenes::rootNamesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 0 );
}

Gaffer::StringPlug *CollectScenes::rootNameVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *CollectScenes::rootNameVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *CollectScenes::sourceRootPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *CollectScenes::sourceRootPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

void CollectScenes::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );

	const bool affectsSceneScope =
		input == rootNameVariablePlug() ||
		input == sourceRootPlug()
	;

	if(
		input == outPlug()->childBoundsPlug() ||
		affectsSceneScope ||
		input == inPlug()->boundPlug()
	)
	{
		outputs.push_back( outPlug()->boundPlug() );
	}

	if( affectsSceneScope || input == inPlug()->transformPlug() )
	{
		outputs.push_back( outPlug()->transformPlug() );
	}

	if( affectsSceneScope || input == inPlug()->attributesPlug() )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}

	if( affectsSceneScope || input == inPlug()->objectPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}

	if(
		input == rootNamesPlug() ||
		affectsSceneScope ||
		input == inPlug()->existsPlug() ||
		input == inPlug()->childNamesPlug()
	)
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}

	if(
		input == outPlug()->childNamesPlug() ||
		input == rootNameVariablePlug() ||
		input == inPlug()->globalsPlug()
	)
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}

	if(
		input == outPlug()->childNamesPlug() ||
		input == inPlug()->setNamesPlug() ||
		input == rootNameVariablePlug()
	)
	{
		outputs.push_back( outPlug()->setNamesPlug() );
	}

	if(
		input == outPlug()->childNamesPlug() ||
		input == inPlug()->setPlug() ||
		input == sourceRootPlug() ||
		input == rootNameVariablePlug()
	)
	{
		outputs.push_back( outPlug()->setPlug() );
	}
}

void CollectScenes::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 0 )
	{
		h = outPlug()->childBoundsPlug()->hash();
	}
	else
	{
		SceneScope sceneScope( context, rootNameVariablePlug()->getValue(), path, sourceRootPlug() );
		h = inPlug()->boundPlug()->hash();
	}
}

Imath::Box3f CollectScenes::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 0 )
	{
		return outPlug()->childBoundsPlug()->getValue();
	}
	else
	{
		SceneScope sceneScope( context, rootNameVariablePlug()->getValue(), path, sourceRootPlug() );
		return inPlug()->boundPlug()->getValue();
	}
}

void CollectScenes::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 0 )
	{
		SceneProcessor::hashTransform( path, context, parent, h );
	}
	else
	{
		SceneScope sceneScope( context, rootNameVariablePlug()->getValue(), path, sourceRootPlug() );
		h = inPlug()->transformPlug()->hash();
	}
}

Imath::M44f CollectScenes::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 0 )
	{
		return M44f();
	}
	else
	{
		SceneScope sceneScope( context, rootNameVariablePlug()->getValue(), path, sourceRootPlug() );
		return inPlug()->transformPlug()->getValue();
	}
}

void CollectScenes::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 0 )
	{
		SceneProcessor::hashAttributes( path, context, parent, h );
	}
	else
	{
		SceneScope sceneScope( context, rootNameVariablePlug()->getValue(), path, sourceRootPlug() );
		h = inPlug()->attributesPlug()->hash();
	}
}

IECore::ConstCompoundObjectPtr CollectScenes::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 0 )
	{
		return outPlug()->attributesPlug()->defaultValue();
	}
	else
	{
		SceneScope sceneScope( context, rootNameVariablePlug()->getValue(), path, sourceRootPlug() );
		return inPlug()->attributesPlug()->getValue();
	}
}

void CollectScenes::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 0 )
	{
		SceneProcessor::hashObject( path, context, parent, h );
	}
	else
	{
		SceneScope sceneScope( context, rootNameVariablePlug()->getValue(), path, sourceRootPlug() );
		h = inPlug()->objectPlug()->hash();
	}
}

IECore::ConstObjectPtr CollectScenes::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 0 )
	{
		return outPlug()->objectPlug()->defaultValue();
	}
	else
	{
		SceneScope sceneScope( context, rootNameVariablePlug()->getValue(), path, sourceRootPlug() );
		return inPlug()->objectPlug()->getValue();
	}
}

void CollectScenes::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 0 )
	{
		SceneProcessor::hashChildNames( path, context, parent, h );
		rootNamesPlug()->hash( h );
	}
	else
	{
		SceneScope sceneScope( context, rootNameVariablePlug()->getValue(), path, sourceRootPlug() );
		if( path.size() == 1 )
		{
			const auto &upstreamPath = Context::current()->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
			if( !inPlug()->exists( upstreamPath ) )
			{
				h = inPlug()->childNamesPlug()->defaultValue()->Object::hash();
				return;
			}
		}
		h = inPlug()->childNamesPlug()->hash();
	}
}

IECore::ConstInternedStringVectorDataPtr CollectScenes::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 0 )
	{
		ConstStringVectorDataPtr rootNamesData = rootNamesPlug()->getValue();
		const vector<string> &rootNames = rootNamesData->readable();

		InternedStringVectorDataPtr childNamesData = new InternedStringVectorData;
		vector<InternedString> &childNames = childNamesData->writable();

		for( vector<string>::const_iterator it = rootNames.begin(), eIt = rootNames.end(); it != eIt; ++it )
		{
			if( it->empty() )
			{
				continue;
			}
			InternedString childName( *it );
			if( find( childNames.begin(), childNames.end(), childName ) == childNames.end() )
			{
				childNames.push_back( childName );
			}
		}

		return childNamesData;
	}
	else
	{
		SceneScope sceneScope( context, rootNameVariablePlug()->getValue(), path, sourceRootPlug() );
		if( path.size() == 1 )
		{
			const auto &upstreamPath = Context::current()->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
			if( !inPlug()->exists( upstreamPath ) )
			{
				return inPlug()->childNamesPlug()->defaultValue();
			}
		}
		return inPlug()->childNamesPlug()->getValue();
	}
}

void CollectScenes::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstInternedStringVectorDataPtr rootNamesData = outPlug()->childNames( ScenePath() );
	const vector<InternedString> &rootNames = rootNamesData->readable();
	if( rootNames.size() )
	{
		SceneScope sceneScope( context, rootNameVariablePlug()->getValue() );
		sceneScope.setRootName( rootNames[0] );
		h = inPlug()->globalsPlug()->hash();
	}
	else
	{
		h = inPlug()->globalsPlug()->defaultValue()->Object::hash();
	}
}

IECore::ConstCompoundObjectPtr CollectScenes::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstInternedStringVectorDataPtr rootNamesData = outPlug()->childNames( ScenePath() );
	const vector<InternedString> &rootNames = rootNamesData->readable();
	if( rootNames.size() )
	{
		SceneScope sceneScope( context, rootNameVariablePlug()->getValue() );
		sceneScope.setRootName( rootNames[0] );
		return inPlug()->globalsPlug()->getValue();
	}
	else
	{
		return inPlug()->globalsPlug()->defaultValue();
	}
}

void CollectScenes::hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashSetNames( context, parent, h );

	ConstInternedStringVectorDataPtr rootNamesData = outPlug()->childNames( ScenePath() );
	const vector<InternedString> &rootNames = rootNamesData->readable();

	const ValuePlug *inSetNamesPlug = inPlug()->setNamesPlug();

	SceneScope sceneScope( context, rootNameVariablePlug()->getValue() );
	for( vector<InternedString>::const_iterator it = rootNames.begin(), eIt = rootNames.end(); it != eIt; ++it )
	{
		sceneScope.setRootName( *it );
		inSetNamesPlug->hash( h );
	}
}

IECore::ConstInternedStringVectorDataPtr CollectScenes::computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstInternedStringVectorDataPtr rootNamesData = outPlug()->childNames( ScenePath() );
	const vector<InternedString> &rootNames = rootNamesData->readable();

	InternedStringVectorDataPtr setNamesData = new InternedStringVectorData;
	vector<InternedString> &setNames = setNamesData->writable();

	const InternedStringVectorDataPlug *inSetNamesPlug = inPlug()->setNamesPlug();

	SceneScope sceneScope( context, rootNameVariablePlug()->getValue() );
	for( vector<InternedString>::const_iterator it = rootNames.begin(), eIt = rootNames.end(); it != eIt; ++it )
	{
		sceneScope.setRootName( *it );
		ConstInternedStringVectorDataPtr inSetNamesData = inSetNamesPlug->getValue();
		const vector<InternedString> &inSetNames = inSetNamesData->readable();
		for( vector<InternedString>::const_iterator sIt = inSetNames.begin(), sEIt = inSetNames.end(); sIt != sEIt; ++sIt )
		{
			if( find( setNames.begin(), setNames.end(), *sIt ) == setNames.end() )
			{
				setNames.push_back( *sIt );
			}
		}
	}

	return setNamesData;
}

void CollectScenes::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashSet( setName, context, parent, h );

	ConstInternedStringVectorDataPtr rootNamesData = outPlug()->childNames( ScenePath() );
	const vector<InternedString> &rootNames = rootNamesData->readable();

	const PathMatcherDataPlug *inSetPlug = inPlug()->setPlug();
	const StringPlug *sourceRootPlug = this->sourceRootPlug();

	SceneScope sceneScope( context, rootNameVariablePlug()->getValue() );
	for( vector<InternedString>::const_iterator it = rootNames.begin(), eIt = rootNames.end(); it != eIt; ++it )
	{
		sceneScope.setRootName( *it );
		inSetPlug->hash( h );
		sourceRootPlug->hash( h );
		h.append( *it );
	}
}

IECore::ConstPathMatcherDataPtr CollectScenes::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	PathMatcherDataPtr setData = new PathMatcherData;
	PathMatcher &set = setData->writable();

	ConstInternedStringVectorDataPtr rootNamesData = outPlug()->childNames( ScenePath() );
	const vector<InternedString> &rootNames = rootNamesData->readable();

	const PathMatcherDataPlug *inSetPlug = inPlug()->setPlug();
	const StringPlug *sourceRootPlug = this->sourceRootPlug();

	SceneScope sceneScope( context, rootNameVariablePlug()->getValue() );
	vector<InternedString> prefix( 1 );
	for( vector<InternedString>::const_iterator it = rootNames.begin(), eIt = rootNames.end(); it != eIt; ++it )
	{
		sceneScope.setRootName( *it );
		ConstPathMatcherDataPtr inSetData = inSetPlug->getValue();
		const PathMatcher &inSet = inSetData->readable();
		if( !inSet.isEmpty() )
		{
			prefix[0] = *it;
			const string root = sourceRootPlug->getValue();
			if( !root.empty() )
			{
				set.addPaths( inSet.subTree( root ), prefix );
			}
			else
			{
				set.addPaths( inSet, prefix );
			}
		}
	}

	return setData;
}

