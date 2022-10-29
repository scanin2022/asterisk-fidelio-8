#!/usr/bin/python
import serial, time, io, os
#initialization and open the port
#possible timeout values:
# 1. None: wait forever, block call
#    2. 0: non-blocking mode, return immediately
#    3. x, x is bigger than 0, float allowed, timeout block call

ser = serial.Serial()
ser.port = "/dev/ttyr00"
#    ser.port = "/dev/ttyUSB7"
    #ser.port = "/dev/ttyS2"
#ser.port = 'COM7'

ser.baudrate = 9600
#ser.baudrate = 38400
#ser.baudrate = 57600
ser.bytesize = serial.EIGHTBITS #number of bits per bytes
ser.parity = serial.PARITY_NONE #set parity check: no parity
ser.stopbits = serial.STOPBITS_ONE #number of stop bits
#ser.timeout = None          #block read
ser.timeout = 1            #non-block read
    #ser.timeout = 2              #timeout block read
ser.xonxoff = False     #disable software flow control
ser.rtscts = False     #disable hardware (RTS/CTS) flow control
ser.dsrdtr = False       #disable hardware (DSR/DTR) flow control
ser.writeTimeout = 1     #timeout for write
#ser.writeTimeout = None     #timeout for write


#-------------------------------------------------------------------------------
def log(text):
    print text
    f.write(text)

#-------------------------------------------------------------------------------
def countBCC(text):
    chars = []
    outputXOR = int('0x03',16)   # Take ETX first
    chars.extend(text)
    for x in chars:
       try:
           num = ord(x)
       except:
           log('CANNOT CONVERT TO DIGIT!!!: ' + chr(x))
           return 0

       outputXOR = outputXOR ^ num
    return outputXOR

#-------------------------------------------------------------------------------
def sendACK(waitcountFile):
    ser.flushOutput()
    ser.write('\x06')  #Write ACK
    log('SEND ACK!!!\n')
    if waitcountFile > 3:
        TakePmsClean()
        return 0
    return waitcountFile

#-------------------------------------------------------------------------------
def sendNAK():
    ser.flushOutput()
    ser.write('\x15')  #Write NAK
    log('SEND NAK!!!\n')

#-------------------------------------------------------------------------------
def sendAYT():
    ser.flushOutput()
    x = countBCC('210')
    ser.write('\x02' + '210' + '\x03' + chr(x))
    log('Send AYT: ' + chr(int('0x02',16)) + str('210') + chr(int('0x03',16)) + chr(x) + str('\n'))

#-------------------------------------------------------------------------------
def send201121():
    ser.flushOutput()
    x = countBCC('201121')
    ser.write('\x02' + '201121' + '\x03' + chr(x))
    log('Send AYT: ' + chr(int('0x02',16)) + str('201121') + chr(int('0x03',16)) + chr(x) + str('\n'))

#-------------------------------------------------------------------------------
def sendRID():
    ser.flushOutput()
    x = countBCC('220')
    ser.write('\x02' + '220' + '\x03' + chr(x))
    log('Send RID: ' + chr(int('0x02',16)) + str('220') + chr(int('0x03',16)) + chr(x) + str('\n'))

#-------------------------------------------------------------------------------
def TakePmsClean():
    mypath = "/pms/pms-clean"
    i = ''
    fline = ''
    for i in os.listdir(mypath):
        withpath = os.path.join(mypath,i)
        if os.path.isfile(withpath):
           f = open(withpath, 'r')
           log('Open Clean file' + withpath + str('\n'))
           fline = f.readline()
           log('Read Clean file' + fline + str('\n'))
           f.close()
           
           try:
               num = int(str(fline[0]) + str(fline[1]) + str(fline[2]))
           except:
               log('ERROR not FATAL!!! In Clean file, not integer room number:' + fline + str('\n'))
               try:
                   os.system('rm -f ' + withpath) # Delete Bad file
                   return
               except Exception as e:
                   log('ERROR IN RM Command, can`t not delete file!!!!:' + withpath + str(e))
                   return
                   
           try:
               flag = int(str(fline[4]))
           except:
               log('ERROR not FATAL!!! In Clean file, not integer flag number:' + fline + str('\n'))
               try:
                   os.system('rm -f ' + withpath) # Delete Bad file
                   return
               except Exception as e:
                   log('ERROR IN RM Command, can`t not delete file!!!!:' + withpath + str(e))
                   return
           try:
               os.system('rm -f ' + withpath) # Delete Bad file
           except Exception as e:
               log('ERROR IN RM Command, can`t not delete file!!!!:' + withpath + str(e))
               return
               
           sendRoomStatus(num, flag)
           
           timeout1 = 0
           while readACK == 0:
               log('Can`t recieve ACK - send repeat' + str(timeout1) + str('\n'))
               sendRoomStatus(num, flag)
               timeout1 += 1
               if timeout1 == 3:
                   timeout = 0
                   break

