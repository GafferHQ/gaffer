//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

/// Threading
///
///		- can we allow multiple computes() at once?
///		- or do we have to resort to computes() being threaded internally?
///		- perhaps we could have a method which takes a bunch of input plugs, and guarantees
///		  that they'll have been computed upon return? that method could deal with the threading.
///		- do we need to separate plugs from the values they hold? so we can deal with computes()
///		  at different times? and if we did that then does that help with the threading?
///			- if we did that and used CompoundObject as a DataBlock then we could map IECore::Parameters
///			  straight to Plugs very very easily.
///				- what is the overhead?
class Node : public GraphComponent
{

	public :

		Node( const std::string &name=staticTypeName() );
		virtual ~Node();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Node, NodeTypeId, GraphComponent );

		typedef boost::signal<void (PlugPtr)> UnaryPlugSignal;
		typedef boost::signal<void (PlugPtr, PlugPtr)> BinaryPlugSignal;
		
		/// @name Plug iterators
		//////////////////////////////////////////////////////////////
		//@{
		PlugIterator plugsBegin() const;
		PlugIterator plugsEnd() const;
		InputPlugIterator inputPlugsBegin() const;
		InputPlugIterator inputPlugsEnd() const;
		OutputPlugIterator outputPlugsBegin() const;
		OutputPlugIterator outputPlugsEnd() const;
		//@}
		
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
		virtual bool acceptsChild( ConstGraphComponentPtr potentialChild ) const;
		/// Accepts only Nodes.
		virtual bool acceptsParent( const GraphComponent *potentialParent ) const;
		
	protected :
		
		/// Called when an input plug becomes dirty. Must be implemented to dirty any
		/// output plugs which depend on the input.
		virtual void dirty( ConstPlugPtr dirty ) const = 0;
		/// Called when getValue() is called on an output plug which is dirty. Must
		/// be implemented to calculate and set the value for this Plug.
		virtual void compute( PlugPtr output ) const = 0;
		
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
