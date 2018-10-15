//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design. All rights reserved.
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
//      * Neither the name of Image Engine Design nor the names of
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

#ifndef GAFFERVDB_VDBRENDERABLE_H
#define GAFFERVDB_VDBRENDERABLE_H

#include "IECoreVDB/VDBObject.h"

#include "IECoreGL/Renderable.h"

#include "IECoreGL/Group.h"

#include "IECore/MurmurHash.h"

namespace GafferVDBUI
{

class VDBRenderable : public IECoreGL::Renderable
{
public:
    VDBRenderable( const IECoreVDB::VDBObject *vdbObject ) : m_vdbObject( vdbObject ), m_renderType( 0 ) {}

    void render( IECoreGL::State *currentState ) const override;
    Imath::Box3f bound()  const override;
private:
    IECoreVDB::ConstVDBObjectPtr m_vdbObject;

    mutable IECoreGL::GroupPtr m_group;
    mutable int m_renderType;
    mutable std::string m_gridName;
    mutable IECore::MurmurHash m_hash;
};

} // namespace GafferVDB

#endif // GAFFERVDB_VDBRENDERABLE_H

