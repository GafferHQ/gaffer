//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Don Boogert. All rights reserved.
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
//      * Neither the name of Don Boogert nor the names of
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

#ifndef GAFFEROSL_OSLVDB_H
#define GAFFEROSL_OSLVDB_H

#include "GafferOSL/Export.h"
#include "GafferOSL/TypeIds.h"

#include "GafferScene/SceneElementProcessor.h"
#include "GafferScene/ShaderPlug.h"

#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"

namespace GafferOSL
{

class GAFFEROSL_API OSLVDB : public GafferScene::SceneElementProcessor
{
public :

	OSLVDB( const std::string &name=defaultName<SceneElementProcessor>() );
	~OSLVDB() override;

	IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferOSL::OSLVDB, OSLVDBTypeId, GafferScene::SceneElementProcessor );

	GafferScene::ShaderPlug *shaderPlug();
	const GafferScene::ShaderPlug *shaderPlug() const;

    Gaffer::StringPlug *gridPlug();
    const Gaffer::StringPlug *gridPlug() const;

    Gaffer::IntPlug *modePlug();
    const Gaffer::IntPlug *modePlug() const;

	void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

protected :

	bool acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const override;

	bool processesBound() const override;
	void hashProcessedBound( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
	Imath::Box3f computeProcessedBound( const ScenePath &path, const Gaffer::Context *context, const Imath::Box3f &inputBound ) const override;

	bool processesObject() const override;
	void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
	IECore::ConstObjectPtr computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const override;

private :

	static size_t g_firstPlugIndex;
};

} // namespace GafferOSL


#endif //GAFFEROSL_OSLVDB_H