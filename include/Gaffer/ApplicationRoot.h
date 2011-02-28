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

#ifndef GAFFER_APPLICATIONROOT_H
#define GAFFER_APPLICATIONROOT_H

#include "Gaffer/ScriptNode.h"

namespace Gaffer
{

class ApplicationRoot : public GraphComponent
{

	public :
	
		ApplicationRoot();
		virtual ~ApplicationRoot();
		
		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( ApplicationRoot, ApplicationRootTypeId, GraphComponent );

		/// Accepts no user added children.				
		virtual bool acceptsChild( ConstGraphComponentPtr potentialChild ) const;
		/// Accepts no parent.
		virtual bool acceptsParent( const GraphComponent *potentialParent ) const;
		
		ScriptContainerPtr scripts();
		ConstScriptContainerPtr scripts() const;
		
		//! @name Clipboard
		/// The ApplicationRoot class holds a clipboard which is
		/// shared by all ScriptNodes belonging to the application.
		/// The cut, copy and paste methods of the ScriptNodes
		/// operate using this central clipboard. The contents of the
		/// clipboard is simply stored as an IECore::Object.
		////////////////////////////////////////////////////////
		//@{
		/// Returns the clipboard contents, a copy should be taken
		/// if it must be modified.
		IECore::ConstObjectPtr getClipboardContents() const;
		/// Sets the clipboard contents - a copy of clip is taken.
		void setClipboardContents( IECore::ConstObjectPtr clip );
		//@}
		
		/// \todo Implement
		//NodePtr preferences();
		//ConstNodePtr preferences() const;

	private :
	
		IECore::ObjectPtr m_clipboardContents;
	
};

IE_CORE_DECLAREPTR( ApplicationRoot );

} // namespace Gaffer

#endif // GAFFER_APPLICATIONROOT_H