#-------------------------------------------------------------------------------
def sendRoomStatus(num, flag):
    ser.flushOutput()
    x = countBCC('12' + str(flag) + str(num) + '      ')
    ser.write('\x02' + '12' + str(flag) + str(num) + '      ' + '\x03' + chr(x))
    log('Send Room Status: ' + chr(int('0x02',16)) + '12' + str(flag) + str(num) + '      ' + chr(int('0x03',16)) + chr(x) + str('\n'))

#-------------------------------------------------------------------------------
def readACK():
    waitcount = 0
    joined_seq = ''
    while True:
        count = ser.inWaiting()
        if count > 0:
            out = ser.read(count)

            for v in out:
                joined_seq += str(v)

            ser.flushInput()  #flush input buffer, discarding all its contents
            log('ser.flushInput()\n')
            ser.flushOutput()
            log('ser.flushOutput()\n')

            if count == 1 and out[0] == '\x06':
                    log('RESEIVE ACK!!!' + joined_seq + str('\n'))
                    return 1

            elif count == 1 and out[0] == '\x15':
                    log('RESEIVE NAK!!!' + joined_seq + str('\n'))
                    return 0
            else:
                log('READ DATA NOT ACK OR NAK!!!: ' + joined_seq + str('\n'))
                return 0
        else:
           waitcount += 0.2
           time.sleep(0.2)  #give the serial port sometime to receive the data
           #log('time.sleep(0.2)\n')
           if waitcount > 1.5:
               log('DATA TIMEOUT!!!: ' + str('\n'))
               return 0

    log('ERROR in def readACK()!!!: ' + str('\n'))
    return 0
    
#-------------------------------------------------------------------------------

f = open('/pms/log-com-7.txt','w')
log('------------------START NEW TRANSMITION------------------------------\n')
log('Port USED: ' + ser.portstr + '\n')



try:
    ser.open()

except Exception as e:
    log('error open serial port: ' + str(e))
    f.close()
    exit()

if ser.isOpen():
    try:
        numOfLines = 0
        out = []
        ser.flushInput()  #flush input buffer, discarding all its contents
        log('ser.flushInput()\n')
        ser.flushOutput() #flush output buffer, aborting current output
        log('ser.flushOutput()\n') #and discard all that is in buffer
                          
        time.sleep(0.5)  #give the serial port sometime to receive the data
        log('time.sleep(0.5)\n')

        flagInit = 0     # flag initialize PMS after 100 seconds without data
        waitcountFile = 0        
        
        while True:
            waitcount = 0
            waitcount60 = 0
            joined_seq = ''
            out = []
            while True:
                time.sleep(0.2)  #give the serial port sometime to receive the data
                #log('time.sleep(0.2)\n')
                
                if waitcountFile > 10:
                    TakePmsClean()
                    waitcountFile = 0

                count = ser.inWaiting()
                if count > 0:
                    out = ser.read(count)
                    joined_seq = ''
                    for v in out:
                        joined_seq += str(v)

                    ser.flushInput()                   #flush input buffer, discarding all its contents
                    log('ser.flushInput()\n')
                    ser.flushOutput() #flush output buffer, aborting current output
                    log('ser.flushOutput()\n') #and discard all that is in buffer


                    if out[0] == '\x06' or out[0] == '\x15':  #Take first byte and check it. We need ACK or NAK
                        if flagInit == 1:
                            log('SEND RID after 100 seconds no data from PMS!!!' + joined_seq + str('\n'))
                            sendRID()        # Send Request to Initiate Database update
                            flagInit = 0
                        log('RESEIVE ACK OR NAK!!!' + joined_seq + str('\n'))
                        break

                    if out[0] == '\x02':                      #Take first byte and check it. We need STX
                        if count > 9 and out[1] == '1' and out[2] == '0':   #Take second and third byte and check FUNCTION CHECK-IN AND CHECK-OUT
                            if count == 32 and out[3] == '1':                 #Take PROCESS code 1- Normal check in
                                try:
                                    num = int(str(out[4]) + str(out[5]) + str(out[6])) #  + str(out[7]) We use only 3 digits in KK Nadezhda
                                except:
                                    log('ERROR not FATAL!!! Come Unknow command, not integer room number:' + joined_seq + str('\n'))
                                    sendNAK()
                                    break

                                #MYSQL commands to allow phone calls
                                try:
                                    os.system('/pms/mysql-update.sh ' + str(num) + ' ' + '5') # allow only Local calls
                                except Exception as e:
                                    log('ERROR IN MYSQL FILE EXECUTING!!!!: ' + str(e))
                                    
                                log('CHECK IN Normal!!!:' + joined_seq + str('\n'))
                                waitcountFile = sendACK(waitcountFile) # Send normal ACT

                            elif count == 32 and out[3] == '3':               #Take PROCESS code 3- Update check in
                                try:
                                    num = int(str(out[4]) + str(out[5]) + str(out[6])) #  + str(out[7]) We use only 3 digits in KK Nadezhda
                                except:
                                    log('ERROR not FATAL!!! Come Unknow command, not integer room number:' + joined_seq + str('\n'))
                                    sendNAK()
                                    break

                                #MYSQL commands to allow phone calls
