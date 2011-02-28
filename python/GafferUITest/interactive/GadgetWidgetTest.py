import IECore
import Gaffer
import GafferUI
import IECore
import gtk
		
window = GafferUI.Window( title="GadgetWidget test" )
window.gtkWidget().connect( "delete_event", gtk.main_quit )

n = Gaffer.Node()
s = GafferUI.GadgetWidget( GafferUI.NodeGadget( n ) )
window.setChild( s )

window.show()

GafferUI.EventLoop.start()
