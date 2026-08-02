//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Lucien Fostier. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "GafferOFX/GLContextManager.h"

#if defined(__APPLE__) || defined(_WIN32)
	// The macOS (CGL) and Windows (WGL) backends are not implemented yet.
	// The Linux path below is the only backend; the other platforms will
	// mirror it using the CGL*/WGL* APIs and their own GL function lookup
	// (see include/GafferOFX/GLContextManager.h for the design).
#error "GLContextManager: only the Linux (EGL) backend is implemented"
#endif

#include <GL/gl.h>
#include <GL/glext.h>

#include <EGL/egl.h>
#include <EGL/eglext.h>

// Not present in older EGL headers.
#ifndef EGL_CONTEXT_OPENGL_PROFILE_MASK
#define EGL_CONTEXT_OPENGL_PROFILE_MASK 0x30FD
#endif
#ifndef EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT
#define EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT 0x00000002
#endif

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>

using namespace GafferOFX;

GLContextManager& GLContextManager::instance()
{
	static GLContextManager mgr;
	return mgr;
}

GLContextManager::GLContextManager()
{
	m_eglDisplay = nullptr;
	m_eglContext = nullptr;
	m_eglSurface = nullptr;
	m_backendName = "none";
	m_contextIsSoftware = false;

	// Honor the LIBGL_ALWAYS_SOFTWARE=1 convention: only try software
	// devices and skip the default-display fallback, so the GL path can
	// be exercised without a hardware GPU.
	const char *softwareEnv = getenv( "LIBGL_ALWAYS_SOFTWARE" );
	createContext( softwareEnv && softwareEnv[0] == '1', false );

	// Auto selection prefers hardware and only falls back to the software
	// device when no GPU initialises, so the startup device class is the
	// machine's capability signal (a forced-software run reports no
	// hardware).
	m_initialContextIsSoftware = m_contextIsSoftware;
}

bool GLContextManager::hardwareAvailable() const
{
	return !m_initialContextIsSoftware;
}