#                                try:
#                                    os.system('/pms/mysql-update.sh ' + str(num) + ' ' + '5') # allow only Local calls
#                                except Exception as e:
#                                    log('ERROR IN MYSQL FILE EXECUTING!!!!: ' + str(e))
                                
                                log('CHECK IN Update!!!:' + joined_seq + str('\n'))
                                waitcountFile = sendACK(waitcountFile) # Send normal ACT

                            elif count == 10 and out[3] == '0':               #Take PROCESS code 0- Normal check out
                                try:
                                    num = int(str(out[4]) + str(out[5]) + str(out[6])) #  + str(out[7]) We use only 3 digits in KK Nadezhda
                                except:
                                    log('ERROR not FATAL!!! Come Unknow command, not integer room number:' + joined_seq + str('\n'))
                                    sendNAK()
                                    break

                                #MYSQL commands to disallow phone calls
                                try:
                                    os.system('/pms/mysql-update.sh ' + str(num) + ' ' + '2') # disable International and allow only Local calls
                                except Exception as e:
                                    log('ERROR IN MYSQL FILE EXECUTING!!!!: ' + str(e))
                                
                                log('CHECK OUT Normal!!!:' + joined_seq + str('\n'))
                                waitcountFile = sendACK(waitcountFile) # Send normal ACT

                            elif count == 10 and out[3] == '2':               #Take PROCESS code 3- Update check out
                                try:
                                    num = int(str(out[4]) + str(out[5]) + str(out[6])) #  + str(out[8]) We use only 3 digits in KK Nadezhda
                                except:
                                    log('ERROR not FATAL!!! Come Unknow command, not integer room number:' + joined_seq + str('\n'))
                                    sendNAK()
                                    break

                                #MYSQL commands to disallow phone calls
                                try:
                                    os.system('/pms/mysql-update.sh ' + str(num) + ' ' + '2') # disable International and allow only Local calls
                                except Exception as e:
                                    log('ERROR IN MYSQL FILE EXECUTING!!!!: ' + str(e))
                                
                                log('CHECK OUT Update!!!:' + joined_seq + str('\n'))
                                waitcountFile = sendACK(waitcountFile) # Send normal ACT

                            elif count == 32 and out[3] == '4':               #Take PROCESS code 4 - Update check out (No in documentation!)
                                try:
                                    num = int(str(out[4]) + str(out[5]) + str(out[6])) #  + str(out[8]) We use only 3 digits in KK Nadezhda
                                except:
                                    log('ERROR not FATAL!!! Come Unknow command, not integer room number:' + joined_seq + str('\n'))
                                    sendNAK()
                                    break

                                #MYSQL commands to disallow phone calls
                                try:
                                    os.system('/pms/mysql-update.sh ' + str(num) + ' ' + '2') # disable International and allow only Local calls
                                except Exception as e:
                                    log('ERROR IN MYSQL FILE EXECUTING!!!!: ' + str(e))
                                
                                log('CHECK OUT Update!!!:' + joined_seq + str('\n'))
                                waitcountFile = sendACK(waitcountFile) # Send normal ACT
                                
                            elif count == 32 and out[3] == '0':               #Take PROCESS code 0- Update check out NOT NORMAL NO IN DOCUMENTATION!
                                try:
                                    num = int(str(out[4]) + str(out[5]) + str(out[6])) #  + str(out[7]) We use only 3 digits in KK Nadezhda
                                except:
                                    log('ERROR not FATAL!!! Come Unknow command, not integer room number:' + joined_seq + str('\n'))
                                    sendNAK()
                                    break

                                #MYSQL commands to disallow phone calls
                                try:
                                    os.system('/pms/mysql-update.sh ' + str(num) + ' ' + '2') # disable International and allow only Local calls
                                except Exception as e:
                                    log('ERROR IN MYSQL FILE EXECUTING!!!!: ' + str(e))
                                
                                log('CHECK OUT Normal!!!:' + joined_seq + str('\n'))
                                waitcountFile = sendACK(waitcountFile) # Send normal ACT                            

                            else:                             #Take PROCESS unknow code!!! send ACK
                               log('ERROR not FATAL!!! Come Unknow process code:' + joined_seq + str('\n'))
                               waitcountFile = sendACK(waitcountFile)
                               break
