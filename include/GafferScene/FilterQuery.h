//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

#ifndef GAFFERSCENE_FILTERQUERY_H
#define GAFFERSCENE_FILTERQUERY_H

#include "GafferScene/Export.h"
#include "GafferScene/TypeIds.h"

#include "Gaffer/ComputeNode.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlug.h"

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( ScenePlug )
IE_CORE_FORWARDDECLARE( FilterPlug )

class GAFFERSCENE_API FilterQuery : public Gaffer::ComputeNode
{

	public :

		FilterQuery( const std::string &name=defaultName<FilterQuery>() );
		~FilterQuery() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::FilterQuery, FilterQueryTypeId, ComputeNode );

		ScenePlug *scenePlug();
		const ScenePlug *scenePlug() const;

		FilterPlug *filterPlug();
		const FilterPlug *filterPlug() const;

		Gaffer::StringPlug *locationPlug();
		const Gaffer::StringPlug *locationPlug() const;

		Gaffer::BoolPlug *exactMatchPlug();
		const Gaffer::BoolPlug *exactMatchPlug() const;

		Gaffer::BoolPlug *descendantMatchPlug();
		const Gaffer::BoolPlug *descendantMatchPlug() const;

		Gaffer::BoolPlug *ancestorMatchPlug();
		const Gaffer::BoolPlug *ancestorMatchPlug() const;

		Gaffer::StringPlug *closestAncestorPlug();
		const Gaffer::StringPlug *closestAncestorPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		Gaffer::IntPlug *matchPlug();
		const Gaffer::IntPlug *matchPlug() const;

		// Used in the computation of `ancestorMatchPlug()`. This uses
		// `${scene:path}` rather than `locationPlug()` so can be used in
		// recursive computes to inherit results from ancestor contexts.
		Gaffer::StringPlug *closestAncestorInternalPlug();
		const Gaffer::StringPlug *closestAncestorInternalPlug() const;

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;
		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( FilterQuery )

} // namespace GafferScene

#endif // GAFFERSCENE_FILTERQUERY_H
