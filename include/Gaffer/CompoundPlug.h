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

#ifndef GAFFER_COMPOUNDPLUG_H
#define GAFFER_COMPOUNDPLUG_H

#include "Gaffer/ValuePlug.h"

namespace Gaffer
{

class CompoundPlug : public ValuePlug
{

	public :
			
		CompoundPlug( const std::string &name=staticTypeName(), Direction direction=In, unsigned flags=Default );
		virtual ~CompoundPlug();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( CompoundPlug, CompoundPlugTypeId, ValuePlug );

		/// Accepts any child provided it's a Plug and has the same direction
		/// as this CompoundPlug.
		virtual bool acceptsChild( ConstGraphComponentPtr potentialChild ) const;
				
		/// Only accepts inputs which are CompoundPlugs with child
		/// Plugs compatible with this plug.
		virtual bool acceptsInput( ConstPlugPtr input ) const;
		/// Makes connections between the corresponding child Plugs of
		/// input and this Plug.
		virtual void setInput( PlugPtr input );

		/// Sets all child plugs dirty.
		virtual void setDirty();

	protected :

		virtual void setFromInput();
		
	private :
	
		void parentChanged();
		void childAddedOrRemoved();
	
		boost::signals::connection m_plugInputChangedConnection;
		void plugInputChanged( PlugPtr plug );

		boost::signals::connection m_plugSetConnection;
		void plugSet( PlugPtr plug );
		
		void updateInputFromChildInputs( PlugPtr checkFirst );
		
};

IE_CORE_DECLAREPTR( CompoundPlug );

} // namespace Gaffer

#endif // GAFFER_COMPOUNDPLUG_H
