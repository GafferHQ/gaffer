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

#pragma once

#include "GafferScene/BranchCreator.h"

namespace GafferScene
{

class GAFFERSCENE_API Scatter : public BranchCreator
{

	public :

		explicit Scatter( const std::string &name=defaultName<Scatter>() );
		~Scatter() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::Scatter, ScatterTypeId, BranchCreator );

		Gaffer::StringPlug *namePlug();
		const Gaffer::StringPlug *namePlug() const;

		Gaffer::FloatPlug *densityPlug();
		const Gaffer::FloatPlug *densityPlug() const;

		Gaffer::StringPlug *densityPrimitiveVariablePlug();
		const Gaffer::StringPlug *densityPrimitiveVariablePlug() const;

		Gaffer::StringPlug *referencePositionPlug();
		const Gaffer::StringPlug *referencePositionPlug() const;

		Gaffer::StringPlug *uvPlug();
		const Gaffer::StringPlug *uvPlug() const;

		Gaffer::StringPlug *primitiveVariablesPlug();
		const Gaffer::StringPlug *primitiveVariablesPlug() const;

		Gaffer::StringPlug *pointTypePlug();
		const Gaffer::StringPlug *pointTypePlug() const;

	protected :

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
		void hashBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const override;

		bool affectsBranchChildNames( const Gaffer::Plug *input ) const override;
		void hashBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstInternedStringVectorDataPtr computeBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Scatter )

} // namespace GafferScene