bool GLContextManager::createContext( bool softwareOnly, bool hardwareOnly )
{
	// ---- EGL context creation with device enumeration ----
	//
	// Goal: a single shared offscreen GL context that OFX plugins render
	// into.  EGL is used because it can create a GPU context without any
	// window system connection (GLX needs an X display, and this host
	// commonly runs headless or under RDP where no NVIDIA GLX driver is
	// available).
	//
	// The context is created from a concrete EGL device rather than
	// EGL_DEFAULT_DISPLAY because the default display resolves to whatever
	// the platform registers first — often the software device.  We need
	// to pick a hardware GPU when one exists, and we need to know which
	// class of device we got (hardware vs software) so the render-mode
	// machinery can rebuild onto a different class on demand.
	//
	// Selection procedure:
	//   1. Enumerate all EGL devices (EGL_EXT_device_enumeration) and try
	//      each one via EGL_EXT_platform_device.  Devices are processed in
	//      two passes: pass 0 = hardware only, pass 1 = software only, so
	//      a working GPU always wins over the software device.  The
	//      device class is detected from the device extension string
	//      (EGL_MESA_device_software marks software devices).
	//   2. For each candidate device, in order:
	//        eglGetPlatformDisplayEXT → eglInitialize → eglChooseConfig
	//        (RGBA8 + 24-bit depth + 8-bit stencil, pbuffer-renderable)
	//        → eglBindAPI(EGL_OPENGL_API) → eglCreateContext with a
	//        compatibility profile → create a 1x1 pbuffer surface →
	//        eglMakeCurrent → probe the renderer string.
	//      The 1x1 pbuffer gives FBO 0 a valid backing store, which
	//      matters because some plugins render to the default framebuffer
	//      instead of an FBO we hand them.
	//      The compatibility profile is requested because many OFX
	//      plugins are GL 2.1-era code that relies on fixed-function GL
	//      and glGetString(GL_EXTENSIONS), which are absent from core
	//      profiles.
	//   3. The renderer-string probe is the acceptance test: a device
	//      whose context fails to make current, or that reports no
	//      renderer, is torn down and the next candidate is tried.
	//   4. If no enumerated device produced a working context, fall back
	//      to the default EGL display (whatever is registered as primary).
	//      This fallback is skipped for an explicit hardware-only request,
	//      since the default display could be software.
	//
	// On success the context is unbound before returning, so no thread
	// owns it at rest; makeCurrent() binds it on the thread that renders.
	// The softwareOnly/hardwareOnly flags restrict selection to a single
	// device class (used when the render mode demands a rebuild) and
	// disable the default-display fallback.

	// Fetch the EGL extension entry points via eglGetProcAddress — they
	// are not exported by the linked libEGL (GLVND), only by the vendor
	// driver the loader has chosen.
	PFNEGLQUERYDEVICESEXTPROC queryDevices = (PFNEGLQUERYDEVICESEXTPROC)
		eglGetProcAddress( "eglQueryDevicesEXT" );
	PFNEGLGETPLATFORMDISPLAYEXTPROC getPlatformDisplay = (PFNEGLGETPLATFORMDISPLAYEXTPROC)
		eglGetProcAddress( "eglGetPlatformDisplayEXT" );
	PFNEGLQUERYDEVICESTRINGEXTPROC queryDeviceString = (PFNEGLQUERYDEVICESTRINGEXTPROC)
		eglGetProcAddress( "eglQueryDeviceStringEXT" );

	// The framebuffer config is shared by every device attempt: 8-bit
	// RGBA + 24-bit depth + 8-bit stencil, and must be renderable to a
	// pbuffer (offscreen) surface.
	const EGLint configAttribs[] = {
		EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
		EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT,
		EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8,
		EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8,
		EGL_DEPTH_SIZE, 24, EGL_STENCIL_SIZE, 8,
		EGL_NONE
	};
	// 1x1 pbuffer: just enough backing store to make FBO 0 valid — some
	// plugins render to the default framebuffer rather than a host FBO.
	// EGL_NONE terminates the attribute list, as in configAttribs.
	const EGLint pbAttribs[] = { EGL_WIDTH, 1, EGL_HEIGHT, 1, EGL_NONE };

	// Device enumeration is optional (some platforms lack the extension);
	// without it we fall through to the default-display path below.
	if( queryDevices && getPlatformDisplay )
	{
		const EGLint maxDevices = 16;
		EGLDeviceEXT devices[maxDevices];
		EGLint numDevices = 0;
		if( queryDevices( maxDevices, devices, &numDevices ) && numDevices > 0 )
		{
			// Two passes: pass 0 = hardware only, pass 1 = software only.
			// Loop conditions also check m_eglContext so the first
			// successful device short-circuits every remaining attempt.
			const int firstPass = softwareOnly ? 1 : 0;
			const int lastPass = hardwareOnly ? 0 : 1;
			for( int pass = firstPass; pass <= lastPass && !m_eglContext; ++pass )
			{
				for( EGLint i = 0; i < numDevices && !m_eglContext; ++i )
				{
					// Classify the device from its extension string so
					// each pass only tries devices of its own class.
					if( queryDeviceString )
					{
						const char *exts = queryDeviceString( devices[i], EGL_EXTENSIONS );
						bool isSoftware = exts && strstr( exts, "EGL_MESA_device_software" );
						if( ( pass == 0 && isSoftware ) || ( pass == 1 && !isSoftware ) )
						{
							continue;
						}
					}
					else if( pass == 1 )
					{
						continue;   // can't identify software — skip pass 1
					}

					// Create a display handle bound to this specific
					// device, then initialize it.  Every failure below
					// tears down whatever was created and tries the next
					// device — a broken vendor driver must not abort the
					// whole selection.
					EGLDisplay dpy = getPlatformDisplay(
						EGL_PLATFORM_DEVICE_EXT, devices[i], nullptr
					);
					if( dpy == EGL_NO_DISPLAY )
					{
						continue;
					}

					EGLint major, minor;
					if( !eglInitialize( dpy, &major, &minor ) )
					{
						eglTerminate( dpy );
						continue;
					}

					EGLConfig config;
					EGLint numConfigs;
					if( !eglChooseConfig( dpy, configAttribs, &config, 1, &numConfigs ) ||
					    numConfigs == 0 )
					{
						eglTerminate( dpy );
						continue;
					}

					// Create the GL context on this display.
					eglBindAPI( EGL_OPENGL_API );

					// Request an OpenGL compatibility profile so legacy GL
					// queries (glGetString(GL_EXTENSIONS), etc.) and fixed-
					// function constructs work.  OFX plugins from the GL 2.1
					// era depend on this.
					const EGLint ctxAttribs[] = {
						EGL_CONTEXT_OPENGL_PROFILE_MASK,
						EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT,
						EGL_NONE
					};
					EGLContext ctx = eglCreateContext( dpy, config, EGL_NO_CONTEXT, ctxAttribs );
					if( ctx == EGL_NO_CONTEXT )
					{
						eglTerminate( dpy );
						continue;
					}
					// The context needs a surface to be made current
					// against; the pbuffer supplies it offscreen.
					EGLSurface surf = eglCreatePbufferSurface( dpy, config, pbAttribs );
					if( surf == EGL_NO_SURFACE )
					{
						eglDestroyContext( dpy, ctx );
						eglTerminate( dpy );
						continue;
					}

					// Make current, then probe the renderer string — the
					// acceptance test for this device.  A context that
					// cannot be bound, or that reports no renderer, is
					// torn down and the next device tried.
					if( eglMakeCurrent( dpy, surf, surf, ctx ) )
					{
						auto getStringFn = (const GLubyte* (*)(GLenum))eglGetProcAddress( "glGetString" );
						const char *renderer = getStringFn ? (const char*)getStringFn( GL_RENDERER ) : nullptr;
						if( renderer && renderer[0] )
						{
							m_eglDisplay = (void*)dpy;
							m_eglContext = (void*)ctx;
							m_eglSurface = (void*)surf;
							m_rendererString = renderer;
							m_backendName = "EGL";

							// Device accepted.  Load the GL entry points
							// we need (FBO functions) and keep the
							// context only if they resolve.
							if( initGLEW() )
							{
								// Probe succeeded.  Unbind properly per
								// EGL §3.7.3: both surfaces must be
								// EGL_NO_SURFACE when ctx is EGL_NO_CONTEXT.
								eglMakeCurrent( dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT );
								break;	// device accepted — stop searching
							}
							else
							{
								// GL unusable after all — discard this
								// device's objects and continue.
								eglMakeCurrent( dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT );
								eglDestroySurface( dpy, surf );
								eglDestroyContext( dpy, ctx );
								eglTerminate( dpy );
								m_eglDisplay = nullptr;
								m_eglContext = nullptr;
								m_eglSurface = nullptr;
							}
							break;
						}
						// Renderer probe failed — unbind and fall through
						// to the cleanup below.
						eglMakeCurrent( dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT );
					}

					eglDestroySurface( dpy, surf );
					eglDestroyContext( dpy, ctx );
					eglTerminate( dpy );
				}
			}
		}
	}

	// Fallback: if device enumeration didn't produce a working context,
	// try the default EGL display (whatever is registered as the primary
	// display).  Skipped for an explicit GPU request — the default display
	// could be software.
	if( !m_eglContext && !hardwareOnly )
	{
		EGLDisplay eglDpy = eglGetDisplay( EGL_DEFAULT_DISPLAY );
		if( eglDpy == EGL_NO_DISPLAY )
		{
			eglDpy = eglGetDisplay( nullptr );
		}

		if( eglDpy != EGL_NO_DISPLAY )
		{
			EGLint major, minor;
			if( eglInitialize( eglDpy, &major, &minor ) )
			{
				EGLConfig eglConfig;
				EGLint numConfigs;
				if( eglChooseConfig( eglDpy, configAttribs, &eglConfig, 1, &numConfigs ) &&
				    numConfigs > 0 )
				{
					eglBindAPI( EGL_OPENGL_API );
					// Same compatibility-profile context as the device
					// path — legacy OFX plugin GL needs it.
					const EGLint fallbackCtxAttribs[] = {
						EGL_CONTEXT_OPENGL_PROFILE_MASK,
						EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT,
						EGL_NONE
					};
					EGLContext eglCtx = eglCreateContext( eglDpy, eglConfig, EGL_NO_CONTEXT, fallbackCtxAttribs );
					if( eglCtx != EGL_NO_CONTEXT )
					{
						EGLSurface surf = eglCreatePbufferSurface( eglDpy, eglConfig, pbAttribs );
						if( surf != EGL_NO_SURFACE )
						{
							// Acceptance probe, same as the device path:
							// the context counts only if it binds and
							// reports a renderer string.
							if( eglMakeCurrent( eglDpy, surf, surf, eglCtx ) )
							{
								auto getStringFn = (const GLubyte* (*)(GLenum))eglGetProcAddress( "glGetString" );
								const char *renderer = getStringFn ? (const char*)getStringFn( GL_RENDERER ) : nullptr;
								if( renderer && renderer[0] )
								{
									m_eglDisplay = (void*)eglDpy;
									m_eglContext = (void*)eglCtx;
									m_eglSurface = (void*)surf;
									m_rendererString = renderer;
									m_backendName = "EGL";
								}
								// Unbind so no thread owns it at rest.
								eglMakeCurrent( eglDpy, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT );
							}
							if( !m_eglContext )
							{
								eglDestroySurface( eglDpy, surf );
							}
						}
						if( !m_eglContext )
						{
							eglDestroyContext( eglDpy, eglCtx );
						}
					}
				}
			}
		}
	}

	if( m_eglContext )
	{
		m_contextIsSoftware =
			strstr( m_rendererString.c_str(), "llvmpipe" ) ||
			strstr( m_rendererString.c_str(), "soft" );
	}

	return m_eglContext != nullptr;
}

