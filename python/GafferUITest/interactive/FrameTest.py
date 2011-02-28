import IECore
import Gaffer
import GafferUI
import IECore
import gtk
		
window = GafferUI.Window( title="Frame test" )
window.gtkWidget().connect( "delete_event", gtk.main_quit )

t = GafferUI.TextGadget( IECore.Font( "/usr/X11R6/lib/X11/fonts/TTF/Vera.ttf" ), "hello" )
f = GafferUI.Frame( t )

window.setChild( GafferUI.GadgetWidget( f ) )

window.show()

GafferUI.EventLoop.start()
