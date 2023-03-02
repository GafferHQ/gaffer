//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferScene/Filter.h"

#include "Gaffer/TypedObjectPlug.h"

namespace GafferScene
{

/// \todo Investigate whether or not caching is actually beneficial for this node
class GAFFERSCENE_API PathFilter : public Filter
{

	public :

		GAFFER_NODE_DECLARE_TYPE( GafferScene::PathFilter, PathFilterTypeId, Filter );

		PathFilter( const std::string &name=defaultName<PathFilter>() );
		~PathFilter() override;

		Gaffer::StringVectorDataPlug *pathsPlug();
		const Gaffer::StringVectorDataPlug *pathsPlug() const;

		FilterPlug *rootsPlug();
		const FilterPlug *rootsPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		void hashMatch( const ScenePlug *scene, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		unsigned computeMatch( const ScenePlug *scene, const Gaffer::Context *context ) const override;

	private :

		// Used to compute a PathMatcher from `pathsPlug()`.
		Gaffer::PathMatcherDataPlug *pathMatcherPlug();
		const Gaffer::PathMatcherDataPlug *pathMatcherPlug() const;

		// Used to compute a list containing the lengths of
		// all the relevant roots matched by `rootsPlug()`.
		// This is computed on a per-location basis, and roots
		// are ordered by length with the shortest appearing first.
		Gaffer::IntVectorDataPlug *rootSizesPlug();
		const Gaffer::IntVectorDataPlug *rootSizesPlug() const;

		void hashRootSizes( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		IECore::ConstIntVectorDataPtr computeRootSizes( const Gaffer::Context *context ) const;

		// Optimisation for when `pathsPlug()` contains a constant
		// value. We can store a constant `m_pathMatcher` instead
		// of needing to compute `pathMatcherPlug()`.
		void plugDirtied( const Gaffer::Plug *plug );
		IECore::PathMatcherDataPtr m_pathMatcher;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( PathFilter )

} // namespace GafferScene
