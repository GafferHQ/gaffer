import threading
import GafferUI

def threadFunction() :

	GafferUI.EventLoop.executeOnUIThread(
		GafferUI.EventLoop.mainEventLoop().stop
	)

thread = threading.Thread( target = threadFunction )
thread.start()

GafferUI.EventLoop.mainEventLoop().start()