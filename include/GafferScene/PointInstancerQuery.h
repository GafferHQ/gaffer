//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//       *Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//       *Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//       *Neither the name of John Haddon nor the names of
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

#include "GafferScene/Export.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/TypeIds.h"

#include "Gaffer/ComputeNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlug.h"

#include "IECoreScene/PointInstancer.h"

namespace GafferScene
{

class GAFFERSCENE_API PointInstancerQuery : public Gaffer::ComputeNode
{

	public :

		explicit PointInstancerQuery( const std::string& name = defaultName<PointInstancerQuery>() );
		~PointInstancerQuery() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::PointInstancerQuery, PointInstancerQueryTypeId, Gaffer::ComputeNode );

		ScenePlug *scenePlug();
		const ScenePlug *scenePlug() const;

		Gaffer::StringPlug *locationPlug();
		const Gaffer::StringPlug *locationPlug() const;

		Gaffer::IntPlug *idPlug();
		const Gaffer::IntPlug *idPlug() const;

		Gaffer::BoolPlug *existsPlug();
		const Gaffer::BoolPlug *existsPlug() const;

		Gaffer::StringPlug *prototypePlug();
		const Gaffer::StringPlug *prototypePlug() const;

		Gaffer::M44fPlug *transformPlug();
		const Gaffer::M44fPlug *transformPlug() const;

		Gaffer::BoolPlug *visiblePlug();
		const Gaffer::BoolPlug *visiblePlug() const;

		Gaffer::CompoundObjectPlug *attributesPlug();
		const Gaffer::CompoundObjectPlug *attributesPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

	private :

		struct IDMapData;
		IE_CORE_DECLAREPTR( IDMapData );

		// Used to cache precomputed maps that allow us to avoid linear search
		// through the `instanceId` and `invisibleIds` primitive variables.
		// Linear search would be fine if querying a few instances, but would
		// lead to `O(n^2)` performance if querying all instances.
		Gaffer::ObjectPlug *idMapPlug();
		const Gaffer::ObjectPlug *idMapPlug() const;

		using QuerySource = std::tuple<IECoreScene::ConstPointInstancerPtr, int64_t, ConstIDMapDataPtr>;
		bool affectsQuerySource( const Gaffer::Plug *input ) const;
		void hashQuerySource( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		QuerySource querySource( const Gaffer::Context *context ) const;

		static size_t g_firstPlugIndex;

};

} // GafferScene
