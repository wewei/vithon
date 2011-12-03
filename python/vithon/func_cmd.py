import vim

##
# VIM Function wrapper
#

def _trans_key(key):
    '''
    @brief translate the key for VIM Dictionary object
    @param key the python value to be translated
    @return the string represents the VIM Dictionary key
    '''
    if type(key) == int:
        return str(key)
    elif type(key) == bool:
        return str(int(key))
    elif type(key) == str:
        return '\'%s\'' % key.encode('string_escape')
    else:
        raise TypeError('VIM Dictionary doesn\'t accept "%s" type as key.'
                        % str(type(key)))

def _trans_kvpare(kvpare):
    '''
    @brief translate the key-value-pare for VIM Dictionary object
    @param kvpare a tuple (key, value) or list [key, value]
    @return the string represents the VIM Dictionary key-value-pare
    '''
    return '%s: %s' % (_trans_key(kvpare[0]), _trans_value(kvpare[1]))

def _trans_value(value):
    '''
    @brief translate a python object into VIM value
    @param value the python object to be translated
    @return the string represents the VIM value
    '''
    if type(value) == int or type(value) == float:
        return str(value)
    elif type(value) == bool:
        return str(int(value))
    elif type(value) == str:
        return '\'%s\'' % value.encode('string_escape')
    elif type(value) == list or type(value) == tuple:
        return '[%s]' % ', '.join(map(_trans_value, value))
    elif type(value) == dict:
        return '{%s}' % ', '.join(map(_trans_kvpare, value.items()))
    elif type(value) == _vimfunc:
        return 'function(\'%s\')' % value.name
    else:
        raise TypeError('Cannot convert "%s" type value to VIM constant.'
                        % str(type(value)))

def _trans_params(params):
    '''
    @brief translate the function parameter list into VIM function
           parameter list
    @param params a tuple or list of all the parameters
    @return the string represents the parameter list
    '''
    return ', '.join(map(_trans_value, params))


class _vimfunc(object):
    '''
    @brief a python wrapper of the VIM function.
           It's a function object delegating to the VIM function. The `name'
           property represents the name of the VIM function.
           Objects of this type cannot be created outside this module. Even in
           this module, they can only be created by _vimfunc_co.__getattr__ in
           order to ensure each VIM function has only 1 wrapper.
    '''
    def __init__(self, name):
        self.__name = name

    @property
    def name(self):
        return self.__name

    def __call__(self, *params):
        return vim.eval('%s(%s)' % (self.__name, _trans_params(params)))

class _vimfunc_co(object):
    '''
    @brief collection of _vimfunc.
           It's a singleton. The VIM functions can be accessed by
           vithon.vimfuncs.func-name
    '''
    def __init__(self):
        self.__func_dict = {}

    def __getattr__(self, name):
        if self.__func_dict.has_key(name):
            return self.__func_dict[name]
        elif int(vim.eval('exists(\'*%s\')' % name)):
            func = _vimfunc(name)
            self.__func_dict[name] = func
            return func
        raise AttributeError(name)

vimfuncs = _vimfunc_co()

##
# Vithon callback functions
#

def _setupVithonFunc(vfunc):
    '''
    @brief setup the VIM version of VCF
    '''
    args = [
        'vithon:%s(...)' % vfunc.name,
        '\tpython ret = vithon.vithonfuncs.%s.vimcall()' % vfunc.name,
        '\tpython vim.command(\'let l:ret = %s\' % ret)',
        '\treturn l:ret',
        'endfunction']
    vimcmds.function('\n'.join(args))

class _vithonfunc(object):
    '''
    @brief Vithon Callback Function(VCF).
           A VCF named `foo' can be reached in VIM with `vithon:foo', and its
           `name' property is `foo'.
           The VCF named `foo' can be called from python with foo(). The 
           `vimcall' method should not be invoked by users. It's only be used
           for callback from VIM.
    '''
    def __init__(self, name, func):
        self.__name = name
        self.__func = func

    @property
    def name(self):
        return self.__name

    def __call__(self, *params):
        return self.__func(*params)

    def vimcall(self):
        '''
        @brief The callback entry from VIM. It retrieves the parameters and
               translates the return values.
        '''
        params = vim.eval('a:000')
        ret = self.__func(*params)
        if ret == None:
            ret = 0
        return _trans_value(ret)

