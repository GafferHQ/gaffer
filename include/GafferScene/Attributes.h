//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#pragma once

#include "GafferScene/AttributeProcessor.h"

#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/TypedObjectPlug.h"

namespace GafferScene
{

class GAFFERSCENE_API Attributes : public AttributeProcessor
{

	public :

		explicit Attributes( const std::string &name=defaultName<Attributes>() );
		~Attributes() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::Attributes, AttributesTypeId, AttributeProcessor );

		Gaffer::CompoundDataPlug *attributesPlug();
		const Gaffer::CompoundDataPlug *attributesPlug() const;

		Gaffer::BoolPlug *globalPlug();
		const Gaffer::BoolPlug *globalPlug() const;

		Gaffer::CompoundObjectPlug *extraAttributesPlug();
		const Gaffer::CompoundObjectPlug *extraAttributesPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		/// Automatically adds plugs for all attributes for the specified renderer, based
		/// on `attribute:{rendererPrefix}:*` metadata registrations.
		Attributes( const std::string &name, const std::string &rendererPrefix );

		void hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundObjectPtr computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const override;

		bool affectsProcessedAttributes( const Gaffer::Plug *input ) const override;
		void hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundObjectPtr computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, const IECore::CompoundObject *inputAttributes ) const override;

	private :

		void plugSet( Gaffer::Plug *plug );
		void plugInputChanged( Gaffer::Plug *plug );
		void updateInternalConnections();

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Attributes )

} // namespace GafferScene
