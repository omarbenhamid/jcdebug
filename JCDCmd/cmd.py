"""
cmd is a framework to manage command lines.

cmd.py some-command --long-arg=value1 -s <othervalue> <nooptvalue1> <nooptvalue2>

to a call to :
some_command('nooptvalue1','nooptvalue2',long_arg='value1',s='othervalue')


to do this this function should be registerd :

@cmd.reg
some_command(_arg1,_arg2,long_arg,s='defaultvalue', *args):
 "Command docuemntation"
 

"""
import argparse
import sys
import inspect

parser=argparse.ArgumentParser(prog='jcd')
subparsers = parser.add_subparsers()

def _name2opt(name):
    if name.startswith('-'): return name
    if len(name) == 1: return '-%s'% name
    return '--%s' % name

class Command:
    def __init__(self, name, callable, args=[], opts=[], help="", argparser=None):
        """ 
        name the name of comamnd
        callabel the method to execute
        args : the list of arguments to pass in. Each item is either :
            - A simple string
            - A dictionnary with ArgumentParser.add_argument() kw params. A special entry "name" contains the name of the argument
        opts : the list of names of available options. Each item is either :
            - A simple string
            - A dictionnary with ArgumentParser.add_argument() kw params. A special entry "name" contains the name of the option (with or without -)
        help: Quick help of the command
        argparser : the argument parser : if set args/opts are ignored
        """
        self.name = name
        self.callable = callable
        
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
        self.callable(**args)



def printall(**kwargs):
    print kwargs

def reg(f):
    Command(f.__name__,f,help=f.__doc__,
        args=list(arg.lstrip('_') for arg in inspect.getargspec(f).args if arg.startswith('_')),
        opts=list(arg.lstrip('_') for arg in inspect.getargspec(f).args if not arg.startswith('_')) )
    return f

@reg
def setup(_p1,_p2,truc,truac):
    pass
if __name__ == '__main__':
    Command('hello',printall,help='Say hallow',args=['message',{'name':'label','help':'The display label of my stuff'}])
    Command('bye',printall,help='Say bye',args=['message'], opts=['s','--k',{'name':'smook','help':'do some spoopic stuff'}])
    args = parser.parse_args()
    par=dict(vars(args))
    del par['cmd']
    args.cmd.invoke(par)
    
    