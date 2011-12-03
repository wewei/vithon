import vim

class _buf_co(object):
	def __getitem__(self, key):
		if type(key) == int:
			for buf in vim.buffers:
				if buf.number == key:
					return buf
		raise KeyError(key)

buffers = _buf_co()

