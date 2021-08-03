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

#ifndef GAFFERSCENE_SUBTREE_H
#define GAFFERSCENE_SUBTREE_H

#include "GafferScene/SceneProcessor.h"

#include "Gaffer/StringPlug.h"

namespace GafferScene
{

/// \todo I think we need a TreeProcessor base class for this, Group and BranchCreator.
/// There would be a single virtual method for servicing queries about the mapping between
/// output and input paths. This would be necessary for backtracking in the SceneInspector
/// to provide information about who modified what.
class GAFFERSCENE_API SubTree : public SceneProcessor
{

	public :

		SubTree( const std::string &name=defaultName<SubTree>() );
		~SubTree() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::SubTree, SubTreeTypeId, SceneProcessor );

		Gaffer::StringPlug *rootPlug();
		const Gaffer::StringPlug *rootPlug() const;

		Gaffer::BoolPlug *includeRootPlug();
		const Gaffer::BoolPlug *includeRootPlug() const;

		Gaffer::BoolPlug *inheritTransformPlug();
		const Gaffer::BoolPlug *inheritTransformPlug() const;

		Gaffer::BoolPlug *inheritAttributesPlug();
		const Gaffer::BoolPlug *inheritAttributesPlug() const;

		Gaffer::BoolPlug *inheritSetMembershipPlug();
		const Gaffer::BoolPlug *inheritSetMembershipPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;

		Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		Imath::M44f computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstCompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstInternedStringVectorDataPtr computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstPathMatcherDataPtr computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const override;

	private :

		enum SourceMode
		{
			Default, // Pass through source path
			CreateRoot, // Create a root
			EmptyRoot, // Create an empty root
		};

		// Generally the work of the SubTree node is easy - we just remap the
		// output path to a source path and pass through the results unchanged from
		// that source path. There are two situations in which this won't work :
		//
		// - When outputPath == "/" and includeRoot == true. In this case we must
		//   actually perform some computation to create the right bounding box and
		//   the right child name.
		// - When outputPath == "/" and !exists( root ). In this case we must return
		//   an empty scene.
		//
		// This method returns the appropriate source path for the default case, and for
		// the more complex cases sets `sourceMode` appropriately and returns the
		// root path itself.
		ScenePath sourcePath( const ScenePath &outputPath, SourceMode &sourceMode ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( SubTree )

} // namespace GafferScene

#endif // GAFFERSCENE_SUBTREE_H
