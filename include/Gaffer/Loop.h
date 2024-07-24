//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, John Haddon. All rights reserved.
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"

namespace Gaffer
{

class GAFFER_API Loop : public ComputeNode
{

	public :

		GAFFER_NODE_DECLARE_TYPE( Gaffer::Loop, LoopTypeId, ComputeNode );

		explicit Loop( const std::string &name=GraphComponent::defaultName<Loop>() );
		~Loop() override;

		/// \undoable
		void setup( const ValuePlug *plug );

		ValuePlug *inPlug();
		const ValuePlug *inPlug() const;

		ValuePlug *outPlug();
		const ValuePlug *outPlug() const;

		ValuePlug *nextPlug();
		const ValuePlug *nextPlug() const;

		ValuePlug *previousPlug();
		const ValuePlug *previousPlug() const;

		IntPlug *iterationsPlug();
		const IntPlug *iterationsPlug() const;

		StringPlug *indexVariablePlug();
		const StringPlug *indexVariablePlug() const;

		Gaffer::BoolPlug *enabledPlug() override;
		const Gaffer::BoolPlug *enabledPlug() const override;

		Gaffer::Plug *correspondingInput( const Gaffer::Plug *output ) override;
		const Gaffer::Plug *correspondingInput( const Gaffer::Plug *output ) const override;

		/// Returns the context that will be used to evaluate `nextPlug()` in
		/// the next iteration of the loop (relative to the current context).
		ContextPtr nextIterationContext() const;

		/// Returns the input plug and context that form the previous iteration of the loop
		/// with respect to the `output` plug and the current context. Returns `{ nullptr, nullptr }`
		/// if there is no such iteration.
		std::pair<const ValuePlug *, ContextPtr> previousIteration( const ValuePlug *output ) const;

		void affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const override;
		void compute( ValuePlug *output, const Context *context ) const override;

	private :

		size_t m_inPlugIndex;
		size_t m_outPlugIndex;
		size_t m_firstPlugIndex;

		Signals::Connection m_childAddedConnection;

		void childAdded();
		bool setupPlugs();

		void addAffectedPlug( const ValuePlug *output, DependencyNode::AffectedPlugsContainer &outputs ) const;
		const ValuePlug *ancestorPlug( const ValuePlug *plug, std::vector<IECore::InternedString> &relativeName ) const;
		const ValuePlug *descendantPlug( const ValuePlug *plug, const std::vector<IECore::InternedString> &relativeName ) const;
		const ValuePlug *sourcePlug( const ValuePlug *output, const Context *context, int &sourceLoopIndex, IECore::InternedString &indexVariable ) const;

};

IE_CORE_DECLAREPTR( Loop )

} // namespace Gaffer
