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
#include "GafferOFX/EffectImageInstance.h"
#include "GafferOFX/ClipInstance.h"
#include "GafferOFX/ParamInstance.h"
#include "GafferOFX/OFXImageNode.h"

#include "Gaffer/Context.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/Plug.h"

#include "GafferImage/ImagePlug.h"
#include "GafferImage/Sampler.h"
#include "GafferImage/FormatPlug.h"

#include "IECore/SimpleTypedData.h"
#include "IECore/VectorTypedData.h"

#include "HostSupport/ofxhPluginCache.h"
#include "HostSupport/ofxhImageEffectAPI.h"

#include "tbb/task_arena.h"

#include <iostream>

namespace
{

// Must match sanitizeName in ParamInstance.cpp
std::string sanitizeName( const std::string &name )
{
	std::string result = name;
	for( char &c : result )
	{
		if(
			!( c >= 'A' && c <= 'Z' ) &&
			!( c >= 'a' && c <= 'z' ) &&
			!( c >= '0' && c <= '9' ) &&
			c != '_' && c != ':'
		)
		{
			c = '_';
		}
	}
	return result;
}

// Read RGBA channels from an ImagePlug into a flat interleaved OfxRGBAColourF
// buffer covering the given data window.  If the input lacks an Alpha channel,
// alpha=1.0 is injected.
void readPlugToRGBA( const GafferImage::ImagePlug *plug, OfxRGBAColourF *buffer, const Imath::Box2i &dataWindow, int width )
{
	GafferImage::Sampler rSampler( plug, "R", dataWindow );
	GafferImage::Sampler gSampler( plug, "G", dataWindow );
	GafferImage::Sampler bSampler( plug, "B", dataWindow );

	IECore::ConstStringVectorDataPtr channelNamesData = plug->channelNamesPlug()->getValue();
	bool hasAlpha = false;
	for( const auto &ch : channelNamesData->readable() )
	{
		if( ch == "A" )
		{
			hasAlpha = true;
			break;
		}
	}

	std::unique_ptr<GafferImage::Sampler> aSampler;
	if( hasAlpha )
	{
		aSampler = std::make_unique<GafferImage::Sampler>( plug, "A", dataWindow );
	}

	for( int y = dataWindow.min.y; y < dataWindow.max.y; ++y )
	{
		for( int x = dataWindow.min.x; x < dataWindow.max.x; ++x )
		{
			int idx = ( y - dataWindow.min.y ) * width + ( x - dataWindow.min.x );
			buffer[idx].r = rSampler.sample( x, y );
			buffer[idx].g = gSampler.sample( x, y );
			buffer[idx].b = bSampler.sample( x, y );
			buffer[idx].a = aSampler ? aSampler->sample( x, y ) : 1.0f;
		}
	}
}

// Read the alpha channel from an ImagePlug into a flat single-channel float
// buffer covering the given data window.  Used for Alpha (mask) clip images,
// whose component count is 1 — the plugin reads the first component as the
// mask value.  Masks follow Gaffer's own convention: coverage lives in A
// (Grade, ColorCorrect, etc. all sample the mask's alpha channel).
void readPlugToFloatA( const GafferImage::ImagePlug *plug, float *buffer, const Imath::Box2i &dataWindow, int width )
{
	GafferImage::Sampler aSampler( plug, "A", dataWindow );

	for( int y = dataWindow.min.y; y < dataWindow.max.y; ++y )
	{
		for( int x = dataWindow.min.x; x < dataWindow.max.x; ++x )
		{
			int idx = ( y - dataWindow.min.y ) * width + ( x - dataWindow.min.x );
			buffer[idx] = aSampler.sample( x, y );
		}
	}
}

} // anonymous namespace

using namespace GafferOFX;

// Thread-local stack of active render invocations (stored as pointers so the
// original invocation object owns its outputImage — no double-free from copies).
// A stack (vs single slot) correctly handles nested/stolen renders when
// TBB steals a render task while the thread is blocked inside a Gaffer pull.
thread_local std::vector<RenderInvocation*> g_renderStack;

