//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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
#include "Gaffer/PlugIterator.h"
#include "Gaffer/FilteredChildIterator.h"

#include "IECore/Object.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Plug )
IE_CORE_FORWARDDECLARE( ValuePlug )
IE_CORE_FORWARDDECLARE( Node )
IE_CORE_FORWARDDECLARE( ScriptNode )
IE_CORE_FORWARDDECLARE( Context )

class Node : public GraphComponent
{

	public :

		Node( const std::string &name=staticTypeName() );
		virtual ~Node();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Node, NodeTypeId, GraphComponent );

		typedef boost::signal<void (Plug *)> UnaryPlugSignal;
		typedef boost::signal<void (Plug *, Plug *)> BinaryPlugSignal;
		
		typedef std::vector<const ValuePlug *> AffectedPlugsContainer;
		
		/// @name Plug signals
		/// These signals are emitted on events relating to child Plugs
		/// of this Node. They are implemented on the Node rather than
		/// on individual Plugs to limit the proliferation of huge numbers
		/// of signals.
		//////////////////////////////////////////////////////////////
		//@{
		/// Called when the value on a plug of this node is set.
		UnaryPlugSignal &plugSetSignal();
		/// Called when a plug of this node is dirtied.
		UnaryPlugSignal &plugDirtiedSignal();
		/// Called when the input changes on a plug of this node.
		UnaryPlugSignal &plugInputChangedSignal();
		//@}
		
		/// Convenience function which simply returns ancestor<ScriptNode>()
		ScriptNodePtr scriptNode();
		/// Convenience function which simply returns ancestor<ScriptNode>()
		ConstScriptNodePtr scriptNode() const;
		
		/// Accepts only Nodes and Plugs.
		virtual bool acceptsChild( const GraphComponent *potentialChild ) const;
		/// Accepts only Nodes.
		virtual bool acceptsParent( const GraphComponent *potentialParent ) const;
				
		/// Must be implemented to fill outputs with all the plugs whose computation
		/// will be affected by the specified input.
		virtual void affects( const ValuePlug *input, AffectedPlugsContainer &outputs ) const;
		
	protected :

		/// May be overridden to restrict the inputs that plugs on this node will
		/// accept. Default implementation accepts all plugs. Note that
		/// PlugType::acceptsInput() must also be true to allow a successful
		/// connection, so this function may only place additional restrictions on
		/// inputs - it cannot enable inputs that the plugs themselves will not accept.
		/// This is protected, and its results are made public by Plug::acceptsInput()
		/// which calls through to this.
		virtual bool acceptsInput( const Plug *plug, const Plug *inputPlug ) const;
		
		/// Called to compute the hashes for output Plugs. Must be implemented to call the base
		/// class method, then call input->hash( h ) for all input plugs used in the computation
		/// of output. Must also hash in the value of any context items that will be accessed by
		/// the computation.
		///
		/// In the special case that the node will pass through a value from an input plug
		/// unchanged, the hash for the input plug should be assigned directly to the result
		/// (rather than appended) - this allows cache entries to be shared.
		virtual void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const;
		/// Called to compute the values for output Plugs. Must be implemented to compute
		/// an appropriate value and apply it using output->setValue().
		virtual void compute( ValuePlug *output, const Context *context ) const;

		/// Implemented to remove all connections when the node is being
		/// unparented.
		virtual void parentChanging( Gaffer::GraphComponent *newParent );
		
	private :
		
		friend class Plug;
		friend class ValuePlug;
	
		UnaryPlugSignal m_plugSetSignal;
		UnaryPlugSignal m_plugDirtiedSignal;
		UnaryPlugSignal m_plugInputChangedSignal;
		
};

typedef FilteredChildIterator<TypePredicate<Node> > ChildNodeIterator;

} // namespace Gaffer

#endif // GAFFER_NODE_H
