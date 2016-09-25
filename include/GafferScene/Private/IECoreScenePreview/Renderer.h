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

#ifndef IECORESCENEPREVIEW_RENDERER_H
#define IECORESCENEPREVIEW_RENDERER_H

#include "IECore/CompoundObject.h"
#include "IECore/Display.h"
#include "IECore/Camera.h"

namespace IECoreScenePreview
{

/// \todo Derive from RunTimeTyped - we're just avoiding doing that
/// right now so we don't have to shuffle TypeIds between Gaffer and Cortex.
class Renderer : public IECore::RefCounted
{

	public :

		enum RenderType
		{
			/// Locations are emitted to the renderer immediately
			/// and not retained for later editing.
			Batch,
			/// Locations are retained, allowing interactive
			/// editing to be performed during rendering.
			Interactive,
			/// A scene description is serialised to file.
			SceneDescription
		};

		IE_CORE_DECLAREMEMBERPTR( Renderer )

		static const std::vector<IECore::InternedString> &types();
		/// Filename is only used if the renderType is SceneDescription.
		static Ptr create( const IECore::InternedString &type, RenderType renderType = Batch, const std::string &fileName = "" );

		/// \todo Rename Display->Output in Cortex.
		typedef IECore::Display Output;

		/// Sets a global option for the render. In interactive renders an option may
		/// be unset by passing a NULL value.
		///
		/// Standard Options
		/// ----------------
		///
		/// "camera", StringData, "", The name of the primary render camera.
		virtual void option( const IECore::InternedString &name, const IECore::Data *value ) = 0;
		/// Adds an output image to be rendered, In interactive renders an output may be
		/// removed by passing NULL as the value.
		virtual void output( const IECore::InternedString &name, const Output *output ) = 0;

		IE_CORE_FORWARDDECLARE( AttributesInterface );

		/// A handle to a block of attributes.
		class AttributesInterface : public IECore::RefCounted
		{

			public :

				IE_CORE_DECLAREMEMBERPTR( AttributesInterface );

			protected :

				virtual ~AttributesInterface();

		};

		/// Creates a block of attributes which can subsequently
		/// be assigned to objects. Each block of attributes may
		/// be assigned to multiple objects, but each object may
		/// only have one attribute block assigned at a time.
		///
		/// Standard Attributes
		/// -------------------
		///
		/// "doubleSided", BoolData, true
		/// "surface", ObjectVector of IECore::Shaders
		/// "light", ObjectVector of IECore::Shaders
		/// "sets", InternedStringVectorData of set names
		///
		/// Renderer Specific Attributes
		/// ----------------------------
		///
		/// "<rendererSpecificPrefix>:name"
		virtual AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes ) = 0;

		IE_CORE_FORWARDDECLARE( ObjectInterface );

		/// A handle to an object in the renderer. The reference counting semantics of an
		/// ObjectInterfacePtr are as follows :
		///
		/// - For Interactive renders, releasing the Ptr (removing the last reference)
		///   removes the object from the render.
		/// - For Batch and SceneDescription renders, releasing the Ptr flushes the
		///   object to the renderer.
		class ObjectInterface : public IECore::RefCounted
		{

			public :

				IE_CORE_DECLAREMEMBERPTR( ObjectInterface )

				/// Assigns a transform to the object, replacing any previously
				/// assigned transform. For Interactive renders transforms may be
				/// modified at any time the renderer is paused.
				/// \todo Should we introduce a TransformInterface that can be
				/// passed directly to `Renderer::object()` etc in the same
				/// way that attributes are? This might be a way of supporting
				/// renderers with more complex transform models than just flattened
				/// matrices.
				virtual void transform( const Imath::M44f &transform ) = 0;
				/// As above, but specifying a moving transform.
				virtual void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) = 0;
				/// Assigns a new block of attributes to the object, replacing any
				/// previously assigned attributes. This may only be used in Interactive
				/// mode, and then only when the renderer is paused.
				virtual void attributes( const AttributesInterface *attributes ) = 0;

			protected :

