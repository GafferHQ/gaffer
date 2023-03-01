//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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
#include "Gaffer/TypedObjectPlug.h"

namespace Gaffer
{

class GAFFER_API RandomChoice : public ComputeNode
{

	public :

		RandomChoice( const std::string &name=defaultName<RandomChoice>() );
		~RandomChoice() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::RandomChoice, RandomChoiceTypeId, ComputeNode );

		/// Sets up the node to output the specified plug type. The passed plug
		/// is used as a template, but will not be parented to the node
		/// itself - typically you will pass a plug which you will connect to
		/// the node after calling `setup()`.
		/// \undoable
		void setup( const ValuePlug *plug );
		/// Returns true if `plug` is suitable for passing to `setup()`. Not
		/// all plug types are supported.
		static bool canSetup( const ValuePlug *plug );

		IntPlug *seedPlug();
		const IntPlug *seedPlug() const;

		StringPlug *seedVariablePlug();
		const StringPlug *seedVariablePlug() const;

		/// Compound plug that groups the `choices.values` and `choices.weights`
		/// plugs.
		ValuePlug *choicesPlug();
		const ValuePlug *choicesPlug() const;

		/// The type of the `choices.values` plug is dictated by the type of
		/// `outPlug`. For example, `choices.values` is a StringVectorDataPlug when
		/// `out` is a StringPlug.
		template<typename T=ValuePlug>
		T *choicesValuesPlug();
		template<typename T=ValuePlug>
		const T *choicesValuesPlug() const;

		FloatVectorDataPlug *choicesWeightsPlug();
		const FloatVectorDataPlug *choicesWeightsPlug() const;

		/// The type of the `out` plug matches the type passed to `setup()`.
		template<typename T=ValuePlug>
		T *outPlug();
		template<typename T=ValuePlug>
		const T *outPlug() const;

		void affects( const Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const override;
		void compute( ValuePlug *output, const Context *context ) const override;

	private :

		ValuePlug *outPlugInternal();
		const ValuePlug *outPlugInternal() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( RandomChoice )

} // namespace Gaffer

#include "Gaffer/RandomChoice.inl"
