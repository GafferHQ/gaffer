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

namespace GafferScene
{

class GAFFERSCENE_API VisibilityQuery : public Gaffer::ComputeNode
{

	public :

		explicit VisibilityQuery( const std::string& name = defaultName<VisibilityQuery>() );
		~VisibilityQuery() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::VisibilityQuery, VisibilityQueryTypeId, Gaffer::ComputeNode );

		ScenePlug *scenePlug();
		const ScenePlug *scenePlug() const;

		Gaffer::StringPlug *locationPlug();
		const Gaffer::StringPlug *locationPlug() const;

		Gaffer::BoolPlug *visiblePlug();
		const Gaffer::BoolPlug *visiblePlug() const;

		Gaffer::StringVectorDataPlug *invisibleAncestorsPlug();
		const Gaffer::StringVectorDataPlug *invisibleAncestorsPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

	private :

		// Vector of bools corresponding to the visibility of the
		// elements of `${scene:path}`. We compute this recursively,
		// allowing us to cache all intermediate results. The public
		// `visible` and `invisibleAncestors` plugs derive their result
		// directly from this.
		Gaffer::BoolVectorDataPlug *ancestorVisibilityPlug();
		const Gaffer::BoolVectorDataPlug *ancestorVisibilityPlug() const;

		bool affectsAncestorVisibility( const Gaffer::Plug *input ) const;
		void hashAncestorVisibility( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		IECore::ConstBoolVectorDataPtr computeAncestorVisibility( const Gaffer::Context *context ) const;

		// Convenience functions for accessing `ancestorVisibility` results
		// for the location specified by `locationPlug()`.
		bool affectsAncestorVisibilityForLocation( const Gaffer::Plug *input ) const;
		void hashAncestorVisibilityForLocation( const Gaffer::Context *context, IECore::MurmurHash &h, std::string *location = nullptr ) const;
		IECore::ConstBoolVectorDataPtr ancestorVisibilityForLocation( const Gaffer::Context *context, std::string *location = nullptr ) const;

		bool affectsVisible( const Gaffer::Plug *input ) const;
		void hashVisible( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		bool computeVisible( const Gaffer::Context *context ) const;

		bool affectsInvisibleAncestors( const Gaffer::Plug *input ) const;
		void hashInvisibleAncestors( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		IECore::ConstStringVectorDataPtr computeInvisibleAncestors( const Gaffer::Context *context ) const;

		static size_t g_firstPlugIndex;

};

} // GafferScene
