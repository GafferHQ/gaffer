//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, John Haddon. All rights reserved.
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

#ifndef GAFFERSCENE_COPYPRIMITIVEVARIABLES_H
#define GAFFERSCENE_COPYPRIMITIVEVARIABLES_H

#include "GafferScene/Deformer.h"

#include "Gaffer/StringPlug.h"

namespace GafferScene
{

class GAFFERSCENE_API CopyPrimitiveVariables : public Deformer
{

	public :

		CopyPrimitiveVariables( const std::string &name=defaultName<CopyPrimitiveVariables>() );
		~CopyPrimitiveVariables() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::CopyPrimitiveVariables, CopyPrimitiveVariablesTypeId, Deformer );

		GafferScene::ScenePlug *sourcePlug();
		const GafferScene::ScenePlug *sourcePlug() const;

		Gaffer::StringPlug *primitiveVariablesPlug();
		const Gaffer::StringPlug *primitiveVariablesPlug() const;

		Gaffer::StringPlug *sourceLocationPlug();
		const Gaffer::StringPlug *sourceLocationPlug() const;

		Gaffer::StringPlug *prefixPlug();
		const Gaffer::StringPlug *prefixPlug() const;

	protected :

		bool affectsProcessedObject( const Gaffer::Plug *input ) const override;
		void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const override;
		bool adjustBounds() const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( CopyPrimitiveVariables )

} // namespace GafferScene

#endif // GAFFERSCENE_COPYPRIMITIVEVARIABLES_H
