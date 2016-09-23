//--JCD-PROCESS-BEGIN{papdu}
//@JCD-GEN-BEGIN{1}
//Code managed by JCD-GEN, do not modify. Use "jcd clean" to remvoe it
if(JCD.processAPDU(papdu)) return;
try {
//@JCD-GEN-END

//--JCD-CATCH{PoppyException}
//@JCD-GEN-BEGIN{2}
//Code managed by JCD-GEN, do not modify. Use "jcd clean" to remvoe it
}catch(PoppyException jcdException){ JCD.processException(jcdException); JCD.log(3);
//@JCD-GEN-END
//--JCD-PROCESS-END
//@JCD-GEN-BEGIN{2}
//Code managed by JCD-GEN, do not modify. Use "jcd clean" to remvoe it
}catch(JCD.JCDStopException jcdException){return;}
catch(Throwable jcdException){JCD.processException(jcdException);}
//@JCD-GEN-END

//! I log something
//@JCD-GEN-BEGIN{1}
//Code managed by JCD-GEN, do not modify. Use "jcd clean" to remvoe it
JCD.log((short)4);
//@JCD-GEN-END

//! I log something else
//@JCD-GEN-BEGIN{1}
//Code managed by JCD-GEN, do not modify. Use "jcd clean" to remvoe it
JCD.log((short)5);
//@JCD-GEN-END

//! Haha again and again
//@JCD-GEN-BEGIN{1}
//Code managed by JCD-GEN, do not modify. Use "jcd clean" to remvoe it
JCD.log((short)6);
//@JCD-GEN-END


//--JCD-INSTALL
//@JCD-GEN-BEGIN{1}
//Code managed by JCD-GEN, do not modify. Use "jcd clean" to remvoe it
JCD.install((byte)0xD0,(byte)0x66,(short)200,true);
//@JCD-GEN-END
