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

#ifndef GAFFERSCENE_IMAGENODE_H
#define GAFFERSCENE_IMAGENODE_H

#include "Gaffer/Node.h"

#include "GafferImage/ImagePlug.h"

namespace GafferImage
{

/// The SceneNode class is the base class for all Nodes which are capable of generating
/// or manipulating images.
class ImageNode : public Gaffer::Node
{

	public :

		ImageNode( const std::string &name=staticTypeName() );
		virtual ~ImageNode();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( ImageNode, ImageNodeTypeId, Gaffer::Node );
		
		/// All ImageNodes have at least one output ImagePlug for passing on their result. More
		/// may be added by derived classes if necessary.
		ImagePlug *outPlug();
		const ImagePlug *outPlug() const;
				
	protected :
				
		/// Implemented to call the compute*() methods below whenever output is part of an ImagePlug.
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;
		
		virtual Imath::Box2i computeDisplayWindow( const Gaffer::Context *context, const ImagePlug *parent ) const = 0;
		virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const = 0;
		virtual IECore::StringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const = 0;
		virtual IECore::FloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const = 0;
		
};

} // namespace GafferImage

#endif // GAFFERSCENE_IMAGENODE_H
