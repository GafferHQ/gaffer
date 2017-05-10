//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#ifndef IECORE_GEOMETRY_H
#define IECORE_GEOMETRY_H

#include "GafferScene/Export.h"

#include "GafferScene/TypeIds.h"

#include "IECoreScene/VisibleRenderable.h"

namespace IECoreScenePreview
{

/// Class used to represent additional geometry types supported
/// by specific renderers but not present in Cortex (think RiGeometry).
class GAFFERSCENE_API Geometry : public IECoreScene::VisibleRenderable
{

	public:

		Geometry( const std::string &type = "", const Imath::Box3f &bound = Imath::Box3f(), const IECore::CompoundDataPtr &parameters = nullptr );

		IE_CORE_DECLAREEXTENSIONOBJECT( IECoreScenePreview::Geometry, GafferScene::PreviewGeometryTypeId, IECoreScene::VisibleRenderable );

		void setType( const std::string &type );
		const std::string &getType() const;

		void setBound( const Imath::Box3f &bound );
		const Imath::Box3f &getBound() const;

		IECore::CompoundData *parameters();
		const IECore::CompoundData *parameters() const;

		Imath::Box3f bound() const override;
		void render( IECoreScene::Renderer *renderer ) const override;

	private:

		static const unsigned int m_ioVersion;

		std::string m_type;
		Imath::Box3f m_bound;
		IECore::CompoundDataPtr m_parameters;

};

IE_CORE_DECLAREPTR( Geometry );

} // namespace IECoreScenePreview

#endif // IECORE_GEOMETRY_H
