import IECore
import Gaffer
import GafferUI
import gtk

## \todo Rejig this to remove all gtk specific code, and use only GafferUI classes instead

window = GafferUI.Window( "Panel test" )
window.gtkWidget().connect( "delete_event", gtk.main_quit )

window.setChild( GafferUI.CompoundEditor( Gaffer.ScriptNode() ) )

window.show()

GafferUI.EventLoop.start()
