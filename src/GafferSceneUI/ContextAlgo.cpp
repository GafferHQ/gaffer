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

#include "IECore/VectorTypedData.h"

#include "Gaffer/Context.h"

#include "GafferScene/ScenePlug.h"

#include "GafferSceneUI/ContextAlgo.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

InternedString g_expandedPathsName( "ui:scene:expandedPaths" );
InternedString g_selectedPathsName( "ui:scene:selectedPaths" );

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

void setExpandedPaths( Context *context, const IECore::PathMatcher &paths )
{
	context->set( g_expandedPathsName, new IECore::PathMatcherData( paths ) );
}

IECore::PathMatcher getExpandedPaths( const Gaffer::Context *context )
{
	if( const IECore::PathMatcherData *expandedPaths = context->get<IECore::PathMatcherData>( g_expandedPathsName, nullptr ) )
	{
		return expandedPaths->readable();
	}

	return IECore::PathMatcher();
}

void expand( Context *context, const PathMatcher &paths, bool expandAncestors )
{
	IECore::PathMatcherData *expandedPaths = const_cast<IECore::PathMatcherData *>( context->get<IECore::PathMatcherData>( g_expandedPathsName, nullptr ) );
	if( !expandedPaths )
	{
		expandedPaths = new IECore::PathMatcherData();
		context->set( g_expandedPathsName, expandedPaths );
	}

	IECore::PathMatcher &expanded = expandedPaths->writable();

	bool needUpdate = false;
	if( expandAncestors )
	{
		for( IECore::PathMatcher::RawIterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
		{
			needUpdate |= expanded.addPath( *it );
		}
	}
	else
	{
		for( IECore::PathMatcher::Iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
		{
			needUpdate |= expanded.addPath( *it );
		}
	}

	if( needUpdate )
	{
		// We modified the expanded paths in place to avoid unecessary copying,
		// so the context doesn't know they've changed. So we emit the changed
		// signal ourselves
		context->changedSignal()( context, g_expandedPathsName );
	}
}

IECore::PathMatcher expandDescendants( Context *context, const IECore::PathMatcher &paths, const ScenePlug *scene, int depth )
{
	IECore::PathMatcherData *expandedPaths = const_cast<IECore::PathMatcherData *>( context->get<IECore::PathMatcherData>( g_expandedPathsName, nullptr ) );
	if( !expandedPaths )
	{
		expandedPaths = new IECore::PathMatcherData();
		context->set( g_expandedPathsName, expandedPaths );
	}

	IECore::PathMatcher &expanded = expandedPaths->writable();

	bool needUpdate = false;
	IECore::PathMatcher leafPaths;

	// \todo: parallelize the walk
	for( IECore::PathMatcher::Iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
	{
		needUpdate |= expandWalk( *it, scene, depth + 1, expanded, leafPaths );
	}

	if( needUpdate )
	{
		// We modified the expanded paths in place to avoid unecessary copying,
		// so the context doesn't know they've changed. So we emit the changed
		// signal ourselves
		context->changedSignal()( context, g_expandedPathsName );
	}

	return leafPaths;
}

void clearExpansion( Gaffer::Context *context )
{
	setExpandedPaths( context, IECore::PathMatcher() );
}

void setSelectedPaths( Context *context, const IECore::PathMatcher &paths )
{
	/// \todo: Switch to storing PathMatcherData after some thorough
	/// testing and a major version break.
	StringVectorDataPtr s = new StringVectorData;
	paths.paths( s->writable() );

	context->set( g_selectedPathsName, s.get() );
}

IECore::PathMatcher getSelectedPaths( const Gaffer::Context *context )
{
	IECore::PathMatcher result;

	if( const StringVectorData *selection = context->get<StringVectorData>( g_selectedPathsName, nullptr ) )
	{
		const std::vector<std::string> &values = selection->readable();
		result.init( values.begin(), values.end() );
	}

	return result;
}

} // namespace ContextAlgo

} // namespace GafferSceneUI
