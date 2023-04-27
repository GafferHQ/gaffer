//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/AttributeProcessor.h"

#include "Gaffer/NumericPlug.h"
#include "Gaffer/SplinePlug.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferScene
{

class GAFFERSCENE_API AttributeVisualiser : public AttributeProcessor
{

	public :

		explicit AttributeVisualiser( const std::string &name=defaultName<AttributeVisualiser>() );
		~AttributeVisualiser() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::AttributeVisualiser, AttributeVisualiserTypeId, AttributeProcessor );

		enum Mode
		{
			Color,
			FalseColor,
			Random,
			ShaderNodeColor
		};

		Gaffer::StringPlug *attributeNamePlug();
		const Gaffer::StringPlug *attributeNamePlug() const;

		Gaffer::IntPlug *modePlug();
		const Gaffer::IntPlug *modePlug() const;

		Gaffer::FloatPlug *minPlug();
		const Gaffer::FloatPlug *minPlug() const;

		Gaffer::FloatPlug *maxPlug();
		const Gaffer::FloatPlug *maxPlug() const;

		Gaffer::SplinefColor3fPlug *rampPlug();
		const Gaffer::SplinefColor3fPlug *rampPlug() const;

		Gaffer::StringPlug *shaderTypePlug();
		const Gaffer::StringPlug *shaderTypePlug() const;

		Gaffer::StringPlug *shaderNamePlug();
		const Gaffer::StringPlug *shaderNamePlug() const;

		Gaffer::StringPlug *shaderParameterPlug();
		const Gaffer::StringPlug *shaderParameterPlug() const;

	protected :

		bool affectsProcessedAttributes( const Gaffer::Plug *input ) const override;
		void hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundObjectPtr computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, const IECore::CompoundObject *inputAttributes ) const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( AttributeVisualiser )

} // namespace GafferScene
