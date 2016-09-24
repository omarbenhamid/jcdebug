import cmd
import os, sys, tempfile, shutil, re, json
from ConfigParser import ConfigParser
from datetime import datetime

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
    return _getconfig().get(section,name)
    

@cmd.subcmd
def init():
    """ Initialize JCD workspace with default setup"""
    if os.path.exists('.jcdworkspace'):
        raise Exception, 'A workspace already exists here'
        
    cp = ConfigParser()
    cp.add_section('main')
    cp.set('main','source-folder','src')
    cp.set('main','debuginfo-path','jcd.debuginfo')
    cp.set('main','persist-log','true')
    cp.set('main','log-size','200')
    cp.set('main','cla','D0')
    cp.set('main','ins','66')
    cp.write(open('.jcdworkspace','w'))
    return """Workspace initialized.
You can use 'jcd gen' now to enable Java Card Logging and Debugging on your applet. The current source folder is supposed to be :
%s
If this is not right, use "jcd setup --source-folder=..." to set it somewhere else. 
""" % os.path.join(_getwsroot(),'src')


@cmd.subcmd
def setup(source_folder=None, backup_folder=None, debuginfo_path=None,log_size=None,cla=None,ins=None, persist_log=cmd.ArgSpec(choices=['yes','no','true','false'],help="When set to no, log buffer is transient and cleard on reset. This can be useful as transient buffer is not cleared in case of transactional rollback.")):
    """ Show / modify configuration of jcdebug """
    cfg = _getconfig()
    dirty = {'val':False}
    
    def set(name,value):
        if value == None: return
        cfg.set('main',name,value)
        print '%s updated' % name
        dirty['val']=True
        
    set('source-folder',source_folder)
    set('debuginfo-path',debuginfo_path)
    set('log-size',log_size)
    
    if persist_log == 'yes': persist_log = 'true'
    if persist_log == 'no': persist_log = 'false'
    
    set('persist-log',persist_log)
    set('cla',cla)
    set('ins',ins)
    if dirty['val']: cfg.write(open(os.path.join(_getwsroot(),'.jcdworkspace'),'w'))
    print 'Current config :'
    cfg.write(sys.stdout)
    print "You can use 'jcd gen' now to enable/refresh Java Card Logging and Debugging on your applet."

def _recurseforjava(d):
    for f in os.listdir(d):
        prop = os.path.join(d,f)
        if os.path.isdir(prop): 
            for i in _recurseforjava(prop): yield i
        if(prop.lower().endswith('.java')): 
            yield prop
    
class Backup:
    def __init__(self, dir = None):
        self.command = sys.argv[:]
        self.time = datetime.now()
        if dir==None:
            self.bkpdir = tempfile.mkdtemp('.jcd-bkp')
            open(os.path.join(self.bkpdir,'bkp.info'),'w').close() 
        else: self.bkpdir=dir
    
    def rollback(self):
        #recover previously backuped files
        shutil.rmtree(self.bkpdir)
    
    def commit(self):
        if os.path.exists('.jcd-bkp'):
            shutil.rmtree('.jcd-bkp')
        shutil.move(self.bkpdir, '.jcd-bkp')
        out=open('.jcd-bkp/manifest','wb')
        json.dump({'command':' '.join(self.command), 'time': str(self.time)},out)
        out.close()
    
    def stage(self,rpath):
        """ Stage the given file and return path to temporary copy """
        path = os.path.abspath(os.path.join(_getparam('source-folder'), rpath))
        tgt=os.path.join(self.bkpdir,rpath)
        if os.path.exists(tgt): return #already staged
        tgtd = os.path.dirname(tgt)
        if not os.path.exists(tgtd): os.makedirs(tgtd)
        shutil.copy(path,tgt)
        return tgt
        
    def restore(self, rpath):
        path = os.path.abspath(os.path.join(_getparam('source-folder'), rpath))
        tgt=os.path.join(self.bkpdir,rpath)
        if not os.path.exists(tgt): raise Exception, 'Trying to recover not staged file'
        if os.path.exists(path): os.remove(path)
        if not os.path.exists(os.path.dirname(path)): os.makedirs(os.path.dirname(path))
        shutil.copy(tgt,path)
        
    def unstage(self, rpath):
        path = os.path.abspath(os.path.join(_getparam('source-folder'), rpath))
        tgt=os.path.join(self.bkpdir,rpath)
        os.remove(tgt)
        tgtd = os.path.dirname(tgt)
        if len(os.listdir(tgtd)) == 0: os.removedirs(tgtd)
        
    def liststaged(self):
        for file in _recurseforjava(self.bkpdir): yield os.path.relpath(file,self.bkpdir)

