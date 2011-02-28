import IECore
import Gaffer
import GafferUI
import IECore
import gtk
		
window = GafferUI.Window( title="Graph Editor test" )
window.gtkWidget().connect( "delete_event", gtk.main_quit )

s = Gaffer.ScriptNode()

e = GafferUI.GraphEditor( s )
window.setChild( e )

window.show()

GafferUI.EventLoop.start()
