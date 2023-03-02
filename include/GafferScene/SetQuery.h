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

#include "GafferScene/Export.h"
#include "GafferScene/TypeIds.h"

#include "Gaffer/ComputeNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlug.h"

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( ScenePlug )

class GAFFERSCENE_API SetQuery : public Gaffer::ComputeNode
{

	public :

		SetQuery( const std::string &name=defaultName<SetQuery>() );
		~SetQuery() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::SetQuery, SetQueryTypeId, ComputeNode );

		ScenePlug *scenePlug();
		const ScenePlug *scenePlug() const;

		Gaffer::StringPlug *locationPlug();
		const Gaffer::StringPlug *locationPlug() const;

		Gaffer::StringPlug *setsPlug();
		const Gaffer::StringPlug *setsPlug() const;

		Gaffer::BoolPlug *inheritPlug();
		const Gaffer::BoolPlug *inheritPlug() const;

		Gaffer::StringVectorDataPlug *matchesPlug();
		const Gaffer::StringVectorDataPlug *matchesPlug() const;

		Gaffer::StringPlug *firstMatchPlug();
		const Gaffer::StringPlug *firstMatchPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		// Internal plug used to compute MatchesData, from which the output
		// for `matchesPlug()` and `firstMatch()` plug is derived. This uses
		// `${scene:path}` rather than `locationPlug()` so we can use recursive
		// computes to inherit from ancestor locations.
		Gaffer::ObjectPlug *matchesInternalPlug();
		const Gaffer::ObjectPlug *matchesInternalPlug() const;

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;

	private :

		bool affectsMatchesInternal( const Gaffer::Plug *input ) const;
		void hashMatchesInternal( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		IECore::ConstObjectPtr computeMatchesInternal( const Gaffer::Context *context ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( SetQuery )

} // namespace GafferScene
