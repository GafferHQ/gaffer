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

#pragma once

#include "GafferSceneUI/Export.h"

#include "GafferSceneUI/Private/AttributeInspector.h"

#include "IECoreScene/ShaderNetwork.h"

namespace GafferSceneUI
{

namespace Private
{

class GAFFERSCENEUI_API ParameterInspector : public AttributeInspector
{

	public :

		ParameterInspector(
			const GafferScene::ScenePlugPtr &scene, const Gaffer::PlugPtr &editScope,
			IECore::InternedString attribute, const IECoreScene::ShaderNetwork::Parameter &parameter
		);

		IE_CORE_DECLAREMEMBERPTR( ParameterInspector );

	protected :

		GafferScene::SceneAlgo::History::ConstPtr history() const override;

	private :

		IECore::ConstObjectPtr value( const GafferScene::SceneAlgo::History *history ) const override;
		IECore::ConstObjectPtr fallbackValue( const GafferScene::SceneAlgo::History *history, std::string &description ) const override;
		Gaffer::ValuePlugPtr source( const GafferScene::SceneAlgo::History *history, std::string &editWarning ) const override;
		EditFunctionOrFailure editFunction( Gaffer::EditScope *editScope, const GafferScene::SceneAlgo::History *history ) const override;

		const IECoreScene::ShaderNetwork::Parameter m_parameter;

};

IE_CORE_DECLAREPTR( ParameterInspector )

} // namespace Private

} // namespace GafferSceneUI