RenderInvocationGuard::RenderInvocationGuard( RenderInvocation &inv )
{
	g_renderStack.push_back( &inv );
}

RenderInvocationGuard::~RenderInvocationGuard()
{
	if( m_active )
	{
		g_renderStack.pop_back();
	}
}

const RenderInvocation &RenderInvocationGuard::invocation() const
{
	return *g_renderStack.back();
}

RenderInvocation *EffectImageInstance::currentInvocation()
{
	if( g_renderStack.empty() )
	{
		return nullptr;
	}
	return g_renderStack.back();
}

// Instance registration functions from libOfxGafferHost.so
// Used to track valid Param::Instance* pointers for safe handle validation
// without touching the handle's memory (avoids __dynamic_cast SIGSEGV).
namespace OFX { namespace Host { namespace Param {
	void registerInstance(Instance* inst, const void* descriptorHandle);
	void unregisterInstance(Instance* inst);
} } }


EffectImageInstance::EffectImageInstance( OFX::Host::ImageEffect::ImageEffectPlugin* plugin, OFX::Host::ImageEffect::Descriptor& desc, const std::string& context): OFX::Host::ImageEffect::Instance(plugin,desc,context,false)
{
}

EffectImageInstance::~EffectImageInstance()
{
	// Unregister all param instances before they are destroyed by ~SetInstance
	try {
		const auto& params = getParams();
		for(const auto& [name, inst] : params) {
			OFX::Host::Param::unregisterInstance(inst);
		}
	} catch(...) {}
}

OFX::Host::ImageEffect::ClipInstance* EffectImageInstance::newClipInstance(OFX::Host::ImageEffect::Instance* plugin, OFX::Host::ImageEffect::ClipDescriptor* descriptor, int index)
{
	return new ClipInstance(this,descriptor);
}


const std::string &EffectImageInstance::getDefaultOutputFielding() const
{
	static const std::string v(kOfxImageFieldNone);
	return v;    
}

OfxStatus EffectImageInstance::vmessage(const char* type, const char* id, const char* format, va_list args)
{
	return kOfxStatOK;
}

OfxStatus EffectImageInstance::setPersistentMessage(const char* type, const char* id, const char* format, va_list args)
{
	return vmessage(type, id, format, args);
}

OfxStatus EffectImageInstance::clearPersistentMessage()
{
	return kOfxStatOK;
}

void EffectImageInstance::getProjectSize(double& xSize, double& ySize) const
{
	if( auto inv = currentInvocation() )
	{
		if( inv->projectWidth > 0 && inv->projectHeight > 0 )
		{
			xSize = inv->projectWidth;
			ySize = inv->projectHeight;
			return;
		}
	}

	if( auto ctx = Gaffer::Context::current() )
	{
		auto gafferFormat = GafferImage::FormatPlug::getDefaultFormat( ctx );
		xSize = gafferFormat.width();
		ySize = gafferFormat.height();
	}
	else
	{
		xSize = 1920;
		ySize = 1080;
	}
}

void EffectImageInstance::getProjectOffset(double& xOffset, double& yOffset) const
{
	xOffset = 0;
	yOffset = 0;
}

void EffectImageInstance::getProjectExtent(double& xSize, double& ySize) const
{
	if( auto ctx = Gaffer::Context::current() )
	{
		auto gafferFormat = GafferImage::FormatPlug::getDefaultFormat( ctx );
		xSize = gafferFormat.width();
		ySize = gafferFormat.height();
	}
	else
	{
		xSize = 1920;
		ySize = 1080;
	}
}

double EffectImageInstance::getProjectPixelAspectRatio() const
{
	if( auto ctx = Gaffer::Context::current() )
	{
		auto gafferFormat = GafferImage::FormatPlug::getDefaultFormat( ctx );
		return gafferFormat.getPixelAspect();
	}
	return 1.0;
}

double EffectImageInstance::getEffectDuration() const
{
	
	auto start = 1;
	auto end = 100;
	if( auto sn = scriptNode() )
	{
		start = sn->frameStartPlug()->getValue();
		end = sn->frameEndPlug()->getValue();
	}
	return end - start;
}

