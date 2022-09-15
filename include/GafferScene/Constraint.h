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

#ifndef GAFFERSCENE_CONSTRAINT_H
#define GAFFERSCENE_CONSTRAINT_H

#include "GafferScene/SceneElementProcessor.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferScene
{

class GAFFERSCENE_API Constraint : public SceneElementProcessor
{

	public :

		Constraint( const std::string &name=defaultName<Constraint>() );
		~Constraint() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::Constraint, ConstraintTypeId, SceneElementProcessor );

		enum TargetMode
		{
			Origin = 0,
			BoundMin = 1,
			BoundMax = 2,
			BoundCenter = 3,
			UV = 4,
			Vertex = 5
		};

		ScenePlug *targetScenePlug();
		const ScenePlug *targetScenePlug() const;

		Gaffer::StringPlug *targetPlug();
		const Gaffer::StringPlug *targetPlug() const;

		Gaffer::BoolPlug *ignoreMissingTargetPlug();
		const Gaffer::BoolPlug *ignoreMissingTargetPlug() const;

		Gaffer::IntPlug *targetModePlug();
		const Gaffer::IntPlug *targetModePlug() const;

		Gaffer::V2fPlug *targetUVPlug();
		const Gaffer::V2fPlug *targetUVPlug() const;

		Gaffer::IntPlug *targetVertexPlug();
		const Gaffer::IntPlug *targetVertexPlug() const;

		Gaffer::V3fPlug *targetOffsetPlug();
		const Gaffer::V3fPlug *targetOffsetPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		/// Reimplemented from SceneElementProcessor to call the constraint functions below.
		bool processesTransform() const override;
		void hashProcessedTransform( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		Imath::M44f computeProcessedTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const override;

		/// Must be implemented to return true if the specified plug affects the computation of the constraint.
		virtual bool affectsConstraint( const Gaffer::Plug *input ) const = 0;
		/// Must be implemented to hash in any plugs which will be used in computing the constraint.
		virtual void hashConstraint( const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		/// Must be implemented to return a new full (absolute in world space) transform constraining fullInputTransform to
		/// fullTargetTransform in some way.
		virtual Imath::M44f computeConstraint( const Imath::M44f &fullTargetTransform, const Imath::M44f &fullInputTransform, const Imath::M44f &inputTransform ) const = 0;

	private :

		// Plug used to cache the matrix computed from the `TargetMode`
		// separately. The UV mode in particular is expensive, and caching it
		// separately allows us to avoid repeating that part of the computation
		// when the geometry is static but the transform is animated.
		const Gaffer::M44fPlug *targetModeMatrixPlug() const;

		bool affectsTargetModeMatrix( const Gaffer::Plug *input ) const;
		void hashTargetModeMatrix( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		Imath::M44f computeTargetModeMatrix( const Gaffer::Context *context ) const;

		struct Target
		{
			ScenePath path;
			const ScenePlug *scene;
		};

		bool affectsTarget( const Gaffer::Plug *input ) const;
		std::optional<Target> target() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Constraint )

} // namespace GafferScene

#endif // GAFFERSCENE_CONSTRAINT_H
