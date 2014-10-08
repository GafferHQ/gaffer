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

#ifndef GAFFERSCENE_SCENENODE_H
#define GAFFERSCENE_SCENENODE_H

#include "Gaffer/ComputeNode.h"

#include "GafferScene/ScenePlug.h"

namespace GafferScene
{

/// The SceneNode class is the base class for all Nodes which are capable of generating
/// or processing scene graphs.
class SceneNode : public Gaffer::ComputeNode
{

	public :

		SceneNode( const std::string &name=defaultName<SceneNode>() );
		virtual ~SceneNode();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::SceneNode, SceneNodeTypeId, Gaffer::ComputeNode );

		/// All SceneNodes have at least one output ScenePlug for passing on their result. More
		/// may be added by derived classes if necessary.
		ScenePlug *outPlug();
		const ScenePlug *outPlug() const;

		/// The enabled plug provides a mechanism for turning the effect of the node on and off.
		virtual Gaffer::BoolPlug *enabledPlug();
		virtual const Gaffer::BoolPlug *enabledPlug() const;

		/// Implemented so that enabledPlug() affects outPlug().
		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		typedef ScenePlug::ScenePath ScenePath;

		/// Implemented to call the hash*() methods below whenever output is part of a ScenePlug and the node is enabled.
		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		/// Hash methods for the individual children of outPlug(). A derived class must either :
		///
		///    * Implement the method to call the base class implementation and then append to the hash.
		///
		/// or :
		///
		///    * Implement the method to assign directly to the hash from some input hash to signify that
		///      an input will be passed through unchanged by the corresponding compute*() method. Note
		///      that if you wish to pass through an input unconditionally, regardless of context, it is
		///      faster to use a connection as described below.
		///
		/// or :
		///
		///    * Make an input connection into the corresponding plug, so that the hash and compute methods
		///      are never called for it.
		virtual void hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;

		/// Implemented to call the compute*() methods below whenever output is part of a ScenePlug and the node is enabled.
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

		/// Compute methods for the individual children of outPlug() - these must be implemented by derived classes, or
		/// an input connection must be made to the plug, so that the method is not called.
		virtual Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual Imath::M44f computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstCompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstInternedStringVectorDataPtr computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstCompoundObjectPtr computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const;

		/// Convenience function to compute the correct bounding box for a path from the bounding box and transforms of its
		/// children. Using this from computeBound() should be a last resort, as it implies peeking inside children to determine
		/// information about the parent - the last thing we want to be doing when defining large scenes procedurally.
		Imath::Box3f unionOfTransformedChildBounds( const ScenePath &path, const ScenePlug *out ) const;
		/// A hash for the result of the computation in unionOfTransformedChildBounds().
		IECore::MurmurHash hashOfTransformedChildBounds( const ScenePath &path, const ScenePlug *out ) const;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( SceneNode )

} // namespace GafferScene

#endif // GAFFERSCENE_SCENENODE_H
