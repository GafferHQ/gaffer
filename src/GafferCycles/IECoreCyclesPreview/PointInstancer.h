//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "NodeDeleter.h"

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

namespace IECoreCycles
{

class PointInstancer : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		using SharedGeometryPtr = std::shared_ptr<const ccl::Geometry>;

		PointInstancer(
			ccl::Scene *scene,
			NodeDeleter *nodeDeleter,
			const IECoreScenePreview::Renderer::PointInstancerSamples &samples,
			const std::vector<SharedGeometryPtr> &prototypes
		);

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override;
		void transform( const IECoreScenePreview::Renderer::TransformSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &times ) override;
		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override;

		void assignID( uint32_t id ) override;
		void assignInstanceID( uint32_t id ) override;

	private :

		ccl::Scene *m_scene;
		NodeDeleter *m_nodeDeleter;
		// Keep geometry alive as long as `m_instances` references it.
		std::vector<SharedGeometryPtr> m_prototypes;

		using UniqueObjectPtr = std::unique_ptr<ccl::Object, NodeDeleter::ObjectDeleter>;

		struct Instance
		{
			UniqueObjectPtr object;
			IECoreScenePreview::Renderer::Samples<ccl::Transform> transformSamples;
		};

		std::vector<Instance> m_instances;

};

} // namespace IECoreCycles