void GLContextManager::teardownContext()
{
	if( m_eglDisplay )
	{
		// Best-effort unbind on the calling thread; if another thread
		// owns the context this fails silently and we destroy the
		// objects anyway (the owning thread must not touch it after).
		eglMakeCurrent( (EGLDisplay)m_eglDisplay, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT );
		if( m_eglSurface )
		{
			eglDestroySurface( (EGLDisplay)m_eglDisplay, (EGLSurface)m_eglSurface );
		}
		eglDestroyContext( (EGLDisplay)m_eglDisplay, (EGLContext)m_eglContext );
		eglTerminate( (EGLDisplay)m_eglDisplay );
	}
	m_eglDisplay = nullptr;
	m_eglContext = nullptr;
	m_eglSurface = nullptr;
	m_contextIsSoftware = false;

	// GL objects created on the destroyed context are dead; invalidate
	// everything that caches their IDs so the next render recreates them.
	m_outputFBO = 0;
	m_outputTex = 0;
	m_outputTexW = 0;
	m_outputTexH = 0;
	m_textures.clear();
	++m_contextGeneration;
}

GLContextManager::~GLContextManager()
{
	// Skip GL cleanup if not on the owning thread — the context isn't
	// current here, so glDeleteTextures / glDeleteFramebuffers would be
	// silent no-ops (leaked GPU memory).  At process exit the driver
	// reclaims everything anyway; at module unload the worker has already
	// been joined.
	if( m_ownerThread != std::thread::id() &&
	    m_ownerThread != std::this_thread::get_id() )
	{
		// Let the worker's textures leak — driver cleanup at exit.
		m_textures.clear();
		m_outputFBO = 0;
		m_outputTex = 0;
	}
	else
	{
		cleanupTextures();
	}

	if( m_eglContext )
	{
		teardownContext();
	}
}

