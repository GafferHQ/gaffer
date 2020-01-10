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

#ifndef GAFFERSCENE_CAMERA_H
#define GAFFERSCENE_CAMERA_H

#include "Gaffer/CompoundDataPlug.h"
#include "GafferScene/ObjectSource.h"

namespace GafferScene
{

class GAFFERSCENE_API Camera : public ObjectSource
{

	public :

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferScene::Camera, CameraTypeId, ObjectSource );

		Camera( const std::string &name=defaultName<Camera>() );
		~Camera() override;

		Gaffer::StringPlug *projectionPlug();
		const Gaffer::StringPlug *projectionPlug() const;

		enum PerspectiveMode
		{
			FieldOfView,
			ApertureFocalLength
		};

		Gaffer::IntPlug *perspectiveModePlug();
		const Gaffer::IntPlug *perspectiveModePlug() const;

		Gaffer::FloatPlug *fieldOfViewPlug();
		const Gaffer::FloatPlug *fieldOfViewPlug() const;

		Gaffer::FloatPlug *apertureAspectRatioPlug();
		const Gaffer::FloatPlug *apertureAspectRatioPlug() const;

		Gaffer::V2fPlug *aperturePlug();
		const Gaffer::V2fPlug *aperturePlug() const;

		Gaffer::FloatPlug *focalLengthPlug();
		const Gaffer::FloatPlug *focalLengthPlug() const;

		Gaffer::V2fPlug *orthographicAperturePlug();
		const Gaffer::V2fPlug *orthographicAperturePlug() const;

		Gaffer::V2fPlug *apertureOffsetPlug();
		const Gaffer::V2fPlug *apertureOffsetPlug() const;

		Gaffer::FloatPlug *fStopPlug();
		const Gaffer::FloatPlug *fStopPlug() const;

		Gaffer::FloatPlug *focalLengthWorldScalePlug();
		const Gaffer::FloatPlug *focalLengthWorldScalePlug() const;

		Gaffer::FloatPlug *focusDistancePlug();
		const Gaffer::FloatPlug *focusDistancePlug() const;

		Gaffer::V2fPlug *clippingPlanesPlug();
		const Gaffer::V2fPlug *clippingPlanesPlug() const;

		Gaffer::CompoundDataPlug *renderSettingOverridesPlug();
		const Gaffer::CompoundDataPlug *renderSettingOverridesPlug() const;

		Gaffer::CompoundDataPlug *visualiserAttributesPlug();
		const Gaffer::CompoundDataPlug *visualiserAttributesPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeSource( const Gaffer::Context *context ) const override;

		void hashAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundObjectPtr computeAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;

		IECore::ConstInternedStringVectorDataPtr computeStandardSetNames() const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Camera )

} // namespace GafferScene

#endif // GAFFERSCENE_CAMERA_H
