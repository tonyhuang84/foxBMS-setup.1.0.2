# @copyright &copy; 2010 - 2017, Fraunhofer-Gesellschaft zur Foerderung der angewandten Forschung e.V. All rights reserved.
#
# BSD 3-Clause License
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
# 1.  Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
# 2.  Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
# 3.  Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# We kindly request you to use one or more of the following phrases to refer to foxBMS in your hardware, software, documentation or advertising materials:
#
# &Prime;This product uses parts of foxBMS&reg;&Prime;
#
# &Prime;This product includes parts of foxBMS&reg;&Prime;
#
# &Prime;This product is derived from foxBMS&reg;&Prime;

import unittest
import serial
import sys
import time
import logging

# bootloader command set from ST application note AN3155
command = {"Get": 0x00,
           "GetVersion": 0x01,
           "GetID": 0x02,
           "ReadMemory": 0x11,
           "Go": 0x21,
           "WriteMemory": 0x31,
           "Erase": 0x43,
           "ExtendedErase": 0x44,
           "WriteProtect": 0x63,
           "WriteUnprotect": 0x73,
           "ReadoutProtect": 0x82,
           "ReadoutUnprotect": 0x92}

commandExt = {"Init": 0x7F}

payloadEraseMode = {"Full": chr(0xFF) + chr(0xFF) + chr(0x00),
             "Bank1": chr(0xFF) + chr(0xFE) + chr(0x01),
             "Bank2": chr(0xFF) + chr(0xFD) + chr(0x02),
             "Section0": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x00) + chr(0x00),
             "Section1": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x01) + chr(0x01),
             "Section2": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x02) + chr(0x02),
             "Section3": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x03) + chr(0x03),
             "Section4": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x04) + chr(0x04),
             "Section5": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x05) + chr(0x05),
             "Section6": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x06) + chr(0x06),
             "Section7": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x07) + chr(0x07),
             "Section8": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x08) + chr(0x08),
             "Section9": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x09) + chr(0x09),
             "Section10": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x0A) + chr(0x0A),
             "Section11": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x0B) + chr(0x0B),
             "Section12": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x0C) + chr(0x0C),
             "Section13": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x0D) + chr(0x0D),
             "Section14": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x0E) + chr(0x0E),
             "Section15": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x0F) + chr(0x0F),
             "Section16": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x10) + chr(0x10),
             "Section17": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x11) + chr(0x11),
             "Section18": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x12) + chr(0x12),
             "Section19": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x13) + chr(0x13),
             "Section20": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x14) + chr(0x14),
             "Section21": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x15) + chr(0x15),
             "Section22": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x16) + chr(0x16),
             "Section23": chr(0x00) + chr(0x00) + chr(0x00) + chr(0x17) + chr(0x17),
             "AllButBootloader": chr(0x00) + chr(0x09) # Number of sections
                               + chr(0x00) + chr(0x02) + chr(0x00) + chr(0x03) # Section numbers
                               + chr(0x00) + chr(0x04) + chr(0x00) + chr(0x05)
                               + chr(0x00) + chr(0x06) + chr(0x00) + chr(0x07)
                               + chr(0x00) + chr(0x08) + chr(0x00) + chr(0x09)
                               + chr(0x00) + chr(0x0A) + chr(0x00) + chr(0x0B)
                               + chr(0x08), # checksum
             }

payLoadWriteProtectSection0 = chr(0x00) + chr(0x00) + chr(0x00)
payLoadWriteUnprotectSection0 = chr

response = {"ACK": 0x79, "NACK": 0x1F}

class InitException(Exception):
    pass

class CmdException(Exception):
    pass

class AckException(Exception):
    pass

class portdummy():
    """
    dummy class for development testing purposes
    """
    def __init__(self):
        pass
    def write(self, c):
        for x in c:
            print hex(ord(x))
    def read(self):
        return chr(0x79)
    def setDTR(self,x):
        self.dtr = x
    def setRTS(self,x):
        self.rts = x