bool GLContextManager::initGLEW()
{
	// We do NOT call glewInit().  Under RDP (or any X server without NVIDIA
	// GLX driver), Qt's GLX init loads libGLX_mesa.so.0 before our code runs.
	// That library's GL* exports capture global-scope symbol bindings for all
	// subsequently-loaded modules.  GLEW resolves through those captured
	// bindings, and its stub sees no current context under our EGL setup.
	// Loading via eglGetProcAddress routes directly through NVIDIA's EGL
	// driver, bypassing the global-scope GLX capture entirely.

	auto getStringFn = (const GLubyte* (*)(GLenum))eglGetProcAddress( "glGetString" );
	const char *renderer = getStringFn ? (const char*)getStringFn( GL_RENDERER ) : nullptr;
	const char *versionStr = getStringFn ? (const char*)getStringFn( GL_VERSION ) : nullptr;
	if( !renderer )
	{
		return false;
	}

	// Re-fetch the FBO entry points whenever the driver dispatch changes.
	// The context can be rebuilt onto a different device (e.g. GPU →
	// software device), where the per-vendor function pointers differ.
	static std::string s_dispatchRenderer;
	if( s_dispatchRenderer != m_rendererString )
	{
		glGenFramebuffersF = nullptr;
		glBindFramebufferF = nullptr;
		glFramebufferTexture2DF = nullptr;
		glCheckFramebufferStatusF = nullptr;
		glDeleteFramebuffersF = nullptr;
		s_dispatchRenderer = m_rendererString;
	}

	bool isHardware = !strstr( renderer, "llvmpipe" ) && !strstr( renderer, "soft" );

	if( isHardware )
	{
		int major = 0, minor = 0;
		if( versionStr )
		{
			sscanf( versionStr, "%d.%d", &major, &minor );
		}
		if( major < 3 || ( major == 3 && minor < 2 ) )
		{
			return false;
		}
	}

	// Load the FBO entry points via eglGetProcAddress (not GLEW), so the
	// same calls work on every backend.  OFX plugins that bind FBO 0 (the
	// pbuffer-backed default framebuffer) during rendering rely on these.
	if( !glGenFramebuffersF )
	{
		glGenFramebuffersF = (unsigned int (*)( unsigned int, unsigned int* ))
			eglGetProcAddress( "glGenFramebuffers" );
	}
	if( !glBindFramebufferF )
	{
		glBindFramebufferF = (void (*)( unsigned int, unsigned int ))
			eglGetProcAddress( "glBindFramebuffer" );
	}
	if( !glFramebufferTexture2DF )
	{
		glFramebufferTexture2DF = (void (*)( unsigned int, unsigned int, unsigned int, unsigned int, int ))
			eglGetProcAddress( "glFramebufferTexture2D" );
	}
	if( !glCheckFramebufferStatusF )
	{
		glCheckFramebufferStatusF = (unsigned int (*)( unsigned int ))
			eglGetProcAddress( "glCheckFramebufferStatus" );
	}
	if( !glDeleteFramebuffersF )
	{
		glDeleteFramebuffersF = (void (*)( unsigned int, const unsigned int* ))
			eglGetProcAddress( "glDeleteFramebuffers" );
	}

	if( !glGenFramebuffersF || !glBindFramebufferF || !glFramebufferTexture2DF ||
	    !glCheckFramebufferStatusF || !glDeleteFramebuffersF )
	{
		return false;
	}

	return true;
}

