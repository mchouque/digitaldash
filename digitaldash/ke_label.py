from typing import NoReturn, List, TypeVar
from kivy.uix.label import Label
from static.constants import KE_PID
from kivy.logger import Logger

KL = TypeVar('KL', bound='KELabel')
class KELabel(Label):
    """
    Simple wrapper around Kivy.uix.label.
    """

    def __init__(self, **args):
        """
        Args:
          default (str)     : The text that should always be displayed ie "Max: <num>"
            (default is nothing)
          color (tuple)     : RGBA values for text color
            (default is white (1, 1, 1, 1))
          font_size (int)   : Font size of label
            (default is 25)
          decimals (int)    : Number of decimal places displayed if receiving data
            (default is 2)
          pid (str)         : Byte code value of PID to get data from
            (default is nothing)
        """
        super(KELabel, self).__init__()
        self.minObserved     = 9999
        self.maxObserved     = -9999
        self.default         = args.get('default', '')
        self.ConfigColor     = args.get('color', (1, 1, 1 ,1)) # White
        self.color           = self.ConfigColor
        self.ConfigFontSize  = args.get('font_size', 25)
        self.font_size       = self.ConfigFontSize
        self.decimals        = str(KE_PID.get(args.get('pid', ''), {}).get('decimals', 2))
        self.ObjectType      = 'Label'
        self.pid             = args.get('pid', None)

        if ( self.default == '__PID__' ):
            if ( args['pid'] in KE_PID ):
                self.default = str(KE_PID[self.pid]['shortName'])
            else:
                self.default = KE_PID[self.pid]['name']
                Logger.error( "Could not load shortName from Static.Constants for PID: "+self.pid+" : "+str(e) )
        if ( 'data' in args and args['data'] ):
            self.text = self.default +' 0'
        else:
            self.text = self.default

        pos_hints = args.get('pos', (0, 0))
        self.pos_hint = {'x':pos_hints[0] / 100, 'y':pos_hints[1] / 100}

    def setData(self: KL, value='') -> NoReturn:
        """
        Send data to Label widget.

        Check for Min/Max key words to cache values with regex checks.

        Args:
            self (<digitaldash.ke_label>): KELabel object
            value (float) : value that label is being updated to
        """
        value = float(value)

        if ( self.default == 'Min: ' ):
            if ( self.minObserved > value ):
                self.minObserved = value
                self.text = ("{0:.%sf}"%(self.decimals)).format(value)
        elif ( self.default == 'Max: ' ):
            if ( self.maxObserved < value ):
                self.maxObserved = value
                self.text = ("{0:.%sf}"%(self.decimals)).format(value)
        else:
            self.text = self.default + ("{0:.%sf}"%(self.decimals)).format(value)
