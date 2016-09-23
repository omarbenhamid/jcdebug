package net.ogiweb.jcdebug;

import javacard.framework.APDU;
import javacard.framework.ISO7816;
import javacard.framework.JCSystem;

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
	public static class JCDStopException extends RuntimeException {}
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
					eidx=(short)((short)(eidx+1) % buffer.length);
					if(eidx==sidx) 
						dropOne();
			}
			
			/**
			 * Drop one data item.
			 * Return true if ok, false in case of error.
			 * @return
			 */
			void dropOne() {
				sidx=(short)((short)(sidx+1)% buffer.length);
			}
			
			byte pop() {
				if(eidx==sidx)  return 0; //Should have checked available
				eidx=(short)((short)(eidx-1)%buffer.length);
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
				for(short i = sidx; i != eidx && (wcount < length); i=(short)((short)(i+1)%buffer.length)) {
					out[(short)(offset+wcount)] = buffer[i];
					wcount++;
				}
				return wcount;
			}
	}
	
	static Rlog logTrace;
	
	private static byte CLA;
	private static byte INS;
	
	private static boolean swallowExceptions = false;
	private static boolean logAPDUs = false;
	
	private static short stopPoint = (short) 0;
	
	public static final short FIRSTUSERTAG = (short) 3;
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
				short nidx =(short)((short)(sidx+2)% buffer.length);
				byte len = buffer[nidx];
				sidx = (short)((short)(nidx+1+(short)(len&0x00FF))% buffer.length);
			}
		};
	}
	
	public static boolean processException(Throwable t) throws Throwable {
		if(this.swallowExceptions) return;
		else throw t;
	}
	 /** must add this line to applet :
	  * if(Debug.processAPDU(apdu)) return;
	  * @param apdu
	  * @return
	  */
	 public static boolean processAPDU(APDU apdu) {
	  byte[] apduBuffer = apdu.getBuffer();
	  if(apduBuffer[ISO7816.OFFSET_CLA] != CLA || apduBuffer[ISO7816.OFFSET_INS] != INS) {
		  if(logAPDUs) log((short)0, apduBuffer, (short)0, (short)5);
		  return false;
	  }
	  switch(apduBuffer[ISO7816.OFFSET_P1]) {
	  case 0:  //DUMP Log
		  apdu.setOutgoing();
		  short len = logTrace.available();
		  apdu.setOutgoingLength(len);
		  logTrace.dump(apdu.getBuffer(), (short)0, len);
		  apdu.sendBytes((short)0,len);
		  return true;
	  case 1: //APDU Log enable
		  logAPDUs = true;
		  return true;
	  case 2: //APDU Log disable
		  logAPDUs = false;
		  return true;
	  case 3: //Swallow exceptions enable
	      swallowExceptions = true;
		  return true;
	  case 4: //Swallow exceptions disable
		  swallowExceptions = false;
		  return true;
	  case 5: //Set StopPoint
		  stopPoint = (short) ( apduBuffer[ISO7816.OFFSET_P2] & 0xFF );
		  return true;
	  default:
	      return true;
	  }
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
		if((short)(offset + len) >(short) buffer.length)
			len = (short)(buffer.length - offset);
		if(len > 0x00FF) len = 0x00FF; //Max length
		if((short)(len + 3)>(short) logTrace.getSize()) { //TLV too big for logTrace buffer : shorten
			len = (short)(logTrace.getSize() - 3);
		}
		logTrace.push((byte)(len & 0xFF));
		for(short i=0 ; i<len; i++)
			logTrace.push(buffer[(short)(offset+i)]);
		
		if(tag >= FIRSTUSERTAG && tag == stopPoint) {
			log((short)2,tag);
			throw new JCDStopException();
		}
	}
	
	public static void log(short tag, byte[] buffer) {
		log(tag, buffer, (short)0, (short)buffer.length);
	}
}
