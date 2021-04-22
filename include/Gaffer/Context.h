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

/// This class provides a dictionary of variables to define the context in which a
/// computation is performed. The most basic variable common to all Contexts is the frame number,
/// but a context may also hold entirely arbitrary variables useful to specific types of
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

		/// Sets a variable to the specified value. A copy is taken so that
		/// subsequent changes to `value` do not affect the context.
		template<typename T, typename Enabler = std::enable_if_t<!std::is_pointer<T>::value>>
		void set( const IECore::InternedString &name, const T &value );
		/// As above, but providing the value as a `Data *`.
		void set( const IECore::InternedString &name, const IECore::Data *value );

		/// Returns a reference to the value of a variable, throwing if it doesn't exist or
		/// has the wrong type : `float f = context->get<float>( "myFloat" )`.
		template<typename T>
		const T &get( const IECore::InternedString &name ) const;
		/// As above, but returns `defaultValue` if the variable doesn't exist.
		/// Note that if you pass in a temporary as the `defaultValue`, you must
		/// copy the return value (if you stored it as a reference, you would be
		/// referencing the temporary after it was destroyed).
		template<typename T>
		const T &get( const IECore::InternedString &name, const T& defaultValue ) const;
		/// Returns a pointer to the value for the variable if it exists and has
		/// the requested type. Returns `nullptr` if the variable doesn't exist,
		/// and throws if it exists but has the wrong type.
		template<typename T>
		const T *getIfExists( const IECore::InternedString &name ) const;

		/// Returns a copy of the variable if it exists, throwing if it doesn't. This
		/// can be used when the type of the variable is unknown, but it is much more
		/// expensive than the `get()` methods above because it allocates memory.
		IECore::DataPtr getAsData( const IECore::InternedString &name ) const;
		/// As above but returns `defaultValue` if the variable does not exist.
		IECore::DataPtr getAsData( const IECore::InternedString &name, const IECore::DataPtr &defaultValue ) const;

		/// Removes a variable from the context, if it exists.
		void remove( const IECore::InternedString &name );
		/// Removes any variables whose names match the space separated patterns
		/// provided. Matching is performed using `StringAlgo::matchMultiple()`.
		void removeMatching( const IECore::StringAlgo::MatchPattern &pattern );

		/// Fills the specified vector with the names of all variables in the Context.
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

				/// Sets a variable with a pointer to a typed value. It is the
				/// caller's responsibility to ensure that the pointer remains
				/// valid for the lifetime of the EditableScope. This is much
				/// faster than `Context::set()` because it doesn't allocating
				/// memory, and should be used in all performance-critical code.
				template<typename T>
				void set( const IECore::InternedString &name, const T *value );

				template<typename T, typename Enabler = std::enable_if_t<!std::is_pointer<T>::value > >
				[[deprecated("Use faster pointer version, or use the more explicit setAllocated if you actually need to allocate ")]]
				void set( const IECore::InternedString &name, const T &value );

				/// Sets a variable from a copy of `value`. This is more expensive than the
				/// pointer version above, and should be avoided where possible.
				template<typename T, typename Enabler = std::enable_if_t<!std::is_pointer<T>::value > >
				void setAllocated( const IECore::InternedString &name, const T &value );
				/// As above, but providing the value as a `Data *`.
				void setAllocated( const IECore::InternedString &name, const IECore::Data *value );

				/// These are fast even though they don't take a pointer,
				/// because the EditableScope has dedicated internal storage for
				/// the frame.
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
				// Provides storage for `setFrame()` and `setTime()` to use
				// (There is no easy way to provide external storage for
				// setTime, because it multiplies the input value).
				float m_frameStorage;

		};

		/// Returns the current context for the calling thread.
		static const Context *current();

		/// Used to register a data type for use in variable values.
		/// See `GafferImage::FormatData` for an example.
		template<typename T>
		struct TypeDescription
		{
			TypeDescription();
		};

	private :

		// Determines the operation of the private copy constructor.
		enum class CopyMode
		{
			// Shares ownership with the source context where possible,
			// allocating copies where necessary. Used by all public copy
			// constructors.
			Owning,
			// References existing values without taking ownership, relying on
			// the source context to outlive this one. Used by EditableScopes.
			NonOwning
		};

		Context( const Context &other, CopyMode mode );

		// Type used for the value of a variable.
		struct Value
		{

			inline Value();
			template<typename T>
			Value( const IECore::InternedString &name, const T *value );
			Value( const IECore::InternedString &name, const IECore::Data *value );
			Value( const Value &other ) = default;

			Value &operator = ( const Value &other ) = default;

			template<typename T>
			inline const T &value() const;
			IECore::TypeId typeId() const { return m_typeId; }
			const void *rawValue() const { return m_value; }
			// Note : This includes the hash of the name passed
			// to the constructor.
			const IECore::MurmurHash &hash() const { return m_hash; }

			bool operator == ( const Value &rhs ) const;
			bool operator != ( const Value &rhs ) const;
			bool references( const IECore::Data *value ) const;

			IECore::DataPtr makeData() const;
			Value copy( IECore::ConstDataPtr &owner ) const;

			template<typename T>
			static void registerType();

			private :

				Value( IECore::TypeId typeId, const void *value, const IECore::MurmurHash &hash );

				IECore::TypeId m_typeId;
				const void *m_value;
				IECore::MurmurHash m_hash;

				struct TypeFunctions
				{
					IECore::DataPtr (*makeData)( const Value &value, const void **dataValue );
					bool (*isEqual)( const Value &a, const Value &b );
					Value (*constructor)( const IECore::InternedString &name, const IECore::Data *data );
					const void *(*value)( const IECore::Data *data );
				};

				using TypeMap = boost::container::flat_map<IECore::TypeId, TypeFunctions>;
				static TypeMap &typeMap();
				static const TypeFunctions &typeFunctions( IECore::TypeId typeId );

		};

		// Sets a variable and emits `changedSignal()` as appropriate. Does not
		// manage ownership in any way. Returns true if the value was assigned,
		// and false if the value was not (due to it being equal to the
		// previously stored value).
		inline bool internalSet( const IECore::InternedString &name, const Value &value );
		// Throws if variable doesn't exist.
		inline const Value &internalGet( const IECore::InternedString &name ) const;
		// Returns nullptr if variable doesn't exist.
		inline const Value *internalGetIfExists( const IECore::InternedString &name ) const;

		typedef boost::container::flat_map<IECore::InternedString, Value> Map;

		Map m_map;
		ChangedSignal *m_changedSignal;
		mutable IECore::MurmurHash m_hash;
		mutable bool m_hashValid;
		const IECore::Canceller *m_canceller;

		// The alloc map holds a smart pointer to data that we allocate.  It must keep the entries
		// alive at least as long as the m_map used for actual accesses is using it, though it may
		// hold data longer than it is actually in use.  ( ie. a fast pointer based set through
		// EditableScope could overwrite a variable without updating m_allocMap )
		typedef boost::container::flat_map<IECore::InternedString, IECore::ConstDataPtr > AllocMap;
		AllocMap m_allocMap;

};

IE_CORE_DECLAREPTR( Context );

} // namespace Gaffer

#include "Gaffer/Context.inl"

#endif // GAFFER_CONTEXT_H
