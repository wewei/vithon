import vim
from func_cmd import vim_function_, vimfuncs, vimcmds
from buf_file import buffers

def _readerFuncName(ptclname):
	return 'ProtocolReader_%s' % ptclname

def _writerFuncName(ptclname):
	return 'ProtocolWriter_%s' % ptclname

class _protocol(object):
	def __init__(self, name):
		self.__name = name
		self.__reader = None
		self.__writer = None

	@property
	def name(self):
		return self.__name

	@property
	def reader(self):
		return self.__reader

	@reader.setter
	def reader(self, rdr):
		assert callable(rdr)
		if self.__reader == None:
			@vim_function_(_readerFuncName(self.name))
			def vimReader():
				bufNum = int(vimfuncs.expand('<abuf>'))
				buf = buffers[bufNum]
				url = vimfuncs.expand('<amatch>')
				buf[:] = self.reader(url)
				if not callable(self.writer):
					vimfuncs.setbufvar(bufNum, '&buftype', 'nowrite')
				else:
					vimfuncs.setbufvar(bufNum, '&buftype', 'acwrite')
			vimcmds.autocmd('BufReadCmd %s://* call vithon:%s()' %
						(self.name, _readerFuncName(self.name)))
		self.__reader = rdr

	@property
	def writer(self):
		return self.__writer

	@writer.setter
	def writer(self, wtr):
		assert callable(wtr)
		if self.__writer == None:
			@vim_function_(_writerFuncName(self.name))
			def vimWriter():
				bufNum = int(vimfuncs.expand('<abuf>'))
				buf = buffers[bufNum]
				url = vimfuncs.expand('<amatch>')
				self.writer(url, buf[:])
			vimcmds.autocmd('BufWriteCmd %s://* call vithon:%s()' %
						(self.name, _writerFuncName(self.name)))
		self.__writer = wtr

	def writer_(self, wtr):
		self.writer = wtr
		return self

def protocol_(reader):
	ptcl = _protocol(reader.func_name)
	ptcl.reader = reader
	return ptcl

