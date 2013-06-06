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

#ifndef GAFFERIMAGE_FILTERPROCESSOR_H
#define GAFFERIMAGE_FILTERPROCESSOR_H

#include "GafferImage/ImageProcessor.h"
#include "Gaffer/InputGenerator.h"

namespace GafferImage
{

/// The FilterProcessor provides a useful base class for nodes that require multiple inputs in order to process and output.
/// It allows derived classes to provide minimum and maximum number of inputs to it's constructor. It creates a minimum number
/// and will manage an optional number of inputs (if minimumInputs < maximumInputs).
/// By default this node will:
/// Be disabled if all inputs aren't connected.
/// Only hash connected inputs (if it is enabled).
/// Expand the data window to by merging all of the connect input's data windows.
/// Use the first display window encountered on a connected input.
class FilterProcessor : public ImageProcessor
{

	public :

		typedef std::vector<Gaffer::InputGenerator<GafferImage::ImagePlug>::PlugClassPtr> ImagePlugList;

		FilterProcessor( const std::string &name=defaultName<FilterProcessor>(), int minimumInputs = 1, int maximumInputs = 1 );
		virtual ~FilterProcessor();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::FilterProcessor, FilterProcessorTypeId, ImageProcessor );

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;
		
		/// Useful accessors for getting an input image plug of a certain index.	
		const ImagePlug *inPlug( int index ) const;
		ImagePlug *inPlug( int index );
		using ImageProcessor::inPlug;

	protected :
	
		/// This implementation checks that all of the inputs are connected and if not, returns false.
		/// This method needs to be overidden if a derived node can operate on any number of connected plugs
		/// and doesn't neccessarily need a minimum number to be connected.
		virtual bool enabled() const;

		/// Reimplemented to hash the input plugs. We only hash those that are connected so that nodes which don't require a minimum number to
		/// be connected such as the "Merge" node only have to overide enabled() (which requires ALL inputs to be connected by default).
		/// This therefore caters for both nodes which require all inputs to be connected and nodes that do not (providing they overload enabled()).
		virtual void hashFormatPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashDataWindowPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelNamesPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelDataPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		
		/// Sets the output display window to the first connected input found.
		virtual GafferImage::Format computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const;

		/// Sets the data window to the union of all of the data windows.
		virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;
		
		/// Creates a union of all of the connected inputs channelNames.
		virtual IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const;
	
		/// A helper class that manages our ImagePlug inputs.
		Gaffer::InputGenerator<ImagePlug> m_inputs;

	private :
		
		/// A convenience method to return an index for a channel that can be used to address Color4f plugs.
		inline int channelIndex( const std::string &channelName ) const { return channelName == "R" ? 0 : channelName == "G" ? 1 : channelName == "B" ? 2 : 3; };

};

} // namespace GafferImage

#endif // GAFFERIMAGE_FILTERPROCESSOR_H
