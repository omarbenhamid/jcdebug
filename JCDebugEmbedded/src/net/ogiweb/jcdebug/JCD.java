package net.ogiweb.jcdebug;

import javacard.framework.APDU;
import javacard.framework.ISO7816;
import javacard.framework.JCSystem;
import javacard.framework.Util;

/**
 * .install() must be called to activate loggin (usually at applet install).
 * if(JCD.processAPDU(apdu)) return; must be added at processAPDU method beginning.
 * 
 * CLA : class defined during install
 * INS: instruction assigned during install
 * P1 : requested dump : 00 means log trace 01 means stacktrace
 * P2 : RFU
 * @author bewigo
 *
 */
public class JCD {
	/**
	 * Rotating log class
	 */
	static class Rlog {
			byte[] buffer;
			short sidx=0; //Points first item
			short eidx=0; //Points after last 

			//FIXME: non persistent version
			Rlog(short sz, boolean persistant) {
				buffer=persistant ? new byte[sz] : JCSystem.makeTransientByteArray(sz, JCSystem.CLEAR_ON_RESET);
			}
			
			public short getSize() {
				return (short)buffer.length;
			}
			
			void push(byte data) {
					buffer[eidx]=data;
					eidx=(short)((eidx+1) % buffer.length);
					if(eidx==sidx) 
						dropOne();
			}
			
			/**
			 * Drop one data item.
			 * Return true if ok, false in case of error.
			 * @return
			 */
			void dropOne() {
				sidx=(short)((sidx+1)% buffer.length);
			}
			
			byte pop() {
				if(eidx==sidx)  return 0; //Should have checked available
				eidx=(short)((eidx-1)%buffer.length);
				byte ret = buffer[eidx];
				return ret;
			}

			/**
			 * Return number of bytes available
			 * @return
			 */
			short available(){
				short ret = (short)(eidx-sidx);
				if(ret < 0) return (short)(ret + buffer.length);
				return ret;
			}
			
			short dump(byte[] out, short offset, short length) {
				short wcount = (short)0;
				for(short i = sidx; i != eidx && (wcount < length); i=(short)((i+1)%buffer.length)) {
					out[offset+wcount] = buffer[i];
					wcount++;
				}
				return wcount;
			}
	}
	
	static Rlog logTrace;
	
	private static byte CLA;
	private static byte INS;
	
	/**
	 * MUST Be called once to enable debug
	 * @param CLA
	 * @param INS
	 * @param stacktraceDepth
	 * @param logsize
	 * @param persist
	 */
	public static void install(byte CLA, byte INS, short logsize, boolean persist) {
		JCD.CLA = CLA;
		JCD.INS = INS;
		if(logsize != 0) logTrace = new Rlog(logsize, persist){
			void dropOne() {
				//Skip a full tlv
				//Skipt tag
				short nidx =(short)((sidx+2)% buffer.length);
				byte len = buffer[nidx];
				sidx = (short)((nidx+1+(short)(len&0x00FF))% buffer.length);
			}
		};
	}
	
	 /** must add this line to applet :
	  * if(Debug.processAPDU(apdu)) return;
	  * @param apdu
	  * @return
	  */
	 public static boolean processAPDU(APDU apdu) {
	  byte[] apduBuffer = apdu.getBuffer();
	  if(apduBuffer[ISO7816.OFFSET_CLA] != CLA || apduBuffer[ISO7816.OFFSET_INS] != INS) return false;
	  apdu.setOutgoing();
	  short len = logTrace.available();
	  apdu.setOutgoingLength(len);
	  logTrace.dump(apdu.getBuffer(), (short)0, len);
	  apdu.sendBytes((short)0,len);
	  return true;
	}
	
	public static void log(short tag) {
		if(logTrace == null) return;
		logTrace.push((byte)((tag >> 8) & (0xFF)));
		logTrace.push((byte)((tag) & (0xFF)));
		logTrace.push((byte)0);
	}
	
	
	public static void log(short tag, byte data) {
		if(logTrace == null) return;
		logTrace.push((byte)((tag >> 8) & (0xFF)));
		logTrace.push((byte)((tag) & (0xFF)));
		logTrace.push((byte)1);
		logTrace.push(data);
	}
	
	public static  void log(short tag, short data) {
		if(logTrace == null) return;
		logTrace.push((byte)((tag >> 8) & (0xFF)));
		logTrace.push((byte)((tag) & (0xFF)));
		logTrace.push((byte)2);
		logTrace.push((byte)((data >> 8) & (0xFF)));
		logTrace.push((byte)((data) & (0xFF)));
	}
	/**
	 * Data length is a byte thus size cannot be more than 256
	 * @param tag
	 * @param len
	 */
	public static void log(short tag, byte[] buffer, short offset, short len) {
		if(logTrace == null) return;
		logTrace.push((byte)((tag >> 8) & (0xFF)));
		logTrace.push((byte)((tag) & (0xFF)));
		if((offset + len) > buffer.length)
			len = (short)(buffer.length - offset);
		if(len > 0x00FF) len = 0x00FF; //Max length
		if((len + 3)> logTrace.getSize()) { //TLV too big for logTrace buffer : shorten
			len = (short)(logTrace.getSize() - 3);
		}
		logTrace.push((byte)(len & 0xFF));
		for(int i=0 ; i<len; i++)
			logTrace.push(buffer[offset+i]);
	}
	
	public static void log(short tag, byte[] buffer) {
		log(tag, buffer, (short)0, (short)buffer.length);
	}
}