#--------------------------------------------------------------------------------------------------------------------------------------------
                        elif count == 32 and  out[1] == '1' and out[2] == '1':              # Directory information signal no need as
                            log('RESEIVE DIRECTORY INFORMATION signal!!! just send ACK:' + joined_seq + str('\n'))
                            waitcountFile = sendACK(waitcountFile)
                            break

#--------------------------------------------------------------------------------------------------------------------------------------------
                        elif count == 16 and  out[1] == '1' and out[2] == '2':              # No right signal from PMS but handle it
                            log('RESEIVE ROOM STATUS!!! just send ACK:' + joined_seq + str('\n'))
                            waitcountFile = sendACK(waitcountFile)
                            break

#--------------------------------------------------------------------------------------------------------------------------------------------
                        elif count == 10 and  out[1] == '1' and out[2] == '3':              # Message Waiting signal no need as
                            log('RESEIVE MESSAGE WAINTING signal!!! just send ACK:' + joined_seq + str('\n'))
                            waitcountFile = sendACK(waitcountFile)
                            break

#--------------------------------------------------------------------------------------------------------------------------------------------
                        elif count == 10 and  out[1] == '1' and out[2] == '4':                # Room Disable signal - what level of phone rights are set
                            if out[3] == '0':                 #Take PROCESS code 0 - level 0
                                try:
                                    num = int(str(out[4]) + str(out[5]) + str(out[6])) #  + str(out[7]) We use only 3 digits in KK Nadezhda
                                except:
                                    log('ERROR not FATAL!!! Come Unknow command, not integer room number:' + joined_seq + str('\n'))
                                    sendNAK()
                                    break

                                #MYSQL commands to allow phone calls at level 0
                                try:
                                    os.system('/pms/mysql-update.sh ' + str(num) + ' ' + '2') # disable International and allow only Local calls
                                except Exception as e:
                                    log('ERROR IN MYSQL FILE EXECUTING!!!!: ' + str(e))
                                
                                log('SET on the phone rights at level 0!!!:' + joined_seq + str('\n'))
                                waitcountFile = sendACK(waitcountFile) # Send normal ACT

                            elif out[3] == '1':                 #Take PROCESS code 1 - level 1
                                try:
                                    num = int(str(out[4]) + str(out[5]) + str(out[6])) #  + str(out[7]) We use only 3 digits in KK Nadezhda
                                except:
                                    log('ERROR not FATAL!!! Come Unknow command, not integer room number:' + joined_seq + str('\n'))
                                    sendNAK()
                                    break

                                #MYSQL commands to allow phone calls at level 1
                                try:
                                    os.system('/pms/mysql-update.sh ' + str(num) + ' ' + '5') # allow International!!!
                                except Exception as e:
                                    log('ERROR IN MYSQL FILE EXECUTING!!!!: ' + str(e))
                                
                                log('SET on the phone rights at level 1!!!:' + joined_seq + str('\n'))
                                waitcountFile = sendACK(waitcountFile) # Send normal ACT

                            elif out[3] == '2':                 #Take PROCESS code 2 - level 2
                                try:                                
                                    num = int(str(out[4]) + str(out[5]) + str(out[6])) #  + str(out[8]) We use only 3 digits in KK Nadezhda
                                except:
                                    log('ERROR not FATAL!!! Come Unknow command, not integer room number:' + joined_seq + str('\n'))
                                    sendNAK()
                                    break

                                #MYSQL commands to allow phone calls at level 2
                                try:
                                    os.system('/pms/mysql-update.sh ' + str(num) + ' ' + '2') # disable International and allow only Local calls
                                except Exception as e:
                                    log('ERROR IN MYSQL FILE EXECUTING!!!!: ' + str(e))                                
                                
                                log('SET on the phone rights at level 0!!!:' + joined_seq + str('\n'))
                                waitcountFile = sendACK(waitcountFile) # Send normal ACT


                            elif out[3] == '3':                 #Take PROCESS code 3 - level 3
                                try:
                                    num = int(str(out[4]) + str(out[5]) + str(out[6])) #  + str(out[7]) We use only 3 digits in KK Nadezhda
                                except:
                                    log('ERROR not FATAL!!! Come Unknow command, not integer room number:' + joined_seq + str('\n'))
                                    sendNAK()
                                    break

                                #MYSQL commands to allow phone calls at level 3
                                try:
                                    os.system('/pms/mysql-update.sh ' + str(num) + ' ' + '2') # disable International and allow only Local calls
                                except Exception as e:
                                    log('ERROR IN MYSQL FILE EXECUTING!!!!: ' + str(e))
                                
                                log('SET on the phone rights at level 3!!!:' + joined_seq + str('\n'))
                                waitcountFile = sendACK(waitcountFile) # Send normal ACT

                            else:                             #Take PROCESS unknow code!!! send ACK
                               log('ERROR not FATAL!!! Come Unknow process code:' + joined_seq + str('\n'))
                               sendNAK()
                               break

