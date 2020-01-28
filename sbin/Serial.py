"""Serial handler class."""
import serial
import time
from kivy.logger import Logger
from subprocess import call

UART_SOL                 = 0xFF
UART_PCKT_SOL_POS        = 0x00
UART_PCKT_LEN_POS        = 0x01
UART_PCKT_CMD_POS        = 0x02
UART_PCKT_DATA_START_POS = 0x03

KE_CP_OP_CODES = {
    'KE_RESERVED'                : 0x00,    # Reserved
    'KE_ACK'                     : 0x01,    # Positive acknowledgment
    'KE_NACK'                    : 0x02,    # Negative acknowledgment
    'KE_HEARTBEAT'               : 0x03,    # Heartbeat
    'KE_SYS_READY'               : 0x04,    # System ready (GUI)
    'KE_PID_STREAM_NEW'          : 0x05,    # Clear current PID request and add new PID(s)
    'KE_PID_STREAM_ADD'          : 0x06,    # Add PID request to current stream
    'KE_PID_STREAM_REMOVE'       : 0x07,    # Remove PID request from current stream
    'KE_PID_STREAM_CLEAR'        : 0x08,    # Clear all PID request from current stream
    'KE_PID_STREAM_REPORT'       : 0x09,    # Report PID Data
    'KE_LCD_ENABLE'              : 0x0A,    # Enable the LCD display
    'KE_LCD_DISABLE'             : 0x0B,    # Disable the LCD display
    'KE_LCD_POWER_CYCLE'         : 0x0C,    # Power cycle the LCD display
    'KE_LCD_FORCE_BRIGHTNESS'    : 0x0D,    # Force an LCD brightness (volatile)
    'KE_LCD_AUTO_BRIGHTNESS'     : 0x0E,    # Re-enable standard LCD brightness control
    'KE_USB_ENABLE'              : 0x0F,    # Enable the USB power
    'KE_USB_DISABLE'             : 0x10,    # Disable the USB power
    'KE_USB_POWER_CYCLE'         : 0x11,    # Power cycle the USB power
    'KE_POWER_ENABLE'            : 0x12,    # Enable Power
    'KE_POWER_DISABLE'           : 0x13,    # Disable Power
    'KE_POWER_CYCLE'             : 0x14,    # Power cycle
    'KE_FIRMWARE_REQ'            : 0x15,    # Request firmware version
    'KE_FIRMWARE_REPORT'         : 0x16,    # Report firmware version
    'KE_FIRMWARE_UPDATE'         : 0x17     # Place device in firmware update mode
}

class Serial():

    def __init__(self):
        super(Serial, self).__init__()
        self.ser = serial.Serial(
            port='/dev/ttyAMA0',
            baudrate=57600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=5
        )
        self.ser.flushInput()
        self.ser_val = [0, 0, 0, 0, 0, 0]
        self.firmwareVerified = False  #False to do a firmware request


    def Start(self):

        """L1612773-4oop for checking Serial connection for data."""
        # Handle grabbing data
        data_line = ''

        try:
            data_line = self.ser.readline()

        except Exception as e:
            Logger.error("Error occured when reading serial data: " + str(e))

        # There shall always be an opcode and EOL
        if ( len(data_line) < 2 ):
            Logger.info("GUI: Data packet of length: " + str(len(data_line)) + " received: " + str(data_line))
            return self.ser_val

        #Logger.info("RAW DATA: " +  str(data_line) )

        # Get the command (Always the 1st byte)
        cmd = data_line[ UART_PCKT_CMD_POS ]

        # Remove the command byte from the payload
        data_line = data_line[ UART_PCKT_DATA_START_POS :len(data_line) - 1 ]

        if cmd == KE_CP_OP_CODES['KE_FIRMWARE_REPORT']:
            Logger.info("GUI: >> [FIRMWARE VERSION] "  + data_line.decode() + "\n")

        elif cmd == KE_CP_OP_CODES['KE_POWER_DISABLE']:
            Logger.info("SYS: Shutdown received")
            positive_ack = [UART_SOL, 0x03, KE_CP_OP_CODES['KE_ACK']]
            self.ser.write(positive_ack)
            call("sudo nohup shutdown -h now", shell=True)

        elif cmd == KE_CP_OP_CODES['KE_ACK']:
            Logger.info("GUI: >> ACK RX'd" + "\n")

        elif cmd == KE_CP_OP_CODES['KE_PID_STREAM_REPORT']:
            positive_ack = [UART_SOL, 0x03, KE_CP_OP_CODES['KE_ACK']]
            self.ser.write(positive_ack)
            Logger.info("Clipped Data: " + str(data_line))
            Logger.info("GUI: << ACK" + "\n")
            count = 0
            data_line = data_line.decode('utf-8')
            for val in data_line.split(';'):
                try:
                    val = float(val)
                    self.ser_val[count] = val
                    count = count + 1
                except ValueError:
                    print("Value error caught for: " + str(val))
                    count = count + 1
            #self.ser_val[2] = self.ser.inWaiting()
            #self.ser.flushInput()
            return self.ser_val

        return self.ser_val

    def UpdateRequirements(self, requirements):
        Logger.info("GUI: Updating requirements: " + str(requirements))
        bytes_written = self.ser.write( [ UART_SOL , 0x07, KE_CP_OP_CODES['KE_PID_STREAM_NEW'],  0x00, 0x0C, 0x00, 0x33 ] );

        msg = "PIDs updated " + str( bytes_written ) + " written"
        Logger.info( msg )

        return( 1, msg )

    def InitializeHardware( self ):
        """
            Handle making sure that our hardware is initialized and
            it is safe to start the main application loop.
        """
        Logger.info( "GUI: Initializing hardware" )

        while self.firmwareVerified != True:
            Logger.info("GUI: Requesting Firmware Version..")
            firmware_request = [UART_SOL, 0x03, KE_CP_OP_CODES['KE_FIRMWARE_REQ']]
            self.ser.write(firmware_request)

            # Wait for the MCU to receive the request and respond
            time.sleep(1)
            data_line = self.ser.readline()

            # Remove the command byte from the payload
            data_line = data_line[ UART_PCKT_DATA_START_POS :len(data_line) - 1 ]
            Logger.info("GUI: Firmware Version Received: " +  data_line.decode() )
            if data_line.decode() == "01.00.00":
                Logger.info("Firmware Up To Date")
                self.firmwareVerified = True
            else :
                Logger.info("Firmware Update Required")

        return ( True, "Hardware: Successfully initiated hardware" )

    def ResetHardware( self ):
        """
            Re-run the hardware initialize function.
        """

        # STUB FOR @MATT
            # Reboot the hardware here
        # END STUB

        # After reboot attempt to initialize the hardware again
        return ( self.InitializeHardware() )

    def PowerCycle( self ):
       """
          Reboot the Raspberry Pi
       """
       ke_power_cycle = [UART_SOL, 0x03, KE_CP_OP_CODES['KE_POWER_CYCLE']]
       ret = self.ser.write(ke_power_cycle)

       msg = "Wrote : " + str(ret) + " bytes for power cycle"

       Logger.info( msg )
       return ( ret, msg )