class _vithonfunc_co(object):
    '''
    @brief collection of _vithonfunc. It's a singleton. The VCF can be accessed
           by vithon.vithonfuncs.func-name
    '''
    def __init__(self):
        self.__func_dict = {}

    def __getattr__(self, name):
        if self.__func_dict.has_key(name):
            return self.__func_dict[name]
        raise AttributeError(name)

    def new(self, name, func):
        '''
        @brief create a new Vithon Callback Function.
        @param name the name of the VCF
        @param func the python function behind the callback
        @return the _vithonfunc object
        '''
        if hasattr(self, name):
            return None
        vfunc = _vithonfunc(name, func)
        self.__func_dict[name] = vfunc
        _setupVithonFunc(vfunc)
        return vfunc
            
vithonfuncs = _vithonfunc_co()

def vim_function_(obj):
    '''
    @brief decorator converting a python function to a VCF
    '''
    if type(obj) == str:
        return lambda func: vithonfuncs.new(obj, func)
    elif callable(obj):
        return vithonfuncs.new(obj.func_name, obj)


##
# VIM command wrapper
#

def _trans_arg(arg):
    '''
    @brief translate a string to a VIM command argument
    @param arg the string to translate
    @return the argument
    '''
    if type(arg) == str:
        return arg.replace(' ', r'\ ')
    raise TypeError('Require "str" objects for command arguments')

def _trans_range(rang):
    '''
    @brief Translate a range into its string representation
    @param rang The range. It may be a single integer, or a tuple of 2
           integers, or the VIM native string range representation
    @return The string representation of the range
    '''
    if rang == None:
        return ''
    elif type(rang) == str:
        return rang
    elif type(rang) == int:
        return str(rang)
    elif type(rang) == tuple:
        if len(rang) == 2:
            return ','.join(map(_trans_range, rang))
    return ''

class _vimcmd(object):
    '''
    @brief The python wrapper of VIM command.
           Objects of this type should never be created by user, it can only
           be created by _vimcmd_co.__getattr__ in order to make sure each
           command has only one wrapper.
    '''
    def __init__(self, name):
        self.__name = name

    @property
    def name(self):
        return self.__name

    def __call__(self, args):
        cmd = ('%s%s %s' % (
                        _trans_range(None),
                        self.__name,
                        args))
#        print cmd
        vim.command(cmd)

class _vimcmd_co(object):
    '''
    @brief The collection of _vimcmd objects. VIM command named `foo' can be
           accessed by vithon.vimcmds.foo
    '''
    def __init__(self):
        self.__cmd_dict = {}

    def __getattr__(self, name):
        if self.__cmd_dict.has_key(name):
            return self.__cmd_dict[name]
        elif int(vim.eval('exists(\':%s\')' % name)) == 2:
            cmd = _vimcmd(name)
            self.__cmd_dict[name] = cmd
            return cmd
        raise AttributeError(name)
            
vimcmds = _vimcmd_co()

##
# Vithon command extension
#
def _setupVithonCmd(cmd):
    '''
    @brief setup the Vithon command extension
    @param cmd _vithoncmd object
    '''
    arglist = []
    if cmd.nargs != None:
        arglist.append('-nargs=%s' % cmd.nargs)
    if cmd.complete != None:
        if type(cmd.complete) == str:
            arglist.append('-complete=%s' % cmd.complete)
        elif type(cmd.complete) == _vithonfunc:
            arglist.append('-complete=customlist,vithon:%s' % cmd.complete.name)
        else:
            assert False, 'Unknown complete type'
    arglist.append(cmd.name)
    arglist.append('python vithon.vithoncmds.%s(\'<args>\')' % cmd.name)
    vimcmds.command(' '.join(arglist))

class _vithoncmd(object):
    '''
    @brief the Vithon command extension.
    '''
    def __init__(self, name, func, nargs, complete):
        self.__name = name
        self.__func = func
        self.__nargs = nargs
        self.__complete = complete

    @property
    def name(self):
        return self.__name

    @property
    def nargs(self):
        return self.__nargs

    @property
    def complete(self):
        return self.__complete

    def __call__(self, args):
        self.__func(args)
 
class _vithoncmd_co(object):
    def __init__(self):
        self.__cmd_dict = {}

    def __getattr__(self, name):
        if self.__cmd_dict.has_key(name):
            return self.__cmd_dict[name]
        raise AttributeError(name)

    def new(self, name, func, nargs, complete):
        '''
        @brief create a new Vithon command
        @param name the name of the Vithon command
        @param func the python function handling the command
        @param nargs specify the number of the command arguments
        @param complete specify the auto complete type
        @return the _vithoncmd object
        '''
        if hasattr(self, name):
            return None
        cmd = _vithoncmd(name, func, nargs, complete)
        self.__cmd_dict[name] = cmd
        _setupVithonCmd(cmd)
        return cmd

vithoncmds = _vithoncmd_co()

def vim_command_(name,
                nargs = None,
                complete = None):
    return lambda func: vithoncmds.new(name, func, nargs, complete)

