//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferImage/Export.h"
#include "GafferImage/TypeIds.h"

#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"

#include "OpenColorIO/OpenColorTypes.h"

namespace GafferImage
{
/// Plug to provide user-level control over the default OCIO config for a ScriptNode.
/// Would typically be used by calling `acquireDefaultConfigPlug()` from a startup file.
class GAFFERIMAGE_API OpenColorIOConfigPlug final : public Gaffer::ValuePlug
{

	public :

		GAFFER_PLUG_DECLARE_TYPE( GafferImage::OpenColorIOConfigPlug, OpenColorIOConfigPlugTypeId, Gaffer::ValuePlug );

		explicit OpenColorIOConfigPlug( const std::string &name = defaultName<OpenColorIOConfigPlug>(), Direction direction = In, unsigned flags = Default );

		Gaffer::StringPlug *configPlug();
		const Gaffer::StringPlug *configPlug() const;

		Gaffer::StringPlug *workingSpacePlug();
		const Gaffer::StringPlug *workingSpacePlug() const;

		Gaffer::ValuePlug *variablesPlug();
		const Gaffer::ValuePlug *variablesPlug() const;

		Gaffer::StringPlug *displayTransformPlug();
		const Gaffer::ValuePlug *displayTransformPlug() const;

		bool acceptsChild( const GraphComponent *potentialChild ) const override;
		Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		static OpenColorIOConfigPlug *acquireDefaultConfigPlug( Gaffer::ScriptNode *scriptNode, bool createIfNecessary = true );

	protected :

		void parentChanged( Gaffer::GraphComponent *oldParent ) override;

	private :

		void plugSet( Gaffer::Plug *plug );
		Gaffer::Signals::ScopedConnection m_plugSetConnection;
};

} // namespace GafferImage
