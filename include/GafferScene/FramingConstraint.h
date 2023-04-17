//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferScene
{

class GAFFERSCENE_API FramingConstraint : public SceneElementProcessor
{

	public :

		FramingConstraint( const std::string &name=defaultName<FramingConstraint>() );
		~FramingConstraint() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::FramingConstraint, FramingConstraintTypeId, SceneElementProcessor );

		ScenePlug *targetScenePlug();
		const ScenePlug *targetScenePlug() const;

		Gaffer::StringPlug *targetPlug();
		const Gaffer::StringPlug *targetPlug() const;

		Gaffer::BoolPlug *ignoreMissingTargetPlug();
		const Gaffer::BoolPlug *ignoreMissingTargetPlug() const;

		Gaffer::StringPlug *boundModePlug();
		const Gaffer::StringPlug *boundModePlug() const;

		Gaffer::FloatPlug *paddingPlug();
		const Gaffer::FloatPlug *paddingPlug() const;

		Gaffer::BoolPlug *extendFarClipPlug();
		const Gaffer::BoolPlug *extendFarClipPlug() const;

		Gaffer::BoolPlug *useTargetFramePlug();
		const Gaffer::BoolPlug *useTargetFramePlug() const;

		Gaffer::FloatPlug *targetFramePlug();
		const Gaffer::FloatPlug *targetFramePlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		Gaffer::ObjectVectorPlug *transformAndObjectPlug();
		const Gaffer::ObjectVectorPlug *transformAndObjectPlug() const;

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		bool processesTransform() const override;
		void hashProcessedTransform( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		Imath::M44f computeProcessedTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const override;

		bool processesObject() const override;
		void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const override;

		struct Target
		{
			ScenePath path;
			const ScenePlug *scene;
		};

		bool affectsTarget( const Gaffer::Plug *input ) const;
		std::optional<Target> target() const;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( FramingConstraint )

} // namespace GafferScene
