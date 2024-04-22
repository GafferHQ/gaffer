//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/ObjectProcessor.h"

#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedPlug.h"

namespace GafferScene
{

class GAFFERSCENE_API MeshTessellate : public ObjectProcessor
{

	public :

		MeshTessellate( const std::string &name=defaultName<MeshTessellate>() );
		~MeshTessellate() override;

		Gaffer::IntPlug *divisionsPlug();
		const Gaffer::IntPlug *divisionsPlug() const;

		Gaffer::BoolPlug *calculateNormalsPlug();
		const Gaffer::BoolPlug *calculateNormalsPlug() const;

		Gaffer::StringPlug *schemePlug();
		const Gaffer::StringPlug *schemePlug() const;

		Gaffer::BoolPlug *tessellatePolygonsPlug();
		const Gaffer::BoolPlug *tessellatePolygonsPlug() const;

		Gaffer::StringPlug *interpolateBoundaryPlug();
		const Gaffer::StringPlug *interpolateBoundaryPlug() const;

		Gaffer::StringPlug *faceVaryingLinearInterpolationPlug();
		const Gaffer::StringPlug *faceVaryingLinearInterpolationPlug() const;

		Gaffer::StringPlug *triangleSubdivisionRulePlug();
		const Gaffer::StringPlug *triangleSubdivisionRulePlug() const;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::MeshTessellate, MeshTessellateTypeId, ObjectProcessor );

	protected :

		bool affectsProcessedObject( const Gaffer::Plug *input ) const override;
		void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const override;

	private:

		Gaffer::ValuePlug::CachePolicy processedObjectComputeCachePolicy() const final;


		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( MeshTessellate )

} // namespace GafferScene