double EffectImageInstance::getFrameRate() const
{
	if( auto ctx = Gaffer::Context::current() )
	{
		return ctx->getFramesPerSecond();
	}
	return 24.0;
}

double EffectImageInstance::getFrameRecursive() const
{
	return Gaffer::Context::current()->getFrame();
;
}

void EffectImageInstance::getRenderScaleRecursive(double &x, double &y) const
{
	x = y = 1.0;
}

// make a parameter instance
namespace
{

void registerParameterMetadata( Gaffer::Plug *plug, const OFX::Host::Param::Descriptor &descriptor, const OFX::Host::Param::SetDescriptor *setDescriptor )
{
	const auto &props = descriptor.getProperties();
	const std::string type = descriptor.getType();

	// Label
	try
	{
		std::string label = props.getStringProperty( kOfxPropLabel );
		if( !label.empty() )
		{
			Gaffer::Metadata::registerValue( plug, "label", new IECore::StringData( label ), false );
		}
	}
	catch( ... )
	{
	}

	// Tooltip
	try
	{
		std::string hint = props.getStringProperty( kOfxParamPropHint );
		if( !hint.empty() )
		{
			Gaffer::Metadata::registerValue( plug, "description", new IECore::StringData( hint ), false );
		}
	}
	catch( ... )
	{
	}

	// Secret or disabled params — hide nodule
	try
	{
		if( props.getIntProperty( kOfxParamPropSecret ) )
		{
			Gaffer::Metadata::registerValue( plug, "nodule:type", new IECore::StringData( "" ), false );
		}
	}
	catch( ... )
	{
	}

	try
	{
		if( !props.getIntProperty( kOfxParamPropEnabled ) )
		{
			Gaffer::Metadata::registerValue( plug, "nodule:type", new IECore::StringData( "" ), false );
		}
	}
	catch( ... )
	{
	}

	// Multi-line and file-path string parameters
	if( type == kOfxParamTypeString )
	{
		try
		{
			std::string stringMode = props.getStringProperty( kOfxParamPropStringMode );
			if( stringMode == kOfxParamStringIsMultiLine )
			{
				Gaffer::Metadata::registerValue( plug, "plugValueWidget:type", new IECore::StringData( "GafferUI.MultiLineStringPlugValueWidget" ), false );
			}
			else if( stringMode == kOfxParamStringIsFilePath )
			{
				Gaffer::Metadata::registerValue( plug, "nodule:type", new IECore::StringData( "" ), false );
				Gaffer::Metadata::registerValue( plug, "plugValueWidget:type", new IECore::StringData( "GafferUI.FileSystemPathPlugValueWidget" ), false );
			}
		}
		catch( ... )
		{
		}
	}

	// Pushbutton params
	if( type == kOfxParamTypePushButton )
	{
		Gaffer::Metadata::registerValue( plug, "plugValueWidget:type", new IECore::StringData( "GafferOFXUI.OFXImageNodeUI._PushButton" ), false );
		Gaffer::Metadata::registerValue( plug, "nodule:type", new IECore::StringData( "" ), false );
	}

	// Numeric range limits
	if( type == kOfxParamTypeInteger || type == kOfxParamTypeDouble )
	{
		try
		{
			double min = props.getDoubleProperty( kOfxParamPropMin );
			double max = props.getDoubleProperty( kOfxParamPropMax );
			Gaffer::Metadata::registerValue( plug, "hardRange", new IECore::V2dData( Imath::V2d( min, max ) ), false );
		}
		catch( ... )
		{
		}

		try
		{
			double min = props.getDoubleProperty( kOfxParamPropDisplayMin );
			double max = props.getDoubleProperty( kOfxParamPropDisplayMax );
			Gaffer::Metadata::registerValue( plug, "softRange", new IECore::V2dData( Imath::V2d( min, max ) ), false );
		}
		catch( ... )
		{
		}
	}

	// Choice presets
	if( type == kOfxParamTypeChoice )
	{
		try
		{
			int numOptions = props.getDimension( kOfxParamPropChoiceOption );
			for( int i = 0; i < numOptions; ++i )
			{
				std::string optionName = props.getStringProperty( kOfxParamPropChoiceOption, i );
				Gaffer::Metadata::registerValue( plug, "preset:" + optionName, new IECore::IntData( i ), false );
			}
		}
		catch( ... )
		{
		}

		Gaffer::Metadata::registerValue( plug, "plugValueWidget:type", new IECore::StringData( "GafferUI.PresetsPlugValueWidget" ), false );
	}

	// Section (page/group membership)
	std::string parentName;
	try { parentName = props.getStringProperty( kOfxParamPropParent ); } catch(...) {}
	if( parentName.empty() && setDescriptor )
	{
		const auto &paramMap = setDescriptor->getParams();
		const std::string &pname = plug->getName().string();
		for( const auto &[name, desc] : paramMap )
		{
			try
			{
				if( desc->getProperties().getStringProperty( kOfxParamPropType ) == kOfxParamTypePage )
				{
					int nChildren = desc->getProperties().getDimension( kOfxParamPropPageChild );
					for( int i = 0; i < nChildren; ++i )
					{
						if( desc->getProperties().getStringProperty( kOfxParamPropPageChild, i ) == pname )
						{
							parentName = name;
							break;
						}
					}
				}
			}
			catch( ... ) {}
			if( !parentName.empty() )
			{
				break;
			}
		}
	}
	if( !parentName.empty() )
	{
		std::string sectionName = parentName;
		if( setDescriptor )
		{
			const auto &paramMap = setDescriptor->getParams();
			auto it = paramMap.find( parentName );
			if( it != paramMap.end() )
			{
				try
				{
					std::string groupLabel = it->second->getProperties().getStringProperty( kOfxPropLabel );
					if( !groupLabel.empty() )
					{
						sectionName = groupLabel;
					}
				}
				catch( ... ) {}
			}
		}
		Gaffer::Metadata::registerValue( plug, "layout:section", new IECore::StringData( sectionName ), false );
	}

	// Internal/descriptive param hiding
	{
		std::string parentName;
		try { parentName = props.getStringProperty( kOfxParamPropParent ); } catch(...) {}
		if( !parentName.empty() )
		{
			const std::string &pname = plug->getName().string();
			bool isMetadata =
				pname.compare( 0, 9, "paramType" ) == 0 ||
				pname.compare( 0, 9, "paramName" ) == 0 ||
				pname.compare( 0, 10, "paramLabel" ) == 0 ||
				pname.compare( 0, 9, "paramHint" ) == 0 ||
				pname.compare( 0, 12, "paramDefault" ) == 0 ||
				pname.compare( 0, 8, "paramMin" ) == 0 ||
				pname.compare( 0, 8, "paramMax" ) == 0 ||
				pname.compare( 0, 9, "inputHint" ) == 0 ||
				pname.compare( 0, 10, "inputLabel" ) == 0 ||
				pname.compare( 0, 9, "inputName" ) == 0 ||
				pname.compare( 0, 4, "wrap" ) == 0 ||
				pname.compare( 0, 6, "mipmap" ) == 0 ||
				pname == "bbox" ||
				pname == "startDate" ||
				pname == "NatronOfxParamStringSublabelName" ||
				pname.compare( 0, 17, "NatronParamFormat" ) == 0;
			if( isMetadata )
			{
				Gaffer::Metadata::registerValue( plug, "nodule:type", new IECore::StringData( "" ), false );
				Gaffer::Metadata::registerValue( plug, "plugValueWidget:type", new IECore::StringData( "" ), false );
			}
		}
	}
}

} // anonymous namespace

