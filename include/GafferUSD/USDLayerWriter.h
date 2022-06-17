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

#ifndef GAFFERUSD_USDLAYERWRITER_H
#define GAFFERUSD_USDLAYERWRITER_H

#include "GafferUSD/Export.h"
#include "GafferUSD/TypeIds.h"

#include "GafferScene/ScenePlug.h"
#include "GafferScene/SceneWriter.h"

#include "GafferDispatch/TaskNode.h"

#include "Gaffer/TypedPlug.h"
#include "Gaffer/StringPlug.h"

namespace GafferUSD
{

class GAFFERUSD_API USDLayerWriter : public GafferDispatch::TaskNode
{

	public :

		USDLayerWriter( const std::string &name=defaultName<USDLayerWriter>() );
		~USDLayerWriter() override;

		GAFFER_NODE_DECLARE_TYPE( GafferUSD::USDLayerWriter, USDLayerWriterTypeId, GafferDispatch::TaskNode );

		Gaffer::StringPlug *fileNamePlug();
		const Gaffer::StringPlug *fileNamePlug() const;

		GafferScene::ScenePlug *basePlug();
		const GafferScene::ScenePlug *basePlug() const;

		GafferScene::ScenePlug *layerPlug();
		const GafferScene::ScenePlug *layerPlug() const;

		GafferScene::ScenePlug *outPlug();
		const GafferScene::ScenePlug *outPlug() const;

	protected :

		IECore::MurmurHash hash( const Gaffer::Context *context ) const override;
		bool requiresSequenceExecution() const override;
		void execute() const override;
		void executeSequence( const std::vector<float> &frames ) const override;

	private :

		const GafferScene::SceneWriter *sceneWriter() const;

		static size_t g_firstPlugIndex;

		// Friendship for the bindings
		friend struct GafferDispatchBindings::Detail::TaskNodeAccessor;

};

IE_CORE_DECLAREPTR( USDLayerWriter )

} // namespace GafferUSD

#endif // GAFFERUSD_USDLAYERWRITER_H
