//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Lucien Fostier All rights reserved.
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

#include "GafferML/Export.h"
#include "GafferML/TensorPlug.h"

#include "GafferScene/SceneNode.h"
#include "Gaffer/TransformPlug.h"

namespace GafferML
{

class GAFFERML_API TensorToScene : public GafferScene::SceneNode
{

	public :

		explicit TensorToScene( const std::string &name=defaultName<TensorToScene>() );
		~TensorToScene() override;

		GAFFER_NODE_DECLARE_TYPE( GafferML::TensorToScene, TensorToSceneTypeId, GafferScene::SceneNode );

		TensorPlug *verticesTensorPlug();
		const TensorPlug *verticesTensorPlug() const;

		TensorPlug *facesTensorPlug();
		const TensorPlug *facesTensorPlug() const;

		void affects( const Gaffer::Plug *input, Gaffer::DependencyNode::AffectedPlugsContainer &outputs ) const override;
	protected :

		void hashBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashAttributes( const ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashObject( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashChildNames( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashGlobals( const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashSetNames( const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const override;

		Imath::Box3f computeBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const override;
		Imath::M44f computeTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const override;
		IECore::ConstCompoundObjectPtr computeAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const override;
		IECore::ConstObjectPtr computeObject( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const override;
		IECore::ConstInternedStringVectorDataPtr computeChildNames( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const override;
		IECore::ConstCompoundObjectPtr computeGlobals( const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const override;
		IECore::ConstInternedStringVectorDataPtr computeSetNames( const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const override;
		IECore::ConstPathMatcherDataPtr computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const override;


		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( TensorToScene )

} // namespace GafferML
