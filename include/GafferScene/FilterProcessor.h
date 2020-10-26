//////////////////////////////////////////////////////////////////////////
//
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

#ifndef GAFFERSCENE_FILTERPROCESSOR_H
#define GAFFERSCENE_FILTERPROCESSOR_H

#include "GafferScene/Filter.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( ArrayPlug )

} // namespace Gaffer

namespace GafferScene
{

/// A base class for filters which operate by processing one
/// or more input filters.
class GAFFERSCENE_API FilterProcessor : public Filter
{

	public :

		/// Constructs with a single input filter plug named "in". Use inPlug()
		/// to access this plug.
		FilterProcessor( const std::string &name=defaultName<FilterProcessor>() );
		/// Constructs with an ArrayPlug called "in". Use inPlug() as a
		/// convenience for accessing the first child in the array, and use
		/// inPlugs() to access the array itself.
		FilterProcessor( const std::string &name, size_t minInputs, size_t maxInputs = Imath::limits<size_t>::max() );

		~FilterProcessor() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::FilterProcessor, FilterProcessorTypeId, Filter );

		/// Returns the primary filter input. For nodes with multiple inputs
		/// this will be the first child of the inPlugs() array. For nodes
		/// with a single input, it will be a plug parented directly to the
		/// node. If the node is disabled via enabledPlug(), then the inPlug()
		/// is automatically passed through directly to the outPlug().
		FilterPlug *inPlug();
		const FilterPlug *inPlug() const;

		/// For nodes with multiple inputs, returns the ArrayPlug which
		/// hosts them. For single input nodes, returns null.
		Gaffer::ArrayPlug *inPlugs();
		const Gaffer::ArrayPlug *inPlugs() const;

		/// Returns inPlug() as the correspondingInput of outPlug();
		Gaffer::Plug *correspondingInput( const Gaffer::Plug *output ) override;
		const Gaffer::Plug *correspondingInput( const Gaffer::Plug *output ) const override;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		/// Reimplemented to pass through the inPlug() hash when the node is disabled.
		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		/// Reimplemented to pass through the inPlug() result when the node is disabled.
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( FilterProcessor )

} // namespace GafferScene

#endif // GAFFERSCENE_FILTERPROCESSOR_H
