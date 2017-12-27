//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERSCENE_ATTRIBUTEPROCESSOR_H
#define GAFFERSCENE_ATTRIBUTEPROCESSOR_H

#include "GafferScene/Export.h"
#include "GafferScene/SceneElementProcessor.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferScene
{

/// The AttributeProcessor base class simplifies the process of manipulating
/// attributes.
class GAFFERSCENE_API AttributeProcessor : public SceneElementProcessor
{

	public :

		AttributeProcessor( const std::string &name=defaultName<AttributeProcessor>() );
		~AttributeProcessor() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::AttributeProcessor, AttributeProcessorTypeId, SceneElementProcessor );

		Gaffer::StringPlug *namesPlug();
		const Gaffer::StringPlug *namesPlug() const;

		Gaffer::BoolPlug *invertNamesPlug();
		const Gaffer::BoolPlug *invertNamesPlug() const;

		/// Implemented so that namesPlug() affects outPlug()->attributesPlug().
		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		bool processesAttributes() const override;
		void hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundObjectPtr computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputAttributes ) const override;

		/// Must be implemented by subclasses to process the attribute.
		virtual IECore::ConstObjectPtr processAttribute( const ScenePath &path, const Gaffer::Context *context, const IECore::InternedString &attributeName, const IECore::Object *inputAttribute ) const = 0;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( AttributeProcessor )

} // namespace GafferScene

#endif // GAFFERSCENE_ATTRIBUTEPROCESSOR_H
