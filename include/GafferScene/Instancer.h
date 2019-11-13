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

		Instancer( const std::string &name=defaultName<Instancer>() );
		~Instancer() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferScene::Instancer, InstancerTypeId, BranchCreator );

		Gaffer::StringPlug *namePlug();
		const Gaffer::StringPlug *namePlug() const;

		ScenePlug *prototypesPlug();
		const ScenePlug *prototypesPlug() const;

		Gaffer::StringPlug *prototypeIndexPlug();
		const Gaffer::StringPlug *prototypeIndexPlug() const;

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

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		bool affectsBranchBound( const Gaffer::Plug *input ) const override;
		void hashBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		Imath::Box3f computeBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const override;

		bool affectsBranchTransform( const Gaffer::Plug *input ) const override;
		void hashBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		Imath::M44f computeBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const override;

		bool affectsBranchAttributes( const Gaffer::Plug *input ) const override;
		void hashBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundObjectPtr computeBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const override;

		bool affectsBranchObject( const Gaffer::Plug *input ) const override;
		// Implemented to remove the parent object, because we "convert" the points into a hierarchy
		bool processesRootObject() const override;
		void hashBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const override;

		bool affectsBranchChildNames( const Gaffer::Plug *input ) const override;
		void hashBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstInternedStringVectorDataPtr computeBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const override;

		bool affectsBranchSetNames( const Gaffer::Plug *input ) const override;
		void hashBranchSetNames( const ScenePath &parentPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstInternedStringVectorDataPtr computeBranchSetNames( const ScenePath &parentPath, const Gaffer::Context *context ) const override;

		bool affectsBranchSet( const Gaffer::Plug *input ) const override;
		void hashBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstPathMatcherDataPtr computeBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context ) const override;

	private :

		IE_CORE_FORWARDDECLARE( EngineData );

		Gaffer::ObjectPlug *enginePlug();
		const Gaffer::ObjectPlug *enginePlug() const;

		Gaffer::AtomicCompoundDataPlug *prototypeChildNamesPlug();
		const Gaffer::AtomicCompoundDataPlug *prototypeChildNamesPlug() const;

		ConstEngineDataPtr engine( const ScenePath &parentPath, const Gaffer::Context *context ) const;
		void engineHash( const ScenePath &parentPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		IECore::ConstCompoundDataPtr prototypeChildNames( const ScenePath &parentPath, const Gaffer::Context *context ) const;
		void prototypeChildNamesHash( const ScenePath &parentPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		struct PrototypeScope : public Gaffer::Context::EditableScope
		{
			PrototypeScope( const Gaffer::Context *context, const ScenePath &branchPath );
		};

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Instancer )

} // namespace GafferScene

#endif // GAFFERSCENE_INSTANCER_H
