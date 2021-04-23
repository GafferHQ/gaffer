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

#ifndef GAFFER_RANDOM_H
#define GAFFER_RANDOM_H

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/ComputeNode.h"
#include "Gaffer/NumericPlug.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

/// Base class for nodes which generate random values based on Context values.
class GAFFER_API Random : public ComputeNode
{

	public :

		Random( const std::string &name=defaultName<Random>() );
		~Random() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::Random, RandomTypeId, ComputeNode );

		IntPlug *seedPlug();
		const IntPlug *seedPlug() const;
		StringPlug *contextEntryPlug();
		const StringPlug *contextEntryPlug() const;

		V2fPlug *floatRangePlug();
		const V2fPlug *floatRangePlug() const;
		FloatPlug *outFloatPlug();
		const FloatPlug *outFloatPlug() const;

		Color3fPlug *baseColorPlug();
		const Color3fPlug *baseColorPlug() const;
		FloatPlug *huePlug();
		const FloatPlug *huePlug() const;
		FloatPlug *saturationPlug();
		const FloatPlug *saturationPlug() const;
		FloatPlug *valuePlug();
		const FloatPlug *valuePlug() const;
		Color3fPlug *outColorPlug();
		const Color3fPlug *outColorPlug() const;

		void affects( const Plug *input, AffectedPlugsContainer &outputs ) const override;

		Imath::Color3f randomColor( unsigned long int seed ) const;

	protected :

		void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const override;
		void compute( ValuePlug *output, const Context *context ) const override;

	private :

		void hashSeed( const Context *context, IECore::MurmurHash &h ) const;
		unsigned long int computeSeed( const Context *context ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Random )

} // namespace Gaffer

#endif // GAFFER_RANDOM_H
