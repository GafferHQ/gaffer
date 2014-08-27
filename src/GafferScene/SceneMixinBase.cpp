//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "IECore/Exception.h"

#include "GafferScene/SceneMixinBase.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( SceneMixinBase );

SceneMixinBase::SceneMixinBase( const std::string &name )
	:	SceneProcessor( name )
{
}

SceneMixinBase::~SceneMixinBase()
{
}

void SceneMixinBase::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	throw Exception( "Unexpected call to SceneMixinBase::hashBound" );
}

void SceneMixinBase::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	throw Exception( "Unexpected call to SceneMixinBase::hashTransform" );
}

void SceneMixinBase::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	throw Exception( "Unexpected call to SceneMixinBase::hashAttributes" );
}

void SceneMixinBase::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	throw Exception( "Unexpected call to SceneMixinBase::hashObject" );
}

void SceneMixinBase::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	throw Exception( "Unexpected call to SceneMixinBase::hashChildNames" );
}

void SceneMixinBase::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	throw Exception( "Unexpected call to SceneMixinBase::hashGlobals" );
}

Imath::Box3f SceneMixinBase::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	throw Exception( "Unexpected call to SceneMixinBase::computeBound" );
}

Imath::M44f SceneMixinBase::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	throw Exception( "Unexpected call to SceneMixinBase::computeTransform" );
}

IECore::ConstCompoundObjectPtr SceneMixinBase::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	throw Exception( "Unexpected call to SceneMixinBase::computeAttributes" );
}

IECore::ConstObjectPtr SceneMixinBase::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	throw Exception( "Unexpected call to SceneMixinBase::computeObject" );
}

IECore::ConstInternedStringVectorDataPtr SceneMixinBase::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	throw Exception( "Unexpected call to SceneMixinBase::computeChildNames" );
}

IECore::ConstCompoundObjectPtr SceneMixinBase::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	throw Exception( "Unexpected call to SceneMixinBase::computeGlobals" );
}
