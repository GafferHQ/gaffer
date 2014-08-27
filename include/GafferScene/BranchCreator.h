//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFERSCENE_BRANCHCREATOR_H
#define GAFFERSCENE_BRANCHCREATOR_H

#include "GafferScene/SceneProcessor.h"
#include "GafferScene/Filter.h"

namespace GafferScene
{

class BranchCreator : public SceneProcessor
{

	public :

		virtual ~BranchCreator();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::BranchCreator, BranchCreatorTypeId, SceneProcessor );

		/// \todo Allow multiple parents to be specified.
		Gaffer::StringPlug *parentPlug();
		const Gaffer::StringPlug *parentPlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		BranchCreator( const std::string &name=defaultName<BranchCreator>() );

		/// Implemented for mappingPlug().
		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

		/// Implemented in terms of the hashBranch*() methods below - derived classes must implement those methods
		/// rather than these ones.
		virtual void hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;

		/// Implemented in terms of the computeBranch*() methods below - derived classes must implement those methods
		/// rather than these ones.
		virtual Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual Imath::M44f computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstCompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstInternedStringVectorDataPtr computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstCompoundObjectPtr computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const;

		/// @name Branch evaluation methods
		/// These must be implemented by derived classes. The hashBranch*() methods must either :
		///
		///   - Call the base class implementation and then append to the hash with anything that
		///     will be used in the corresponding computeBranch*() method.
		///
		/// or :
		///
		///   - Assign directly to the hash from an input hash to signify that the input will be
		///     passed through unchanged by the corresponding computBranch*() method.
		///
		//@{
		virtual void hashBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		virtual Imath::Box3f computeBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const = 0;

		virtual void hashBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		virtual Imath::M44f computeBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const = 0;

		virtual void hashBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		virtual IECore::ConstCompoundObjectPtr computeBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const = 0;

		virtual void hashBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		virtual IECore::ConstObjectPtr computeBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const = 0;

		virtual void hashBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		virtual IECore::ConstInternedStringVectorDataPtr computeBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const = 0;
		//@}

	private :

		/// Used to calculate the name remapping needed to prevent name clashes with
		/// the existing scene.
		Gaffer::ObjectPlug *mappingPlug();
		const Gaffer::ObjectPlug *mappingPlug() const;

		void hashMapping( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		IECore::ConstCompoundDataPtr computeMapping( const Gaffer::Context *context ) const;

		// Computes the relevant parent and branch paths for computing the result
		// at the specified path. Returns a Filter::Result to describe where path is
		// relative to the parent, as follows :
		//
		// AncestorMatch
		//
		// The path is on a branch below the parent, parentPath and branchPath
		// are filled in appropriately, and branchPath will not be empty.
		//
		// ExactMatch
		//
		// The path is at the parent exactly, parentPath will be filled
		// in appropriately and branchPath will be empty.
		//
		// DescendantMatch
		//
		// The path is above the parent, parentPath will be filled in
		// appropriately and branchPath will be empty.
		//
		// NoMatch
		//
		// The path is a direct pass through from the input - neither
		// parentPath nor branchPath will be filled in.
		Filter::Result parentAndBranchPaths( const IECore::CompoundData *mapping, const ScenePath &path, ScenePath &parentPath, ScenePath &branchPath ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( BranchCreator )

} // namespace GafferScene

#endif // GAFFERSCENE_BRANCHCREATOR_H
