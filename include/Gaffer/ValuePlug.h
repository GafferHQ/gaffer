//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

#ifndef GAFFER_VALUEPLUG_H
#define GAFFER_VALUEPLUG_H

#include "Gaffer/Plug.h"
#include "Gaffer/PlugIterator.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( DependencyNode )

/// The Plug base class defines the concept of a connection
/// point with direction. The ValuePlug class extends this concept
/// to allow the connections to pass values between connection
/// points, and for DependencyNode::compute() to be used to compute output
/// values.
class ValuePlug : public Plug
{

	public :

		virtual ~ValuePlug();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::ValuePlug, ValuePlugTypeId, Plug );

		/// Accepts the input only if it is derived from ValuePlug.
		/// Derived classes may accept more types provided they
		/// derive from ValuePlug too, and they can deal with them
		/// in setFrom().
		virtual bool acceptsInput( const Plug *input ) const;
		/// Reimplemented so that values can be propagated from inputs.
		virtual void setInput( PlugPtr input );

		/// Returns true if it is valid to call setFrom(), setToDefault(),
		/// or setValue() on this plug. False will be returned if the plug
		/// has an input connection or the ReadOnly flag is set.
		virtual bool settable() const;

		/// Must be implemented to set the value of this Plug from the other Plug,
		/// performing any necessary conversions on the input value. Should throw
		/// an exception if other is of an unsupported type.
		virtual void setFrom( const ValuePlug *other ) = 0;

		/// Must be implemented by derived classes to set the value
		/// to the default for this Plug.
		virtual void setToDefault() = 0;

		/// Returns a hash to represent the value of this plug
		/// in the current context.
		virtual IECore::MurmurHash hash() const;
		/// Convenience function to append the hash to h.
		void hash( IECore::MurmurHash &h ) const;

		/// @name Cache management
		/// ValuePlug optimises repeated computation by storing a cache of
		/// recently computed values. These functions allow for management
		/// of the cache.
		////////////////////////////////////////////////////////////////////
		//@{
		/// Returns the maximum amount of memory in bytes to use for the cache.
		static size_t getCacheMemoryLimit();
		/// Sets the maximum amount of memory the cache may use in bytes.
		static void setCacheMemoryLimit( size_t bytes );
		/// Returns the current memory usage of the cache in bytes.
		static size_t cacheMemoryUsage();
		//@}

	protected :

		/// The initialValue will be referenced directly (not copied) and
		/// therefore must not be changed after passing to the constructor.
		/// The initialValue must be non-null.
		ValuePlug( const std::string &name, Direction direction,
			IECore::ConstObjectPtr initialValue, unsigned flags );
		/// For use /only/ by CompoundPlug. This results in a null m_staticValue,
		/// which is acceptable only because CompoundPlug values are composed from
		/// the values of child plugs, and aren't computed or stored directly
		/// (CompoundPlug may not call getObjectValue() or setObjectValue() as a result).
		ValuePlug( const std::string &name, Direction direction, unsigned flags );

		/// Internally all values are stored as instances of classes derived
		/// from IECore::Object, although this isn't necessarily visible to the user.
		/// This function updates the value using node()->compute()
		/// or setFrom( getInput() ) as appropriate and then returns it. Typically
		/// this will be called by a subclass getValue() method which will
		/// extract a value from the object and return it to the user in a more
		/// convenient form. Note that this function will often return different
		/// objects with each query - this allows it to support the calculation
		/// of values in different contexts and on different threads.
		///
		/// The value is returned via a reference counted pointer, as
		/// following return from getObjectValue(), it is possible that nothing
		/// else references the value - the value could have come from the cache
		/// and then have been immediately removed by another thread.
		IECore::ConstObjectPtr getObjectValue() const;
		/// Should be called by derived classes when they wish to set the plug
		/// value - the value is referenced directly (not copied) and so must
		/// not be changed following the call.
		void setObjectValue( IECore::ConstObjectPtr value );

		/// Returns true if a computation is currently being performed on this thread -
		/// if we are inside Node::compute().
		bool inCompute() const;

		/// Emits the appropriate Node::plugSetSignal() for this plug and all its
		/// ancestors, then does the same for its output plugs. This is called
		/// automatically by setObjectValue() where appropriate, and typically shouldn't
		/// need to be called manually. It is exposed so that CompoundPlug can
		/// simulate the behaviour of a plug being set when a child is added or removed.
		void emitPlugSet();

	private :

		class Computation;
		class SetValueAction;

		void setValueInternal( IECore::ConstObjectPtr value, bool propagateDirtiness );

		/// For holding the value of input plugs with no input connections.
		IECore::ConstObjectPtr m_staticValue;

};

IE_CORE_DECLAREPTR( ValuePlug )

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, ValuePlug> > ValuePlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, ValuePlug> > InputValuePlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, ValuePlug> > OutputValuePlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, ValuePlug>, PlugPredicate<> > RecursiveValuePlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, ValuePlug>, PlugPredicate<> > RecursiveInputValuePlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, ValuePlug>, PlugPredicate<> > RecursiveOutputValuePlugIterator;

} // namespace Gaffer

#endif // GAFFER_VALUEPLUG_H
