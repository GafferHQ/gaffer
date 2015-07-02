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

#ifndef GAFFER_LOOP_H
#define GAFFER_LOOP_H

#include "Gaffer/ComputeNode.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"

namespace Gaffer
{

/// A generic mixin class for creating loops in computation - it
/// can be used for any ValuePlug type and even for compound plug
/// types.  It is expected that either the BaseType provides plugs named
/// "in" and "out" already, or that it doesn't and they will be
/// added dynamically following construction of the node.
template<typename BaseType>
class Loop : public BaseType
{

	public :

		IECORE_RUNTIMETYPED_DECLARETEMPLATE( Loop<BaseType>, BaseType );

		Loop( const std::string &name=GraphComponent::defaultName<Loop>() );
		virtual ~Loop();

		ValuePlug *nextPlug();
		const ValuePlug *nextPlug() const;

		ValuePlug *previousPlug();
		const ValuePlug *previousPlug() const;

		IntPlug *iterationsPlug();
		const IntPlug *iterationsPlug() const;

		StringPlug *indexVariablePlug();
		const StringPlug *indexVariablePlug() const;

		virtual Gaffer::BoolPlug *enabledPlug();
		virtual const Gaffer::BoolPlug *enabledPlug() const;

		virtual Gaffer::Plug *correspondingInput( const Gaffer::Plug *output );
		virtual const Gaffer::Plug *correspondingInput( const Gaffer::Plug *output ) const;

		void affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const;

	protected :

		virtual void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( ValuePlug *output, const Context *context ) const;

	private :

		size_t m_inPlugIndex;
		size_t m_outPlugIndex;
		size_t m_firstPlugIndex;

		void childAdded();
		bool setupPlugs();

		ValuePlug *inPlugInternal();
		const ValuePlug *inPlugInternal() const;

		ValuePlug *outPlugInternal();
		const ValuePlug *outPlugInternal() const;

		void addAffectedPlug( const ValuePlug *output, DependencyNode::AffectedPlugsContainer &outputs ) const;
		const ValuePlug *ancestorPlug( const ValuePlug *plug, std::vector<IECore::InternedString> &relativeName ) const;
		const ValuePlug *descendantPlug( const ValuePlug *plug, const std::vector<IECore::InternedString> &relativeName ) const;
		const ValuePlug *sourcePlug( const ValuePlug *output, const Context *context, int &sourceLoopIndex, IECore::InternedString &indexVariable ) const;

		IE_CORE_DECLARERUNTIMETYPEDDESCRIPTION( Loop<BaseType> );

};

typedef Loop<ComputeNode> LoopComputeNode;

} // namespace Gaffer

#endif // GAFFER_LOOP_H
