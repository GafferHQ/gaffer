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
//  NONINFRINGEMENT) OR OTHERWISE ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////
#include <GL/gl.h>

#include <iostream>
#include <cmath>

#include "GafferOFX/ClipInstance.h"
#include "GafferOFX/Host.h"
#include "GafferOFX/EffectImageInstance.h"
#include "GafferOFX/GLContextManager.h"
#include "GafferOFX/OFXImageNode.h"

#include "Gaffer/Context.h"

#include "GafferImage/ImagePlug.h"

using namespace GafferOFX;

namespace
{
  const double    kPalPixelAspect = 1.0;
  const int       kPalSizeXPixels = 720;
  const int       kPalSizeYPixels = 576;
  const OfxRectI  kPalRegionPixels = {0, 0, kPalSizeXPixels, kPalSizeYPixels};
}

GafferOFX::Image::Image( ClipInstance &clip, OfxTime time, int view, const OfxRectI *bounds )
	: OFX::Host::ImageEffect::Image( clip )
	, m_data(nullptr)
{
	int width = kPalSizeXPixels;
	int height = kPalSizeYPixels;

	if( bounds )
	{
		width = bounds->x2 - bounds->x1;
		height = bounds->y2 - bounds->y1;
	}

	// Components must describe the actual buffer layout the plugin reads.
	// Mask clips negotiate Alpha (their only supported component), so their
	// images are single-channel; all other clips get RGBA-interleaved data.
	// A mismatch here (e.g. reporting Alpha over an RGBA buffer) makes the
	// plugin compute pixelBytes=4 against a rowBytes=width*16 stride and
	// read every 4th float — quarter-resolution garbage.
	const std::string &clipComps = clip.getComponents();
	if( clipComps == kOfxImageComponentAlpha )
	{
		m_components = 1;
	}
	else
	{
		m_components = 4;
	}

	m_data.reset( new float[width * height * m_components]() );

	OfxRectI imageBounds;
	if( bounds )
	{
		imageBounds = *bounds;
	}
	else
	{
		imageBounds.x1 = 0; imageBounds.y1 = 0;
		imageBounds.x2 = width; imageBounds.y2 = height;
	}

	setDoubleProperty(kOfxImageEffectPropRenderScale, 1.0, 0);
	setDoubleProperty(kOfxImageEffectPropRenderScale, 1.0, 1);

	setPointerProperty(kOfxImagePropData, m_data.get());

	setIntProperty(kOfxImagePropBounds, imageBounds.x1, 0);
	setIntProperty(kOfxImagePropBounds, imageBounds.y1, 1);
	setIntProperty(kOfxImagePropBounds, imageBounds.x2, 2);
	setIntProperty(kOfxImagePropBounds, imageBounds.y2, 3);

	setIntProperty(kOfxImagePropRegionOfDefinition, imageBounds.x1, 0);
	setIntProperty(kOfxImagePropRegionOfDefinition, imageBounds.y1, 1);
	setIntProperty(kOfxImagePropRegionOfDefinition, imageBounds.x2, 2);
	setIntProperty(kOfxImagePropRegionOfDefinition, imageBounds.y2, 3);

	setStringProperty(kOfxImageEffectPropPixelDepth, kOfxBitDepthFloat);
	setStringProperty(
		kOfxImageEffectPropComponents,
		m_components == 1 ? kOfxImageComponentAlpha : kOfxImageComponentRGBA
	);

	setIntProperty(kOfxImagePropRowBytes, width * m_components * (int)sizeof(float));

	setStringProperty(kOfxImagePropField, kOfxImageFieldNone);
}

OfxRGBAColourF* Image::pixel( int x, int y ) const
{
	OfxRectI bounds = getBounds();

	if ((x >= bounds.x1) && ( x< bounds.x2) && ( y >= bounds.y1) && ( y < bounds.y2) )
	{
		int rowBytes = getIntProperty(kOfxImagePropRowBytes);
		float* data = m_data.get();
		int offset = (y - bounds.y1) * (rowBytes / (int)sizeof(float)) + (x - bounds.x1) * m_components;
		return reinterpret_cast<OfxRGBAColourF*>( &data[offset] );
	}

	return 0;
}

Image::~Image()
{
}

GafferOFX::ClipInstance::ClipInstance(
  GafferOFX::EffectImageInstance* effect,
  OFX::Host::ImageEffect::ClipDescriptor* desc )
   : OFX::Host::ImageEffect::ClipInstance( effect, *desc ), m_effect( effect ), m_name( desc->getName() )
{
}

