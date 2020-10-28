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

#ifndef GAFFERSCENE_FILTEREDSCENEPROCESSOR_H
#define GAFFERSCENE_FILTEREDSCENEPROCESSOR_H

#include "GafferScene/Filter.h"
#include "GafferScene/FilterPlug.h"
#include "GafferScene/SceneProcessor.h"

#include <limits>

namespace GafferScene
{

/// The FilteredSceneProcessor provides a base class for limiting the processing of scenes
/// to certain locations using a Filter node.
class GAFFERSCENE_API FilteredSceneProcessor : public SceneProcessor
{

	public :

		FilteredSceneProcessor( const std::string &name=defaultName<FilteredSceneProcessor>(), IECore::PathMatcher::Result filterDefault = IECore::PathMatcher::EveryMatch );
		~FilteredSceneProcessor() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::FilteredSceneProcessor, FilteredSceneProcessorTypeId, SceneProcessor );

		FilterPlug *filterPlug();
		const FilterPlug *filterPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		/// Constructs with an ArrayPlug called "in". Use inPlug() as a
		/// convenience for accessing the first child in the array, and use
		/// inPlugs() to access the array itself.
		FilteredSceneProcessor( const std::string &name, size_t minInputs, size_t maxInputs = std::numeric_limits<size_t>::max() );

		/// Convenience method for appending filterPlug() to a hash. This simply
		/// calls filterPlug()->hash() using a FilterPlug::SceneScope. Note that
		/// if you need to make multiple queries, it is more efficient to make your
		/// own SceneScope and then query the filter directly multiple times.
		void filterHash( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		/// Convenience method for returning the result of filterPlug()->getValue()
		/// cast to the appropriate result type, using a using a FilterPlug::SceneScope.
		/// Note that if you need to make multiple queries, it is more efficient to
		/// make your own SceneScope and then query the filter directly multiple times.
		IECore::PathMatcher::Result filterValue( const Gaffer::Context *context ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( FilteredSceneProcessor )

} // namespace GafferScene

#endif // GAFFERSCENE_FILTEREDSCENEPROCESSOR_H
