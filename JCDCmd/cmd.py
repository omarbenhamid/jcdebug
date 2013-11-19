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

parser=argparse.ArgumentParser(prog='jcd')
subparsers = parser.add_subparsers()

class Command:
    def __init__(self, name, callable, args=[], opts=[], whatis="", doc="", argparser=None):
        """ 
        name the name of comamnd
        callabel the method to execute
        args : the list of names of argumetns to pass in
        opts : the list of names of available options
        whatis: one line summary of the command
        doc : a full  documentation of the command
        argparser : the argument parser : if set args/opts are ignored
        """
        self.name = name
        self.callable = callable
        if argparser != None: 
            self.parser = argparser
            return
        
        self.parser=subparsers.add_parser(name,help=whatis)
        for opt in opts:
            if len(opt) == 1: self.parser.add_argument('-'+opt)
            else: self.parser.add_argument('--'+opt.replace('_','-'))
        for arg in args:
            self.parser.add_argument(arg.replace('_','-'),type=str)
        self.parser.set_defaults(cmd=self)
        
        
        self.args=args
        self.opts = opts
        self.doc = doc
        self.whatis = whatis
    
    def invoke(self,args):
        self.callable(**args)

cmdindex={}

def usage(name):
    print "Usage: %s <command> [command arguments...]" % name
    print "Available commands:"
    for cmd in cmdindex.values():
        print " %s\t%s" % (cmd.name,cmd.whatis)

def printall(**kwargs):
    print kwargs

def registercommand(cmd):
    cmdindex[cmd.name]=cmd

if __name__ == '__main__':
    registercommand(Command('hello',printall,whatis='Say hallow',args=['message']))
    args = parser.parse_args()
    par=dict(vars(args))
    del par['cmd']
    args.cmd.invoke(par)
    
    