def _writecode(out,sourcelines):
    out.write('//@JCD-GEN-BEGIN{%d}\n'%sourcelines.count(';'))
    out.write('//Code managed by JCD-GEN, do not modify. Use "jcd clean" to remvoe it\n')
    out.write(sourcelines)
    out.write('\n//@JCD-GEN-END\n');

strtab=['APDU RECEIVED','EXCEPTION RAISED','STOP POINT HIT']
builtinstrcount=len(strtab)

def _registerstring(strval):
    try:
        return strtab.index(strval.strip())
    except:
        strtab.append(strval.strip())
        return len(strtab)-1

def _getstring(idx):
    if idx >= len(strtab): raise Exception, "Unrecognized log tag %04X, (are you using the right debuginfo file ?)" % idx
    return strtab[idx]

def _savedebuginfo():
    di = os.path.join(_getwsroot(),_getparam('debuginfo-path'))
    didir = os.path.dirname(di)
    if not os.path.exists(didir): os.makedirs(didir)
    out = open(di,'w')
    json.dump(strtab, out)
    out.close()
    
def _loaddebuginfo(di):
    global strtab
    if not os.path.exists(di): raise Exception, "No such debuginfo file %s, use -d flag to point to the right debug info file." % di
    inf=open(di,'rb')
    strtab = json.load(inf)
    inf.close()
    

class Macro:
    def __init__(self, name, regex,template):
        """ Tempalte syntax is 
            %<n>% raw replace by value of group <n>
            $<n>$ register value of group <n> to string table and insert the index in decimal
            {<opt-name>} lookup config parameter <opt-name> and inline value here"""
        self.re = re.compile(regex)
        self.template=template
        self.name = name
        
    def gencode(self, line, srcfile, srcline):
        m = self.re.match(line)
        if m==None: return
        ret = self.template
        for g,v in enumerate(m.groups()):
            ret = ret.replace('%'+ str(g+1) + '%',v)
            if ('$'+ str(g+1) +'$') in ret:
                code = _registerstring('%s (%s:%d)' % (v, srcfile, srcline) )
                ret = ret.replace('$'+ str(g+1) + '$', str(code))
        conf = _getconfig()
        for opt in conf.options('main'):
            ret = ret.replace('{%s}'%opt, conf.get('main',opt))
        return ret

macros = [
    Macro('log_w_param','\\s*//!([^{]*)\\{([^}]*)\\}\\s*$','JCD.log((short)$1$,%2%);'),
    Macro('log','\\s*//!(.*)$','JCD.log((short)$1$);'),
    Macro('process-begin','\\s*//--JCD-PROCESS-BEGIN{([^}]*)}\\s*$','if(JCD.processAPDU(%1%)) return;\ntry {'),
    Macro('process-catch','\\s*//--JCD-CATCH{([^}]*)}\\s*$','}catch(%1% jcdException){ JCD.processException(jcdException); JCD.log($1$);'),
    Macro('process-end','\\s*//--JCD-PROCESS-END\\s*$','}catch(JCD.JCDStopException jcdException){return;}catch(javacard.framework.ISOException jcdException){JCD.processISOException(jcdException);}\ncatch(RuntimeException jcdException){JCD.processException(jcdException);}'),
    Macro('install','\\s*//--JCD-INSTALL\\s*$','JCD.install((byte)0x{cla},(byte)0x{ins},(short){log-size},{persist-log});')
    ]
    
