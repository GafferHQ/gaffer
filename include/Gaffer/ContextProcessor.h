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

#pragma once

#include "Gaffer/ComputeNode.h"
#include "Gaffer/Context.h"

namespace Gaffer
{

/// The ContextProcessor provides a base class to simplify the creation of nodes
/// which evaluate their inputs using a modified context to that provided for the output
/// evaluation - time warps being one good example.
class IECORE_EXPORT ContextProcessor : public ComputeNode
{

	public :

		GAFFER_NODE_DECLARE_TYPE( Gaffer::ContextProcessor, ContextProcessorTypeId, ComputeNode );

		explicit ContextProcessor( const std::string &name=GraphComponent::defaultName<ContextProcessor>() );
		~ContextProcessor() override;

		/// \undoable
		void setup( const Plug *plug );

		Plug *inPlug();
		const Plug *inPlug() const;

		Plug *outPlug();
		const Plug *outPlug() const;

		BoolPlug *enabledPlug() override;
		const BoolPlug *enabledPlug() const override;

		Plug *correspondingInput( const Plug *output ) override;
		const Plug *correspondingInput( const Plug *output ) const override;

		void affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const override;

		/// Returns the context that `inPlug()` will be evaluated in
		/// when `outPlug()` is evaluated in the current context.
		ContextPtr inPlugContext() const;

	protected :

		/// Implemented to return the hash of the matching input using a context modified by
		/// processContext() - derived class should therefore not need to reimplement hash(),
		/// and should only implement processContext().
		void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const override;
		void compute( ValuePlug *output, const Context *context ) const override;

		/// Must be implemented to return true if the input is used in `processContext()`.
		virtual bool affectsContext( const Plug *input ) const = 0;
		/// Must be implemented to modify context in place.
		virtual void processContext( Context::EditableScope &context, IECore::ConstRefCountedPtr &storage ) const = 0;

	private :

		class ProcessedScope;

		static const Plug *correspondingDescendant( const Plug *plug, const Plug *plugAncestor, const Plug *oppositeAncestor );

		/// Returns the input corresponding to the output and vice versa.
		const Plug *oppositePlug( const Plug *plug ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ContextProcessor );

} // namespace Gaffer
