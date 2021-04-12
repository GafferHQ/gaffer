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

#include "GafferScene/FilteredSceneProcessor.h"

#include "Gaffer/TypedObjectPlug.h"

#include "IECore/CompoundData.h"

#include "boost/optional.hpp"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferScene
{

/// A base class to simplify the process of creating new branches in the scene
/// hierarchy. The source data for each branch is specified by the input
/// locations matched by the filter. By default, the branches are made
/// underneath the source locations, but they can be relocated by using the
/// `destination` plug. We use the following terminology :
///
/// - `sourcePath` : An input location matched by `filter`. Each source will create
///   exactly one branch.
/// - `destinationPath` : The location where branch will be created in the output scene.
///   This is specified by `destinationPlug()`, and defaults to `sourcePath`. Multiple
///   branches may have the same destination, but this is handled transparently and
///   doesn't affect derived classes. In the case of branches at the same destination
///   having identical names, numeric suffixes are appended automatically to uniquefy them.
/// - `branchPath` : A path to a location within a branch, specified relative to `destinationPath`.
///   The primary responsibility of derived classes is to generate data for `branchPath` from the
///   information provided by `sourcePath`.
///
/// > Note : The unfortunately-named `parent` plug specifies a `sourcePath` to be used when
/// > no filter is connected. It is a historical artifact from when BranchCreator didn't
/// > support filtering. It remains for backwards compatibility and because it is useful for
/// > simple uses in the Parent node.
class GAFFERSCENE_API BranchCreator : public FilteredSceneProcessor
{

	public :

		~BranchCreator() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::BranchCreator, BranchCreatorTypeId, FilteredSceneProcessor );

		Gaffer::StringPlug *parentPlug();
		const Gaffer::StringPlug *parentPlug() const;

		Gaffer::StringPlug *destinationPlug();
		const Gaffer::StringPlug *destinationPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		BranchCreator( const std::string &name=defaultName<BranchCreator>() );

		/// Implemented for mappingPlug().
		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		/// Implemented in terms of the hashBranch*() methods below - derived classes must implement those methods
		/// rather than these ones.
		void hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;

		/// Implemented in terms of the computeBranch*() methods below - derived classes must implement those methods
		/// rather than these ones.
		Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		Imath::M44f computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstCompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstInternedStringVectorDataPtr computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstInternedStringVectorDataPtr computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstPathMatcherDataPtr computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const override;

		Gaffer::ValuePlug::CachePolicy hashCachePolicy( const Gaffer::ValuePlug *output ) const override;
		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;

		/// @name Branch evaluation methods
		/// These must be implemented by derived classes. The hashBranch*() methods must either :
		///
		///   - Call the base class implementation and then append to the hash with anything that
		///     will be used in the corresponding computeBranch*() method.
		///
		/// or :
		///
		///   - Assign directly to the hash from an input hash to signify that the input will be
		///     passed through unchanged by the corresponding computeBranch*() method.
		///
		/// \todo Make all these methods pure virtual.
		//@{
		virtual bool affectsBranchBound( const Gaffer::Plug *input ) const;
		virtual void hashBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		virtual Imath::Box3f computeBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const = 0;

		virtual bool affectsBranchTransform( const Gaffer::Plug *input ) const;
		virtual void hashBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		virtual Imath::M44f computeBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const = 0;

		virtual bool affectsBranchAttributes( const Gaffer::Plug *input ) const;
		virtual void hashBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		virtual IECore::ConstCompoundObjectPtr computeBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const = 0;

		virtual bool affectsBranchObject( const Gaffer::Plug *input ) const;
		/// \deprecated
		virtual bool processesRootObject() const;
		virtual void hashBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		virtual IECore::ConstObjectPtr computeBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const = 0;

		virtual bool affectsBranchChildNames( const Gaffer::Plug *input ) const;
		virtual void hashBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		virtual IECore::ConstInternedStringVectorDataPtr computeBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const = 0;

		virtual bool affectsBranchSetNames( const Gaffer::Plug *input ) const;
		virtual void hashBranchSetNames( const ScenePath &parentPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstInternedStringVectorDataPtr computeBranchSetNames( const ScenePath &parentPath, const Gaffer::Context *context ) const;
		/// Called to determine if all branches have the same set names. If it returns true,
		/// `computeSetNames()` calls `computeBranchSetNames()` just once, with an empty `parentPath`,
		/// rather than having to accumulate all names from all branches. The default implementation
		/// returns true.
		virtual bool constantBranchSetNames() const;

		virtual bool affectsBranchSet( const Gaffer::Plug *input ) const;
		virtual void hashBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstPathMatcherDataPtr computeBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context ) const;
		//@}

		// Computes the relevant source and branch paths for computing the result
		// at the specified path. Returns a PathMatcher::Result to describe where path is
		// relative to the branch destination, as follows :
		//
		// AncestorMatch
		//
		// The path is on a branch below the destination, `sourcePath` and `branchPath`
		// are filled in appropriately, and `branchPath` will not be empty.
		//
		// ExactMatch
		//
		// The path is at the branch destination exactly. Neither `sourcePath` nor `branchPath`
		// will be filled in.
		//
		// DescendantMatch
		//
		// The path is above one or more branch destinations. Neither `sourcePath` nor `branchPath`
		// will be filled in.
		//
		// NoMatch
		//
		// The path is a direct pass through from the input - neither
		// `sourcePath` nor `branchPath` will be filled in.
		IECore::PathMatcher::Result sourceAndBranchPaths( const ScenePath &path, ScenePath &sourcePath, ScenePath &branchPath ) const;
		/// \deprecated
		IECore::PathMatcher::Result parentAndBranchPaths( const ScenePath &path, ScenePath &parentPath, ScenePath &branchPath ) const;

	private :

		IE_CORE_FORWARDDECLARE( BranchesData );

		/// Returns the path specified by `parentPlug()`, only if it is non-empty
		/// and is valid within the input scene.
		boost::optional<ScenePlug::ScenePath> parentPlugPath() const;

		/// BranchesData telling us what branches we need to make.
		Gaffer::ObjectPlug *branchesPlug();
		const Gaffer::ObjectPlug *branchesPlug() const;
		/// Calls `branchesPlug()->getValue()` in a clean context and
		/// returns the result. This must be used for all access to
		/// `branchesPlug()`.
		ConstBranchesDataPtr branches( const Gaffer::Context *context ) const;

		/// Used to calculate the name remapping needed to prevent name clashes
		/// with the existing scene. Must be evaluated in a context where
		/// "scene:path" is one of the destination paths. This is mapping is
		/// computed separately from `branchesPlug()` so that we can delay calls
		/// to `hashBranch*()` and `computeBranch*()` till as late as possible.
		Gaffer::ObjectPlug *mappingPlug();
		const Gaffer::ObjectPlug *mappingPlug() const;

		void hashMapping( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		IECore::ConstDataPtr computeMapping( const Gaffer::Context *context ) const;

		// Returns `branches()` if it should be used to compute a set, otherwise `nullptr`.
		ConstBranchesDataPtr branchesForSet( const IECore::InternedString &setName, const Gaffer::Context *context ) const;
		bool affectsBranchesForSet( const Gaffer::Plug *input ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( BranchCreator )

} // namespace GafferScene

#endif // GAFFERSCENE_BRANCHCREATOR_H
