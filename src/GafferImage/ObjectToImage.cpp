//////////////////////////////////////////////////////////////////////////
//  
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

#include "IECore/NullObject.h"

#include "GafferImage/ObjectToImage.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( ObjectToImage );

size_t ObjectToImage::g_firstPlugIndex = 0;

ObjectToImage::ObjectToImage( const std::string &name )
	:	ImagePrimitiveNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ObjectPlug( "object", Plug::In, IECore::NullObject::defaultNullObject() ) );
}

ObjectToImage::~ObjectToImage()
{
}
		
Gaffer::ObjectPlug *ObjectToImage::objectPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex );
}

const Gaffer::ObjectPlug *ObjectToImage::objectPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex );
}
				
void ObjectToImage::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImagePrimitiveNode::affects( input, outputs );
	
	if( input == objectPlug() )
	{
		for( ValuePlugIterator it( outPlug() ); it != it.end(); it++ )
		{
			outputs.push_back( it->get() );
		}
	}
}

void ObjectToImage::hashImagePrimitive( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	objectPlug()->hash( h );
}

IECore::ConstImagePrimitivePtr ObjectToImage::computeImagePrimitive( const Gaffer::Context *context ) const
{
	return runTimeCast<const ImagePrimitive>( objectPlug()->getValue() );
}
