//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#pragma once

#include "IECore/PathMatcher.h"

namespace
{

bool allAncestorsMatch( const std::vector<InternedString> &path, const IECore::PathMatcher &pathMatcher, const size_t minimumExpansionDepth )
{
	std::vector<InternedString> parentPath = path;
	while( parentPath.size() > minimumExpansionDepth + 1 )
	{
		parentPath.pop_back();
		if( !( pathMatcher.match( parentPath ) & PathMatcher::ExactMatch ) )
		{
			return false;
		}
	}
	return true;
}

} // namespace

namespace GafferScene
{

inline VisibleSet::Visibility VisibleSet::visibility( const std::vector<InternedString> &path, const size_t minimumExpansionDepth ) const
{

	const unsigned exclusionsMatch = exclusions.match( path );
	if( exclusionsMatch & PathMatcher::ExactMatch && allAncestorsMatch( path, expansions, minimumExpansionDepth ) )
	{
		// If all ancestors are expanded then we consider the bounds of this excluded path to be visible,
		// but none of its descendants to be
		return VisibleSet::Visibility( VisibleSet::Visibility::ExcludedBounds, false );
	}
	else if( exclusionsMatch & ( PathMatcher::ExactMatch | PathMatcher::AncestorMatch ) )
	{
		// This path and its descendants are not visible as it or an ancestor are in `exclusions`
		return VisibleSet::Visibility( VisibleSet::Visibility::None, false );
	}

	if( minimumExpansionDepth >= path.size() )
	{
		// Paths within minimumExpansionDepth are visible and have visible children
		return VisibleSet::Visibility( VisibleSet::Visibility::Visible, true );
	}

	const unsigned inclusionsMatch = inclusions.match( path );
	if( inclusionsMatch & ( PathMatcher::ExactMatch | PathMatcher::AncestorMatch ) )
	{
		// This path and its descendants are visible as it or an ancestor are in `inclusions`
		return VisibleSet::Visibility( VisibleSet::Visibility::Visible, true );
	}

	auto result = VisibleSet::Visibility(
		VisibleSet::Visibility::None,
		// Any descendants in `inclusions` are visible
		inclusionsMatch & PathMatcher::DescendantMatch
	);

	if( allAncestorsMatch( path, expansions, minimumExpansionDepth ) )
	{
		// This path is visible as all its ancestors are expanded
		result.drawMode = VisibleSet::Visibility::Visible;
		// If the path is also expanded then it could have visible children
		result.descendantsVisible |= (bool)(expansions.match( path ) & PathMatcher::ExactMatch);
	}

	return result;

}

inline bool VisibleSet::operator == ( const VisibleSet& rhs ) const
{
	return expansions == rhs.expansions && inclusions == rhs.inclusions && exclusions == rhs.exclusions;
}

inline bool VisibleSet::operator != ( const VisibleSet& rhs ) const
{
	return expansions != rhs.expansions || inclusions != rhs.inclusions || exclusions != rhs.exclusions;
}

inline void murmurHashAppend( MurmurHash &h, const VisibleSet &data )
{
	h.append( data.expansions );
	h.append( data.inclusions );
	h.append( data.exclusions );
}

} // namespace GafferScene
