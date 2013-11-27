"""
cmd is a framework to manage command lines.

cmd.py some-command --long-arg=value1 -s <othervalue> <nooptvalue1> <nooptvalue2>

to a call to :
some_command('nooptvalue1','nooptvalue2',long_arg='value1',s='othervalue')


to do this this function should be registerd :

@cmd.subcmd
def some_command(_arg1,_arg2,long_arg,s=ArgSpec(help="help")):
    "Command docuemntation"
    ...
 
   
....

if __name__ == '__main__':
    cmd.run()


"""
import argparse
import sys
import inspect
from collections import namedtuple

parser=argparse.ArgumentParser(prog='jcd')
subparsers = parser.add_subparsers()

def _name2opt(name):
    if name.startswith('-'): return name
    if len(name) == 1: return '-%s'% name
    return '--%s' % name

class Command:
    def __init__(self, name, callable, args=[], opts=[], mapping={}, help="", argparser=None):
        """ 
        name the name of comamnd
        callabel the method to execute
        args : the list of arguments to pass in. Each item is either :
            - A simple string
            - A dictionnary with ArgumentParser.add_argument() kw params. A special entry "name" contains the name of the argument
        opts : the list of names of available options. Each item is either :
            - A simple string
            - A dictionnary with ArgumentParser.add_argument() kw params. A special entry "name" contains the name of the option (with or without -)
        mapping: maps is a dict between argument names as set in args and opts, and target names in callable. mapping[<cmdlinename>]=<callablename>
        help: Quick help of the command
        
        argparser : the argument parser : if set args/opts are ignored
        """
        self.name = name
        self.callable = callable
        self.mapping = mapping
        self.parser=subparsers.add_parser(name,help=help)
        for opt in opts:
            if not isinstance(opt,str): #not a string : expecting kv
                nopt = dict(opt)
                del nopt['name']
                self.parser.add_argument(_name2opt(opt['name']), **nopt)
            else:
                self.parser.add_argument(_name2opt(opt))
        for arg in args:
            if not isinstance(arg,str): #not a string : expecting kv
                nopt = dict(arg)
                del nopt['name']
                self.parser.add_argument(arg['name'], **nopt)
            else:
                self.parser.add_argument(arg,type=str)
        self.parser.set_defaults(cmd=self)
        
    
    def invoke(self,args):
        try:
            ret = self.callable(**dict((self.mapping[k] if k in self.mapping else k, v) for k,v in args.items()))
            if ret != None: print ret
        except Exception, msg:
            print "** FAILED"
            print msg
            sys.exit(1)

class ArgSpec:
    """ 
This class contains argument specification of acommand line argument.
It is expected to pass the same arguments of argparse.ArgumentParser.add_argument in key=value syntax.
The name of the argument is the argument 'name'
    """
    ALLOWED=['name', 'action', 'nargs', 'const', 'default', 'type', 'choices', 'required', 'help', 'metavar', 'dest']
    
    def __init__(self, **kwargs):
        for k in kwargs.keys():
            if k not in ArgSpec.ALLOWED: raise Exception, ("Unknown parameter for argspec of command : %s" % k)
        self.__dict__.update(kwargs)
    
    def asdict(self):
        return self.__dict__

def run():
    args = parser.parse_args()
    par=dict(vars(args))
    del par['cmd']
    args.cmd.invoke(par)

def subcmd(f):
    """ 
        use as a function or decorator to register this function asa subcommand
        @cmd.subcmd
        def function(_parg1,_parg2,...,narg1,narg2[=ArgSpec(..)]):
            ...
            if ok : return "status msg"
            else raise Exception, "Some error message"
        arguments starting with _ are positionnal and others are options (prefixed with '-' in commandlin)
        
    """
    spec = inspect.getargspec(f)
    #initi with list (<isargument>,<dictcnfig>)
    args = list((arg.startswith('_'),{'name':arg.lstrip('_').replace('_','-')}) for arg in spec.args)
    if spec.defaults != None:
        for idx,item in enumerate(spec.defaults):
            #update dictcnfig part of the tuple
            if item != None: args[len(args)-len(spec.defaults)+idx][1].update(item.asdict())
    
    Command(f.__name__,f,help=f.__doc__,
        args=list(arg for isarg,arg in args if isarg),
        opts=list(arg for isarg,arg in args if not isarg),
        mapping = dict((args[i][1]['name'],spec.args[i]) for i in range(0,len(args)))
        )
    return f



if __name__ == '__main__':
    def printall(**kwargs):
        print kwargs

    Command('hello',printall,help='Say hallow',args=['message',{'name':'label','help':'The display label of my stuff'}])
    Command('bye',printall,help='Say bye',args=['message'], opts=['s','--k',{'name':'smook','help':'do some spoopic stuff'}])
    run()
    
    