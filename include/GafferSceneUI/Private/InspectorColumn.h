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

#include "GafferSceneUI/Export.h"
#include "GafferSceneUI/Private/Inspector.h"

#include "GafferUI/PathColumn.h"

#include "Gaffer/Path.h"

using namespace IECore;

namespace GafferSceneUI
{

namespace Private
{

/// Column type which makes use of an Inspector.
class GAFFERSCENEUI_API InspectorColumn : public GafferUI::PathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( InspectorColumn )

		InspectorColumn( GafferSceneUI::Private::InspectorPtr inspector, const std::string &label, const std::string &toolTip = "", PathColumn::SizeMode sizeMode = Default );
		InspectorColumn( GafferSceneUI::Private::InspectorPtr inspector, const CellData &headerData, PathColumn::SizeMode sizeMode = Default );

		/// Returns the inspector used by this column.
		GafferSceneUI::Private::Inspector *inspector() const;

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override;
		CellData headerData( const IECore::Canceller *canceller ) const override;

	private :

		void inspectorDirtied();

		static IECore::ConstStringDataPtr headerValue( const std::string &columnName );

		const Private::InspectorPtr m_inspector;
		const CellData m_headerData;

};

IE_CORE_DECLAREPTR( InspectorColumn )

} // namespace Private

} // namespace GafferSceneUI
