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

#ifndef GAFFER_VALUEPLUG_H
#define GAFFER_VALUEPLUG_H

#include "Gaffer/Plug.h"

namespace Gaffer
{

/// The Plug base class defines the concept of a connection
/// point with direction. The ValuePlug class extends this concept
/// to allow the connections to pass values between connection
/// points.
class ValuePlug : public Plug
{

	public :
	
		ValuePlug( const std::string &name=staticTypeName(), Direction direction=In,
			unsigned flags=Default );
		virtual ~ValuePlug();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( ValuePlug, ValuePlugTypeId, Plug );

		/// Accepts the input only if it is derived from ValuePlug.
		/// Derived classes may accept more types provided they
		/// derive from ValuePlug too, and they can deal with them
		/// in setFromInput().
		virtual bool acceptsInput( ConstPlugPtr input ) const;
		/// Reimplemented so that values can be propagated from inputs.
		virtual void setInput( PlugPtr input );

		/// Must be implemented by derived classes to set the value
		/// to the default for this Plug.
		/// \todo I think we need this for when an input connection
		/// is removed, so we can revert to default.
		///virtual void setToDefault() = 0;
		
	protected :
	
		/// Internally all values are stored as instances of classes derived
		/// from IECore::Object, although this isn't necessarily visible to the user.
		/// This function updates the value using node()->compute()
		/// or setFromInput() as appropriate and then returns it. Typically
		/// this will be called by a subclass getValue() method which will
		/// extract a value from the object and return it to the user in a more
		/// convenient form. Note that this function will often return different
		/// objects with each query - this allows it to support the calculation
		/// of values in different contexts and on different threads. It is also
		/// possible for 0 to be returned, either if a computation fails or if
		/// the value for the plug has not been set - in this case the subclass
		/// should return the default value from it's getValue() method.
		IECore::ConstObjectPtr getObjectValue() const;
		/// Should be called by derived classes when they wish to set the plug
		/// value.
		void setObjectValue( IECore::ConstObjectPtr value );
				
		/// Must be implemented to set the value of this Plug from the
		/// value of its input. This allows the Plug to perform any
		/// necessary conversions of the input value. Called by the getValue()
		/// function to propagate values through the graph.
		virtual void setFromInput() = 0;
		
	private :
	
		class Computation;
		friend class Computation;
	
		void setValueInternal( IECore::ConstObjectPtr value );
		/// Emits the dirty signal for this plug, and all ancestor ValuePlugs up
		/// to node(). The result of node() can be passed to avoid repeatedly
		/// finding the node in the case of making repeated calls.
		void emitDirtiness( Node *n = 0 );
		/// Calls emitDirtiness() on affected plugs and output connections.
		void propagateDirtiness();
	
		/// For holding the value of input plugs with no input connections.
		IECore::ConstObjectPtr m_staticValue;

};

IE_CORE_DECLAREPTR( ValuePlug )

} // namespace Gaffer

#endif // GAFFER_VALUEPLUG_H