def applymacros(line, srcfile, srcline):
    """ return a tuple : name, replacement code"""
    for macro in macros:
        code = macro.gencode(line, srcfile, srcline)
        if code != None: return macro.name, code
    return None,None

@cmd.subcmd
def gen():
    """ Instrument code in source-folder with JCD """
    os.chdir(_getwsroot())
    
    backup = Backup()
    try:
        filesfound=False
        processapduok=False
        processapduendok=False
        installok=False
        for jfile in _recurseforjava(_getparam('source-folder')):
            rpath = os.path.relpath(os.path.abspath(jfile),os.path.abspath(_getparam('source-folder')))
            filesfound=True
            staged=backup.stage(rpath)
            inf = open(staged,'r')
            out = open(jfile,'w')
            
            changed=False
            linenum = 0
            for line in inf:
                skiped = _skipgenerated(line,inf)
                if skiped != 0:
                    changed = True
                    continue
                linenum += 1
                out.write(line)
                macro, code = applymacros(line, rpath, linenum)
                if macro != None: 
                    _writecode(out,code)
                    changed=True
                if macro == 'process-begin': processapduok=True
                elif macro == 'process-end': processapduendok=True
                elif macro == 'install': installok=True
                
            out.close()
            inf.close()
            if not changed:
                backup.restore(rpath)
                backup.unstage(rpath)
            
                
            
        if not filesfound:
            raise Exception, 'No source java file found in source folder %s \nHINT: use "jcd setup --source-folder <path>" to fix the path if it is wrong.' % _getparam('source-folder')
        if not processapduok:
            raise Exception, 'You need to add "//--JCD-PROCESS-BEGIN{apdu}" as the first line of your processAPDU() function.'
        if not processapduendok:
            raise Exception, 'You need to add "//--JCD-PROCESS-END" as the last line of your processAPDU() function.'
        if not installok:
            raise Exception, 'You need to add "//--JCD-INSTALL" as the first line of you install function.'
        
        _savedebuginfo()
        backup.commit()
    except:
        backup.rollback()
        raise    
    print "Java Card Logging and Debugging successfully enabled on your applet."
    print """
You can now use the following APDUs with your applet :
  - %(cla)s %(ins)s 01 00 00 : to enable APDU logging. This will log all received APDUs. (disabled by default)
  - %(cla)s %(ins)s 02 00 00 : to disable APDU logging.
  - %(cla)s %(ins)s 03 00 00 : Enable Exception Swallow. When an exception is thrown, the memory transaction is rolled back and even the JCDebug logs are rolled back. 
                This APDU enables "swallowing" of all exceptions by JCDebug to avoid this. 
                NOTICE: that this also keeps the state of memory in an uncertain state when an error occurs.
  - %(cla)s %(ins)s 04 00 00 : Disable exception swallowing.
  - %(cla)s %(ins)s 05 XX 00 : Set stop point where XX is the stop point id. When this point of code is reached the program returns. 
                The following stop points are available : 
                      %(stopPoints)s
  - %(cla)s %(ins)s 05 00 00 : Disable stop point.
  - %(cla)s %(ins)s 00 00 00 : to dump the log. The returned hexacimal buffer should be interpreted using 'jcd show' command.

You can customize the class / instruction of these APDUs using 'jcd setup --cla=... --ins=...'.
You can disable Javacard Logging and Debugging with 'jcd clean'
""" % {'cla':_getparam('cla'), 'ins':_getparam('ins'),
       'stopPoints': '\n                      '.join('%02x : %s' % (i+builtinstrcount, v) for i,v in enumerate(strtab[builtinstrcount:]))
    }
    
    
