//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GLWidgetBinding.h"

#include "IECore/Exception.h"
#include "IECore/MessageHandler.h"

#include "QtOpenGL/QGLWidget"

#if defined( __linux__ )
#include "GL/glx.h" // Must come after Qt!
#endif

using namespace boost::python;

namespace
{

#if defined( __linux__ )

class HostedGLContext : public QGLContext
{

	public :

		HostedGLContext( const QGLFormat &format, QPaintDevice *device )
			:	QGLContext( format, device )
		{

			GLXContext hostContext = glXGetCurrentContext();
			m_display = glXGetCurrentDisplay();

			std::vector<int> fbAttribs;
			fbAttribs.push_back( GLX_DOUBLEBUFFER );
			fbAttribs.push_back( format.doubleBuffer() ? True : False );
			fbAttribs.push_back( GLX_RENDER_TYPE );
			fbAttribs.push_back( format.rgba() ? GLX_RGBA_BIT : GLX_COLOR_INDEX_BIT );
			fbAttribs.push_back( None );

			int numFBConfigs = 0;
			GLXFBConfig *fbConfigs = glXChooseFBConfig(
				m_display,
				DefaultScreen( m_display ),
				&fbAttribs.front(),
				&numFBConfigs
			);

			if( !numFBConfigs )
			{
				throw IECore::Exception( "No suitable GLXFBConfig found" );
			}

			m_context = glXCreateNewContext(
				m_display,
				fbConfigs[0],
				GLX_RGBA_TYPE,
				hostContext,
				True
			);

		}

		~HostedGLContext() override
		{
			glXDestroyContext( m_display, m_context );
		}

		void makeCurrent() override
		{
#if QT_VERSION >= 0x050000
			QGLContext::makeCurrent();
#endif
			glXMakeCurrent( m_display, static_cast<QWidget *>( device() )->effectiveWinId(), m_context );
		}

	private :

		Display *m_display;
		GLXContext m_context;

};

#else

class HostedGLContext : public QGLContext
{

	public :

		HostedGLContext( const QGLFormat &format, QPaintDevice *device )
			:	QGLContext( format, device )
		{
			IECore::msg( IECore::Msg::Warning, "HostedGLContext", "Not implemented on this platform." );
		}

};

#endif

void setHostedContext( uint64_t glWidgetAddress, uint64_t glFormatAddress )
{
	QGLWidget *glWidget = reinterpret_cast<QGLWidget *>( glWidgetAddress );
	QGLFormat *glFormat = reinterpret_cast<QGLFormat *>( glFormatAddress );
	glWidget->setContext( new HostedGLContext( *glFormat, glWidget ) );
}

} // namespace

void GafferUIModule::bindGLWidget()
{

	def( "_glWidgetSetHostedContext", &setHostedContext );

}
