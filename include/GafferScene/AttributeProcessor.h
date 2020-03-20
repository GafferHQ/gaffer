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

#include "GafferScene/FilteredSceneProcessor.h"

namespace GafferScene
{

/// Base class for nodes which manipulate attributes in some way.
class GAFFERSCENE_API AttributeProcessor : public FilteredSceneProcessor
{

	public :

		~AttributeProcessor() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferScene::AttributeProcessor, AttributeProcessorTypeId, FilteredSceneProcessor );

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		/// Constructs with a single input ScenePlug named "in". Use inPlug()
		/// to access this plug.
		AttributeProcessor( const std::string &name );
		/// Constructs with an ArrayPlug called "in". Use inPlug() as a
		/// convenience for accessing the first child in the array, and use
		/// inPlugs() to access the array itself.
		AttributeProcessor( const std::string &name, size_t minInputs, size_t maxInputs = Imath::limits<size_t>::max() );

		/// Must be implemented by derived classes to return true if `input` is used
		/// by `computeProcessedAttributes()`. Overrides must start by calling the base
		/// class first, and return true if it returns true.
		virtual bool affectsProcessedAttributes( const Gaffer::Plug *input ) const = 0;
		/// Must be implemented by derived classes to do one of the following :
		///
		/// - Call `AttributeProcessor::hashProcessedAttributes()` and then append to the hash
		///   with all plugs used in `computeProcessedAttributes()`.
		/// - Assign `h = inPlug()->attributesPlug()->hash()` to signify that
		///   `computeProcessedAttributes()` will pass through `inputAttributes`
		///   unchanged.
		virtual void hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		/// Must be implemented by derived classes to return the processed attributes.
		virtual IECore::ConstCompoundObjectPtr computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, const IECore::CompoundObject *inputAttributes ) const = 0;

	private :

		void init();

		void hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const final;
		IECore::ConstCompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const final;

		/// Private constructor and friendship for old nodes which are filtered to everything
		/// by default. This was a mistake, and we want to ensure that we don't repeat the mistake
		/// for new nodes.
		AttributeProcessor( const std::string &name, IECore::PathMatcher::Result filterDefault );
		friend class DeleteAttributes;
		friend class ShaderAssignment;
		friend class Attributes;
		friend class AttributeVisualiser;

};

IE_CORE_DECLAREPTR( AttributeProcessor )

} // namespace GafferScene

#endif // GAFFERSCENE_ATTRIBUTEPROCESSOR_H
