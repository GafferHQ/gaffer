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
	
		/// Derived classes must use this pointer to store and retrieve plug
		/// values. The ValuePlug class doesn't dictate what sort of value
		/// is stored (provided it derives from IECore::Object), but must be
		/// allowed to dictate where it is stored. storage() will return different
		/// locations depending on the current context, enabling multithreading
		/// and caching of results behind the scenes. Passing true will
		/// cause the ValuePlug to first update the current stored value if necessary
		/// by calling node()->compute() or setFromInput(). Typically a derived
		/// class should have a public setValue() method which stores into storage()
		/// and a getValue() method which retrieves from storage( true ).
		IECore::ObjectPtr &storage( bool update );
	
		/// Must be called by derived classes when the value has been
		/// set. This emits any relevant signals and propagates the value to the
		/// Plug's outputs.
		void valueSet();
		
		/// Must be implemented to set the value of this Plug from the
		/// value of its input. This allows the Plug to perform any
		/// necessary conversions of the input value. Called by the valueSet()
		/// function to propagate values through the graph.
		virtual void setFromInput() = 0;
		
	private :
	
		void propagateDirtiness();
	
		/// For holding the value of input plugs with no input connections.
		IECore::ObjectPtr m_staticStorage;

};

IE_CORE_DECLAREPTR( ValuePlug )

} // namespace Gaffer

#endif // GAFFER_VALUEPLUG_H
