//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/Export.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/TypeIds.h"

#include "Gaffer/ComputeNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/TypedObjectPlug.h"

#include <string>

namespace GafferScene
{

struct GAFFERSCENE_API AttributeQuery : Gaffer::ComputeNode
{
	explicit AttributeQuery( const std::string& name = defaultName< AttributeQuery >() );
	~AttributeQuery() override;

	GAFFER_NODE_DECLARE_TYPE( GafferScene::AttributeQuery, AttributeQueryTypeId, Gaffer::ComputeNode );

	ScenePlug* scenePlug();
	const ScenePlug* scenePlug() const;
	Gaffer::StringPlug* locationPlug();
	const Gaffer::StringPlug* locationPlug() const;
	Gaffer::StringPlug* attributePlug();
	const Gaffer::StringPlug* attributePlug() const;
	Gaffer::BoolPlug* inheritPlug();
	const Gaffer::BoolPlug* inheritPlug() const;
	Gaffer::BoolPlug* existsPlug();
	const Gaffer::BoolPlug* existsPlug() const;

	bool isSetup() const;
	bool canSetup( const Gaffer::ValuePlug* plug ) const;
	void setup( const Gaffer::ValuePlug* plug );

	template<typename PlugType = Gaffer::ValuePlug>
	PlugType* defaultPlug();
	template<typename PlugType = Gaffer::ValuePlug>
	const PlugType* defaultPlug() const;
	template<typename PlugType = Gaffer::ValuePlug>
	PlugType* valuePlug();
	template<typename PlugType = Gaffer::ValuePlug>
	const PlugType* valuePlug() const;

	void affects( const Gaffer::Plug* input, AffectedPlugsContainer& outputs ) const override;

protected:

	void hash( const Gaffer::ValuePlug* output, const Gaffer::Context* context, IECore::MurmurHash& h ) const override;
	void compute( Gaffer::ValuePlug* output, const Gaffer::Context* context ) const override;

private:

	IECore::InternedString valuePlugName() const;
	IECore::InternedString defaultPlugName() const;

	Gaffer::ObjectPlug* internalObjectPlug();
	const Gaffer::ObjectPlug* internalObjectPlug() const;

	static size_t g_firstPlugIndex;
};

IE_CORE_DECLAREPTR( AttributeQuery )

} // GafferScene

#include "GafferScene/AttributeQuery.inl"
