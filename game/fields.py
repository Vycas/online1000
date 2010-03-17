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
        super(ThousandCardField, self).__init__(*args, **kwargs)
        self.max_length = max_length
    
    def db_type(self):
        return 'char(%d)' % (self.max_length * 2)
    
    def to_python(self, value):
        if value is None:
            return None
        
        if isinstance(value, list):
            return value
        
        return [ThousandCard(value[i*2:i*2+2].replace('0', '10')) for i in range(0, len(value)/2)]
    
    def get_prep_value(self, value):
        if value is None:
            return None
        
        value = map(lambda x: x.replace('10', '0'), value)
        return ''.join(value)
    
    def get_db_prep_value(self, value):
        return self.get_prep_value(value)
    
    def value_to_string(self, obj):
            value = self._get_val_from_obj(obj)
            return self.get_db_prep_value(value)