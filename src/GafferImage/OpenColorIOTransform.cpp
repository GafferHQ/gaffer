//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/OpenColorIOTransform.h"

#include "Gaffer/Context.h"
#include "Gaffer/Process.h"

#include "IECore/SimpleTypedData.h"

#include "tbb/mutex.h"
#include "tbb/null_mutex.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

namespace
{

// Although the OpenColorIO library is advertised as threadsafe,
// it seems to crash regularly on OS X in getProcessor(), while
// mucking around with the locale(). we mutex the call to getProcessor()
// but still do the actual processing in parallel - this seems to
// have negligible performance impact but a nice not-crashing impact.
// On other platforms we use a null_mutex so there should be no
// performance impact at all.
#ifdef __APPLE__
using OCIOMutex = tbb::mutex;
#else
using OCIOMutex = tbb::null_mutex;
#endif

OCIOMutex g_ocioMutex;

struct ProcessorProcess : public Process
{

	public :

		ProcessorProcess( InternedString type, const OpenColorIOTransform *node )
			:	Process( type, node->outPlug() )
		{
		}

		static InternedString processorProcessType;
		static InternedString processorHashProcessType;

};

InternedString ProcessorProcess::processorProcessType( "openColorIOTransform:processor" );
InternedString ProcessorProcess::processorHashProcessType( "openColorIOTransform:processorHash" );

} // namespace

GAFFER_NODE_DEFINE_TYPE( OpenColorIOTransform );

size_t OpenColorIOTransform::g_firstPlugIndex = 0;

OpenColorIOTransform::OpenColorIOTransform( const std::string &name , bool withContextPlug )
	:	ColorProcessor( name ), m_hasContextPlug( withContextPlug )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	if( m_hasContextPlug )
	{
		addChild( new CompoundDataPlug( "context" ) );
	}
}

OpenColorIOTransform::~OpenColorIOTransform()
{
}

Gaffer::CompoundDataPlug *OpenColorIOTransform::contextPlug()
{
	if( !m_hasContextPlug )
	{
		return nullptr;
	}
	return getChild<CompoundDataPlug>( g_firstPlugIndex );
}

const Gaffer::CompoundDataPlug *OpenColorIOTransform::contextPlug() const
{
	if( !m_hasContextPlug )
	{
		return nullptr;
	}
	return getChild<CompoundDataPlug>( g_firstPlugIndex );
}

OCIO_NAMESPACE::ConstProcessorRcPtr OpenColorIOTransform::processor() const
{
	// Process is necessary to trigger substitutions for plugs
	// pulled on by `transform()` and `ocioContext()`.
	ProcessorProcess process( ProcessorProcess::processorProcessType, this );

	OCIO_NAMESPACE::ConstTransformRcPtr colorTransform = transform();
	if( !colorTransform )
	{
		return OCIO_NAMESPACE::ConstProcessorRcPtr();
	}

	OCIOMutex::scoped_lock lock( g_ocioMutex );
	OCIO_NAMESPACE::ConstConfigRcPtr config = OCIO_NAMESPACE::GetCurrentConfig();
	OCIO_NAMESPACE::ConstContextRcPtr context = ocioContext( config );
	return config->getProcessor( context, colorTransform, OCIO_NAMESPACE::TRANSFORM_DIR_FORWARD );
}

IECore::MurmurHash OpenColorIOTransform::processorHash() const
{
	// Process is necessary to trigger substitutions for plugs
	// that may be pulled on by `hashTransform()`.
	ProcessorProcess process( ProcessorProcess::processorHashProcessType, this );

	IECore::MurmurHash result;
	hashTransform( Context::current(), result );
	if( auto *p = contextPlug() )
	{
		p->hash( result );
	}
	return result;
}

bool OpenColorIOTransform::enabled() const
{
	if( !ColorProcessor::enabled() )
	{
		return false;
	}

	MurmurHash h;
	{
		ImagePlug::GlobalScope c( Context::current() );
		hashTransform( Context::current(), h );
	}
	return ( h != MurmurHash() );
}

bool OpenColorIOTransform::affectsColorData( const Gaffer::Plug *input ) const
{
	if( ColorProcessor::affectsColorData( input ) )
	{
		return true;
	}
	if( contextPlug() && contextPlug()->isAncestorOf( input ) )
	{
		return true;
	}
	return affectsTransform( input );
}

void OpenColorIOTransform::hashColorData( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ColorProcessor::hashColorData( context, h );

	ImagePlug::GlobalScope c( context );
	h.append( processorHash() );
}

OCIO_NAMESPACE::ConstContextRcPtr OpenColorIOTransform::ocioContext( OCIO_NAMESPACE::ConstConfigRcPtr config ) const
{

	OCIO_NAMESPACE::ConstContextRcPtr context = config->getCurrentContext();
	const CompoundDataPlug *p = contextPlug();
	if( !p )
	{
		return context;
	}

	if( !p->children().size() )
	{
		return context;
	}

	OCIO_NAMESPACE::ContextRcPtr mutableContext;
	std::string name;
	std::string value;

	for( NameValuePlug::Iterator it( p ); !it.done(); ++it )
	{
		IECore::DataPtr d = p->memberDataAndName( it->get(), name );
		if( d )
		{
			StringDataPtr data = runTimeCast<StringData>( d );
			if( !data )
			{
				throw( Exception(  "OpenColorIOTransform: Failed to convert context value to string." ) );
			}
			value = data->readable();
			if( !name.empty() && !value.empty() )
			{
				if( !mutableContext )
				{
					mutableContext = context->createEditableCopy();
				}
				mutableContext->setStringVar(name.c_str(), value.c_str() );
			}
		}
	}

	if( mutableContext )
	{
		context = mutableContext;
	}
	return context;
}

void OpenColorIOTransform::processColorData( const Gaffer::Context *context, IECore::FloatVectorData *r, IECore::FloatVectorData *g, IECore::FloatVectorData *b ) const
{
	OCIO_NAMESPACE::ConstProcessorRcPtr processor;
	{
		ImagePlug::GlobalScope c( context );
		processor = this->processor();
	}

	if( !processor )
	{
		return;
	}

	OCIO_NAMESPACE::PlanarImageDesc image(
		r->baseWritable(),
		g->baseWritable(),
		b->baseWritable(),
		nullptr, // alpha
		r->readable().size(), // Treat all pixels as a single line, since geometry doesn't affect OCIO
		1 // height
	);

	OCIO_NAMESPACE::ConstCPUProcessorRcPtr cpuProcessor = processor->getDefaultCPUProcessor();
	cpuProcessor->apply( image );
}