// Static GL function pointer definitions
unsigned int (*GLContextManager::glGenFramebuffersF)( unsigned int, unsigned int* ) = nullptr;
void (*GLContextManager::glBindFramebufferF)( unsigned int, unsigned int ) = nullptr;
void (*GLContextManager::glFramebufferTexture2DF)( unsigned int, unsigned int, unsigned int, unsigned int, int ) = nullptr;
unsigned int (*GLContextManager::glCheckFramebufferStatusF)( unsigned int ) = nullptr;
void (*GLContextManager::glDeleteFramebuffersF)( unsigned int, const unsigned int* ) = nullptr;

bool GLContextManager::makeCurrent()
{
	if( !m_eglContext )
	{
		m_backendName = "none";
		return false;
	}

	// Rebuild the context if the requested device class differs from the
	// active one.  Unbind-on-this-thread only succeeds if we own it; if
	// another thread currently holds the context we defer the rebuild to
	// that thread's next makeCurrent.
	const int requestedMode = renderMode();
	const char *softwareEnv = getenv( "LIBGL_ALWAYS_SOFTWARE" );
	const bool forceSoftware = softwareEnv && softwareEnv[0] == '1';

	// CPU render through the software EGL device.
	if( requestedMode == (int)RenderMode::CPU )
	{
		if( !m_contextIsSoftware )
		{
			if( !eglMakeCurrent( (EGLDisplay)m_eglDisplay, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT ) )
			{
				return false;
			}
			teardownContext();
			if( !createContext( true, false ) )
			{
				m_backendName = "none";
				return false;
			}
		}
	}
	else if( requestedMode == (int)RenderMode::GPU )
	{
		if( m_contextIsSoftware )
		{
			if( !eglMakeCurrent( (EGLDisplay)m_eglDisplay, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT ) )
			{
				return false;
			}
			teardownContext();
			if( !createContext( false, true ) )
			{
				m_backendName = "none";
				return false;
			}
		}
	}
	else
	{
		// Auto: prefer the GPU, fall back to the software EGL device
		// when no hardware device initialises.
		if( m_contextIsSoftware && !forceSoftware )
		{
			if( !eglMakeCurrent( (EGLDisplay)m_eglDisplay, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT ) )
			{
				return false;
			}
			teardownContext();
			if( !createContext( false, true ) )
			{
				// GPU unavailable — fall back to the software device.
				if( !createContext( true, false ) )
				{
					m_backendName = "none";
					return false;
				}
			}
		}
	}

	// Always call eglMakeCurrent.  The constructor unbinds before returning,
	// so no thread owns the context at rest.  Rebinding the same context on
	// the same thread is a valid no-op per EGL spec (no error).
	EGLDisplay dpy = (EGLDisplay)m_eglDisplay;
	EGLContext ctx = (EGLContext)m_eglContext;
	EGLSurface surf = m_eglSurface ? (EGLSurface)m_eglSurface : EGL_NO_SURFACE;

	EGLBoolean ok = eglMakeCurrent( dpy, surf, surf, ctx );
	if( !ok && eglGetError() == 0x3002 )   // EGL_BAD_ACCESS
	{
		// The context is current on another thread (the render worker),
		// so this thread can't bind it.  Benign — the caller should skip
		// GL work.  Keep the previous backend name for diagnostics.
		return false;
	}
	else if( ok && initGLEW() )
	{
		m_ownerThread = std::this_thread::get_id();
		m_backendName = "EGL";
		return true;
	}

	m_backendName = "none";
	return false;
}

