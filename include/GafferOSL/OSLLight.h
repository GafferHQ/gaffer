//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "GafferOSL/Export.h"
#include "GafferOSL/TypeIds.h"

#include "GafferScene/Light.h"
#include "GafferScene/ShaderPlug.h"

namespace GafferOSL
{

class OSLShader;

class GAFFEROSL_API OSLLight : public GafferScene::Light
{

	public :

		GAFFER_NODE_DECLARE_TYPE( GafferOSL::OSLLight, OSLLightTypeId, GafferScene::Light );

		explicit OSLLight( const std::string &name=defaultName<OSLLight>() );
		~OSLLight() override;

		Gaffer::StringPlug *shaderNamePlug();
		const Gaffer::StringPlug *shaderNamePlug() const;

		enum Shape
		{
			Disk = 0,
			Sphere = 1,
			Geometry = 2
		};

		Gaffer::IntPlug *shapePlug();
		const Gaffer::IntPlug *shapePlug() const;

		Gaffer::FloatPlug *radiusPlug();
		const Gaffer::FloatPlug *radiusPlug() const;

		Gaffer::StringPlug *geometryTypePlug();
		const Gaffer::StringPlug *geometryTypePlug() const;

		Gaffer::Box3fPlug *geometryBoundPlug();
		const Gaffer::Box3fPlug *geometryBoundPlug() const;

		Gaffer::CompoundDataPlug *geometryParametersPlug();
		const Gaffer::CompoundDataPlug *geometryParametersPlug() const;

		/// \todo Remove. This is provided by the base class now.
		Gaffer::CompoundDataPlug *attributesPlug();
		const Gaffer::CompoundDataPlug *attributesPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

		void loadShader( const std::string &shaderName );

	protected :

		void hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeSource( const Gaffer::Context *context ) const override;

		/// \todo Remove. This doesn't override anything any more.
		void hashAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundObjectPtr computeAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const override;

		void hashLight( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECoreScene::ConstShaderNetworkPtr computeLight( const Gaffer::Context *context ) const override;

	private :

		OSLShader *shaderNode();
		const OSLShader *shaderNode() const;

		GafferScene::ShaderPlug *shaderInPlug();
		const GafferScene::ShaderPlug *shaderInPlug() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( OSLLight )

} // namespace GafferOSL
