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

#ifndef GAFFER_PROCEDURALHOLDER_H
#define GAFFER_PROCEDURALHOLDER_H

#include "Gaffer/ParameterisedHolder.h"

namespace IECore
{

IE_CORE_FORWARDDECLARE( ParameterisedProcedural )

} // namespace IECore

namespace Gaffer
{

class ProceduralHolder : public ParameterisedHolderComputeNode
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::ProceduralHolder, ProceduralHolderTypeId, ParameterisedHolderComputeNode );

		ProceduralHolder( const std::string &name=defaultName<ProceduralHolder>() );
			
		virtual void setParameterised( IECore::RunTimeTypedPtr parameterised );
		
		/// Convenience function which calls setParameterised( className, classVersion, "IECORE_PROCEDURAL_PATHS" )
		void setProcedural( const std::string &className, int classVersion );
		/// Convenience function which returns runTimeCast<ParameterisedProcedural>( getParameterised() );
		IECore::ParameterisedProceduralPtr getProcedural( std::string *className = 0, int *classVersion = 0 );
		IECore::ConstParameterisedProceduralPtr getProcedural( std::string *className = 0, int *classVersion = 0 ) const;
	
		virtual void affects( const Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :
	
		virtual void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( ValuePlug *output, const Context *context ) const;
				
};

IE_CORE_DECLAREPTR( ProceduralHolder )

} // namespace Gaffer

#endif // GAFFER_PROCEDURALHOLDER_H
