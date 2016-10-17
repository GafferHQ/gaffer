//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_PLUG_H
#define GAFFER_PLUG_H

#include "IECore/Object.h"

#include "Gaffer/GraphComponent.h"
#include "Gaffer/FilteredChildIterator.h"
#include "Gaffer/FilteredRecursiveChildIterator.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Plug )
IE_CORE_FORWARDDECLARE( Node )

/// The Plug class defines a means of making point to point connections
/// between Nodes. A plug may receive a single input connection from
/// another plug, and may have an arbitrary number of output connections
/// to other plugs.
///
/// Plugs may also have child plugs. When this is the case, they may only
/// receive connections from other plugs with equivalent children. When
/// two such parent plugs are connected, the corresponding children are
/// connected automatically too. The reverse also applies - manually connecting
/// all the children will cause the parent connection to be made automatically.
/// Likewise, disconnecting one or more children will cause the parent connection
/// to be broken.
///
/// When two parent plugs are connected, and children are added to or removed
/// from the source plug, the equivalent operation will be automatically
/// performed on the destination plug so as to maintain the parent connection.
class Plug : public GraphComponent
{

	public :

		enum Direction
		{
			Invalid = 0,
			In = 1,
			Out = 2
		};

		enum Flags
		{
			None = 0x00000000,
			/// Dynamic plugs are those which are created outside of the constructor
			/// for a Node. This means that their value alone is not enough when serialising
			/// a script - instead the full Plug definition is serialised so it can
			/// be recreated fully upon loading.
			Dynamic = 0x00000001,
			/// Serialisable plugs are saved into scripts, whereas non-serialisable plugs
			/// are not.
			Serialisable = 0x00000002,
			/// If the AcceptsInputs flag is not set, then acceptsInput() always returns
			/// false.
			AcceptsInputs = 0x00000004,
			/// If the PerformsSubstitutions flag is set then tokens from the plug value
			/// will automatically be substituted with values from the context during
			/// computation. Note that currently this only applies to the StringPlug.
			/// \deprecated. Use the substitutions argument to the StringPlug constructor
			/// instead - this provides finer grained control.
			PerformsSubstitutions = 0x00000008,
			/// If the Cacheable flag is set then values computed during getValue()
			/// calls will be stored in a cache and reused if equivalent computations
			/// are requested in the future.
			Cacheable = 0x00000010,
			/// Read only plugs do not accept any changes to their inputs, and will throw
			/// an exception if an attempt is made to call their setValue() method. It is
			/// not valid to make an output plug read only - in the case of an attempt to
			/// do so an exception will be thrown from setFlags().
			/// \deprecated Use MetadataAlgo instead.
			ReadOnly = 0x00000020,
			/// Generally it is an error to have cyclic dependencies between plugs,
			/// and creating them will cause an exception to be thrown during dirty
			/// propagation. However, it is possible to design nodes that create
			/// pseudo-cycles, where the evaluation of a plug leads to the evaluation
			/// of the very same plug, but in a different context. This is
			/// permissible so long as the context is managed such that the cycle is
			/// not infinite. Because dirty propagation is performed independent of context,
			/// this flag must be used by such nodes to indicate that the cycle is
			/// intentional in this case, and is guaranteed to terminate during compute.
			AcceptsDependencyCycles = 0x00000040,
			/// When adding values, don't forget to update the Default and All values below,
			/// and to update PlugBinding.cpp too!
			Default = Serialisable | AcceptsInputs | PerformsSubstitutions | Cacheable,
			All = Dynamic | Serialisable | AcceptsInputs | PerformsSubstitutions | Cacheable | ReadOnly | AcceptsDependencyCycles
		};

