package net.ogiweb.jcdebug;

import java.util.Arrays;

import junit.framework.Assert;
import junit.framework.TestCase;

public class JCDTest extends TestCase {
	public void testCycleOnBuffer() throws Exception {
		JCD.install((byte)0x00, (byte)0x00, (short)3, (short)10, true);
		JCD.log((short)1);
		JCD.log((short)2,(byte)0xFF);
		JCD.log((short)3,(short)0xA33A);
		JCD.log((short)5);
		JCD.log((short)4,new byte[]{0x11,0x22,0x33});
		byte[] x = new byte[1000];
		JCD.logTrace.dump(x, (short)0, JCD.logTrace.available());
		System.out.println(JCD.logTrace.available());
		for(int i=0; i < 10; i++) {
			System.out.print(String.format("%02X ", new Byte[]{new Byte(x[i])}));
		}
		System.out.println();
	}
}
