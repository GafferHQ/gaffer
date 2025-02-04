//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferSceneUI/Export.h"

#include "GafferSceneUI/Private/Inspector.h"

#include "GafferScene/EditScopeAlgo.h"
#include "GafferScene/ScenePlug.h"

namespace GafferSceneUI
{

namespace Private
{

class GAFFERSCENEUI_API SetMembershipInspector : public Inspector
{

	public :

		SetMembershipInspector(
			const GafferScene::ScenePlugPtr &scene,
			const Gaffer::PlugPtr &editScope,
			IECore::InternedString setName
		);

		/// Convenience method to acquire an edit from `inspection` and
		/// edit the set membership to include or exclude `path`. Returns true
		/// if an edit was made, false otherwise.
		bool editSetMembership(
			const Result *inspection,
			const GafferScene::ScenePlug::ScenePath &path,
			GafferScene::EditScopeAlgo::SetMembership setMembership
		) const;

		IE_CORE_DECLAREMEMBERPTR( SetMembershipInspector );

	protected :

		GafferScene::SceneAlgo::History::ConstPtr history() const override;
		IECore::ConstObjectPtr value( const GafferScene::SceneAlgo::History *history) const override;
		IECore::ConstObjectPtr fallbackValue( const GafferScene::SceneAlgo::History *history, std::string &description ) const override;
		/// For the given `history`, returns either the "sets" `StringPlug` of an `ObjectSource`
		/// node, the "name" `StringPlug` of a `Set` node, the `Spreadsheet::RowPlug` for the
		/// appropriate row of a set membership processor spreadsheet or `nullptr` if none of
		/// those are found.
		Gaffer::ValuePlugPtr source( const GafferScene::SceneAlgo::History *history, std::string &editWarning ) const override;
		AcquireEditFunctionOrFailure acquireEditFunction( Gaffer::EditScope *scope, const GafferScene::SceneAlgo::History *history ) const override;
		DisableEditFunctionOrFailure disableEditFunction( Gaffer::ValuePlug *plug, const GafferScene::SceneAlgo::History *history ) const override;

	private :

		void plugDirtied( Gaffer::Plug *plug );
		void plugMetadataChanged( IECore::InternedString key, const Gaffer::Plug *plug );
		void nodeMetadataChanged( IECore::InternedString key, const Gaffer::Node *node );

		const GafferScene::ScenePlugPtr m_scene;
		const IECore::InternedString m_setName;
};

}

}
