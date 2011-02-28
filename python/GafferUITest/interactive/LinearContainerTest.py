import IECore
import Gaffer
import GafferUI
import gtk
		
window = GafferUI.Window( title="Linear container test" )
window.gtkWidget().connect( "delete_event", gtk.main_quit )

twoByFour = GafferUI.RenderableGadget(
	IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1, -2 ), IECore.V2f( 1, 2 ) ) )
)

fourByFour = GafferUI.RenderableGadget(
	IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -2, -2 ), IECore.V2f( 2, 2 ) ) )
)

fourByTwo = GafferUI.RenderableGadget(
	IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -2, -1 ), IECore.V2f( 2, 1 ) ) )
)
		
c = GafferUI.LinearContainer( orientation=GafferUI.LinearContainer.Orientation.Y, alignment=GafferUI.LinearContainer.Alignment.Min, spacing=1 )
c.c1 = twoByFour
c.c2 = fourByFour
c.c3 = fourByTwo

s = GafferUI.GadgetWidget( c )

window.setChild( s )

window.show()

GafferUI.EventLoop.start()
