import cmd
import os, sys
from ConfigParser import ConfigParser

def _getwsroot():
    curdir = os.path.abspath(os.getcwd())
    while not os.path.exists(os.path.join(curdir,'.jcdworkspace')):
        if os.path.ismount(curdir): raise Exception, 'Not in a JCD workspace, (have you run "jcd init" ?)'
        curdir = os.path.dirname(curdir)
    return curdir

_config=None
def _getconfig():
    global _config
    if _config == None:
        _config = ConfigParser()
        _config.read([os.path.join(_getwsroot(),'.jcdworkspace')])
    return _config
    
def _getparam(name, section='main'):
    return _getconfig().get(section,'name')
    

@cmd.subcmd 
def init():
    """ Initialize JCD workspace with default setup"""
    if os.path.exists('.jcdworkspace'):
        raise Exception, 'Workspace already exists'
    cp = ConfigParser()
    cp.add_section('main')
    cp.set('main','source-folder','src')
    cp.set('main','backup-folder','old')
    cp.set('main','debuginfo-path','jcd.debuginfo')
    cp.set('main','log-size','0')
    cp.set('main','cla','D6')
    cp.set('main','ins','77')
    cp.write(open('.jcdworkspace','w'))

@cmd.subcmd
def setup(source_folder=None, backup_folder=None, debuginfo_path=None,log_size=None,cla=None,ins=None):
    """ Show / modify configuration of jcdebug """
    cfg = _getconfig()
    dirty = {'val':False}
    
    def set(name,value):
        if value == None: return
        cfg.set('main',name,value)
        dirty['val']=True
        
    set('source-folder',source_folder)
    set('backup-folder',backup_folder)
    set('debuginfo-path',debuginfo_path)
    set('log-size',log_size)
    set('cla',cla)
    set('ins',ins)
    if dirty['val']: cfg.write(open(os.path.join(_getwsroot(),'.jcdworkspace'),'w'))
    cfg.write(sys.stdout)


if __name__ == '__main__':
    cmd.run()