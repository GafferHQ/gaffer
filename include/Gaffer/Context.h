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


		Context();
		/// Copy constructor
		Context( const Context &other );
		/// Copy constructor for creating a cancellable context.
		/// The canceller is referenced, not copied, and must remain
		/// alive for as long as the context is in use.
		Context( const Context &other, const IECore::Canceller &canceller );
		/// Copy constructor which can optionally omit an existing canceller
		/// if `omitCanceller = true` is passed.
		Context( const Context &other, bool omitCanceller );
		~Context() override;

		IE_CORE_DECLAREMEMBERPTR( Context )

		typedef boost::signal<void ( const Context *context, const IECore::InternedString & )> ChangedSignal;

		/// Set a context entry with a typed value.
		/// ( This takes a copy so that the value can be safely changed afterwards )
		template<typename T, typename = std::enable_if_t<!std::is_pointer<T>::value > >
		void set( const IECore::InternedString &name, const T &value );

		/// Set a context entry with a generic Data *, which could be of any supported type.
		/// ( This takes a copy so that the value can be safely changed afterwards )
		void set( const IECore::InternedString &name, const IECore::Data *value );

		/// Can be used to retrieve simple types, and is very fast :
		///		float f = context->get<float>( "myFloat" )
		template<typename T>
		const T& get( const IECore::InternedString &name ) const;

		/// As above but returns defaultValue when an entry is not found, rather than throwing
		/// an Exception.  Note that if you pass in a temporary as the defaultValue, you must
		/// copy the return value, rather than storing it as a reference ( if you stored it
		/// as a reference, you would be storing a refernce to the temporary you passed in ).
		template<typename T>
		const T& get( const IECore::InternedString &name, const T& defaultValue ) const;

		/// Returns a pointer to the value for the variable if it exists and has
		/// the requested type. Returns `nullptr` if the variable doesn't exist,
		/// and throws if if exists but has the wrong type.  Equally fast to the get() above.
		template<typename T>
		const T* getIfExists( const IECore::InternedString &name ) const;

		/// Use when you need a Data ptr, and don't know the type of the value you are getting
		/// This allocates a new Data, and is much slower than the typed versions of get() above.
		IECore::DataPtr getAsData( const IECore::InternedString &name ) const;

		/// As above but returns defaultValue when an entry is not found, rather than throwing
		/// an Exception.
		IECore::DataPtr getAsData( const IECore::InternedString &name, IECore::Data *defaultValue ) const;

		/// Removes an entry from the context if it exists
		void remove( const IECore::InternedString& name );

		/// Removes any entries whose names match the space separated patterns
		/// provided. Matching is performed using `StringAlgo::matchMultiple()`.
		void removeMatching( const IECore::StringAlgo::MatchPattern &pattern );

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

		/// Return the hash of a particular variable ( or a default MurmurHash() if not present )
		/// Note that this hash includes the name of the variable
		inline IECore::MurmurHash variableHash( const IECore::InternedString &name ) const;

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

				/// Set a context entry with a pointer to a typed value.  It is the caller's
				/// responsibility to ensure that the memory pointed to stays valid for the
				/// lifetime of the EditableScope.  This is much faster than allocating new memory
				/// inside a Context, and should be used anywhere where putting a value in a
				/// context is performance critical
				template<typename T>
				void set( const IECore::InternedString &name, const T *value );

				template<typename T, typename = std::enable_if_t<!std::is_pointer<T>::value > >
				[[deprecated("Use faster pointer version, or use the more explicit setAllocated if you actually need to allocate ")]]
				void set( const IECore::InternedString &name, const T &value );

				/// Set a context entry with newly allocated Data, taken as a copy of a typed value
				template<typename T, typename = std::enable_if_t<!std::is_pointer<T>::value > >
				void setAllocated( const IECore::InternedString &name, const T &value );

				/// Set a context entry with newly allocated Data, taken as a copy of a generic Data *
				/// of any supported type
				void setAllocated( const IECore::InternedString &name, const IECore::Data *value );

				/// These fast even though they don't take a pointer, because the Context has a special
				/// internal storage just for the frame
				void setFrame( float frame );
				void setTime( float timeInSeconds );

				[[deprecated("Use faster pointer version")]]
				void setFramesPerSecond( float framesPerSecond );
				void setFramesPerSecond( const float *framesPerSecond );

				void remove( const IECore::InternedString &name );
				void removeMatching( const IECore::StringAlgo::MatchPattern &pattern );

				const Context *context() const { return m_context.get(); }

			private :

				Ptr m_context;

		};

		/// Returns the current context for the calling thread.
		static const Context *current();

		template< typename T >
		struct ContextTypeDescription
		{
			ContextTypeDescription();
		};

	private :
		/// The public copy constructor for Context duplicates all entry storage
		/// to make it completely independent of the Context it was copied from.  This
		/// is slow, so when creating an EditableScope, we just take the pointers from the
		/// source context, which is valid because the EditableScope never outlives its
		/// source context
		enum Ownership
		{
			/// Copy all data
			Copied,
			/// The Context simply references values from an existing context
			Borrowed
		};

		Context( const Context &other, Ownership ownership );

		/// Set a context entry from a pointer to a typed value
		/// This internal call does not deal with keeping alive the memory pointed to.
		/// It is called from internalSetAllocated() which is used for safe sets from
		/// the public Context API, and also directly from EditableScope::set which directly
		/// allows fast sets when the caller handles keeping the memory
		template<typename T>
		inline void internalSet( const IECore::InternedString &name, const T *value, const IECore::MurmurHash *knownHash = nullptr );

		// Unlike the externally visible calls, this does not copy the value, so it is appropriate to call
		// from the public set<T>( const T& ), after allocating a fresh TypedData<T>
		void internalSetAllocated( const IECore::InternedString &name, const IECore::ConstDataPtr &value, const IECore::MurmurHash *knownHash = nullptr );

		// Special signature used just by Context::SubstitutionProvider, which dynamically deals with different
		// types, but also needs to run fast, so shouldn't allocate Data
		inline const void* getPointerAndTypeId( const IECore::InternedString &name, IECore::TypeId &typeId ) const;

		// Storage for each entry.
		struct Storage
		{
			template< typename T >
			inline IECore::MurmurHash entryHash( const IECore::InternedString &name );

			IECore::TypeId typeId;
			const void *value;

			// Hash value of this entry's value and name - these will be summed to produce
			// a total hash for the context
			IECore::MurmurHash hash;
		};

		class TypeFunctionTable
		{
		public:
			static IECore::DataPtr makeData( IECore::TypeId typeId, const void *raw );
			static inline void internalSet( IECore::TypeId typeId, Context &c, const IECore::InternedString &name, const IECore::Data *value, const IECore::MurmurHash *knownHash = nullptr );
			static inline bool typedEquals( IECore::TypeId typeId, const void *rawA, const void *rawB );

			template<typename T>
			static void registerType();

		private:
			static TypeFunctionTable &theFunctionTable();

			template<typename T>
			static IECore::DataPtr makeDataTemplate( const void *raw );

			template<typename T>
			static void internalSetTemplate( Context &c, const IECore::InternedString &name, const IECore::Data *value, const IECore::MurmurHash *knownHash );

			template<typename T>
			static bool typedEqualsTemplate( const void *rawA, const void *rawB );

			struct FunctionTableEntry
			{
				IECore::DataPtr (*makeDataFunction)( const void *raw );
				void (*internalSetFunction)( Context &c, const IECore::InternedString &name, const IECore::Data *value, const IECore::MurmurHash *knownHash );
				bool (*typedEqualsFunction)( const void *rawA, const void *rawB );
			};

			using Map = boost::container::flat_map<IECore::TypeId, FunctionTableEntry >;
			Map m_map;
		};

		typedef boost::container::flat_map<IECore::InternedString, Storage> Map;

		Map m_map;
		ChangedSignal *m_changedSignal;
		mutable IECore::MurmurHash m_hash;
		mutable bool m_hashValid;
		const IECore::Canceller *m_canceller;

		// Used to provide storage for the current frame if setFrame or setTime is called
		// ( There is no easy way to provide external storage for setTime, because it multiplies
		// the input value )
		float m_frame;

		// The alloc map holds a smart pointer to data that we allocate.  It must keep the entries
		// alive at least as long as the m_map used for actual accesses is using it, though it may
		// hold data longer than it is actually in use.  ( ie. a fast pointer based set through
		// EditableScope could overwrite an entry without updating m_allocMap )
		typedef boost::container::flat_map<IECore::InternedString, IECore::ConstDataPtr > AllocMap;
		AllocMap m_allocMap;
};

IE_CORE_DECLAREPTR( Context );

} // namespace Gaffer

#include "Gaffer/Context.inl"

#endif // GAFFER_CONTEXT_H
