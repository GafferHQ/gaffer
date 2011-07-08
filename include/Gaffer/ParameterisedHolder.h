//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_PARAMETERISEDHOLDER_H
#define GAFFER_PARAMETERISEDHOLDER_H

#include "Gaffer/Node.h"

namespace IECore
{

class ParameterisedInterface;

} // namespace IECore

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( CompoundParameterHandler );

template<typename BaseType>
class ParameterisedHolder : public BaseType
{

	public :

		IECORE_RUNTIMETYPED_DECLARETEMPLATE( ParameterisedHolder<BaseType>, BaseType );
		IE_CORE_DECLARERUNTIMETYPEDDESCRIPTION( ParameterisedHolder<BaseType> );		

		ParameterisedHolder( const std::string &name=staticTypeName() );
			
		void setParameterised( IECore::RunTimeTypedPtr parameterised );
		void setParameterised( const std::string &className, int classVersion, const std::string &searchPathEnvVar );
		IECore::RunTimeTypedPtr getParameterised( std::string *className = 0, int *classVersion = 0, std::string *searchPathEnvVar = 0 ) const;
		/// Convenience method to return dynamic_cast<const IECore::ParameterisedInterface *>( getParameterised().get() )
		IECore::ParameterisedInterface *parameterisedInterface( std::string *className = 0, int *classVersion = 0, std::string *searchPathEnvVar = 0 );

		CompoundParameterHandlerPtr parameterHandler();
		ConstCompoundParameterHandlerPtr parameterHandler() const;
		
		/// \todo Do we need this now we have parameterHandler()? Do we keep this so that
		/// we're consistent with the interface provided in IECoreMaya?
		void setParameterisedValues();
		
		/// \todo Is this even needed? Can we just use an UndoContext instead?
		class ParameterModificationContext
		{
			public :
				ParameterModificationContext( Ptr parameterisedHolder );
				~ParameterModificationContext();
			private :
				Ptr m_parameterisedHolder;
		};
		
		
	private :
	
		friend class ParameterModificationContext;
	
		IECore::RunTimeTypedPtr m_parameterised;
		CompoundParameterHandlerPtr m_parameterHandler;
	
};

typedef ParameterisedHolder<Node> ParameterisedHolderNode;

IE_CORE_DECLAREPTR( ParameterisedHolderNode )

} // namespace Gaffer

#endif // GAFFER_PARAMETERISEDHOLDER_H
