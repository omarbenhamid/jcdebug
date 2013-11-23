# Perparing you code
To prepare the code for JCD you must 
1. add the following special comment  as the first line of you javacard install command :
    public static void install(....) [
        //--JCD-INSTALL
        ... remaining install code
    }
2. add the following special comment as the first line of you processAPDU function :
    public static void processAPDU(APDU apdu) {
        //--JCD-PROCESS{apdu}
        ... remainging code here
    }

Notice that, for step 2, *apdu* is the name of the argument of processAPDU.

# Logs in JCD
Java Card standard does not support string. Thus, jcdebug uses a special comment line prefixed with *//!* for logs.
    byte[] myvar = ...:
    //! calling foo now with buffer value: {myvar}
    foo.callSomeMethod(myvar);
    //! callSomeMethod was successful
    ...
When *jcd gen* command is run, jcdebug converts each *//!* comment into a log line. Notice also that variables can be saved in log line using {bracket} syntax. For the moment, only one variable can be saved per log line.

# Working with jcd
The command also integrates the jcdebug runtime stub to allow log file manipulation in applet.
Notice that jcdebugs adds to you code new lines, these lines are surrownded by special comments starting with *//--JCDEBUG--* like:
    //@JCD-GEN-BEGIN ...
    some code
    //@JCD-GEN-END
Never delete manually these comments nore modify theire content. They are automatically managed by jcdebug. If you want to clean them use *jcd clean*

# Dumping binlog
Logs are stored in a special compact format on the card called bin log. Binlog can be dumped using the following APDI:
* CLA : the class as set in jcd.CLA setup parameter.
* INS : the instruction as set in jcd.INS setup parameter.
* P1/P2 : 0 / 0
* Lc : 0

The returned buffer can be converted back to human readable textual log using *jcd show*

# jcd Reference 
## jcd init :
 Create jcdebug workspace in current folder. jcd commands can be invoked from any subfolder of current folder to use this workspace setup.
## jcd setup [--<variable>=<value> ...]:
 Show / update current workspace setup variables. With no paramters this comment show current value of setup parameters. With <name>=<value> pairs, values of parameters are set.
 - *source-folder* absolute / relative path to where javacard source resides, defaults to 'src/'.
 - *debuginfo-path* absolute / retlatvie path to where debuginfo file shall reside, defaults to 'jcd.debuginfo'.
 - *log-size* number of bytes in log buffer, this can be computed this way : <desired line count>*3+<variable dump>
 - *cla* class byte in hex of APDU to invoke jcdebug runtime in applet. defaults ot D0.
 - *ins* instruction byte in hex of APDU to invoke jcdebug runtime in applet. defaults to FF.

## jcd gen
Modifies source code to inject jcdebug specific instrumentation. The generated instrumented code can then be compiled and loaded as JavaCard applet. To cancel instrumentation use *jcd clean*

## jcd clean
Removes any JCD instrumentation from code. It is advised to do a clean before any code modification to avoid bugs.

## jcd show [-o <outputpath>] [<binlogfile in hex>]
Converts hex log as read from card to textual human readable log. If no path to binlog file is set, bin log is expected in std in. If no *-o* option is set output is sent to std out.

## jcd restore
Restore source folder from backup. Current source folder is backup in backup folder.