OFX::Host::Param::Instance* EffectImageInstance::newParam(const std::string& name, OFX::Host::Param::Descriptor& descriptor)
{
	OFX::Host::Param::Instance *result = nullptr;

	if(descriptor.getType()==kOfxParamTypeInteger)
	{
		result = new IntegerInstance(this,name,descriptor);
	}
	else if(descriptor.getType()==kOfxParamTypeDouble)
	{
		result = new DoubleInstance(this,name,descriptor);
	}
	else if(descriptor.getType()==kOfxParamTypeBoolean)
	{
		result = new BooleanInstance(this,name,descriptor);
	}
	else if(descriptor.getType()==kOfxParamTypeChoice)
	{
		result = new ChoiceInstance(this,name,descriptor);
	}
	else if(descriptor.getType()==kOfxParamTypeRGBA)
	{
		result = new RGBAInstance(this,name,descriptor);
	}
	else if(descriptor.getType()==kOfxParamTypeRGB)
	{
		result = new RGBInstance(this,name,descriptor);
	}
	else if(descriptor.getType()==kOfxParamTypeDouble2D)
	{
		result = new Double2DInstance(this,name,descriptor);
	}
	else if(descriptor.getType()==kOfxParamTypeInteger2D)
	{
		result = new Integer2DInstance(this,name,descriptor);
	}
	else if(descriptor.getType()==kOfxParamTypePushButton)
	{
		result = new PushbuttonInstance(this,name,descriptor);
	}
	else if(descriptor.getType()==kOfxParamTypeString)
	{
		result = new StringInstance(this,name,descriptor);
	}
	else if(descriptor.getType()==kOfxParamTypeGroup)
	{
		result = new OFX::Host::Param::GroupInstance(descriptor,this);
	}
	else if(descriptor.getType()==kOfxParamTypePage)
	{
		result = new OFX::Host::Param::PageInstance(descriptor,this);
	}
	else if(descriptor.getType()==kOfxParamTypeCustom)
	{
		result = new StringInstance(this,name,descriptor);
	}
	if( result )
	{
		OFX::Host::Param::registerInstance(result, &descriptor);

		auto *plug = const_cast<OFXImageNode*>( static_cast<const OFXImageNode*>( node() ) )->parametersPlug()->getChild<Gaffer::Plug>( sanitizeName( name ) );
		if( plug )
		{
			registerParameterMetadata( plug, descriptor, &getDescriptor() );
		}
	}

	return result;
}

