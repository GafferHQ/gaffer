//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferScene/Attributes.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Attributes );

Attributes::Attributes( const std::string &name )
	:	SceneElementProcessor( name )
{
	addChild(
		new ParameterListPlug(
			"attributes",
			Plug::In,
			Plug::Default | Plug::Dynamic
		)
	);
}

Attributes::Attributes( const std::string &name, Gaffer::Plug::Flags attributesPlugFlags )
	:	SceneElementProcessor( name )
{
	addChild(
		new ParameterListPlug(
			"attributes",
			Plug::In,
			attributesPlugFlags
		)
	);
}

Attributes::~Attributes()
{
}

GafferScene::ParameterListPlug *Attributes::attributesPlug()
{
	return getChild<ParameterListPlug>( "attributes" );
}

const GafferScene::ParameterListPlug *Attributes::attributesPlug() const
{
	return getChild<ParameterListPlug>( "attributes" );
}

void Attributes::affects( const Gaffer::ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );
	
	if( attributesPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

IECore::ConstCompoundObjectPtr Attributes::processAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputAttributes ) const
{
	const ParameterListPlug *ap = attributesPlug();
	if( !ap->children().size() )
	{
		return inputAttributes;
	}
	
	CompoundObjectPtr result = inputAttributes ? inputAttributes->copy() : CompoundObjectPtr( new CompoundObject );
	ap->fillParameterList( result->members() );
	
	return result;
}
