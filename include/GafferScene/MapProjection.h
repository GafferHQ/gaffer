//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, John Haddon. All rights reserved.
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

#ifndef GAFFERSCENE_MAPPROJECTION_H
#define GAFFERSCENE_MAPPROJECTION_H

#include "GafferScene/Export.h"
#include "GafferScene/SceneElementProcessor.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferScene
{

/// Applies texture coordinates via a camera projection.
/// \todo At some point I suspect we should move to storing
/// texture coordinates as a single V2fVectorData primitive
/// variable. It would be better to replace sNamePlug() and
/// tNamePlug() with a single plug specifying a prefix (now)
/// and the name of the primitive variable itself (later).
class GAFFERSCENE_API MapProjection : public SceneElementProcessor
{

	public :

		MapProjection( const std::string &name=defaultName<MapProjection>() );
		virtual ~MapProjection();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::MapProjection, MapProjectionTypeId, SceneElementProcessor );

		Gaffer::StringPlug *cameraPlug();
		const Gaffer::StringPlug *cameraPlug() const;

		Gaffer::StringPlug *sNamePlug();
		const Gaffer::StringPlug *sNamePlug() const;

		Gaffer::StringPlug *tNamePlug();
		const Gaffer::StringPlug *tNamePlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		virtual bool processesObject() const;
		virtual void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstObjectPtr computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( MapProjection )

} // namespace GafferScene

#endif // GAFFERSCENE_MAPPROJECTION_H