@cmd.subcmd
def restore(f=cmd.ArgSpec(action="store_true",help="Force restoring without confirmation")):
    """ Restore source-folder modified files from automatic backup """
    os.chdir(_getwsroot())
    if not os.path.exists('.jcd-bkp'): raise Exception, 'No current backup'
    inf=open('.jcd-bkp/manifest','rb')
    info=json.load(inf)
    inf.close()
    print "Restoring the follwoing backup:\n Date: %s\n Command: %s\n" % (info['time'],info['command'])
    print "The following files will be restored"
    bkp = Backup(".jcd-bkp")
    nbkp = Backup()
    for file in bkp.liststaged() :
        print " %s" % file
    print "(If the goal is to clean JCD generated codes, you can use 'jcd clean' instead.)"
    if not f:
        print "Type enter to contiue or Ctrl-C to cancel (user -f to avoid this message) ..."
        try:
            raw_input()
        except KeyboardInterrupt:
            raise Exception, "Recovery canceled."
    
    for file in bkp.liststaged():
        nbkp.stage(file)
        bkp.restore(file)
    
    nbkp.commit()
    
    return "Files restored. You can recover your previous version running 'jcd restore' again"
BEGIN_RE = re.compile('\\s*//@JCD-GEN-BEGIN\\{([0-9]*)\\}\\s*$')
END_RE = re.compile('\\s*//@JCD-GEN-END\\s*$')

def _skipgenerated(line, inf):
    m = BEGIN_RE.match(line)
    if m == None: return 0
    num=1
    colcount=int(m.group(1))
    for gline in inf: #skip unti end comment
        num+=1
        colcount=colcount-gline.count(';')
        if END_RE.match(gline) != None: break
    if colcount != 0: raise Exception, "JCD generated code seems to have been altered"
    return num
@cmd.subcmd
def clean():
    """ Clean JCD generated code from source"""
    os.chdir(_getwsroot())
    bkp = Backup()
    try:
        for jfile in _recurseforjava(_getparam('source-folder')):
            rpath = os.path.relpath(os.path.abspath(jfile),os.path.abspath(_getparam('source-folder')))
            staged=bkp.stage(rpath)
            inf = open(staged,'r')
            out = open(jfile,'w')
            changed=False
            
            num=0
            for line in inf:
                num+=1
                try: skiped = _skipgenerated(line,inf)
                except Exception, msg:
                    raise Exception, "%s : %d : %s" % (rpath,num,msg)
                if skiped == 0: out.write(line)
                else: 
                    changed=True
                    num += skiped - 1
            inf.close()
            out.close()
            if not changed:
                bkp.restore(rpath)
                bkp.unstage(rpath)
        bkp.commit()
        return "Code cleaned from JCD generated code.\nYou can use 'jcd restore' if you need to recover the previous version."
    except:
        bkp.rollback()
        raise

def _nexthex(inf):
    ret = 'z'
    while ret not in '0123456789ABCDEFabcdef':
        ret = inf.read(1)
        if ret == '': raise Exception, "End of file"
    return ret

def _nexthexs(inf,sz):
    ret = ''
    for i in range(0,sz):
        ret += _nexthex(inf)
    return ret

def _formathex(hexstr):
    if (len(hexstr) % 2 != 0): return hexstr
    ret=''
    for i in range(0,len(hexstr),2):
        ret = ret + hexstr[i:i+2] + ' '
    return ret.rstrip()

@cmd.subcmd
def show(d=cmd.ArgSpec(help="Path to debug info file, by default, path from setup is used.")):
    """ Interpret binary log (data of dump instruction) """
    if d == None: d = os.path.join(_getwsroot(),_getparam('debuginfo-path'))
    _loaddebuginfo(d)
    inf = sys.stdin
    #read byte by byte:
    while True:
        tag = int(_nexthexs(inf,4),16)
        datalen = int(_nexthexs(inf,2),16)
        print "%04x: %s {%s}" % (tag,_getstring(tag), _formathex(_nexthexs(inf,datalen*2)) if datalen != 0 else 'no data')
    #each 4 hexa bytes read interpret the string, read the length byte and dump it.

if __name__ == '__main__':
    cmd.run()