GafferOFX::ClipInstance::~ClipInstance()
{
	if( m_inputTexture )
	{
		GLContextManager& mgr = GLContextManager::instance();
		if( mgr.makeCurrent() )
		{
			GLuint tex = m_inputTexture;
			glDeleteTextures( 1, &tex );
		}
	}
}

Image* ClipInstance::getOutputImage()
{
	auto *inv = EffectImageInstance::currentInvocation();
	return inv ? static_cast<Image*>( inv->outputImage ) : nullptr;
}

const std::string &ClipInstance::getUnmappedBitDepth() const
{
	static const std::string v( kOfxBitDepthFloat );
	return v;
}

const std::string &ClipInstance::getUnmappedComponents() const
{
	static const std::string v( kOfxImageComponentRGBA );
	return v;
}

const std::string &ClipInstance::getPremult() const
{
	static const std::string v( kOfxImagePreMultiplied );
	return v;
}

double ClipInstance::getAspectRatio() const
{
	return m_effect->getProjectPixelAspectRatio();
}

double ClipInstance::getFrameRate() const
{
	if( auto ctx = Gaffer::Context::current() )
	{
		return ctx->getFramesPerSecond();
	}
	return 24.0;
}

void ClipInstance::getFrameRange(double &startFrame, double &endFrame) const
{
	startFrame = 1;
	endFrame = 100;
	if( auto sn = m_effect->scriptNode() )
	{
		startFrame = sn->frameStartPlug()->getValue();
		endFrame = sn->frameEndPlug()->getValue();
	}
}

const std::string &ClipInstance::getFieldOrder() const
{
	static const std::string v( kOfxImageFieldNone );
	return v;
}

bool ClipInstance::getConnected() const
{
	if( m_name == "Output" )
	{
		return true;
	}

	const Gaffer::Node *node = m_effect->node();
	if( !node )
	{
		return false;
	}

	const GafferImage::ImagePlug *plug = nullptr;
	if( m_name == "Source" )
	{
		plug = node->getChild<GafferImage::ImagePlug>( "in" );
	}
	else if( !m_plugName.empty() )
	{
		plug = node->getChild<GafferImage::ImagePlug>( m_plugName );
	}
	return plug && plug->getInput() != nullptr;
}

double ClipInstance::getUnmappedFrameRate() const
{
	return getFrameRate();
}

void ClipInstance::getUnmappedFrameRange(double &unmappedStartFrame, double &unmappedEndFrame) const
{
	getFrameRange( unmappedStartFrame, unmappedEndFrame );
}

bool ClipInstance::getContinuousSamples() const
{
	return false;
}

OfxRectD ClipInstance::getRegionOfDefinition(OfxTime time) const
{
	if( m_name == "Output" )
	{
		double projectWidth = kPalSizeXPixels;
		double projectHeight = kPalSizeYPixels;
		auto* effect = m_effect;
		if( effect )
		{
			effect->getProjectSize( projectWidth, projectHeight );
		}
		OfxRectD v;
		v.x1 = v.y1 = 0;
		v.x2 = projectWidth;
		v.y2 = projectHeight;
		return v;
	}

	// Input clips: report the mapped plug's data window at the given time.
	const Gaffer::Node *node = m_effect ? m_effect->node() : nullptr;
	const GafferImage::ImagePlug *plug = nullptr;
	if( node )
	{
		if( m_name == "Source" )
		{
			plug = node->getChild<GafferImage::ImagePlug>( "in" );
		}
		else if( !m_plugName.empty() )
		{
			plug = node->getChild<GafferImage::ImagePlug>( m_plugName );
		}
	}

	if( plug && plug->getInput() )
	{
		// Scope the invocation context (if any) to read the data window.
		// Override frame for temporal accesses so getRegionOfDefinition
		// reports the correct data window at clip time, not render time.
		auto *inv = EffectImageInstance::currentInvocation();
		if( inv && inv->context )
		{
			if( time == inv->context->getFrame() )
			{
				Gaffer::Context::Scope scope( inv->context.get() );
				Imath::Box2i dw = plug->dataWindowPlug()->getValue();
				OfxRectD v;
				v.x1 = dw.min.x;
				v.y1 = dw.min.y;
				v.x2 = dw.max.x;
				v.y2 = dw.max.y;
				return v;
			}
			else
			{
				Gaffer::Context::EditableScope edit( inv->context.get() );
				edit.setFrame( time );
				Imath::Box2i dw = plug->dataWindowPlug()->getValue();
				OfxRectD v;
				v.x1 = dw.min.x;
				v.y1 = dw.min.y;
				v.x2 = dw.max.x;
				v.y2 = dw.max.y;
				return v;
			}
		}
		else
		{
			Imath::Box2i dw = plug->dataWindowPlug()->getValue();
			OfxRectD v;
			v.x1 = dw.min.x;
			v.y1 = dw.min.y;
			v.x2 = dw.max.x;
			v.y2 = dw.max.y;
			return v;
		}
	}

	// Fallback: project size
	double projectWidth = kPalSizeXPixels;
	double projectHeight = kPalSizeYPixels;
	if( m_effect )
	{
		m_effect->getProjectSize( projectWidth, projectHeight );
	}
	OfxRectD v;
	v.x1 = v.y1 = 0;
	v.x2 = projectWidth;
	v.y2 = projectHeight;
	return v;
}

