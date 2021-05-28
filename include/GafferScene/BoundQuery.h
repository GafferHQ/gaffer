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

#ifndef GAFFERSCENE_BOUNDQUERY_H
#define GAFFERSCENE_BOUNDQUERY_H

#include "GafferScene/Export.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/TypeIds.h"

#include "Gaffer/BoxPlug.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/ComputeNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedPlug.h"

#include <string>

namespace GafferScene
{

struct GAFFERSCENE_API BoundQuery : Gaffer::ComputeNode
{
	enum class Space
	{
		Local    = 0x00,
		World    = 0x01,
		Relative = 0x02
	};

	BoundQuery( std::string const& name = defaultName< BoundQuery >() );
	~BoundQuery() override;

	GAFFER_NODE_DECLARE_TYPE( GafferScene::BoundQuery, BoundQueryTypeId, Gaffer::ComputeNode );

	ScenePlug* scenePlug();
	ScenePlug const* scenePlug() const;
	Gaffer::StringPlug* locationPlug();
	Gaffer::StringPlug const* locationPlug() const;
	Gaffer::IntPlug* spacePlug();
	Gaffer::IntPlug const* spacePlug() const;
	Gaffer::StringPlug* relativeLocationPlug();
	Gaffer::StringPlug const* relativeLocationPlug() const;
	Gaffer::Box3fPlug* boundPlug();
	Gaffer::Box3fPlug const* boundPlug() const;
	Gaffer::V3fPlug* centerPlug();
	Gaffer::V3fPlug const* centerPlug() const;
	Gaffer::V3fPlug* sizePlug();
	Gaffer::V3fPlug const* sizePlug() const;

	void affects( Gaffer::Plug const* input, AffectedPlugsContainer& outputs ) const override;

protected:

	void hash( Gaffer::ValuePlug const* output, Gaffer::Context const* context, IECore::MurmurHash& hash ) const override;
	void compute( Gaffer::ValuePlug* output, Gaffer::Context const* context ) const override;

private:

	Gaffer::AtomicBox3fPlug* internalBoundPlug();
	Gaffer::AtomicBox3fPlug const* internalBoundPlug() const;

	static size_t g_firstPlugIndex;
};

IE_CORE_DECLAREPTR( BoundQuery )

} // GafferScene

#endif // GAFFERSCENE_BOUNDQUERY_H
