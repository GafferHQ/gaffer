//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
//      * Neither the name of Image Engine Design Inc nor the names of
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

#ifndef GAFFERSCENE_RESAMPLEPRIMITIVEVARIABLES_H
#define GAFFERSCENE_RESAMPLEPRIMITIVEVARIABLES_H

#include "GafferScene/Export.h"
#include "GafferScene/PrimitiveVariableProcessor.h"

namespace GafferScene
{

class GAFFERSCENE_API ResamplePrimitiveVariables : public PrimitiveVariableProcessor
{

	public :

		ResamplePrimitiveVariables( const std::string &name = defaultName<ResamplePrimitiveVariables>() );
		~ResamplePrimitiveVariables() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::ResamplePrimitiveVariables, ResamplePrimitiveVariablesTypeId, PrimitiveVariableProcessor );

		Gaffer::IntPlug *interpolationPlug();
		const Gaffer::IntPlug *interpolationPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void processPrimitiveVariable( const ScenePath &path, const Gaffer::Context *context, IECoreScene::ConstPrimitivePtr inputGeometry, IECoreScene::PrimitiveVariable &inputVariable ) const override;
		void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
	private :

		static size_t g_firstPlugIndex;
};

IE_CORE_DECLAREPTR( ResamplePrimitiveVariables )

} // namespace GafferScene

#endif // GAFFERSCENE_RESAMPLEPRIMITIVEVARIABLES_H
