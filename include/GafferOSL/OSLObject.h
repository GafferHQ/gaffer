//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, John Haddon. All rights reserved.
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

#ifndef GAFFEROSL_OSLOBJECT_H
#define GAFFEROSL_OSLOBJECT_H

#include "GafferOSL/Export.h"
#include "GafferOSL/OSLCode.h"
#include "GafferOSL/TypeIds.h"

#include "GafferScene/Deformer.h"
#include "GafferScene/ShaderPlug.h"

#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"

namespace GafferOSL
{

IE_CORE_FORWARDDECLARE( ShadingEngine )

class GAFFEROSL_API OSLObject : public GafferScene::Deformer
{

	public :

		OSLObject( const std::string &name=defaultName<OSLObject>() );
		~OSLObject() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferOSL::OSLObject, OSLObjectTypeId, GafferScene::Deformer );

		Gaffer::IntPlug *interpolationPlug();
		const Gaffer::IntPlug *interpolationPlug() const;

		Gaffer::BoolPlug *useTransformPlug();
		const Gaffer::BoolPlug *useTransformPlug() const;

		Gaffer::BoolPlug *useAttributesPlug();
		const Gaffer::BoolPlug *useAttributesPlug() const;

		Gaffer::Plug *primitiveVariablesPlug();
		const Gaffer::Plug *primitiveVariablesPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		bool affectsProcessedObject( const Gaffer::Plug *input ) const override;
		void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const override;
		bool adjustBounds() const override;

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

	private :

		GafferScene::ShaderPlug *shaderPlug();
		const GafferScene::ShaderPlug *shaderPlug() const;

		GafferScene::ScenePlug *resampledInPlug();
		const GafferScene::ScenePlug *resampledInPlug() const;

		Gaffer::StringPlug *resampledNamesPlug();
		const Gaffer::StringPlug *resampledNamesPlug() const;

		ConstShadingEnginePtr shadingEngine( const Gaffer::Context *context ) const;

		GafferOSL::OSLCode *oslCode();
		const GafferOSL::OSLCode *oslCode() const;

		void primitiveVariableAdded( const Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child );
		void primitiveVariableRemoved( const Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child );

		void updatePrimitiveVariables();

		static size_t g_firstPlugIndex;

};

} // namespace GafferOSL

#endif // GAFFEROSL_OSLOBJECT_H
