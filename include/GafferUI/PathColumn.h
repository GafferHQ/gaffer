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

#ifndef GAFFERUI_PATHCOLUMN_H
#define GAFFERUI_PATHCOLUMN_H

#include "GafferUI/Export.h"

#include "Gaffer/Path.h"

#include "IECore/SimpleTypedData.h"

namespace GafferUI
{

/// Abstract class for extracting properties from a Path in a form
/// suitable for display in a table column. Primarily intended for
/// use in the PathListingWidget.
class GAFFERUI_API PathColumn : public IECore::RefCounted
{

	public :

		IE_CORE_DECLAREMEMBERPTR( PathColumn )

		enum class Role
		{
			/// The primary value to be displayed in a cell or header.
			/// Supported types :
			///
			/// - StringData
			/// - IntData, UIntData, UInt64Data
			/// - FloatData, DoubleData
			/// - DateTimeData
			Value,
			/// An additional icon to be displayed next to the primary
			/// value. Supported types :
			///
			/// - StringData (providing icon name)
			Icon
		};

		/// Returns a value used to draw a cell within the column.
		virtual IECore::ConstRunTimeTypedPtr cellValue( const Gaffer::Path &path, Role role, const IECore::Canceller *canceller = nullptr ) const = 0;
		/// Returns a value used to draw the header for the column.
		virtual IECore::ConstRunTimeTypedPtr headerValue( Role role, const IECore::Canceller *canceller = nullptr ) const = 0;

};

IE_CORE_DECLAREPTR( PathColumn )

/// Standard column type which simply displays a property of the path.
class GAFFERUI_API StandardPathColumn : public PathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( StandardPathColumn )

		StandardPathColumn( const std::string &label, IECore::InternedString property );

		IECore::InternedString property() const;

		IECore::ConstRunTimeTypedPtr cellValue( const Gaffer::Path &path, Role role, const IECore::Canceller *canceller ) const override;
		IECore::ConstRunTimeTypedPtr headerValue( Role role, const IECore::Canceller *canceller ) const override;

	private :

		IECore::ConstStringDataPtr m_label;
		IECore::InternedString m_property;

};

IE_CORE_DECLAREPTR( StandardPathColumn )

/// Column which uses a property of the path to specify an icon.
class GAFFERUI_API IconPathColumn : public PathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( IconPathColumn )

		/// The name for the icon is `<prefix><property>`, with `property` being queried
		/// by `Path::property()`. Supported property types :
		///
		/// - StringData
		/// - IntData, UInt44Data
		/// - BoolData
		IconPathColumn( const std::string &label, const std::string &prefix, IECore::InternedString property );

		IECore::ConstRunTimeTypedPtr cellValue( const Gaffer::Path &path, Role role, const IECore::Canceller *canceller ) const override;
		IECore::ConstRunTimeTypedPtr headerValue( Role role, const IECore::Canceller *canceller ) const override;

	private :

		IECore::ConstStringDataPtr m_label;
		std::string m_prefix;
		IECore::InternedString m_property;

};

IE_CORE_DECLAREPTR( IconPathColumn )

/// Column type suitable for displaying an icon for
/// FileSystemPaths.
class GAFFERUI_API FileIconPathColumn : public PathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( FileIconPathColumn )

		FileIconPathColumn();

		IECore::ConstRunTimeTypedPtr cellValue( const Gaffer::Path &path, Role role, const IECore::Canceller *canceller ) const override;
		IECore::ConstRunTimeTypedPtr headerValue( Role role, const IECore::Canceller *canceller ) const override;

	private :

		const IECore::StringDataPtr m_label;

};

IE_CORE_DECLAREPTR( FileIconPathColumn )

} // namespace GafferUI

#endif // GAFFERUI_PATHCOLUMN_H
