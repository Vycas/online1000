from django.db import models
from cards import ThousandCard


class ThousandCardField(models.Field):
    """
    Represents a list of Thousand cards in a database.
    
    Performs conversions from list of cards to string field and vice versa.
    """
    
    description = "A list of Thousand cards."
    
    __metaclass__ = models.SubfieldBase
    
    def __init__(self, max_length, *args, **kwargs):
        self.max_length = max_length
        super(ThousandCardField, self).__init__(*args, **kwargs)
    
    def db_type(self, connection):
        return 'char(%d)' % (self.max_length * 2)
    
    def to_python(self, value):
        if isinstance(value, list):
            return value
        
        return [ThousandCard(value[i*2:i*2+2].replace('0', '10')) for i in range(0, len(value)/2)]
    
    def get_prep_value(self, value):
        value = map(lambda x: x.replace('10', '0'), value)
        return ''.join(value)