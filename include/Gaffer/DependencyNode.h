//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFER_DEPENDENCYNODE_H
#define GAFFER_DEPENDENCYNODE_H

#include "IECore/MurmurHash.h"

#include "Gaffer/Node.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Context )

class DependencyNode : public Node
{

	public :

		DependencyNode( const std::string &name=staticTypeName() );
		virtual ~DependencyNode();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( DependencyNode, DependencyNodeTypeId, Node );

		typedef std::vector<const ValuePlug *> AffectedPlugsContainer;
		
		/// Must be implemented to fill outputs with all the plugs whose computation
		/// will be affected by the specified input. It is an error to pass a CompoundPlug
		/// for input or to place one in outputs as computations are always performed on the
		/// leaf level plugs only. Implementations of this method should call the base class
		/// implementation first.
		virtual void affects( const ValuePlug *input, AffectedPlugsContainer &outputs ) const = 0;
		
	protected :
		
		/// Called to compute the hashes for output Plugs. Must be implemented to call the base
		/// class method, then call input->hash( h ) for all input plugs used in the computation
		/// of output. Must also hash in the value of any context items that will be accessed by
		/// the computation.
		///
		/// In the special case that the node will pass through a value from an input plug
		/// unchanged, the hash for the input plug should be assigned directly to the result
		/// (rather than appended) - this allows cache entries to be shared.
		virtual void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const = 0;
		/// Called to compute the values for output Plugs. Must be implemented to compute
		/// an appropriate value and apply it using output->setValue().
		virtual void compute( ValuePlug *output, const Context *context ) const = 0;
		
	private :
			
		friend class ValuePlug;
		
};

typedef FilteredChildIterator<TypePredicate<DependencyNode> > DependencyNodeIterator;
typedef FilteredRecursiveChildIterator<TypePredicate<DependencyNode> > RecursiveDependencyNodeIterator;

} // namespace Gaffer

#endif // GAFFER_DEPENDENCYNODE_H
