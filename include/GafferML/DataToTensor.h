//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferML/Export.h"
#include "GafferML/TensorPlug.h"

#include "Gaffer/ComputeNode.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/TypedObjectPlug.h"

namespace GafferML
{

class GAFFERML_API DataToTensor : public Gaffer::ComputeNode
{

	public :

		explicit DataToTensor( const std::string &name=defaultName<DataToTensor>() );
		~DataToTensor() override;

		GAFFER_NODE_DECLARE_TYPE( GafferML::DataToTensor, DataToTensorTypeId, Gaffer::ComputeNode );

		enum class ShapeMode
		{
			Automatic,
			Custom
		};

		bool canSetup( const Gaffer::ValuePlug *prototypeDataPlug );
		void setup( const Gaffer::ValuePlug *prototypeDataPlug );

		template<typename T = Gaffer::ValuePlug>
		T *dataPlug();
		template<typename T = Gaffer::ValuePlug>
		const T *dataPlug() const;

		Gaffer::IntPlug *shapeModePlug();
		const Gaffer::IntPlug *shapeModePlug() const;

		Gaffer::Int64VectorDataPlug *shapePlug();
		const Gaffer::Int64VectorDataPlug *shapePlug() const;

		TensorPlug *tensorPlug();
		const TensorPlug *tensorPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;

	private :

		static size_t g_firstPlugIndex;
		static const IECore::InternedString g_dataPlugName;

};

IE_CORE_DECLAREPTR( DataToTensor )

} // namespace GafferML

#include "GafferML/DataToTensor.inl"