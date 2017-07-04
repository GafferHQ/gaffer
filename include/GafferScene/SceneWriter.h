//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2014, Image Engine Design inc. All rights reserved.
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

#ifndef GAFFERSCENE_SCENEWRITER_H
#define GAFFERSCENE_SCENEWRITER_H

#include "IECore/SceneInterface.h"

#include "Gaffer/TypedPlug.h"

#include "GafferDispatch/TaskNode.h"

#include "GafferScene/Export.h"
#include "GafferScene/TypeIds.h"
#include "GafferScene/ScenePlug.h"

namespace GafferScene
{

class GAFFERSCENE_API SceneWriter : public GafferDispatch::TaskNode
{

	public :

		SceneWriter( const std::string &name=defaultName<SceneWriter>() );
		virtual ~SceneWriter();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::SceneWriter, SceneWriterTypeId, GafferDispatch::TaskNode );

		Gaffer::StringPlug *fileNamePlug();
		const Gaffer::StringPlug *fileNamePlug() const;

		ScenePlug *inPlug();
		const ScenePlug *inPlug() const;

		ScenePlug *outPlug();
		const ScenePlug *outPlug() const;

		virtual IECore::MurmurHash hash( const Gaffer::Context *context ) const;

		virtual void execute() const;

		/// Re-implemented to open the file for writing, then iterate through the
		/// frames, modifying the current Context and calling writeLocation().
		virtual void executeSequence( const std::vector<float> &frames ) const;

		/// Re-implemented to return true, since the entire file must be written at once.
		virtual bool requiresSequenceExecution() const;

	private :

		void createDirectories( const std::string &fileName ) const;
		void writeLocation( const GafferScene::ScenePlug *scene, const ScenePlug::ScenePath &scenePath, Gaffer::Context *context, IECore::SceneInterface *output, double time ) const;

		static size_t g_firstPlugIndex;

		static const double g_frameRate;
};

IE_CORE_DECLAREPTR( SceneWriter )

} // namespace GafferScene

#endif // GAFFERSCENE_SCENEWRITER_H
