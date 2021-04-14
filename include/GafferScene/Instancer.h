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

#ifndef GAFFERSCENE_INSTANCER_H
#define GAFFERSCENE_INSTANCER_H

#include "GafferScene/BranchCreator.h"

namespace GafferScene
{

class GAFFERSCENE_API Instancer : public BranchCreator
{

	public :


		/// Compound plug for representing an image format in a way
		/// easily edited by users, with individual child plugs for
		/// each aspect of the format.
		class ContextVariablePlug : public Gaffer::ValuePlug
		{

			public :

				GAFFER_PLUG_DECLARE_TYPE( ContextVariablePlug, InstancerContextVariablePlugTypeId, Gaffer::ValuePlug );

				ContextVariablePlug(
					const std::string &name = defaultName<ContextVariablePlug>(),
					Direction direction=In,
					bool defaultEnable = true,
					unsigned flags = Default
				);

				~ContextVariablePlug() override;

				/// Accepts no children following construction.
				bool acceptsChild( const GraphComponent *potentialChild ) const override;
				Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

				Gaffer::BoolPlug *enabledPlug();
				const Gaffer::BoolPlug *enabledPlug() const;

				Gaffer::StringPlug *namePlug();
				const Gaffer::StringPlug *namePlug() const;

				Gaffer::FloatPlug *quantizePlug();
				const Gaffer::FloatPlug *quantizePlug() const;

		};

		IE_CORE_DECLAREPTR( ContextVariablePlug );

		Instancer( const std::string &name=defaultName<Instancer>() );
		~Instancer() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::Instancer, InstancerTypeId, BranchCreator );

		enum class PrototypeMode
		{
			IndexedRootsList = 0,
			IndexedRootsVariable,
			RootPerVertex,
		};

		Gaffer::StringPlug *namePlug();
		const Gaffer::StringPlug *namePlug() const;

		ScenePlug *prototypesPlug();
		const ScenePlug *prototypesPlug() const;

		Gaffer::IntPlug *prototypeModePlug();
		const Gaffer::IntPlug *prototypeModePlug() const;

		Gaffer::StringPlug *prototypeIndexPlug();
		const Gaffer::StringPlug *prototypeIndexPlug() const;

		Gaffer::StringPlug *prototypeRootsPlug();
		const Gaffer::StringPlug *prototypeRootsPlug() const;

		Gaffer::StringVectorDataPlug *prototypeRootsListPlug();
		const Gaffer::StringVectorDataPlug *prototypeRootsListPlug() const;

		Gaffer::StringPlug *idPlug();
		const Gaffer::StringPlug *idPlug() const;

		Gaffer::StringPlug *positionPlug();
		const Gaffer::StringPlug *positionPlug() const;

		Gaffer::StringPlug *orientationPlug();
		const Gaffer::StringPlug *orientationPlug() const;

		Gaffer::StringPlug *scalePlug();
		const Gaffer::StringPlug *scalePlug() const;

		Gaffer::StringPlug *attributesPlug();
		const Gaffer::StringPlug *attributesPlug() const;

		Gaffer::StringPlug *attributePrefixPlug();
		const Gaffer::StringPlug *attributePrefixPlug() const;

		Gaffer::BoolPlug *encapsulateInstanceGroupsPlug();
		const Gaffer::BoolPlug *encapsulateInstanceGroupsPlug() const;

		Gaffer::BoolPlug *seedEnabledPlug();
		const Gaffer::BoolPlug *seedEnabledPlug() const;

		Gaffer::StringPlug *seedVariablePlug();
		const Gaffer::StringPlug *seedVariablePlug() const;

		Gaffer::IntPlug *seedsPlug();
		const Gaffer::IntPlug *seedsPlug() const;

		Gaffer::IntPlug *seedPermutationPlug();
		const Gaffer::IntPlug *seedPermutationPlug() const;

		Gaffer::BoolPlug *rawSeedPlug();
		const Gaffer::BoolPlug *rawSeedPlug() const;

		Gaffer::ValuePlug *contextVariablesPlug();
		const Gaffer::ValuePlug *contextVariablesPlug() const;

		ContextVariablePlug *timeOffsetPlug();
		const ContextVariablePlug *timeOffsetPlug() const;

		Gaffer::AtomicCompoundDataPlug *variationsPlug();
		const Gaffer::AtomicCompoundDataPlug *variationsPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;
		Gaffer::ValuePlug::CachePolicy hashCachePolicy( const Gaffer::ValuePlug *output ) const override;

		bool affectsBranchBound( const Gaffer::Plug *input ) const override;
		void hashBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		Imath::Box3f computeBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const override;

		bool affectsBranchTransform( const Gaffer::Plug *input ) const override;
		void hashBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		Imath::M44f computeBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const override;

		bool affectsBranchAttributes( const Gaffer::Plug *input ) const override;
		void hashBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundObjectPtr computeBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const override;

		bool affectsBranchObject( const Gaffer::Plug *input ) const override;
		// Implemented to remove the parent object, because we "convert" the points into a hierarchy
		bool processesRootObject() const override;
		void hashBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const override;

		void hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;

		bool affectsBranchChildNames( const Gaffer::Plug *input ) const override;
		void hashBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstInternedStringVectorDataPtr computeBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const override;

		void hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		IECore::ConstInternedStringVectorDataPtr computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;

		bool affectsBranchSetNames( const Gaffer::Plug *input ) const override;
		void hashBranchSetNames( const ScenePath &sourcePath, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstInternedStringVectorDataPtr computeBranchSetNames( const ScenePath &sourcePath, const Gaffer::Context *context ) const override;

		bool affectsBranchSet( const Gaffer::Plug *input ) const override;
		void hashBranchSet( const ScenePath &sourcePath, const IECore::InternedString &setName, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstPathMatcherDataPtr computeBranchSet( const ScenePath &sourcePath, const IECore::InternedString &setName, const Gaffer::Context *context ) const override;

		void hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		IECore::ConstPathMatcherDataPtr computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const override;

	private :

		IE_CORE_FORWARDDECLARE( EngineData );

		Gaffer::ObjectPlug *enginePlug();
		const Gaffer::ObjectPlug *enginePlug() const;

		Gaffer::AtomicCompoundDataPlug *prototypeChildNamesPlug();
		const Gaffer::AtomicCompoundDataPlug *prototypeChildNamesPlug() const;

		GafferScene::ScenePlug *capsuleScenePlug();
		const GafferScene::ScenePlug *capsuleScenePlug() const;

		// This plug does heavy lifting when necessary to do an expensive set plug computation
		// It uses a TaskCollaborate policy to allow threads to cooperate, and is evaluated with
		// a scenePath in the context to return a PathMatcher for the set contents for one branch
		Gaffer::PathMatcherDataPlug *setCollaboratePlug();
		const Gaffer::PathMatcherDataPlug *setCollaboratePlug() const;

		ConstEngineDataPtr engine( const ScenePath &sourcePath, const Gaffer::Context *context ) const;
		void engineHash( const ScenePath &sourcePath, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		IECore::ConstCompoundDataPtr prototypeChildNames( const ScenePath &sourcePath, const Gaffer::Context *context ) const;
		void prototypeChildNamesHash( const ScenePath &sourcePath, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		struct PrototypeScope : public Gaffer::Context::EditableScope
		{
			PrototypeScope( const Gaffer::ObjectPlug *enginePlug, const Gaffer::Context *context, const ScenePath *parentPath, const ScenePath *branchPath );
		private:
			ScenePlug::ScenePath m_prototypePath;
		};

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Instancer )

} // namespace GafferScene

#endif // GAFFERSCENE_INSTANCER_H