OfxStatus EffectImageInstance::editBegin(const std::string& name)
{
	return kOfxStatErrMissingHostFeature;
}

OfxStatus EffectImageInstance::editEnd()
{
	return kOfxStatErrMissingHostFeature;
}

void  EffectImageInstance::progressStart(const std::string &message, const std::string &messageid)
{
}

void  EffectImageInstance::progressEnd()
{
}

bool  EffectImageInstance::progressUpdate(double t)
{
	return true;
}


double  EffectImageInstance::timeLineGetTime()
{
	return Gaffer::Context::current()->getFrame();
}

void  EffectImageInstance::timeLineGotoTime(double t)
{
}

void  EffectImageInstance::timeLineGetBounds(double &t1, double &t2)
{

	t1 = 1;
	t2 = 100;
	if( auto sn = scriptNode() )
	{
		t1 = sn->frameStartPlug()->getValue();
		t2 = sn->frameEndPlug()->getValue();
	}
}

const Gaffer::Node* EffectImageInstance::node() const
{
	return m_node;
}

const Gaffer::ScriptNode* EffectImageInstance::scriptNode() const
{
	return m_node->ancestor<Gaffer::ScriptNode>();
}

void EffectImageInstance::setNode(const Gaffer::Node* node)
{
	m_node = node;
}

void EffectImageInstance::markParamInteracted( const std::string &name )
{
	m_interactedParams.insert( name );
}

void EffectImageInstance::clearInteractedParams()
{
	m_interactedParams.clear();
}

const std::unordered_set<std::string> &EffectImageInstance::interactedParams() const
{
	return m_interactedParams;
}

// Helper: detect if this is a Mode 1 call (vtable[13](this) → return handle)
// vs a Mode 2 call (vtable[13](this, action, handle, inArgs, outArgs) → dispatch).
// In Mode 1, the action pointer is whatever was left in rsi (typically not "Ofx*").
// In Mode 2, action is always a valid OFX action string starting with "Ofx".
static inline bool isMode1Call( const char* action, const void* handle )
{
	if( !action )
	{
		return true;
	}
	const char* p = action;
	if( p[0] != 'O' || p[1] != 'f' || p[2] != 'x' )
	{
		return true;
	}
	return false;
}

