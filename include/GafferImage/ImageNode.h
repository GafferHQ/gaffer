//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/Export.h"
#include "GafferImage/ImagePlug.h"

#include "Gaffer/ComputeNode.h"

namespace GafferImage
{

/// The ImageNode class is the base class for all Nodes which are capable of generating
/// or manipulating images.
class GAFFERIMAGE_API ImageNode : public Gaffer::ComputeNode
{

	public :

		ImageNode( const std::string &name=defaultName<ImageNode>() );
		~ImageNode() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::ImageNode, ImageNodeTypeId, Gaffer::ComputeNode );

		/// All ImageNodes have at least one output ImagePlug for passing on their result. More
		/// may be added by derived classes if necessary.
		ImagePlug *outPlug();
		const ImagePlug *outPlug() const;

		/// The enabled plug provides a mechanism for turning the effect of a node on and off.
		/// When disabled the node will just pass through the plug's default values.
		Gaffer::BoolPlug *enabledPlug() override;
		const Gaffer::BoolPlug *enabledPlug() const override;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		/// The enabled() and channelEnabled( channel ) methods provide a means to disable the node
		/// under particular circumstances such as when the input plugs produce no effect.
		/// enabled() is called to query the nodes state when hashing and computing the image plug.
		/// When computing or hashing the channelData plug channelEnabled( channel ) is also called
		/// to query if the particular channel is enabled or not.
		///
		/// Derived classes can overide one or both methods to return false if their plugs are in
		/// a state that makes the node produce no effect. This stops duplication of data in the
		/// cache and improves performance and memory efficiency. It is guaranteed that the hash*()
		/// methods below and compute*() methods below will never be called if enabled() is false,
		/// or channelEnabled() is false (in the case of *channelData()).
		///
		/// Any derived classes that do reimplement these methods need to call the respective method
		/// on the base class before then computing whether or not it is in fact enabled.
		virtual bool channelEnabled( const std::string &channel ) const { return true; };
		/// The default implementation of enabled returns the value of the enabled plug.
		/// \deprecated remove this once all derived classes stop using it.
		virtual bool enabled() const;

		/// Implemented to call the hash*() methods below whenever output is part of an ImagePlug.
		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		/// Hash methods for the individual children of outPlug(). A derived class must either :
		///
		///    * Implement the method to call the base class implementation and then append to the hash.
		///
		/// or
		///
		///    * Implement the method to assign directly to the hash from some input hash to signify that
		///      an input will be passed through unchanged by the corresponding compute*() method. Note
		///      that if you wish to pass through an input unconditionally, regardless of context, it is
		///      faster to use a connection as described below.
		///
		/// or :
		///
		///    * Make an input connection into the corresponding plug, so that the hash and compute methods
		///      are never called for it.
		virtual void hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		/// Implemented to call the compute*() methods below whenever output is part of an ImagePlug.
		/// Derived classes should reimplement the specific compute*() methods rather than compute() itself.
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;
		/// Compute methods for the individual children of outPlug() - these must be implemented by derived classes, or
		/// an input connection must be made to the plug, so that the method is not called.
		virtual GafferImage::Format computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual IECore::ConstCompoundDataPtr computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual bool computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual IECore::ConstIntVectorDataPtr computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;

	private :

		static size_t g_firstPlugIndex;
};

IE_CORE_DECLAREPTR( ImageNode )

} // namespace GafferImage

#endif // GAFFERSCENE_IMAGENODE_H
