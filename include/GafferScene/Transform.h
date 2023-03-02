//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/SceneElementProcessor.h"

#include "Gaffer/TransformPlug.h"

namespace GafferScene
{

class GAFFERSCENE_API Transform : public SceneElementProcessor
{

	public :

		Transform( const std::string &name=defaultName<Transform>() );
		~Transform() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::Transform, TransformTypeId, SceneElementProcessor );

		enum Space
		{
			Local,
			Parent,
			World,
			ResetLocal,
			ResetWorld
		};

		Gaffer::IntPlug *spacePlug();
		const Gaffer::IntPlug *spacePlug() const;

		Gaffer::TransformPlug *transformPlug();
		const Gaffer::TransformPlug *transformPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		bool processesTransform() const override;
		void hashProcessedTransform( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		Imath::M44f computeProcessedTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const override;

	private :

		Imath::M44f fullParentTransform( const ScenePath &path ) const;
		IECore::MurmurHash fullParentTransformHash( const ScenePath &path ) const;
		// Returns the transform of the parent of path, either relative to an ancestor matched
		// by the filter or to the root if no matching ancestor is found. This is useful for
		// the world reset mode because when a matching ancestor is found we know what its output
		// transform will be already.
		Imath::M44f relativeParentTransform( const ScenePath &path, const Gaffer::Context *context, bool &matchingAncestorFound ) const;
		IECore::MurmurHash relativeParentTransformHash( const ScenePath &path, const Gaffer::Context *context ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Transform )

} // namespace GafferScene