void GLContextManager::release()
{
	// Worker-owned context: we never unbind.  The context stays bound
	// on the worker thread persistently.
}

void GLContextManager::registerTexture( unsigned int id )
{
	m_textures.push_back( id );
}

void GLContextManager::cleanupTextures()
{
	if( !m_textures.empty() )
	{
		makeCurrent();
		glDeleteTextures( (GLsizei)m_textures.size(), (const GLuint*)m_textures.data() );
		m_textures.clear();
	}

	if( m_outputFBO || m_outputTex )
	{
		makeCurrent();
		if( m_outputFBO && glDeleteFramebuffersF )
		{
			glDeleteFramebuffersF( 1, &m_outputFBO );
		}
		if( m_outputTex )
		{
			glDeleteTextures( 1, &m_outputTex );
		}
		m_outputFBO = 0;
		m_outputTex = 0;
		m_outputTexW = 0;
		m_outputTexH = 0;
	}
}

void GLContextManager::setOutputFBO( unsigned int fbo, unsigned int tex, int width, int height )
{
	// Clean up previous FBO/texture if different
	if( m_outputFBO && m_outputFBO != fbo )
	{
		GLuint oldFbo = m_outputFBO;
		GLuint oldTex = m_outputTex;
		m_outputFBO = 0;
		m_outputTex = 0;
		makeCurrent();
		if( glDeleteFramebuffersF )
		{
			glDeleteFramebuffersF( 1, &oldFbo );
		}
		glDeleteTextures( 1, &oldTex );
	}
	m_outputFBO = fbo;
	m_outputTex = tex;
	m_outputTexW = width;
	m_outputTexH = height;
}

const char* GLContextManager::backendName() const
{
	return m_backendName;
}
