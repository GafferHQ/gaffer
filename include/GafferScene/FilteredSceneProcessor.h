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

#include "GafferScene/SceneProcessor.h"
#include "GafferScene/Filter.h"

namespace GafferScene
{

/// The FilteredSceneProcessor provides a base class for limiting the processing of scenes
/// to certain locations using a Filter node.
class FilteredSceneProcessor : public SceneProcessor
{

	public :

		FilteredSceneProcessor( const std::string &name=defaultName<FilteredSceneProcessor>(), Filter::Result filterDefault = Filter::EveryMatch );
		virtual ~FilteredSceneProcessor();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::FilteredSceneProcessor, FilteredSceneProcessorTypeId, SceneProcessor );

		Gaffer::IntPlug *filterPlug();
		const Gaffer::IntPlug *filterPlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		/// Implemented to prevent non-Filter nodes being connected to the filter plug.
		virtual bool acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const;

		/// Convenience method which creates a temporary context for use in
		/// passing the input scene to the filter. Such a context must be current
		/// before calling filterPlug()->hash() or filterPlug()->getValue().
		Gaffer::ContextPtr filterContext( const Gaffer::Context *context ) const;
		/// Convenience method for appending filterPlug() to a hash. This simply
		/// calls filterPlug()->hash() after making filterContext() current. Note that
		/// if you need to make multiple queries, it is more efficient to call filterContext()
		/// yourself once and then query the filter directly multiple times.
		void filterHash( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		/// Convenience method for returning the result of filterPlug()->getValue()
		/// cast to the appropriate result type, using a context created with filterContext().
		/// Note that if you need to make multiple queries, it is more efficient to call
		/// filterContext() yourself once and then query the filter directly multiple times.
		Filter::Result filterValue( const Gaffer::Context *context ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( FilteredSceneProcessor )

} // namespace GafferScene

#endif // GAFFERSCENE_FILTEREDSCENEPROCESSOR_H
