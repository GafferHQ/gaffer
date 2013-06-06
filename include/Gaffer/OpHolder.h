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

#ifndef GAFFER_OPHOLDER_H
#define GAFFER_OPHOLDER_H

#include "Gaffer/ParameterisedHolder.h"

namespace IECore
{

IE_CORE_FORWARDDECLARE( Op )

} // namespace IECore

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( ParameterHandler )

class OpHolder : public ParameterisedHolderComputeNode
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::OpHolder, OpHolderTypeId, ParameterisedHolderComputeNode );

		OpHolder( const std::string &name=defaultName<OpHolder>() );
			
		virtual void setParameterised( IECore::RunTimeTypedPtr parameterised, bool keepExistingValues=false );
		
		/// Convenience function which calls setParameterised( className, classVersion, "IECORE_OP_PATHS", keepExistingValues )
		void setOp( const std::string &className, int classVersion, bool keepExistingValues=false );
		/// Convenience function which returns runTimeCast<Op>( getParameterised() );
		IECore::OpPtr getOp( std::string *className = 0, int *classVersion = 0 );
		IECore::ConstOpPtr getOp( std::string *className = 0, int *classVersion = 0 ) const;

		virtual void affects( const Plug *input, AffectedPlugsContainer &outputs ) const;
	
	protected :
	
		virtual void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( ValuePlug *output, const Context *context ) const;
		
	private :
	
		ParameterHandlerPtr m_resultParameterHandler;
		
};

IE_CORE_DECLAREPTR( OpHolder )

} // namespace Gaffer

#endif // GAFFER_OPHOLDER_H