// Resolve the fetch region for getImage.
// Returns the clipped integer region; true if valid.
static bool resolveFetchRegion(
	const ClipInstance &clip, OfxTime time, const OfxRectD *optionalBounds,
	OfxRectI &outRegion
)
{
	OfxRectD rod = clip.getRegionOfDefinition( time );
	OfxRectD desired;

	if( optionalBounds )
	{
		desired = *optionalBounds;
	}
	else if( auto *inv = EffectImageInstance::currentInvocation() )
	{
		auto it = inv->clipRoIs.find( clip.getName() );
		if( it != inv->clipRoIs.end() )
		{
			desired = it->second;
		}
		else
		{
			desired = rod;
		}
	}
	else
	{
		desired = rod;
	}

	// Clamp to RoD with floor/ceil to avoid losing a pixel at negative coords
	OfxRectI region;
	region.x1 = (int)std::floor( std::max( desired.x1, rod.x1 ) );
	region.y1 = (int)std::floor( std::max( desired.y1, rod.y1 ) );
	region.x2 = (int)std::ceil(  std::min( desired.x2, rod.x2 ) );
	region.y2 = (int)std::ceil(  std::min( desired.y2, rod.y2 ) );

	if( region.x1 >= region.x2 || region.y1 >= region.y2 )
	{
		return false;
	}

	outRegion = region;
	return true;
}

OFX::Host::ImageEffect::Image* ClipInstance::getImage(OfxTime time, const OfxRectD *optionalBounds)
{

	OfxRectI region;
	if( !resolveFetchRegion( *this, time, optionalBounds, region ) )
	{
		return nullptr;
	}

	if( m_name == "Output" )
	{
		auto *inv = EffectImageInstance::currentInvocation();
		if( !inv )
		{
			return nullptr;
		}

		// Output clip: allocate the union of optionalBounds and renderWindow
		// to ensure the buffer covers both the plugin's request and the
		// invocation's render window.
		OfxRectI imageBounds;
		if( optionalBounds )
		{
			imageBounds.x1 = std::min( (int)optionalBounds->x1, inv->renderWindow.x1 );
			imageBounds.y1 = std::min( (int)optionalBounds->y1, inv->renderWindow.y1 );
			imageBounds.x2 = std::max( (int)optionalBounds->x2, inv->renderWindow.x2 );
			imageBounds.y2 = std::max( (int)optionalBounds->y2, inv->renderWindow.y2 );
		}
		else
		{
			imageBounds.x1 = inv->renderWindow.x1;
			imageBounds.y1 = inv->renderWindow.y1;
			imageBounds.x2 = inv->renderWindow.x2;
			imageBounds.y2 = inv->renderWindow.y2;
		}

		// Reuse existing invocation output image if bounds match
		if( inv->outputImage )
		{
			OfxRectI existingBounds = inv->outputImage->getBounds();
			if( existingBounds.x1 == imageBounds.x1 && existingBounds.y1 == imageBounds.y1 &&
			    existingBounds.x2 == imageBounds.x2 && existingBounds.y2 == imageBounds.y2 )
			{
				inv->outputImage->addReference();
				return inv->outputImage;
			}
			inv->outputImage->releaseReference();
			inv->outputImage = nullptr;
		}

		inv->outputImage = new Image( *this, time, 0, &imageBounds );
		inv->outputImage->addReference();
		return inv->outputImage;
	}

	// Input clip: check prefetched first (set up by compute thread before
	// GL dispatch to avoid Gaffer pulls inside the worker).
	auto *inv = EffectImageInstance::currentInvocation();
	if( inv )
	{
		auto it = inv->prefetched.find( m_name );
		if( it != inv->prefetched.end() )
		{
			OfxRectI bounds = it->second->getBounds();
			if( region.x1 >= bounds.x1 && region.y1 >= bounds.y1 &&
			    region.x2 <= bounds.x2 && region.y2 <= bounds.y2 )
			{
				it->second->addReference();
				return it->second;
			}
		}
	}
	return m_effect->fetchInputImage( *this, time, region );
}