#--------------------------------------------------------------------------------------------------------------------------------------------3
                        elif count == 14 and  out[1] == '1' and out[2] == '5':                 # Automatic Wake-Up signal no need as
                            log('Reseive Automatic Wake-Up signal!!! just send ACK: ' + joined_seq + str('\n'))
                            waitcountFile = sendACK(waitcountFile)
                            break

#--------------------------------------------------------------------------------------------------------------------------------------------
                        elif count == 9 and  out[1] == '2' and out[2] == '0':                  # Confirmation Message signal no need as
                            log('Reseive Confirmation Message signal!!! just send ACK: ' + joined_seq + str('\n'))
                            waitcountFile = sendACK(waitcountFile)
                            break

#--------------------------------------------------------------------------------------------------------------------------------------------
                        elif count == 6 and  out[1] == '2' and out[2] == '1':                  # Status Inquiry/Maintenance Request signal no need as
                            log('Reseive Status Inquiry/Maintenance Request signal!!! send ACK: ' + joined_seq + str('\n'))
                            waitcountFile = sendACK(waitcountFile)
                            time.sleep(0.4)  #give the serial port sometime to receive the data
                            sendRID()        # Send Request to Initiate Database update
                            break

#--------------------------------------------------------------------------------------------------------------------------------------------
                        elif count > 3 and  out[1] == '2' and out[2] == '2':                   # Database update signal no need as and PMS can`t send it but we handle this signal
                            log('Reseive Status Inquiry/Maintenance Request signal!!! send ACK: ' + joined_seq + str('\n'))
                            waitcountFile = sendACK(waitcountFile)
                            time.sleep(0.4)  #give the serial port sometime to receive the data
                            sendRID()        # Send Request to Initiate Database update
                            break

#--------------------------------------------------------------------------------------------------------------------------------------------
                        else:
                            log('ERROR not FATAL!!! Come Unknow command:' + joined_seq + str('\n'))
                            ser.flushInput()  #flush input buffer, discarding all its contents
                            log('ser.flushInput()\n')
                            ser.flushOutput() #flush output buffer, aborting current output
                            log('ser.flushOutput()\n')
                            sendNAK()
                            break
                    else:
                        log('ERROR not FATAL!!! Come Unknow command:' + joined_seq + str('\n'))
                        ser.flushInput()  #flush input buffer, discarding all its contents
                        log('ser.flushInput()\n')
                        ser.flushOutput() #flush output buffer, aborting current output
                        log('ser.flushOutput()\n')
                        sendNAK()
                        break

                else:
                    waitcount += 0.2
                    waitcount60 += 0.2
                    waitcountFile += 1
                    time.sleep(0.2)  #give the serial port sometime to receive the data
                    #log('time.sleep(0.2)\n')
                    if waitcount60 > 60:
                       #send201121()
                       sendAYT()
                       readACK()
                       waitcount60 = 0
                       break                       
                    if waitcount > 500:
                       sendAYT()	# Send Are You There signal, when PMS not response with about 500 seconds
                       readACK()
                       flagInit = 1
                       break

        ser.close()
        log('NOT NORMAL------------------END TRANSMITION------------------------------\n')
        f.close()

    except Exception as e1:
        log('error communicating...: ' + str(e1) + '\n')
        log('FATAL1!------------------END TRANSMITION------------------------------\n')
        f.close()

else:
    log('cannot open serial port \n')
    log('FATAL2!------------------END TRANSMITION------------------------------\n')
    f.close()
