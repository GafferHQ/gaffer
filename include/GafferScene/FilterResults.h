//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERSCENE_FILTERRESULTS_H
#define GAFFERSCENE_FILTERRESULTS_H

#include "GafferScene/Export.h"
#include "GafferScene/TypeIds.h"

#include "Gaffer/ComputeNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlug.h"

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( ScenePlug )
IE_CORE_FORWARDDECLARE( FilterPlug )

class GAFFERSCENE_API FilterResults : public Gaffer::ComputeNode
{

	public :

		FilterResults( const std::string &name=defaultName<FilterResults>() );
		~FilterResults() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::FilterResults, FilterResultsTypeId, ComputeNode );

		ScenePlug *scenePlug();
		const ScenePlug *scenePlug() const;

		FilterPlug *filterPlug();
		const FilterPlug *filterPlug() const;

		Gaffer::StringPlug *rootPlug();
		const Gaffer::StringPlug *rootPlug() const;

		Gaffer::PathMatcherDataPlug *outPlug();
		const Gaffer::PathMatcherDataPlug *outPlug() const;

		Gaffer::StringVectorDataPlug *outStringsPlug();
		const Gaffer::StringVectorDataPlug *outStringsPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;
		Gaffer::ValuePlug::CachePolicy hashCachePolicy( const Gaffer::ValuePlug *output ) const override;

	private :

		Gaffer::PathMatcherDataPlug *internalOutPlug();
		const Gaffer::PathMatcherDataPlug *internalOutPlug() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( FilterResults )

} // namespace GafferScene

#endif // GAFFERSCENE_FILTERRESULTS_H