class STM32Interface(object):
    '''
    abstraction of serial interface to STM32 microcontroller
    '''
    def __init__(self,port=None, baudrate=115200):
        if port == None and sys.platform.startswith('win'):
            port = "COM13"
        else:
            port = port
        #self._port = portdummy()
        self._port = serial.Serial(
            port=port,
            baudrate=baudrate,     # baudrate, recommended between 1200 and 115200
            bytesize=8,
            parity=serial.PARITY_EVEN,
            stopbits=1,
            xonxoff=0,              # don't enable software flow control
            rtscts=0,               # don't enable RTS/CTS flow control
            dsrdtr=0,               # don't enable RTS/CTS flow control
            timeout=1               # set a timeout value, None for waiting forever
            )
        logging.debug("Opened serial connection: %s" %self._port)

    def __enter__(self,port=None, baudrate=115200):
        self.__init__(port, baudrate)

    def __exit__ (self, exception_type, exception_value,  traceback):
        self._port.close()

    def _address(self, address):
        byte3 = (address >> 0) & 0xFF
        byte2 = (address >> 8) & 0xFF
        byte1 = (address >> 16) & 0xFF
        byte0 = (address >> 24) & 0xFF
        crc = byte0 ^ byte1 ^ byte2 ^ byte3
        self._port.write(chr(byte0) + chr(byte1) + chr(byte2) + chr(byte3) + chr(crc))
        logging.debug("Address is {0:#x}".format(address))
        return self._ack()

    def _cmd(self, commandCode):
        self._port.write(chr(commandCode))
        #according to STM AN3155 p.7 complement has to be sent after command
        self._port.write(chr(commandCode ^ 0xFF))
        logging.debug("Command Code: {0}".format(commandCode))
        return self._ack()

    def _ack(self):
        try:
            r = ord(self._port.read())
        except:
            raise AckException("Can't read port or timeout")
        else:
            if r == response["ACK"]:
                return True
            elif r == response["NACK"]:
                return False
            else:
                raise AckException("Unknown response: "+hex(r))
    def _readbytes(self, noOfBytes):
        bytes = []
        try:
            asdf = map(lambda c: ord(c), self._port.read(noOfBytes))
            bytes += asdf
        except:
            pass
        finally:
            return bytes

    def init(self):
        ''' sends INIT command (= 0x7f) to initialize bootloader in microcontroller '''
        try:
            self._port.write(chr(commandExt["Init"]))
            if self._ack():
                logging.info( "Initialized and in bootstate now!")
            else:
                logging.info("Could not initialize!")
        except:
            raise InitException("Could not initialize bootsequence. Is the Fox plugged in correctly?")

    def get(self):
        ''' sends GET command (= 0x00) to receive bootloader version and support command codes '''
        if self._cmd(command["Get"]):
            return self._readbytes()

    def getVersion(self):
        ''' sends GETVERSION command (= 0x01) to receive bootloader version '''
        if self._cmd(command["GetVersion"]):
            return self._readbytes()

    def getId(self):
        ''' sends GETID command (= 0x02) to receive product ID (e.g. 0x0419 for STM32F429 '''
        if self._cmd(command["GetID"]):
            return self._readbytes()

    def readMemory(self,address, length):
        ''' reads up to 256 bytes from address) '''
        if self._cmd(command["ReadMemory"]):
            if self._address(address):
                self._port.write(chr(length-1) + chr((length-1) ^ 0xFF))
                if self._ack():
                    return self._readbytes(length)

    def writeMemory(self, address, data):
        ''' writes up to 256 bytes of data at given address.
        writing the memory seems to be very picky. seen various obscure behaviour while testing'''
        if self._cmd(command["WriteMemory"]):
            if self._address(address):
                crc = len(data)-1
                self._port.write(chr(len(data)-1))
                for byte in data:
                    crc ^= byte
                    self._port.write(chr(byte))
                self._port.write(chr(crc))
                #logging.debug("Address: {0:#x}, Length: {1}, Data: {2}, CRC: {3}".format(address, len(data)-1, data, crc))
                if self._ack():
                    return True
                else:
                    return False

    def go(self, address):
        ''' starts program from given address '''
        if self._cmd(command["Go"]):
            self._port.write(self._address(address))
            if self._ack():
                return True
            else:
                return False

    def erase(self):
        '''not implemented according to appnote for now
        because bootloader version > v3.0 in STM32F4
        '''
        self.extendedErase("Full")


    def extendedErase(self,eraseMode=None):
        ''' full, bank1 and bank2 erase are the only modes implemented for now'''
        if self._cmd(command["ExtendedErase"]):
            logging.debug("This erase can take a while, so increase timeout")
            to = self._port.timeout
            self._port.timeout = 30
            self._port.write(payloadEraseMode[eraseMode])

            if self._ack():
                self._port.timeout = to
                return True
            else:
                self._port.timeout = to
                return False


    def writeProtect(self):
        '''        not needed now        '''
        pass

    def writeUnprotect(self):
        '''        not needed now        '''
        pass

    def readoutProtect(self):
        '''        not needed now        '''
        pass

    def readoutUnprotect(self):
        '''        not needed now        '''
        pass




class serialIfTest(unittest.TestCase):
    def setUp(self):
        #foxBMS entering bootloader mode and resetting
        self.stm32if = STM32Interface(port= "COM14")
        self.stm32if._port.setDTR(1)
        self.stm32if._port.setRTS(1)
        time.sleep(1)
        self.stm32if._port.setRTS(0)
        time.sleep(1)
        self.stm32if.init()
    def test_get(self):
        self.assertEqual(self.stm32if.get(),
                         [11,0x31,0x00,0x01,0x02,0x11,0x21,0x31,0x44,0x63,0x73,0x82,0x92,0x79])
    def test_getVerion(self):
        self.assertEqual(self.stm32if.getVersion(),
                         [0x31,0x00,0x00,0x79])
    def test_getId(self):
        self.assertEqual(self.stm32if.getId(),
                         [1,4,25,0x79])
    def test_readwriteMem(self):
        '''this test randomly fails obscurely.
        '''
        self.stm32if.writeMemory(0x08000800, range(0x100))
        self.assertEqual(self.stm32if.readMemory(0x08000800, 256), range(256))
    def test_erase(self):
        self.stm32if.writeMemory(0x08000800, [0]*255)
        self.stm32if.extendedErase("Full")
        self.assertEqual(self.stm32if.readMemory(0x08000800, 256),[0xff]*256)
    def tearDown(self):
        self.stm32if._port.close()


if __name__ == "__main__":
    unittest.main()

    # for manual testing use the following code example and comment line above
    stm32if = STM32Interface()
    stm32if._port.setDTR(1)
    stm32if._port.setRTS(1)
    time.sleep(1)
    stm32if._port.setRTS(0)
    time.sleep(1)
    stm32if.init()
    print stm32if.get()
    print stm32if.getId()
    print stm32if.getVersion()
    print stm32if.readMemory (0x080000ff, 0x1F)
    print stm32if.writeMemory(0x080000ff, [1,1,1,1,4,3,2,1,1,2,3,4])
    print stm32if.readMemory (0x080000ff, 0x2F)
    print stm32if.writeMemory(0x0800010f, [1,1,1,1,4,3,2,1,1,2,3,4])
    print stm32if.readMemory (0x080000fe, 0x2F)
