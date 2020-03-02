//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

#ifndef GAFFERSCENE_MERGESCENES_H
#define GAFFERSCENE_MERGESCENES_H

#include "GafferScene/SceneProcessor.h"

#include <bitset>

namespace GafferScene
{

class GAFFERSCENE_API MergeScenes : public SceneProcessor
{

	public :

		MergeScenes( const std::string &name=defaultName<MergeScenes>() );
		~MergeScenes() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferScene::MergeScenes, MergeScenesTypeId, SceneProcessor );

		enum class Mode
		{
			Keep,
			Replace,
			Merge
		};

		Gaffer::IntPlug *transformModePlug();
		const Gaffer::IntPlug *transformModePlug() const;

		Gaffer::IntPlug *attributesModePlug();
		const Gaffer::IntPlug *attributesModePlug() const;

		Gaffer::IntPlug *objectModePlug();
		const Gaffer::IntPlug *objectModePlug() const;

		Gaffer::IntPlug *globalsModePlug();
		const Gaffer::IntPlug *globalsModePlug() const;

		Gaffer::BoolPlug *adjustBoundsPlug();
		const Gaffer::BoolPlug *adjustBoundsPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		void hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;

		void hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		Imath::M44f computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;

		void hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;

		void hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;

		void hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		IECore::ConstInternedStringVectorDataPtr computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;

		void hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundObjectPtr computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const override;

		void hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		IECore::ConstInternedStringVectorDataPtr computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const override;

		void hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		IECore::ConstPathMatcherDataPtr computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const override;

	private :

		using InputMask = std::bitset<32>;

		// Plugs used to track which inputs are valid
		// at the current location. The value can be
		// converted directly to an `InputMask` for use
		// with `visit()`.
		Gaffer::IntPlug *activeInputsPlug();
		const Gaffer::IntPlug *activeInputsPlug() const;

		Gaffer::AtomicBox3fPlug *mergedDescendantsBoundPlug();
		const Gaffer::AtomicBox3fPlug *mergedDescendantsBoundPlug() const;

		void hashActiveInputs( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		int computeActiveInputs( const Gaffer::Context *context ) const;

		void hashMergedDescendantsBound( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		const Imath::Box3f computeMergedDescendantsBound( const Gaffer::Context *context ) const;

		enum class InputType
		{
			Sole,
			First,
			Other
		};

		enum VisitOrder
		{
			Forwards,
			Backwards,
			FirstOnly,
			LastOnly
		};

		VisitOrder visitOrder( Mode mode, VisitOrder replaceOrder = VisitOrder::LastOnly ) const;
		InputMask connectedInputs() const;

		// Calls `visitor( inputType, inputIndex, input )` for all inputs specified by `inputMask`.
		// Visitor may return `true` to continue to subsequent inputs or `false` to stop iteration.
		template<typename Visitor>
		void visit( InputMask inputMask, Visitor &&visitor, VisitOrder order = VisitOrder::Forwards ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( MergeScenes )

} // namespace GafferScene

#endif // GAFFERSCENE_MERGESCENES_H
