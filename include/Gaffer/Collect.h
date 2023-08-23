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
#include "Gaffer/Export.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/TypeIds.h"

namespace Gaffer
{

class GAFFER_API Collect : public ComputeNode
{

	public :

		Collect( const std::string &name = defaultName<Collect>() );
		~Collect() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::Collect, CollectTypeId, ComputeNode );

		StringPlug *contextVariablePlug();
		const StringPlug *contextVariablePlug() const;

		StringPlug *indexContextVariablePlug();
		const StringPlug *indexContextVariablePlug() const;

		StringVectorDataPlug *contextValuesPlug();
		const StringVectorDataPlug *contextValuesPlug() const;

		BoolPlug *enabledPlug() override;
		const BoolPlug *enabledPlug() const override;

		ValuePlug *inPlug();
		const ValuePlug *inPlug() const;

		ValuePlug *outPlug();
		const ValuePlug *outPlug() const;

		ObjectPlug *enabledValuesPlug();
		const ObjectPlug *enabledValuesPlug() const;

		bool canAddInput( const ValuePlug *prototype ) const;
		ValuePlug *addInput( const ValuePlug *prototype );
		void removeInput( ValuePlug *inputPlug );

		ValuePlug *outputPlugForInput( const ValuePlug *inputPlug );
		const ValuePlug *outputPlugForInput( const ValuePlug *inputPlug ) const;

		ValuePlug *inputPlugForOutput( const ValuePlug *outputPlug );
		const ValuePlug *inputPlugForOutput( const ValuePlug *outputPlug ) const;

		void affects( const Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const override;
		void compute( ValuePlug *output, const Context *context) const override;

		ValuePlug::CachePolicy hashCachePolicy( const ValuePlug *output ) const override;
		ValuePlug::CachePolicy computeCachePolicy( const ValuePlug *output ) const override;

	private :

		// We collect the values for all output plugs in a single compute and cache
		// them in a CompoundObject on this internal plug, indexing them by plug name.
		// This provides greater ValuePlug cache coherency when multiple inputs depend
		// on the same upstream computes (for instance, when they are each collecting
		// a property of the same scene location).
		CompoundObjectPlug *collectionPlug();
		const CompoundObjectPlug *collectionPlug() const;

		void inputAdded( GraphComponent *input );
		void inputRemoved( GraphComponent *input );
		void inputNameChanged( GraphComponent *input, IECore::InternedString oldName );

		std::unordered_map<GraphComponent *, Signals::ScopedConnection> m_inputNameChangedConnections;

		static size_t g_firstPlugIndex;

};

}  // namespace Gaffer
