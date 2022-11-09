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

#include "GafferSceneUI/ContextAlgo.h"

#include "GafferScene/ScenePlug.h"
#include "GafferScene/VisibleSet.h"
#include "GafferScene/VisibleSetData.h"

#include "Gaffer/Context.h"

#include "IECore/VectorTypedData.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

InternedString g_selectedPathsName( "ui:scene:selectedPaths" );
InternedString g_lastSelectedPathName( "ui:scene:lastSelectedPath" );
InternedString g_visibleSetName( "ui:scene:visibleSet" );

bool expandWalk( const ScenePlug::ScenePath &path, const ScenePlug *scene, size_t depth, PathMatcher &expanded, PathMatcher &leafPaths )
{
	bool result = false;

	ConstInternedStringVectorDataPtr childNamesData = scene->childNames( path );
	const std::vector<InternedString> &childNames = childNamesData->readable();

	if( childNames.size() )
	{
		result |= expanded.addPath( path );

		ScenePlug::ScenePath childPath = path;
		childPath.push_back( InternedString() ); // room for the child name
		for( std::vector<InternedString>::const_iterator cIt = childNames.begin(), ceIt = childNames.end(); cIt != ceIt; cIt++ )
		{
			childPath.back() = *cIt;
			if( depth == 1 )
			{
				// at the bottom of the expansion - consider the child a leaf
				result |= leafPaths.addPath( childPath );
			}
			else
			{
				// continue the expansion
				result |= expandWalk( childPath, scene, depth - 1, expanded, leafPaths );
			}
		}
	}
	else
	{
		// we have no children, just mark the leaf of the expansion.
		result |= leafPaths.addPath( path );
	}

	return result;
}

} // namespace

namespace GafferSceneUI
{

namespace ContextAlgo
{

void setVisibleSet( Context *context, const GafferScene::VisibleSet &visibleSet )
{
	context->set( g_visibleSetName, visibleSet );
}

GafferScene::VisibleSet getVisibleSet( const Gaffer::Context *context )
{
	return context->get<VisibleSet>( g_visibleSetName, VisibleSet() );
}

bool affectsVisibleSet( const IECore::InternedString &name )
{
	return name == g_visibleSetName;
}

void setExpandedPaths( Context *context, const IECore::PathMatcher &paths )
{
	auto visibleSet = getVisibleSet( context );
	visibleSet.expansions = paths;
	setVisibleSet( context, visibleSet );
}

IECore::PathMatcher getExpandedPaths( const Gaffer::Context *context )
{
	auto visibleSet = getVisibleSet( context );
	return visibleSet.expansions;
}

bool affectsExpandedPaths( const IECore::InternedString &name )
{
	return name == g_visibleSetName;
}

void expand( Context *context, const PathMatcher &paths, bool expandAncestors )
{
	const auto *visibleSet = context->getIfExists<VisibleSet>( g_visibleSetName );
	if( !visibleSet )
	{
		setVisibleSet( context, VisibleSet() );
		visibleSet = context->getIfExists<VisibleSet>( g_visibleSetName );
	}
	VisibleSet &visible = *const_cast<VisibleSet*>(visibleSet);

	bool needUpdate = false;
	if( expandAncestors )
	{
		for( IECore::PathMatcher::RawIterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
		{
			needUpdate |= visible.expansions.addPath( *it );
		}
	}
	else
	{
		for( IECore::PathMatcher::Iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
		{
			needUpdate |= visible.expansions.addPath( *it );
		}
	}

	if( needUpdate )
	{
		// We modified the expanded paths in place with const_cast to avoid unecessary copying,
		// so the context doesn't know they've changed. So we must let it know
		// about the change.
		setVisibleSet( context, *visibleSet );
	}
}

IECore::PathMatcher expandDescendants( Context *context, const IECore::PathMatcher &paths, const ScenePlug *scene, int depth )
{
	auto visibleSet = getVisibleSet( context );

	bool needUpdate = false;
	IECore::PathMatcher leafPaths;

	// \todo: parallelize the walk
	for( IECore::PathMatcher::Iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
	{
		needUpdate |= expandWalk( *it, scene, depth + 1, visibleSet.expansions, leafPaths );
	}

	if( needUpdate )
	{
		// If we modified the expanded paths, we need to set the value back on the context
		setVisibleSet( context, visibleSet );
	}

	return leafPaths;
}

void clearExpansion( Gaffer::Context *context )
{
	setExpandedPaths( context, IECore::PathMatcher() );
}

void setSelectedPaths( Context *context, const IECore::PathMatcher &paths )
{
	context->set( g_selectedPathsName, paths );

	if( paths.isEmpty() )
	{
		context->remove( g_lastSelectedPathName );
	}
	else
	{
		std::vector<IECore::InternedString> lastSelectedPath = getLastSelectedPath( context );
		if( !(paths.match( lastSelectedPath ) & PathMatcher::ExactMatch) )
		{
			const PathMatcher::Iterator it = paths.begin();
			context->set( g_lastSelectedPathName, *it );
		}
	}
}

IECore::PathMatcher getSelectedPaths( const Gaffer::Context *context )
{
	return context->get<PathMatcher>( g_selectedPathsName, IECore::PathMatcher() );
}

bool affectsSelectedPaths( const IECore::InternedString &name )
{
	return name == g_selectedPathsName;
}

void setLastSelectedPath( Gaffer::Context *context, const std::vector<IECore::InternedString> &path )
{
	if( path.empty() )
	{
		context->remove( g_lastSelectedPathName );
	}
	else
	{
		PathMatcher selectedPaths = getSelectedPaths( context );
		if( selectedPaths.addPath( path ) )
		{
			context->set( g_selectedPathsName, selectedPaths );
		}
		context->set( g_lastSelectedPathName, path );
	}
}

std::vector<IECore::InternedString> getLastSelectedPath( const Gaffer::Context *context )
{
	return context->get<std::vector<IECore::InternedString>>( g_lastSelectedPathName, {} );
}

bool affectsLastSelectedPath( const IECore::InternedString &name )
{
	return name == g_lastSelectedPathName;
}

} // namespace ContextAlgo

} // namespace GafferSceneUI
