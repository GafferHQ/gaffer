//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/FilteredChildIterator.h"
#include "Gaffer/FilteredRecursiveChildIterator.h"
#include "Gaffer/GraphComponent.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Plug )
IE_CORE_FORWARDDECLARE( ScriptNode )

#define GAFFER_NODE_DECLARE_TYPE( TYPE, TYPEID, BASETYPE ) \
	IE_CORE_DECLARERUNTIMETYPEDEXTENSION( TYPE, TYPEID, BASETYPE ) \
	using Iterator = Gaffer::FilteredChildIterator<Gaffer::TypePredicate<TYPE>>; \
	using RecursiveIterator = Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<TYPE>, Gaffer::TypePredicate<Gaffer::Node>>; \
	using Range = Gaffer::FilteredChildRange<Gaffer::TypePredicate<TYPE>>; \
	using RecursiveRange = Gaffer::FilteredRecursiveChildRange<Gaffer::TypePredicate<TYPE>, Gaffer::TypePredicate<Gaffer::Node>>;

#define GAFFER_NODE_DEFINE_TYPE( TYPE ) \
	IE_CORE_DEFINERUNTIMETYPED( TYPE )

/// The primary class from which node graphs are constructed. Nodes may
/// have any number of child plugs which provide values and/or define connections
/// to the plugs of other nodes. They provide signals for the monitoring of changes
/// to the plugs and their values, flags and connections. The Node class itself
/// doesn't define any means of performing computations - this is instead provided by
/// the DependencyNode and ComputeNode derived classes.
class GAFFER_API Node : public GraphComponent
{

	public :

		Node( const std::string &name=defaultName<Node>() );
		~Node() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::Node, NodeTypeId, GraphComponent );

		using UnaryPlugSignal = Signals::Signal<void (Plug *), Signals::CatchingCombiner<void>>;
		using BinaryPlugSignal = Signals::Signal<void (Plug *, Plug *), Signals::CatchingCombiner<void>>;

		/// @name Plug signals
		/// These signals are emitted on events relating to child Plugs
		/// of this Node. They are implemented on the Node rather than
		/// on individual Plugs to limit the proliferation of huge numbers
		/// of signals.
		//////////////////////////////////////////////////////////////
		//@{
		/// Emitted immediately after each call to ValuePlug::setValue() for
		/// unconnected input plugs on this node. Also called for all outputs
		/// of such plugs, as in effect they are also having their value set too.
		/// It is acceptable for slots connected to this signal to rewire the
		/// node graph by adding and removing connections and nodes, and changing
		/// the values of other plugs.
		/// \note Passive observers of the plug value should use plugDirtiedSignal()
		/// rather than plugSetSignal().
		UnaryPlugSignal &plugSetSignal();
		/// Emitted immediately when a plug's input is changed. Also emitted
		/// for all outputs of such plugs, as in effect their input is being changed
		/// too. As with plugSetSignal(), it is acceptable for slots connected to
		/// this signal to rewire the node graph.
		UnaryPlugSignal &plugInputChangedSignal();
		/// Emitted when a plug of this node is dirtied - this signifies that any
		/// values previously retrieved from the plug via ValuePlug::getValue() are
		/// now invalid and should be recalculated.
		///
		/// Unlike the signals above, this signal is not emitted immediately. Instead,
		/// a list of dirtied plugs is accumulated as dirtiness is propagated through
		/// the graph and when this propagation is complete, the dirtiness is signalled
		/// for each plug. This means that dirtiness is only signalled once for each plug,
		/// and only when all plugSet and plugInputChanged slots have finished any rewiring
		/// they may wish to perform. A consequence of this is that slots connected to
		/// this signal must not rewire the graph - they should be passive observers only.
		///
		/// \note Although only DependencyNodes can define the relationships necessary
		/// for dirtying a plug, the signal is defined on the Node base class,
		/// because dirtiness may be propagated from an output plug of a DependencyNode
		/// onto an input plug of a plain Node (and potentially onwards if that plug
		/// has its own output connections).
		UnaryPlugSignal &plugDirtiedSignal();
		//@}

		/// It's common for users to want to create their own plugs on
		/// nodes for the purposes of driving expressions and suchlike.
		/// So that there is no danger of name clashes between such plugs
		/// and plugs Gaffer itself might add in the future, this plug
		/// is provided, under which users may add any plugs they want. Plugs
		/// added to the user plug will need the Plug::Dynamic flag to be set
		/// so that they can be saved and loaded successfully.
		Gaffer::Plug *userPlug();
		const Gaffer::Plug *userPlug() const;

		/// Convenience function which returns the script this node belongs to,
		/// or the node itself if it is a ScriptNode.
		ScriptNode *scriptNode();
		const ScriptNode *scriptNode() const;

		/// Accepts only Nodes and Plugs.
		bool acceptsChild( const GraphComponent *potentialChild ) const override;
		/// Accepts only Nodes.
		bool acceptsParent( const GraphComponent *potentialParent ) const override;

		/// Signal type for communicating errors. The plug argument is the
		/// plug being processed when the error occurred. The source argument
		/// specifies the original source of the error, since it may be being
		/// propagated downstream from an original upstream error. The error
		/// argument is a description of the problem.
		using ErrorSignal = Signals::Signal<
			void ( const Plug *plug, const Plug *source, const std::string &error ),
			Signals::CatchingCombiner<void>
		>;
		/// Signal emitted when an error occurs while processing this node.
		/// This is intended to allow UI elements to display errors that occur
		/// during processing triggered by other parts of the UI.
		///
		/// Note that C++ exceptions are still the primary mechanism for error handling
		/// within Gaffer - the existence of this signal does nothing to change
		/// that. The signal merely allows passive observers of the graph to be
		/// notified of errors during processing - clients which invoke such
		/// processing must still use C++ exception handling to deal directly with
		/// any errors which occur.
		///
		/// \threading Since node graph processing may occur on any thread, it is
		/// important to note that this signal may also be emitted on any thread.
		/// \todo Signals are not intended to be threadsafe, and we shouldn't be
		/// emitting them concurrently - see comments in SlotBase. Perhaps we
		/// should use `ParallelAlgo::callOnUIThread()` to schedule later emission
		/// on the UI thread?
		ErrorSignal &errorSignal();
		const ErrorSignal &errorSignal() const;

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
		void parentChanging( Gaffer::GraphComponent *newParent ) override;

	private :

		static size_t g_firstPlugIndex;

		friend class Plug;

		UnaryPlugSignal m_plugSetSignal;
		UnaryPlugSignal m_plugInputChangedSignal;
		UnaryPlugSignal m_plugDirtiedSignal;
		ErrorSignal m_errorSignal;

};

IE_CORE_DECLAREPTR( Node )

} // namespace Gaffer

#endif // GAFFER_NODE_H
