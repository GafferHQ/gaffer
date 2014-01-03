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

#include "boost/python.hpp"

#include "GafferBindings/NodeBinding.h"

#include "GafferImage/ImageProcessor.h"

#include "GafferImageUI/ImageView.h"
#include "GafferImageUIBindings/ImageViewBinding.h"

using namespace std;
using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferImage;
using namespace GafferImageUI;

class ImageViewWrapper : public NodeWrapper<ImageView>
{
	
	public :
	
		ImageViewWrapper( PyObject *self, const std::string &name )
			:	NodeWrapper<ImageView>( self, name )
		{
		}

};

IE_CORE_DECLAREPTR( ImageViewWrapper );

struct DisplayTransformCreator
{
	DisplayTransformCreator( object fn )
		:	m_fn( fn )
	{
	}
	
	ImageProcessorPtr operator()()
	{
		IECorePython::ScopedGILLock gilLock;
		ImageProcessorPtr result = extract<ImageProcessorPtr>( m_fn() );
		return result;
	}
	
	private :
	
		object m_fn;

};

static void registerDisplayTransform( const std::string &name, object creator )
{
	ImageView::registerDisplayTransform( name, DisplayTransformCreator( creator ) );
}

static boost::python::list registeredDisplayTransforms()
{
	vector<string> n;
	ImageView::registeredDisplayTransforms( n );
	boost::python::list result;
	for( vector<string>::const_iterator it = n.begin(), eIt = n.end(); it != eIt; ++it )
	{
		result.append( *it );
	}
	
	return result;
}

void GafferImageUIBindings::bindImageView()
{

	GafferBindings::NodeClass<ImageView, ImageViewWrapperPtr>()
		.def( init<const std::string &>() )
		.def( "_insertConverter", &ImageView::insertConverter )
		.def( "registerDisplayTransform", &registerDisplayTransform )
		.staticmethod( "registerDisplayTransform" )
		.def( "registeredDisplayTransforms", &registeredDisplayTransforms )
		.staticmethod( "registeredDisplayTransforms" )
	;
	
}
