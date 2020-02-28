//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2013, John Haddon. All rights reserved.
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

#ifndef GAFFER_CONTEXT_H
#define GAFFER_CONTEXT_H

#include "Gaffer/Export.h"
#include "Gaffer/ThreadState.h"

#include "IECore/Canceller.h"
#include "IECore/Data.h"
#include "IECore/InternedString.h"
#include "IECore/MurmurHash.h"
#include "IECore/StringAlgo.h"

#include "boost/container/flat_map.hpp"
#include "boost/signals.hpp"

namespace Gaffer
{

/// This class provides a dictionary of IECore::Data objects to define the context in which a
/// computation is performed. The most basic entry common to all Contexts is the frame number,
/// but a context may also hold entirely arbitrary entries useful to specific types of
/// computation.
///
/// Contexts are made current using the nested Scope class - any computation triggered by
/// ValuePlug::getValue() calls will be made with respect to the current Context. Each thread
/// maintains a stack of contexts, allowing computations in different contexts to be performed
/// in parallel, and allowing contexts to be changed temporarily for a specific computation.
///
/// It is common for Nodes to need to evaluate their upstream inputs in a modified context.
/// The EditableScope class should be used for this purpose since it is more efficient than
/// copy constructing a new Context.
///
/// \note The various UI components currently use "ui:" prefixed context variables for their
/// own purposes. These variables are expected to never affect computation, and are therefore
/// excluded from hash(). Other code may find that it too needs to ignore them in order to
/// avoid unnecessary recomputation. In the future we may explore having the UI use a separate
/// container for such variables, or a more general mechanism for variables guaranteed to be
/// unrelated to computation.
class GAFFER_API Context : public IECore::RefCounted
{

	public :

		/// Since there are costs associated with constructing,
		/// copying and reference counting the Data values that make
		/// up a Context, various ownership options are provided which
		/// trade performance for additional constraints on client code.
		enum Ownership
		{
			/// The Context takes its own copy of a value to be held
			/// internally. This requires no additional constraints on the
			/// part of client code, but has the worst performance.
			Copied,
			/// The Context shares the value with others, incrementing
			/// the reference count to ensure it remains alive for as
			/// long as the Context needs it. Because the Context
			/// doesn't have sole ownership of the value, other code
			/// could change the value without its knowledge. It is the
			/// responsibility of client code to either ensure that this does
			/// not happen, or to manually call Context::changed() as
			/// necessary when it does. This avoids the overhead of copying
			/// values when setting them.
			Shared,
			/// The Context simply references an existing value, and doesn't
			/// even increment its reference count. In addition to the constraints
			/// for shared ownership, it is also the responsibility
			/// of client code to ensure that the value remains alive for the
			/// lifetime of the Context. This is significantly faster than
			/// either of the previous options.
			Borrowed
		};

		Context();
		/// Copy constructor. The ownership argument is deprecated - use
		/// an EditableScope instead of Borrowed ownership.
		Context( const Context &other, Ownership ownership = Copied );
		/// Copy constructor for creating a cancellable context.
		/// The canceller is referenced, not copied, and must remain
		/// alive for as long as the context is in use.
		Context( const Context &other, const IECore::Canceller &canceller );
		~Context() override;

		IE_CORE_DECLAREMEMBERPTR( Context )

		typedef boost::signal<void ( const Context *context, const IECore::InternedString & )> ChangedSignal;

		template<typename T, typename Enabler=void>
		struct Accessor;

		/// Calling with simple types (e.g float) will automatically
		/// create a TypedData<T> to store the value.
		template<typename T>
		void set( const IECore::InternedString &name, const T &value );
		/// Can be used to retrieve simple types :
		///		float f = context->get<float>( "myFloat" )
		/// And also IECore::Data types :
		///		const FloatData *f = context->get<FloatData>( "myFloat" )
		template<typename T>
		typename Accessor<T>::ResultType get( const IECore::InternedString &name ) const;
		/// As above but returns defaultValue when an entry is not found, rather than throwing
		/// an Exception.
		template<typename T>
		typename Accessor<T>::ResultType get( const IECore::InternedString &name, typename Accessor<T>::ResultType defaultValue ) const;

		/// Removes an entry from the context if it exists
		void remove( const IECore::InternedString& name );

		/// Removes any entries whose names match the space separated patterns
		/// provided. Matching is performed using `StringAlgo::matchMultiple()`.
		void removeMatching( const IECore::StringAlgo::MatchPattern &pattern );

		/// When a Shared or Borrowed value is changed behind the scenes, this method
		/// must be called to notify the Context of the change.
		void changed( const IECore::InternedString &name );

		/// Fills the specified vector with the names of all items in the Context.
		void names( std::vector<IECore::InternedString> &names ) const;

