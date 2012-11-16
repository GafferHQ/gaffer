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

#ifndef GAFFERUI_VIEW_H
#define GAFFERUI_VIEW_H

#include "Gaffer/Node.h"

#include "GafferUI/ViewportGadget.h"
#include "GafferUIBindings/ViewBinding.h" // to enable friend declaration for updateViewFromPlug().

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( View )

/// The View classes provide the content for the Viewer, which is implemented in the
/// GafferUI python module. The View presents whatever is connected into inPlug(),
/// and may provide further settings via additional plugs.
class View : public Gaffer::Node
{

	public :

		/// This typedef should be overridden by derived classes.
		typedef Gaffer::Plug InPlugType;

		virtual ~View();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( View, ViewTypeId, Gaffer::Node );

		/// The contents for the view are provided by the input to this plug.
		/// The view can be switched by connecting a new input.
		template<typename T>
		T *inPlug();
		template<typename T>
		const T *inPlug() const;
		
		/// The Context in which the View should operate.
		Gaffer::Context *getContext();
		const Gaffer::Context *getContext() const;
		void setContext( Gaffer::ContextPtr context );

		/// Subclasses are responsible for presenting their content in this viewport.
		ViewportGadget *viewportGadget();
		const ViewportGadget *viewportGadget() const;

		/// A signal the view may use when it needs to be updated due
		/// to user action.
		UnarySignal &updateRequestSignal();
		
		/// @name Factory
		///////////////////////////////////////////////////////////////////
		//@{
		/// Creates a View for the specified plug.
		static ViewPtr create( Gaffer::PlugPtr input );
		typedef boost::function<ViewPtr ( Gaffer::PlugPtr )> ViewCreator;
		/// Registers a function which will return a View instance for a
		/// plug of a specific type.
		static void registerView( IECore::TypeId nodeType, ViewCreator creator );
		//@}
		
	protected :

		View( const std::string &name, Gaffer::PlugPtr input );

		/// Must be implemented by derived classes to update the view from inPlug()
		/// using the context provided by getContext(). This method will be called
		/// by the Viewer whenever appropriate. See notes in Viewer.__plugDirtied
		/// explaining why it's better for the Viewer to be responsible for calling
		/// this than the View to do it itself.
		/// \see View::updateRequestSignal().
		virtual void updateFromPlug() = 0;
		
		/// May be overridden by derived classes to control the region that is framed
		/// when "F" is pressed.
		virtual Imath::Box3f framingBound() const;
				
		template<class T>
		struct ViewDescription
		{
			ViewDescription( IECore::TypeId plugType );
			static ViewPtr creator( Gaffer::PlugPtr input );
		};
		
	private :
	
		ViewportGadgetPtr m_viewportGadget;
		Gaffer::ContextPtr m_context;
		UnarySignal m_updateRequestSignal;

		bool keyPress( GadgetPtr gadget, const KeyEvent &keyEvent );
		
		typedef std::map<IECore::TypeId, ViewCreator> CreatorMap;
		static CreatorMap &creators();
	
		static size_t g_firstPlugIndex;
		
		friend void GafferUIBindings::updateViewFromPlug( View & );
					
};

} // namespace GafferUI

#include "GafferUI/View.inl"

#endif // GAFFERUI_VIEW_H
