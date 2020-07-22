from kivy.uix.widget import Widget
from digitaldash.needles.needle import Needle
from kivy.properties import NumericProperty
from kivy.properties import StringProperty

class NeedleEllipse(Needle, Widget):
    """
    Create Ellipse widget.
    """
    update       = NumericProperty()
    source       = StringProperty()
    degrees      = NumericProperty()
    angle_start  = NumericProperty()
    sizex        = NumericProperty()
    sizey        = NumericProperty()

    def __init__(self, **kwargs):
        super(NeedleEllipse, self).__init__()

        self.SetUp(**kwargs)
        self.SetOffset()
        self.angle_start = -self.offset
        self.Type = 'Ellipse'

    def _size(self, gauge):
        '''Helper method that runs when gauge face changes size.'''

        if self.sizex == 512: return
        (self.sizex, self.sizey) = gauge.face.norm_image_size