OfxStatus EffectImageInstance::mainEntry(const char *action, const void *handle, OFX::Host::Property::Set *inArgs, OFX::Host::Property::Set *outArgs)
{
	typedef OFX::Host::ImageEffect::Instance BaseInstance;
	return BaseInstance::mainEntry( action, handle, inArgs, outArgs );
}

OFX::Host::ImageEffect::Image *EffectImageInstance::fetchInputImage(
	const ClipInstance &clip, OfxTime time, const OfxRectI &region
) const
{
	const GafferImage::ImagePlug *plug = nullptr;
	const std::string &clipName = clip.getName();

	if( clipName == "Source" )
	{
		plug = static_cast<const OFXImageNode*>( m_node )->inPlug();
	}
	else if( clipName != "Output" )
	{
		const std::string &plugName = clip.plugName();
		if( !plugName.empty() )
		{
			plug = m_node->getChild<GafferImage::ImagePlug>( plugName );
		}
	}

	if( !plug || !plug->getInput() )
	{
		return nullptr;
	}

	int width = region.x2 - region.x1;
	int height = region.y2 - region.y1;
	if( width <= 0 || height <= 0 )
	{
		return nullptr;
	}

	// Create output Image — allocates its own buffer
	OfxRectI bufBounds = { region.x1, region.y1, region.x2, region.y2 };
	Image *image = new Image( const_cast<ClipInstance&>( clip ), time, 0, &bufBounds );

	// Fill the image's pixel data by pulling from Gaffer under isolate
	// (prevents TBB task stealing during the pull).
	const bool isAlpha = ( image->getStringProperty( kOfxImageEffectPropComponents ) == kOfxImageComponentAlpha );
	OfxRGBAColourF *pixelData = isAlpha ? nullptr : image->pixel( region.x1, region.y1 );
	float *alphaData = isAlpha ? reinterpret_cast<float*>( image->pixel( region.x1, region.y1 ) ) : nullptr;

	auto *inv = currentInvocation();
	const Gaffer::Context *baseCtx = inv ? inv->context.get() : Gaffer::Context::current();

	if( baseCtx && ( pixelData || alphaData ) )
	{
		if( time == baseCtx->getFrame() )
		{
			Gaffer::Context::Scope scope( baseCtx );
			try
			{
				tbb::this_task_arena::isolate( [&]() {
					Imath::Box2i imgRegion(
						Imath::V2i( region.x1, region.y1 ),
						Imath::V2i( region.x2, region.y2 )
					);
					if( isAlpha )
					{
						readPlugToFloatA( plug, alphaData, imgRegion, width );
					}
					else
					{
						readPlugToRGBA( plug, pixelData, imgRegion, width );
					}
				} );
			}
			catch( ... )
			{
				if( auto *activeInv = currentInvocation() )
				{
					activeInv->exception = std::current_exception();
				}
				image->releaseReference();
				return nullptr;
			}
		}
		else
		{
			// Temporal access: override frame (EditableScope alone copies and scopes)
			Gaffer::Context::EditableScope edit( baseCtx );
			edit.setFrame( time );
			try
			{
				tbb::this_task_arena::isolate( [&]() {
					Imath::Box2i imgRegion(
						Imath::V2i( region.x1, region.y1 ),
						Imath::V2i( region.x2, region.y2 )
					);
					if( isAlpha )
					{
						readPlugToFloatA( plug, alphaData, imgRegion, width );
					}
					else
					{
						readPlugToRGBA( plug, pixelData, imgRegion, width );
					}
				} );
			}
			catch( ... )
			{
				if( auto *activeInv = currentInvocation() )
				{
					activeInv->exception = std::current_exception();
				}
				image->releaseReference();
				return nullptr;
			}
		}
	}

	return image;
}
