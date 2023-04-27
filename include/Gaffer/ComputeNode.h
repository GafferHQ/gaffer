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

#pragma once

#include "Gaffer/DependencyNode.h"

#include "IECore/MurmurHash.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Context )

/// The ComputeNode class extends DependencyNode to define a mechanism via which
/// computations can be performed. When an output ValuePlug::getValue() method is
/// called the value will be computed using a combination of the hash() and compute()
/// methods defined by the ComputeNode. ComputeNode computations are threadsafe (multiple
/// threads may call getValue() with multiple Contexts concurrently) and make use
/// of an in-memory caching mechanism to avoid repeated computations of the same thing.
class GAFFER_API ComputeNode : public DependencyNode
{

	public :

		explicit ComputeNode( const std::string &name=defaultName<ComputeNode>() );
		~ComputeNode() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::ComputeNode, ComputeNodeTypeId, DependencyNode );

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

		/// Called to determine how calls to `hash()` should be cached. If `hash( output )`
		/// will spawn TBB tasks then one of the task-based policies _must_ be used.
		virtual ValuePlug::CachePolicy hashCachePolicy( const ValuePlug *output ) const;
		/// Called to determine how calls to `compute()` should be cached. If `compute( output )`
		/// will spawn TBB tasks then one of the task-based policies _must_ be used.
		virtual ValuePlug::CachePolicy computeCachePolicy( const ValuePlug *output ) const;

	private :

		friend class ValuePlug;

};

} // namespace Gaffer
