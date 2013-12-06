//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFER_CONTEXTPROCESSOR_H
#define GAFFER_CONTEXTPROCESSOR_H

#include "Gaffer/ComputeNode.h"

namespace Gaffer
{

/// The ContextProcessor provides a base class to simplify the creation of nodes
/// which evaluate their inputs using a modified context to that provided for the output
/// evaluation - time warps being one good example. The ContextProcessor adds no plugs
/// of it's own, but will automatically map all in* plugs to their out* equivalents.
template<typename BaseType>
class ContextProcessor : public BaseType
{

	public :

		IECORE_RUNTIMETYPED_DECLARETEMPLATE( ContextProcessor<BaseType>, BaseType );
		IE_CORE_DECLARERUNTIMETYPEDDESCRIPTION( ContextProcessor<BaseType> );
		
		ContextProcessor( const std::string &name=GraphComponent::defaultName<ContextProcessor>() );
		virtual ~ContextProcessor();

		virtual BoolPlug *enabledPlug();
		virtual const BoolPlug *enabledPlug() const;
		
		virtual Plug *correspondingInput( const Plug *output );
		virtual const Plug *correspondingInput( const Plug *output ) const;

		virtual void affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const;
		
	protected :
		
		/// Implemented to return the hash of the matching input using a context modified by
		/// processContext() - derived class should therefore not need to reimplement hash(),
		/// and should only implement processContext().
		virtual void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( ValuePlug *output, const Context *context ) const;
		
		/// Should be called by derived class affects() methods when the input
		/// affects their implementation of processContext().
		void appendAffectedPlugs( DependencyNode::AffectedPlugsContainer &outputs ) const;
		
		/// Must be implemented to modify context in place.
		virtual void processContext( Context *context ) const = 0;
		
	private :
	
		/// Returns the input corresponding to the output and vice versa.
		const ValuePlug *oppositePlug( const ValuePlug *plug ) const;
	
		static size_t g_firstPlugIndex;

};

typedef ContextProcessor<ComputeNode> ContextProcessorComputeNode;
IE_CORE_DECLAREPTR( ContextProcessorComputeNode );

} // namespace Gaffer

#endif // GAFFER_CONTEXTPROCESSOR_H
