//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "Gaffer/DependencyNode.h"

#include "GafferScene/ScenePlug.h"

namespace GafferScene
{

/// The SceneNode class is the base class for all Nodes which are capable of generating
/// or processing scene graphs.
class SceneNode : public Gaffer::DependencyNode
{

	public :

		SceneNode( const std::string &name=staticTypeName() );
		virtual ~SceneNode();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( SceneNode, SceneNodeTypeId, Gaffer::DependencyNode );
		
		/// All SceneNodes have at least one output ScenePlug for passing on their result. More
		/// may be added by derived classes if necessary.
		ScenePlug *outPlug();
		const ScenePlug *outPlug() const;
				
	protected :
		
		typedef std::string ScenePath;
		
		/// Implemented to call the compute*() methods below whenever output is part of a ScenePlug.
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;
		
		virtual Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const = 0;
		virtual Imath::M44f computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const = 0;
		virtual IECore::ConstCompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const = 0;
		virtual IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const = 0;
		virtual IECore::ConstStringVectorDataPtr computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const = 0;
		virtual IECore::ConstObjectVectorPtr computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const = 0;
		
		/// Convenience function to compute the correct bounding box for a path from the bounding box and transforms of its
		/// children. Using this from computeBound() should be a last resort, as it implies peeking inside children to determine
		/// information about the parent - the last thing we want to be doing when defining large scenes procedurally.
		Imath::Box3f unionOfTransformedChildBounds( const ScenePath &path, const ScenePlug *out ) const;
		/// A hash for the result of the computation in unionOfTransformedChildBounds().
		IECore::MurmurHash hashOfTransformedChildBounds( const ScenePath &path, const ScenePlug *out ) const;
	
	private :
	
		static size_t g_firstPlugIndex;
		
};

} // namespace GafferScene

#endif // GAFFERSCENE_SCENENODE_H
