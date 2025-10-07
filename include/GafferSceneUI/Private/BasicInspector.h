//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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
#include "GafferSceneUI/TypeIds.h"

#include <functional>

namespace GafferSceneUI::Private
{

/// A basic inspector subclass which defers to lambda functions for getting
/// values from the history. Doesn't support editing, but does make it very
/// simple to create a simple read-only inspector.
class GAFFERSCENEUI_API BasicInspector : public Inspector
{

	public :

		/// Constructs an inspector to inspect `plug` and its history by calling
		/// `valueFunction`.
		template<typename PlugType, typename ValueFunctionType>
		BasicInspector(
			PlugType *plug, const Gaffer::PlugPtr &editScope,
			/// The function used to inspect the value. Signature must be
			/// `ConstObjectPtr ( const PlugType * )`.
			const ValueFunctionType &&valueFunction,
			const std::string &type = "", const std::string &name = ""
		);

		~BasicInspector() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( BasicInspector, BasicInspectorTypeId, Inspector );

	protected :

		GafferScene::SceneAlgo::History::ConstPtr history() const override;
		IECore::ConstObjectPtr value( const GafferScene::SceneAlgo::History *history ) const override;

	private :

		// Logically part of constructor, but in a separate function to avoid
		// bloating the template.
		void init();

		const Gaffer::ValuePlugPtr m_plug;
		using ValueFunction = std::function<IECore::ConstObjectPtr( const Gaffer::Plug * )>;
		ValueFunction m_valueFunction;

};

IE_CORE_DECLAREPTR( BasicInspector )

} // namespace GafferSceneUI::Private

#include "GafferSceneUI/Private/BasicInspector.inl"
