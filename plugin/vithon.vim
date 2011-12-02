if !has('python')
	echo 'Error: require vim build with +python'
	finish
endif

if exists('*VithonInit')
	finish
endif

au BufNewFile,BufRead ~/.vithonrc set syntax=python

function VithonInit()
python<<ENDPY
import sys
import os
import vim

sys.path.append(os.environ['HOME'] + '/.vim/python')
import vithon
ENDPY
	if filereadable($HOME.'/.vithonrc')
		pyfile $HOME/.vithonrc
	endif
endfunction

call VithonInit()