				virtual ~ObjectInterface();

		};

		/// Adds a named camera to the render. Cameras should be specified prior to all
		/// other lights/objects, as some renderers (for instance a streaming OpenGL renderer)
		/// may be unable to operate otherwise.
		///
		/// Standard Parameters
		/// -------------------
		///
		/// "resolution", V2iData
		/// The resolution of any output images. Should default to 640x480 if not specified.
		///
		/// "pixelAspectRatio", FloatData
		/// The xSize/ySize aspect ratio for a pixel.
		///
		/// "screenWindow", Box2fData
		/// The region in screen space which is mapped to the output resolution.
		///
		/// "renderRegion", Box2iData
		/// The region in image pixels which should actually be rendered - this allows just
		/// a section of the full resolution to be rendered, or an area larger than the
		/// resolution to be rendered, creating overscan outside the displayWindow.  The
		/// default value is the whole standard resolution, running from
		/// 0,0 to resolution.x - 1, resolution.y - 1,
		/// with 0,0 representing the upper left corner.
		///
		/// \todo This follows the conventions of Cortex, and matches the OpenEXR display window,
		/// but does not match Gaffer image conventions ( origin in lower left corner,
		/// indexing pixel corners rather than pixel centers ).  We are planning to switch
		/// this to match the Gaffer convention instead.
		///
		/// "projection" StringData, "perspective"
		/// The projection that determines how camera coordinates are converted to screen space
		/// coordinates. Implementations should support "perspective" and "orthographic", with
		/// orthographic being the default if not specified.
		///
		/// "projection:fov", FloatData
		/// In the case of the "projection" parameter specifying a perspective projection, this
		/// specifies the field of view (in degrees) which is visible between -1 and 1 in screen
		/// space. Defaults to 90 degrees if unspecified.
		///
		/// "clippingPlanes", V2fData
		/// The near and far clipping planes. Defaults to 0.01, 100000 if unspecified.
		///
		/// "shutter", V2fData
		/// The time interval for which the shutter is open - this is used in conjunction with the
		/// times passed to motionBegin() to specify motion blur. Defaults to 0,0 if unspecified.
		virtual ObjectInterfacePtr camera( const std::string &name, const IECore::Camera *camera, const AttributesInterface *attributes ) = 0;

		/// Adds a named light with the initially supplied set of attributes, which are expected
		/// to provide at least a light shader. Object may be non-NULL to specify arbitrary geometry
		/// for a geometric area light, or NULL to indicate that the light shader specifies its own
		/// geometry internally (or is non-geometric in nature).
		/// \todo Should object be typed as Primitive?
		virtual ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) = 0;

		/// Adds a named object to the render with the initally supplied set of attributes.
		/// The attributes may subsequently be edited in interactive mode using
		/// ObjectInterface::attributes().
		/// \todo Rejig class hierarchy so we can have something less generic than
		/// Object here, but still pass CoordinateSystems. Or should
		/// coordinate systems have their own dedicated calls?
		virtual ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) = 0;
		/// As above, but specifying a deforming object.
		virtual ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) = 0;

		/// Performs the render - should be called after the
		/// entire scene has been specified using the methods
		/// above. Batch and SceneDescripton renders will have
		/// been completed upon return from this method. Interactive
		/// renders will return immediately and perform the
		/// rendering in the background, allowing pause() to be
		/// used to make edits before calling render() again.
		virtual void render() = 0;
		/// If an interactive render is running, pauses it so
		/// that edits may be made.
		virtual void pause() = 0;

	protected :

		Renderer();
		virtual ~Renderer();

		/// Construct a static instance of this to register a
		/// renderer implementation.
		/// \todo Derive this from RunTimeTyped::TypeDescription.
		template<class T>
		struct TypeDescription
		{

			/// \todo Take the type name from RunTimeTyped::staticTypeId().
			TypeDescription( const IECore::InternedString &typeName )
			{
				registerType( typeName, creator );
			}

			private :

				static Ptr creator( RenderType renderType, const std::string &fileName )
				{
					return new T( renderType, fileName );
				}

		};

	private :

		static void registerType( const IECore::InternedString &typeName, Ptr (*creator)( RenderType, const std::string & ) );


};

IE_CORE_DECLAREPTR( Renderer )

} // namespace IECoreScenePreview

#endif // IECORESCENEPREVIEW_RENDERER_H
