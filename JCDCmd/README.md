# Logs in JCD
Java Card standard does not support string. Thus, jcdebug uses a special comment line prefixed with *//!* for logs.
    byte[] myvar = ...:
    //! calling foo now with buffer value: {myvar}
    foo.callSomeMethod(myvar);
    //! callSomeMethod was successful
    ...
When *jcd gen* command is run, jcdebug convers each *//!* comment into a log line. Notice also that variables can be saved in log line using {bracket} syntax. For the moment, only one variable can be saved per log line.
The command also integrates the jcdebug runtime stub to allow log file manipulation in applet.

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
## jcd setup [<varname>=<varval> ...]:
 Show / update current workspace setup variables. With no paramters this comment show current value of setup parameters. With <name>=<value> pairs, values of parameters are set.
 - *source.folder* absolute / relative path to where javacard source resides, defaults to 'src/'.
 - *output.folder* absolute / relative path to where to generate instrumented code, defaults to 'gen/'.
 - *debuginfo.file* absolute / retlatvie path to where debuginfo file shall reside, defaults to 'jcd.debuginfo'.
 - *logbuffer.size* number of bytes in log buffer, this can be computed this way : <desired line count>*3+<variable dump>
 - *jcd.CLA* class byte in hex of APDU to invoke jcdebug runtime in applet. defaults ot D0.
 - *jcd.INS* instruction byte in hex of APDU to invoke jcdebug runtime in applet. defaults to FF.

## jcd gen
Generated instrumented code in *output.folder*. The generated instrumented code can then be compiled and loaded as JavaCard applet.
 
## jcd show [-o <outputpath>] [<binlogfile in hex>]
Converts hex log as read from card to textual human readable log. If no path to binlog file is set, bin log is expected in std in. If no *-o* option is set output is sent to std out.