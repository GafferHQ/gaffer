//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/Export.h"
#include "GafferScene/FilterPlug.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/TypeIds.h"

#include "Gaffer/ComputeNode.h"
#include "Gaffer/OptionalValuePlug.h"
#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/ValuePlug.h"

namespace GafferScene
{

class GAFFERSCENE_API SceneStats : public Gaffer::ComputeNode
{

	public :

		explicit SceneStats( const std::string &name = defaultName<SceneStats>() );
		~SceneStats() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::SceneStats, SceneStatsTypeId, Gaffer::ComputeNode );

		ScenePlug *scenePlug();
		const ScenePlug *scenePlug() const;

		GafferScene::FilterPlug *filterPlug();
		const GafferScene::FilterPlug *filterPlug() const;

		Gaffer::ValuePlug *queriesPlug();
		const Gaffer::ValuePlug *queriesPlug() const;

		/// Outputs, one per child of `queriesPlug()`, sharing the same name.
		Gaffer::ValuePlug *outPlug();
		const Gaffer::ValuePlug *outPlug() const;

		/// Adds a query whose `value` is a counterpart of `plug`. Returns the
		/// newly created plug, which is parented to `queriesPlug()`.
		Gaffer::OptionalValuePlug *addQuery( const Gaffer::ValuePlug *plug, const std::string &name );
		/// Removes a query and its corresponding output. Throws if `plug` is
		/// not a child of `queriesPlug()`.
		void removeQuery( Gaffer::ValuePlug *plug );

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

	private :

		void queryNameChanged( const GraphComponent *query, IECore::InternedString oldName );
		std::tuple<const Gaffer::ValuePlug *, const Gaffer::ValuePlug *> outPlugAncestors( const Gaffer::ValuePlug *output ) const;

		Gaffer::ObjectPlug *statsDataPlug();
		const Gaffer::ObjectPlug *statsDataPlug() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( SceneStats )

} // GafferScene