		/// @name Time
		/// Contexts give special meaning to a couple of variables in
		/// order to represent time. Because Gaffer is primarily used for
		/// the generation of image sequences, time is stored as a
		/// floating point frame number in a context variable called "frame".
		/// A second context variable called "framesPerSecond" allows this
		/// value to be mapped to and from time in seconds. The methods below
		/// provide convenient access for setting the variables, and for
		/// dealing with time in seconds rather than frames. It is strongly
		/// recommended that these methods be used in preference to direct
		/// variable access.
		////////////////////////////////////////////////////////////////////
		//@{
		/// Convenience method returning `get<float>( "frame" )`.
		float getFrame() const;
		/// Convenience method calling `set<float>( "frame", frame )`.
		void setFrame( float frame );
		/// Convenience method returning `get<float>( "framesPerSecond" )`.
		float getFramesPerSecond() const;
		/// Convenience method calling `set<float>( "framesPerSecond", framesPerSecond )`.
		void setFramesPerSecond( float framesPerSecond );
		/// Convenience method for getting the time in seconds. Returns
		/// `getFrame() / getFramesPerSecond()`.
		float getTime() const;
		/// Convenience method for setting the frame variable from a time in
		/// seconds. Calls `setFrame( timeInSeconds * getFramesPerSecond() )`.
		void setTime( float timeInSeconds );
		//@}

		/// A signal emitted when an element of the context is changed.
		ChangedSignal &changedSignal();

		IECore::MurmurHash hash() const;

		bool operator == ( const Context &other ) const;
		bool operator != ( const Context &other ) const;

		/// Uses `IECore::StringAlgo::substitute()` to perform variable
		/// substitutions using values from the context.
		std::string substitute( const std::string &input, unsigned substitutions = IECore::StringAlgo::AllSubstitutions ) const;
		/// An `IECore::StringAlgo::VariableProvider` that can be used to
		/// pass context variables to `IECore::StringAlgo::substitute()`.
		class SubstitutionProvider;

		/// Used to request cancellation of long running background operations.
		/// May be null. Nodes that perform expensive work should check for
		/// cancellation periodically by calling `Canceller::check( context->canceller() )`.
		inline const IECore::Canceller *canceller() const;

		/// The Scope class is used to push and pop the current context on
		/// the calling thread.
		class Scope : private ThreadState::Scope
		{

			public :

				/// Constructing the Scope pushes the current context.
				Scope( const Context *context );
				/// Destruction of the Scope pops the previously pushed context.
				~Scope();

		};

		/// Creates a lightweight editable copy of a context,
		/// scoping it as the current context on the calling
		/// thread. Typically used in Node internals to
		/// evaluate upstream inputs in a modified context.
		/// Note that there are no Python bindings for this class,
		/// because it is harder to provide the necessary lifetime
		/// guarantees there, and performance critical code should
		/// not be implemented in Python in any case.
		class EditableScope : private ThreadState::Scope
		{

			public :

				/// It is the caller's responsibility to
				/// guarantee that `context` outlives
				/// the EditableScope.
				EditableScope( const Context *context );
				/// Copies the specified thread state to this thread,
				/// and scopes an editable copy of the context contained
				/// therein. It is the caller's responsibility to ensure
				/// that `threadState` outlives the EditableScope.
				EditableScope( const ThreadState &threadState );
				~EditableScope();

				template<typename T>
				void set( const IECore::InternedString &name, const T &value );

				void setFrame( float frame );
				void setFramesPerSecond( float framesPerSecond );
				void setTime( float timeInSeconds );

				void remove( const IECore::InternedString &name );
				void removeMatching( const IECore::StringAlgo::MatchPattern &pattern );

				const Context *context() const { return m_context.get(); }

			private :

				Ptr m_context;

		};

		/// Returns the current context for the calling thread.
		static const Context *current();

	private :

		Context( const Context &other, Ownership ownership, const IECore::Canceller *canceller );

		// Storage for each entry.
		struct Storage
		{
			Storage() : data( nullptr ), ownership( Copied ) {}
			// We reference the data with a raw pointer to avoid the compulsory
			// overhead of an intrusive pointer.
			const IECore::Data *data;
			// And use this ownership flag to tell us when we need to do explicit
			// reference count management.
			Ownership ownership;
		};

		typedef boost::container::flat_map<IECore::InternedString, Storage> Map;

		Map m_map;
		ChangedSignal *m_changedSignal;
		mutable IECore::MurmurHash m_hash;
		mutable bool m_hashValid;
		const IECore::Canceller *m_canceller;

};

IE_CORE_DECLAREPTR( Context );

} // namespace Gaffer

#include "Gaffer/Context.inl"

#endif // GAFFER_CONTEXT_H
