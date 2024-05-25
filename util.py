import datetime, traceback

currentTime = lambda: datetime.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S')
# The above lambda is equivalent to:
# def currentTime():
# 	return datetime.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S')

def onUpdateWrapper(callback):
	def _wrapper(data):
		try:
			return callback(data)
		except: # Exception as ex:
			try:
				print("Got an exception")
				print(traceback.format_exc())
				print("End of exception")
			except Exception as ex:
				print("Exception printing exception: '",ex,"'",sep='')

	return _wrapper