		Plug( const std::string &name=defaultName<Plug>(), Direction direction=In, unsigned flags=Default );
		virtual ~Plug();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::Plug, PlugTypeId, GraphComponent );

		/// @name Parent-child relationships
		//////////////////////////////////////////////////////////////////////
		//@{
		/// Accepts only Plugs with the same direction.
		virtual bool acceptsChild( const GraphComponent *potentialChild ) const;
		/// Accepts only Nodes or Plugs as a parent.
		virtual bool acceptsParent( const GraphComponent *potentialParent ) const;
		/// Just returns ancestor<Node>() as a syntactic convenience.
		Node *node();
		/// Just returns ancestor<Node>() as a syntactic convenience.
		const Node *node() const;
		//@}

		Direction direction() const;

		/// Returns the current state of the flags.
		unsigned getFlags() const;
		/// Returns true if all the flags passed are currently set.
		bool getFlags( unsigned flags ) const;
		/// Sets the current state of the flags.
		/// \undoable
		void setFlags( unsigned flags );
		/// Sets or unsets the specified flags depending on the enable
		/// parameter. All other flags remain at their current values.
		/// \undoable
		void setFlags( unsigned flags, bool enable );

		/// @name Connections
		///////////////////////////////////////////////////////////////////////
		//@{
		typedef std::list<Plug *> OutputContainer;
		/// Plugs may accept or reject a potential input by
		/// implementing this method to return true for
		/// acceptance and false for rejection. Implementations
		/// should call their base class and only accept an
		/// input if their base class does too. The default
		/// implementation accepts inputs provided that :
		///
		///  - direction()==In and the AcceptsInputs flag is set
		///  - the ReadOnly flag is not set
		///  - node()->acceptsInput() also accepts the input
		///  - corresponding child plugs also accept the input
		virtual bool acceptsInput( const Plug *input ) const;
		/// Sets the input to this plug if acceptsInput( input )
		/// returns true, otherwise throws an IECore::Exception.
		/// Pass 0 to remove the current input.
		/// \undoable
		virtual void setInput( PlugPtr input );
		/// Returns the immediate input to this Plug - the
		/// one set with setInput().
		template<typename T>
		T *getInput();
		template<typename T>
		const T *getInput() const;
		/// The immediate input to this Plug as returned by getInput() may
		/// itself have an input, which may itself have an input and so on.
		/// This method follows such connections and returns the first plug
		/// without an input of its own - this can be used to find the node
		/// ultimately responsible for delivering information to the plug.
		/// \note If a plug has no input then source() returns the
		/// plug itself.
		/// \note The cast to type T is performed after finding the
		/// source, and not on the intermediate inputs along
		/// the way.
		template<typename T>
		T *source();
		template<typename T>
		const T *source() const;
		/// Removes all outputs from this plug.
		void removeOutputs();
		/// Allows iteration over all the outputs of this plug.
		const OutputContainer &outputs() const;
		//@}

		/// Creates a new Plug which is a copy of this, but with a specified name and direction.
		virtual PlugPtr createCounterpart( const std::string &name, Direction direction ) const;

	protected :

		virtual void parentChanging( Gaffer::GraphComponent *newParent );

		/// Initiates the propagation of dirtiness from the specified
		/// plug to its outputs and affected plugs (as defined by
		/// DependencyNode::affects()).
		static void propagateDirtiness( Plug *plugToDirty );

		/// Called by propagateDirtiness() to inform a plug that it has
		/// been dirtied. For plugs that implement caching of results, this
		/// provides an opportunity for the plug to invalidate its cache.
		/// This is called _before_ Node::plugDirtiedSignal() is emitted,
		/// so that the plug can be ready for any queries from slots
		/// connected to the signal.
		virtual void dirty();

	private :

		void parentChanged();
		static void propagateDirtinessForParentChange( Plug *plugToDirty );

		void setFlagsInternal( unsigned flags );

		class AcceptsInputCache;
		bool acceptsInputInternal( const Plug *input ) const;
		void setInput( PlugPtr input, bool setChildInputs, bool updateParentInput );
		void setInputInternal( PlugPtr input, bool emit );
		void emitInputChanged();

		void updateInputFromChildInputs( Plug *checkFirst );

		static void pushDirtyPropagationScope();
		static void popDirtyPropagationScope();
		// DirtyPropagationScope allowed friendship, as we use
		// it to declare an exception-safe public interface to
		// the two private methods above.
		friend class DirtyPropagationScope;

		class DirtyPlugs;

		Direction m_direction;
		Plug *m_input;
		OutputContainer m_outputs;
		unsigned m_flags;

		bool m_skipNextUpdateInputFromChildInputs;

};

IE_CORE_DECLAREPTR( Plug );

template<Plug::Direction D=Plug::Invalid, typename T=Plug>
struct PlugPredicate
{
	typedef T ChildType;

	bool operator()( const GraphComponentPtr &g ) const
	{
		const T *p = IECore::runTimeCast<T>( g.get() );
		if( !p )
		{
			return false;
		}
		if( D==Plug::Invalid )
		{
			return true;
		}
		return D==p->direction();
	}
};

typedef FilteredChildIterator<PlugPredicate<> > PlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, Plug> > InputPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Plug> > OutputPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<>, PlugPredicate<> > RecursivePlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Plug>, PlugPredicate<> > RecursiveInputPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Plug>, PlugPredicate<> > RecursiveOutputPlugIterator;

} // namespace Gaffer

#include "Gaffer/Plug.inl"

#endif // GAFFER_PLUG_H
