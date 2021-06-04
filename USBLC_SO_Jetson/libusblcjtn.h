#ifndef LIBUSBLCJTN_H
#define LIBUSBLCJTN_H

quint16 ls_libversion();
void ls_initialize(qint32 pipesize, qint32 packetlength);
quint16 ls_enumdevices();
quint16 ls_getmcu1version(qint32 index);
char* ls_getvendorname(qint32 index);
char* ls_getproductname(qint32 index);
char* ls_getserialnumber(qint32 index);
quint8 ls_devicecount();
qint32 ls_currentdeviceindex();
qint32 ls_opendevicebyindex(qint32 index);
qint32 ls_opendevicebyserial(char* pcserialnum);
qint32 ls_closedevice();
void ls_waitforpipe(quint32 timeout);
qint32 ls_getpipe(void* lpBuffer, qint32 nNumberOfBytesToRead);
qint32 ls_setpacketlength(qint32 packetlength);
quint32 ls_getfps();
qint32 ls_resetfifo(quint32 timeout);
qint32 ls_getsensortype(quint16 &sensortype, quint16 &pixelcount, quint32 timeout);
char* ls_geterrorstring(qint32 ierr);

qint32 ls_setmode(quint8 ucmode, quint32 timeout);
qint32 ls_setstate(quint8 ucstate, quint32 timeout);
qint32 ls_setinttime(quint32 inttime, quint32 timeout);
qint32 ls_getmcu2version(quint16 &wversion, quint32 timeout);
qint32 ls_getmcu2sensortype(quint16 &sensortype, quint32 timeout);
qint32 ls_getmode(quint8 &ucmode, quint32 timeout);
qint32 ls_getstate(quint8 &ucstate, quint32 timeout);
qint32 ls_getinttime(quint32 &inttime, quint32 timeout);
qint32 ls_getpacketlength(qint32 &packetlength,quint32 timeout);
qint32 ls_customfirmware(quint32 &custom, quint32 timeout);

qint32 ls_getsensorconfigmask(quint16 sensortype, quint16 &maskand, quint16 &maskor);
qint32 ls_getsensormuxmask(quint16 sensortype, quint16 &maskand, quint16 &maskor);

qint32 ls_getsensordefaultparameter(quint16 sensortype, quint16 &config, quint16 &mux, quint16 &rpga, quint16 &roffset,
                                    quint16 &gpga, quint16 &goffset, quint16 &bpga, quint16 &boffset);
char* ls_getsensorname(quint16 sensortype);
qint32 lsgetminmaxtime(quint16 sensortype, quint32 tmin, quint32 tmax);

qint32 ls_savesettings(quint32 timeout);
qint32 ls_getadcconfig(quint16 &config, quint32 timeout);
qint32 ls_getadcmux(quint16 &mux, quint32 timeout);
qint32 ls_getadcpga1(quint16 &pga, quint32 timeout);
qint32 ls_getadcpga2(quint16 &pga, quint32 timeout);
qint32 ls_getadcpga3(quint16 &pga, quint32 timeout);
qint32 ls_getadcoffset1(quint16 &offset, quint32 timeout);
qint32 ls_getadcoffset2(quint16 &offset, quint32 timeout);
qint32 ls_getadcoffset3(quint16 &offset, quint32 timeout);
qint32 ls_setadcconfig(quint16 config, quint32 timeout);
qint32 ls_setadcmux(quint16 mux, quint32 timeout);
qint32 ls_setadcpga(quint16 rpga, quint16 gpga, quint16 bpga,quint32 timeout);
qint32 ls_setadc3xpga(quint16 pga, quint32 timeout);
qint32 ls_setadcpga1(quint16 pga, quint32 timeout);
qint32 ls_setadcpga2(quint16 pga, quint32 timeout);
qint32 ls_setadcpga3(quint16 pga, quint32 timeout);
qint32 ls_setadcoffset(quint16 roffset, quint16 goffset, quint16 boffset, quint32 timeout);
qint32 ls_setadc3xoffset(quint16 offset, quint32 timeout);
qint32 ls_setadcoffset1(quint16 offset, quint32 timeout);
qint32 ls_setadcoffset2(quint16 offset, quint32 timeout);
qint32 ls_setadcoffset3(quint16 offset, quint32 timeout);

qint32 ls_readi2c(quint8 i2caddr, unsigned char* pbuf, quint16 &wlength, quint8 &ucstate, quint32 timeout);
qint32 ls_writei2c(quint8 i2caddr, unsigned char* pbuf, quint16 wlength, quint8 &ucstate, quint32 timeout);
qint32 ls_seti2cfreq(quint8 freq, quint32 timeout);
qint32 ls_geti2cfreq(quint8 &freq, quint32 timeout);
qint32 ls_geti2cstat(quint8 &stat, quint32 timeout);
char* ls_geti2cstring(quint8 stat);

#endif // LIBUSBLCJTN_H

