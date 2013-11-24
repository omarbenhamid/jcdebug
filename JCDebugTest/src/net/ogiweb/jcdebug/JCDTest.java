package net.ogiweb.jcdebug;

import java.util.Arrays;

import junit.framework.Assert;
import junit.framework.TestCase;

public class JCDTest extends TestCase {
	private static void printhex(byte[] x){
		for(int i=0; i < x.length; i++) {
			System.out.print(String.format("%02X ", new Byte[]{new Byte(x[i])}));
		}
	}
	public void testCycleOnBuffer() throws Exception {
		JCD.install((byte)0x00, (byte)0x00, (short)10, true);
		JCD.log((short)1);
		JCD.log((short)2,(byte)0xFF);
		JCD.log((short)3,(short)0xA33A);
		JCD.log((short)5);
		JCD.log((short)4,new byte[]{0x11,0x22,0x33});
		byte[] x = new byte[JCD.logTrace.available()];
		JCD.logTrace.dump(x, (short)0, JCD.logTrace.available());
		Assert.assertTrue(Arrays.equals(x, new byte[]{0x00 , 0x05 , 0x00 , 0x00 , 0x04 , 0x03 , 0x11 , 0x22 , 0x33} ));
		//printhex(x);
	}
	
	public void testNoCycleOnBuffer() throws Exception {
		JCD.install((byte)0x00, (byte)0x00, (short)100, true);
		JCD.log((short)1);
		JCD.log((short)2,(byte)0xFF);
		JCD.log((short)3,(short)0xA33A);
		JCD.log((short)5);
		JCD.log((short)4,new byte[]{0x11,0x22,0x33});
		byte[] x = new byte[JCD.logTrace.available()];
		JCD.logTrace.dump(x, (short)0, JCD.logTrace.available());
		Assert.assertTrue(Arrays.equals(x, new byte[]{0x00 , 0x01 , 0x00 , 0x00 , 0x02 , 0x01 , (byte)0xFF , 0x00 , 0x03 , 0x02 , (byte)0xA3 
				, 0x3A , 0x00 , 0x05 , 0x00 , 0x00 , 0x04 , 0x03 , 0x11 , 0x22 , 0x33 } ));
		//printhex(x);
	}
}
