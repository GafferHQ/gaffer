//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlug.h"

#include "GafferScene/Export.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/TypeIds.h"

namespace GafferScene
{

class GAFFERSCENE_API PointInstancerCore : public Gaffer::ComputeNode
{

	public :

		PointInstancerCore( const std::string &name=defaultName<PointInstancerCore>() );
		~PointInstancerCore() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::PointInstancerCore, PointInstancerCoreTypeId, Gaffer::ComputeNode );

		Gaffer::ObjectPlug *inPointsPlug();
		const Gaffer::ObjectPlug *inPointsPlug() const;

		Gaffer::StringPlug *timeOffsetPlug();
		const Gaffer::StringPlug *timeOffsetPlug() const;

		Gaffer::StringPlug *contextVariablesPlug();
		const Gaffer::StringPlug *contextVariablesPlug() const;

		Gaffer::StringPlug *prototypeFormatPlug();
		const Gaffer::StringPlug *prototypeFormatPlug() const;

		Gaffer::ObjectPlug *outPointsPlug();
		const Gaffer::ObjectPlug *outPointsPlug() const;

		Gaffer::StringVectorDataPlug *prototypeNamesPlug();
		const Gaffer::StringVectorDataPlug *prototypeNamesPlug() const;

		Gaffer::StringPlug *prototypeSelectorPlug();
		const Gaffer::StringPlug *prototypeSelectorPlug() const;

		Gaffer::StringPlug *prototypePlug();
		const Gaffer::StringPlug *prototypePlug() const;

		Gaffer::FloatPlug *prototypeTimeOffsetPlug();
		const Gaffer::FloatPlug *prototypeTimeOffsetPlug() const;

		Gaffer::AtomicCompoundDataPlug *prototypeContextPlug();
		const Gaffer::AtomicCompoundDataPlug *prototypeContextPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

	private :

		bool affectsPrototypeMap( const Gaffer::Plug *input ) const;
		void hashPrototypeMap( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		IECore::ConstObjectPtr computePrototypeMap() const;

		bool affectsOutPoints( const Gaffer::Plug *input ) const;
		void hashOutPoints( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		IECore::ConstObjectPtr computeOutPoints() const;

		bool affectsPrototypeNames( const Gaffer::Plug *input ) const;
		void hashPrototypeNames( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		IECore::ConstStringVectorDataPtr computePrototypeNames() const;

		bool affectsPrototype( const Gaffer::Plug *input ) const;
		void hashPrototype( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		std::string computePrototype() const;

		bool affectsPrototypeTimeOffset( const Gaffer::Plug *input ) const;
		void hashPrototypeTimeOffset( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		float computePrototypeTimeOffset() const;

		bool affectsPrototypeContext( const Gaffer::Plug *input ) const;
		void hashPrototypeContext( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		IECore::ConstCompoundDataPtr computePrototypeContext() const;

		Gaffer::ObjectPlug *prototypeMapPlug();
		const Gaffer::ObjectPlug *prototypeMapPlug() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( PointInstancerCore )

} // namespace GafferScene