#ifdef OFX_SUPPORTS_OPENGLRENDER
OFX::Host::ImageEffect::Texture* ClipInstance::loadTexture( OfxTime time, const char *format, const OfxRectD *optionalBounds )
{
	if( m_name == "Output" )
	{
		GLContextManager& mgr = GLContextManager::instance();
		unsigned int tex = mgr.outputTexture();
		int texW = mgr.outputTexWidth();
		int texH = mgr.outputTexHeight();
		if( !tex || texW <= 0 || texH <= 0 )
		{
			return nullptr;
		}

		OfxRectI bounds;
		bounds.x1 = 0; bounds.y1 = 0;
		bounds.x2 = texW;
		bounds.y2 = texH;

		GafferTexture* ret = new GafferTexture(
			*this,
			1.0, 1.0,
			tex, GL_TEXTURE_2D,
			bounds, bounds,
			bounds.x2 * 4 * (int)sizeof(float),
			"none",
			""
		);
		return ret;
	}

	// For input clips, pull image data via getImage, then upload to GL texture
	Image *img = static_cast<Image*>( getImage( time, optionalBounds ) );
	if( !img )
	{
		return nullptr;
	}

	OfxRectI bounds = img->getBounds();
	int w = bounds.x2 - bounds.x1;
	int h = bounds.y2 - bounds.y1;
	if( w <= 0 || h <= 0 )
	{
		img->releaseReference();
		return nullptr;
	}

	GLContextManager& mgr = GLContextManager::instance();
	if( !mgr.makeCurrent() )
	{
		img->releaseReference();
		return nullptr;
	}

	if( !m_inputTexture || m_inputTexW != w || m_inputTexH != h ||
	    m_inputTextureGeneration != mgr.contextGeneration() )
	{
		if( m_inputTexture )
		{
			glDeleteTextures( 1, &m_inputTexture );
		}

		glGenTextures( 1, &m_inputTexture );
		glBindTexture( GL_TEXTURE_2D, m_inputTexture );
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST );
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST );
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE );
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE );

		const bool isAlpha = img->getStringProperty( kOfxImageEffectPropComponents ) == kOfxImageComponentAlpha;
		glTexImage2D(
			GL_TEXTURE_2D, 0,
			isAlpha ? GL_R32F : GL_RGBA32F,
			w, h, 0,
			isAlpha ? GL_RED : GL_RGBA,
			GL_FLOAT, nullptr
		);

		m_inputTexW = w;
		m_inputTexH = h;
		m_inputTextureGeneration = mgr.contextGeneration();

		mgr.registerTexture( m_inputTexture );
	}

	// Upload pixel data from the pulled image
	glBindTexture( GL_TEXTURE_2D, m_inputTexture );
	glPixelStorei( GL_UNPACK_ALIGNMENT, 1 );
	const bool isAlpha = img->getStringProperty( kOfxImageEffectPropComponents ) == kOfxImageComponentAlpha;
	if( isAlpha )
	{
		glTexSubImage2D( GL_TEXTURE_2D, 0, 0, 0, w, h, GL_RED, GL_FLOAT, img->pixel( bounds.x1, bounds.y1 ) );
	}
	else
	{
		OfxRGBAColourF *pixelData = img->pixel( bounds.x1, bounds.y1 );
		glTexSubImage2D( GL_TEXTURE_2D, 0, 0, 0, w, h, GL_RGBA, GL_FLOAT, pixelData );
	}

	img->releaseReference();

	OfxRectI texBounds;
	texBounds.x1 = 0; texBounds.y1 = 0;
	texBounds.x2 = w; texBounds.y2 = h;

	return new GafferTexture(
		*this,
		1.0, 1.0,
		m_inputTexture, GL_TEXTURE_2D,
		texBounds, texBounds,
		isAlpha ? w * (int)sizeof(float) : w * 4 * (int)sizeof(float),
		"none",
		""
	);
}
#endif

GafferTexture::GafferTexture(
	ClipInstance& instance,
	double renderScaleX,
	double renderScaleY,
	unsigned int index,
	unsigned int target,
	const OfxRectI &bounds,
	const OfxRectI &rod,
	int rowBytes,
	const std::string &field,
	const std::string &uniqueIdentifier
)
	: OFX::Host::ImageEffect::Texture(
		instance,
		renderScaleX,
		renderScaleY,
		index,
		target,
		bounds,
		rod,
		rowBytes,
		field,
		uniqueIdentifier
	),
	m_textureId( index )
{
}

GafferTexture::~GafferTexture()
{
}
