//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_NODE_H
#define GAFFER_NODE_H

#include "Gaffer/GraphComponent.h"
#include "Gaffer/FilteredChildIterator.h"
#include "Gaffer/FilteredRecursiveChildIterator.h"
#include "Gaffer/TypedPlug.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( CompoundPlug )
IE_CORE_FORWARDDECLARE( ScriptNode )

/// The primary class from which node graphs are constructed. Nodes may
/// have any number of child plugs which provide values and/or define connections
/// to the plugs of other nodes. They provide signals for the monitoring of changes
/// to the plugs and their values, flags and connections. The Node class itself
/// doesn't define any means of performing computations - this is instead provided by
/// the DependencyNode and ComputeNode derived classes.
class Node : public GraphComponent
{

	public :

		Node( const std::string &name=defaultName<Node>() );
		virtual ~Node();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::Node, NodeTypeId, GraphComponent );

		typedef boost::signal<void (Plug *)> UnaryPlugSignal;
		typedef boost::signal<void (Plug *, Plug *)> BinaryPlugSignal;
				
		/// @name Plug signals
		/// These signals are emitted on events relating to child Plugs
		/// of this Node. They are implemented on the Node rather than
		/// on individual Plugs to limit the proliferation of huge numbers
		/// of signals.
		//////////////////////////////////////////////////////////////
		//@{
		/// Called when the value of an unconnected input plug of
		/// this node is set.
		UnaryPlugSignal &plugSetSignal();
		/// Called when the input changes on a plug of this node.
		UnaryPlugSignal &plugInputChangedSignal();
		/// Called when the flags are changed for a plug of this node.
		UnaryPlugSignal &plugFlagsChangedSignal();
		/// Called when a plug of this node is dirtied - this signifies that
		/// any previously calculated values are invalid and should be recalculated.
		/// Although only DependencyNodes can define the relationships necessary
		/// for dirtying a plug, the signal is defined on the Node base class,
		/// because dirtiness may be propagated from an output plug of a DependencyNode
		/// onto an input plug of a plain Node (and potentially onwards if that plug
		/// has its own output connections).
		UnaryPlugSignal &plugDirtiedSignal();
		//@}
		
		/// It's common for users to want to create their own plugs on
		/// nodes for the purposes of driving expressions and suchlike.
		/// So that there is no danger of name clashes between such plugs
		/// and plugs Gaffer itself might add in the future, this CompoundPlug
		/// is provided, under which users may add any plugs they want. Plugs
		/// added to the user plug will need the Plug::Dynamic flag to be set
		/// so that they can be saved and loaded successfully.
		Gaffer::CompoundPlug *userPlug();
		const Gaffer::CompoundPlug *userPlug() const;

		/// Convenience function which simply returns ancestor<ScriptNode>()
		ScriptNode *scriptNode();
		/// Convenience function which simply returns ancestor<ScriptNode>()
		const ScriptNode *scriptNode() const;
		
		/// Accepts only Nodes and Plugs.
		virtual bool acceptsChild( const GraphComponent *potentialChild ) const;
		/// Accepts only Nodes.
		virtual bool acceptsParent( const GraphComponent *potentialParent ) const;
	
	protected :

		/// May be overridden to restrict the inputs that plugs on this node will
		/// accept. Default implementation accepts all plugs. Note that
		/// PlugType::acceptsInput() must also be true to allow a successful
		/// connection, so this function may only place additional restrictions on
		/// inputs - it cannot enable inputs that the plugs themselves will not accept.
		/// Similarly, when overriding this method, you must first call the base class
		/// implementation, and only return true if that too returned true. In other
		/// words, classes must not be more permissive than their base classes
		/// in accepting connections.
		/// 
		/// This is protected, and its results are made public by Plug::acceptsInput()
		/// which calls through to this.
		virtual bool acceptsInput( const Plug *plug, const Plug *inputPlug ) const;
		
		/// Implemented to remove all connections when the node is being
		/// unparented.
		virtual void parentChanging( Gaffer::GraphComponent *newParent );
		
	private :
		
		static size_t g_firstPlugIndex;

		friend class Plug;
	
		UnaryPlugSignal m_plugSetSignal;
		UnaryPlugSignal m_plugInputChangedSignal;
		UnaryPlugSignal m_plugFlagsChangedSignal;
		UnaryPlugSignal m_plugDirtiedSignal;
		
};

IE_CORE_DECLAREPTR( Node )

typedef FilteredChildIterator<TypePredicate<Node> > NodeIterator;
typedef FilteredRecursiveChildIterator<TypePredicate<Node> > RecursiveNodeIterator;

} // namespace Gaffer

#endif // GAFFER_NODE_H
