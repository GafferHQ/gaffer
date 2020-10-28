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

#ifndef GAFFER_DEPENDENCYNODE_H
#define GAFFER_DEPENDENCYNODE_H

#include "Gaffer/Node.h"
#include "Gaffer/TypedPlug.h"

namespace Gaffer
{

/// DependencyNodes extend the Node concept to define dependencies between the input
/// and output plugs, with the implication being that outputs represent the result of some
/// operation the node will perform based on the inputs. These dependencies allow the ripple
/// down effect of changes to an input plug to be tracked through the graph. Note however that
/// the DependencyNode does not define how operations should be performed - see the ComputeNode
/// derived class for the primary means of achieving that.
class GAFFER_API DependencyNode : public Node
{

	public :

		DependencyNode( const std::string &name=defaultName<DependencyNode>() );
		~DependencyNode() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::DependencyNode, DependencyNodeTypeId, Node );

		typedef std::vector<const Plug *> AffectedPlugsContainer;

		/// Must be implemented to fill outputs with all the plugs whose computation
		/// will be affected by the specified input. It is an error to pass a compound plug
		/// for input or to place one in outputs as computations are always performed on the
		/// leaf level plugs only. Implementations of this method should call the base class
		/// implementation first.
		/// \todo Make this protected, and add an accessor on the Plug class instead.
		/// The general principle in effect elsewhere in Gaffer is that plugs provide
		/// the public interface to the work done by nodes.
		virtual void affects( const Plug *input, AffectedPlugsContainer &outputs ) const = 0;

		/// @name Enable/Disable Behaviour
		/// DependencyNodes can optionally define a means of being enabled and disabled.
		/// If they do, then they can also specify an input plug corresponding
		/// to each output plug. By providing a corresponding plug, the node
		/// is promising that the input will pass-through to the output in some
		/// meaningful way when the node is disabled.
		//////////////////////////////////////////////////////////////
		//@{
		/// Returns the enable plug, or 0 if this node is not disable-able.
		virtual BoolPlug *enabledPlug();
		virtual const BoolPlug *enabledPlug() const;
		/// Returns the input plug corresponding to the given output plug. Note that each
		/// node is responsible for ensuring that this correspondence is respected.
		virtual Plug *correspondingInput( const Plug *output );
		virtual const Plug *correspondingInput( const Plug *output ) const;
		//@}

};

/// \deprecated Use DependencyNode::Iterator etc instead.
typedef FilteredChildIterator<TypePredicate<DependencyNode> > DependencyNodeIterator;
typedef FilteredRecursiveChildIterator<TypePredicate<DependencyNode> > RecursiveDependencyNodeIterator;

} // namespace Gaffer

#endif // GAFFER_DEPENDENCYNODE_H
