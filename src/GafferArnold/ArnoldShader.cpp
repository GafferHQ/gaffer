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

#include "boost/format.hpp"

#include "ai.h"

#include "IECore/MessageHandler.h"

#include "IECoreArnold/UniverseBlock.h"

#include "Gaffer/TypedPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/CompoundNumericPlug.h"

#include "GafferArnold/ArnoldShader.h"

using namespace std;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace GafferArnold;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( ArnoldShader );

ArnoldShader::ArnoldShader( const std::string &name )
	:	GafferScene::Shader( name )
{
	addChild( new StringPlug( "__shaderName" ) );
}

ArnoldShader::~ArnoldShader()
{
}

void ArnoldShader::setShader( const std::string &shaderName )
{
	IECoreArnold::UniverseBlock arnoldUniverse;
	
	const AtNodeEntry *shader = AiNodeEntryLookUp( shaderName.c_str() );
	if( !shader )
	{
		throw Exception( str( format( "Shader \"%s\" not found" ) % shaderName ) );
	}

	getChild<StringPlug>( "__shaderName" )->setValue( AiNodeEntryGetName( shader ) );
	
	AtParamIterator *it = AiNodeEntryGetParamIterator( shader );  	
	while( const AtParamEntry *param = AiParamIteratorGetNext( it ) )
	{
		PlugPtr plug = 0;
		/// \todo Proper handler mechanism a bit like ParameterHandler? At least we need to deal with
		/// reloading shaders and changing versions while using existing plugs.
		switch( AiParamGetType( param ) )
		{
			case AI_TYPE_FLOAT :
			
				plug = new FloatPlug(
					AiParamGetName( param ),
					Plug::In,
					AiParamGetDefault( param )->FLT
				);
			
				break;
				
			case AI_TYPE_INT :
			
				plug = new IntPlug(
					AiParamGetName( param ),
					Plug::In,
					AiParamGetDefault( param )->INT
				);
			
				break;
				
			case AI_TYPE_BOOLEAN :
			
				plug = new BoolPlug(
					AiParamGetName( param ),
					Plug::In,
					AiParamGetDefault( param )->BOOL
				);
			
				break;	
				
			case AI_TYPE_RGB :
			
				plug = new Color3fPlug(
					AiParamGetName( param ),
					Plug::In,
					Color3f(
						AiParamGetDefault( param )->RGB.r,
						AiParamGetDefault( param )->RGB.g,
						AiParamGetDefault( param )->RGB.b
					)
				);
			
				break;
				
			case AI_TYPE_RGBA :
			
				plug = new Color4fPlug(
					AiParamGetName( param ),
					Plug::In,
					Color4f(
						AiParamGetDefault( param )->RGBA.r,
						AiParamGetDefault( param )->RGBA.g,
						AiParamGetDefault( param )->RGBA.b,
						AiParamGetDefault( param )->RGBA.a
					)
				);
			
				break;	
				
			case AI_TYPE_POINT2 :
			
				plug = new V2fPlug(
					AiParamGetName( param ),
					Plug::In,
					V2f(
						AiParamGetDefault( param )->PNT2.x,
						AiParamGetDefault( param )->PNT2.y
					)
				);
			
				break;
				
			case AI_TYPE_POINT :
			
				plug = new V3fPlug(
					AiParamGetName( param ),
					Plug::In,
					V3f(
						AiParamGetDefault( param )->PNT.x,
						AiParamGetDefault( param )->PNT.y,
						AiParamGetDefault( param )->PNT.z
					)
				);
			
				break;	
				
			case AI_TYPE_VECTOR :
			
				plug = new V3fPlug(
					AiParamGetName( param ),
					Plug::In,
					V3f(
						AiParamGetDefault( param )->VEC.x,
						AiParamGetDefault( param )->VEC.y,
						AiParamGetDefault( param )->VEC.z
					)
				);
			
				break;	
				
			case AI_TYPE_ENUM :
			
				{
					AtEnum e = AiParamGetEnum( param );
					plug = new StringPlug(
						AiParamGetName( param ),
						Plug::In,
						AiEnumGetString( e, AiParamGetDefault( param )->INT )
					);
				
				}			
				break;	
		
			case AI_TYPE_STRING :
			
				{
					plug = new StringPlug(
						AiParamGetName( param ),
						Plug::In,
						AiParamGetDefault( param )->STR
					);
				
				}
		
		}
		
		if( plug )
		{
			addChild( plug );
			plug->setFlags( Plug::Dynamic, true );
		}
		else
		{
			msg(
				Msg::Warning,
				"ArnoldShader::setShader",
				format( "Unsupported parameter \"%s\" of type \"%s\"" ) %
					AiParamGetName( param ) %
					AiParamGetTypeName( AiParamGetType( param ) )
			);
		}	
		
	}
	AiParamIteratorDestroy( it );
			
	PlugPtr outPlug = 0;
	const int outputType = AiNodeEntryGetOutputType( shader );
	switch( outputType )
	{
		case AI_TYPE_RGB :
			
			outPlug = new Color3fPlug(
				"out",
				Plug::Out
			);
		
			break;
			
		case AI_TYPE_RGBA :
			
			outPlug = new Color4fPlug(
				"out",
				Plug::Out
			);
		
			break;	
		
		case AI_TYPE_FLOAT :
			
			outPlug = new FloatPlug(
				"out",
				Plug::Out
			);
		
			break;
			
		case AI_TYPE_INT :
			
			outPlug = new IntPlug(
				"out",
				Plug::Out
			);
		
			break;	
	
	}
	
	if( outPlug )
	{
		outPlug->setFlags( Plug::Dynamic, true );
		addChild( outPlug );
	}
	else
	{
		if( outputType != AI_TYPE_NONE )
		{
			msg(
				Msg::Warning,
				"ArnoldShader::setShader",
				format( "Unsupported output parameter of type \"%s\"" ) %
					AiParamGetTypeName( AiNodeEntryGetOutputType( shader ) )
			);
		}
	}
	
}

IECore::ShaderPtr ArnoldShader::shader() const
{
	return new IECore::Shader( getChild<StringPlug>( "__shaderName" )->getValue() );
}
