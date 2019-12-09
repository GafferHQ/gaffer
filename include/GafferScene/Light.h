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

#ifndef GAFFERSCENE_LIGHT_H
#define GAFFERSCENE_LIGHT_H

#include "GafferScene/ObjectSource.h"

#include "IECoreScene/ShaderNetwork.h"

namespace GafferScene
{

class GAFFERSCENE_API Light : public ObjectSource
{

	public :

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferScene::Light, LightTypeId, ObjectSource );

		Light( const std::string &name=defaultName<Light>() );
		~Light() override;

		Gaffer::Plug *parametersPlug();
		const Gaffer::Plug *parametersPlug() const;

		Gaffer::BoolPlug *defaultLightPlug();
		const Gaffer::BoolPlug *defaultLightPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeSource( const Gaffer::Context *context ) const override;

		void hashAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundObjectPtr computeAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;

		void hashBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		Imath::Box3f computeBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;

		void hashStandardSetNames( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstInternedStringVectorDataPtr computeStandardSetNames() const override;

		/// Must be implemented by derived classes to hash and generate the light to be placed
		/// in the scene graph.
		virtual void hashLight( const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		virtual IECoreScene::ShaderNetworkPtr computeLight( const Gaffer::Context *context ) const = 0;

		Gaffer::FloatPlug *visualiserScalePlug();
		const Gaffer::FloatPlug *visualiserScalePlug() const;
		Gaffer::BoolPlug *visualiserShadedPlug();
		const Gaffer::BoolPlug *visualiserShadedPlug() const;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Light )

} // namespace GafferScene

#endif // GAFFERSCENE_LIGHT_H
