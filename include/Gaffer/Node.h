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

class Node : public GraphComponent
{

	public :

		Node( const std::string &name=staticTypeName() );
		virtual ~Node();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Node, NodeTypeId, GraphComponent );

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
		
		/// @name Enable/Disable Behaviour
		/// Nodes can optionally define a means of being enabled and disabled.
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
