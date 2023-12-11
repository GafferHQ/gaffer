//////////////////////////////////////////////////////////////////////////
//
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

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/ComputeNode.h"
#include "Gaffer/NumericPlug.h"

namespace Gaffer
{

class GAFFER_API Switch : public ComputeNode
{

	public :

		GAFFER_NODE_DECLARE_TYPE( Gaffer::Switch, SwitchTypeId, ComputeNode );

		explicit Switch( const std::string &name=GraphComponent::defaultName<Switch>() );
		~Switch() override;

		/// Sets up the switch to work with the specified plug type.
		/// The passed plug is used as a template, but will not be
		/// referenced by the Switch itself - typically you will pass a plug
		/// which you will connect to the Switch after calling
		/// `setup()`.
		/// \undoable
		void setup( const Plug *plug );

		/// Will return null unless `setup()` has been called.
		ArrayPlug *inPlugs();
		const ArrayPlug *inPlugs() const;

		/// Will return null unless `setup()` has been called.
		Plug *outPlug();
		const Plug *outPlug() const;

		/// Returns the input plug which will be passed through
		/// by the switch in the current context.
		/// \todo Remove, and add `nullptr` default to the version
		/// below.
		Plug *activeInPlug();
		const Plug *activeInPlug() const;
		/// Returns the input plug which will be passed through
		/// by the switch when evaluating `outPlug` in the
		/// current context.
		Plug *activeInPlug( const Plug *outPlug );
		const Plug *activeInPlug( const Plug *outPlug ) const;

		IntPlug *indexPlug();
		const IntPlug *indexPlug() const;

		BoolPlug *enabledPlug() override;
		const BoolPlug *enabledPlug() const override;

		Plug *correspondingInput( const Plug *output ) override;
		const Plug *correspondingInput( const Plug *output ) const override;

		void affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const override;

	protected :

		// Implemented to reject input branches inputs if they wouldn't be accepted by the output.
		bool acceptsInput( const Plug *plug, const Plug *inputPlug ) const override;

		// The hash() and compute() methods are implemented to pass through the results from
		// the input branch specified by indexPlug(). They operate via the hashInternal() and
		// computeInternal() methods, which are specialised for the cases where we do and do
		// not inherit from ComputeNode.
		void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const override;
		void compute( ValuePlug *output, const Context *context ) const override;

	private :

		void childAdded( GraphComponent *child );
		void plugSet( Plug *plug );
		void plugInputChanged( Plug *plug );
		size_t inputIndex( const Context *context ) const;

		// Returns the input corresponding to the output and vice versa. Returns null
		// if plug is not meaningful to the switching process.
		const Plug *oppositePlug( const Plug *plug, const Context *context = nullptr ) const;

		void updateInternalConnection();

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Switch );

using SwitchComputeNode = Switch;
using SwitchComputeNodePtr = SwitchPtr;
using ConstSwitchComputeNodePtr = ConstSwitchPtr;

} // namespace Gaffer
