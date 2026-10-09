//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Deformer.h"

#include "Gaffer/TweakPlug.h"

namespace GafferScene
{


class GAFFERSCENE_API PrimitiveVariablePaint : public Deformer
{

	public :

		explicit PrimitiveVariablePaint( const std::string &name=defaultName<PrimitiveVariablePaint>() );
		~PrimitiveVariablePaint() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::PrimitiveVariablePaint, PrimitiveVariablePaintTypeId, Deformer );

		Gaffer::Plug *primitiveVariablesPlug();
		const Gaffer::Plug *primitiveVariablesPlug() const;

		class PaintOperation;
		IE_CORE_DECLAREPTR( PaintOperation );


	protected :

		bool affectsProcessedObject( const Gaffer::Plug *input ) const override;
		void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const override;

		bool adjustBounds() const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( PrimitiveVariablePaint )

// Store a bundle of data needed to apply a modification to part of a primitive variable,
// targeted using opacity or indices.
// TODO - should go in class namespace?
class GAFFERSCENE_API PrimitiveVariablePaint::PaintOperation : public IECore::Object
{

	public :

		PaintOperation(
			IECore::DataPtr valueData = nullptr,
			IECore::FloatVectorDataPtr opacityData = nullptr,
			IECore::IntVectorDataPtr indicesData = nullptr
		);

		~PaintOperation() override;

		IE_CORE_DECLAREEXTENSIONOBJECT( GafferScene::PrimitiveVariablePaint::PaintOperation, PaintOperationTypeId, IECore::Object );

		void apply( IECore::DataPtr &resultData, size_t outputSize ) const;

		// We store the value premultiplied, to avoid one multiply when applying it.
		IECore::DataPtr m_valueData;

		IECore::FloatVectorDataPtr m_opacityData;

		// If present, the indices control which elements of the primvar the values and opacities apply to.
		// Otherwise, there must be a value and opacity for every element.
		IECore::IntVectorDataPtr m_indicesData;

};

} // namespace GafferScene
