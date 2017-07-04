//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, John Haddon. All rights reserved.
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

#ifndef GAFFERSCENE_DUPLICATE_H
#define GAFFERSCENE_DUPLICATE_H

#include "Gaffer/TransformPlug.h"

#include "GafferScene/Export.h"
#include "GafferScene/BranchCreator.h"

namespace GafferScene
{

class GAFFERSCENE_API Duplicate : public BranchCreator
{

	public :

		Duplicate( const std::string &name=defaultName<Duplicate>() );
		virtual ~Duplicate();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::Duplicate, DuplicateTypeId, BranchCreator );

		Gaffer::StringPlug *targetPlug();
		const Gaffer::StringPlug *targetPlug() const;

		Gaffer::IntPlug *copiesPlug();
		const Gaffer::IntPlug *copiesPlug() const;

		Gaffer::StringPlug *namePlug();
		const Gaffer::StringPlug *namePlug() const;

		Gaffer::TransformPlug *transformPlug();
		const Gaffer::TransformPlug *transformPlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

		virtual void hashBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual Imath::Box3f computeBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const;

		virtual void hashBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual Imath::M44f computeBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const;

		virtual void hashBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstCompoundObjectPtr computeBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const;

		virtual void hashBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstObjectPtr computeBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const;

		virtual void hashBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstInternedStringVectorDataPtr computeBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const;

		virtual void hashBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual GafferScene::ConstPathMatcherDataPtr computeBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context ) const;

	private :

		// The BranchCreator::parentPlug() must be used to define the place where the duplicates
		// are to be parented, but it's much more natural for the user to simply specify which object
		// they want to duplicate, and expect that the duplicates will appear alongside the original.
		// This output plug is used to compute the appropriate parent from the target, and is connected
		// into BranchCreator::parentPlug() so that the user doesn't need to worry about it.
		Gaffer::StringPlug *outParentPlug();
		const Gaffer::StringPlug *outParentPlug() const;

		// We need the list of names of the duplicates in both computeBranchChildNames()
		// and computeBranchTransform(), so we compute it on this intermediate plug so that
		// the list is cached and the work is shared between the two methods.
		Gaffer::InternedStringVectorDataPlug *childNamesPlug();
		const Gaffer::InternedStringVectorDataPlug *childNamesPlug() const;

		void sourcePath( const ScenePath &branchPath, ScenePath &source ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Duplicate )

} // namespace GafferScene

#endif // GAFFERSCENE_DUPLICATE_H
