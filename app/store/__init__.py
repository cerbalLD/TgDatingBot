from .store import Store as ClassStore
from .models import *

Store = ClassStore()
Store.init_db()

__all__ = ['Store'] + [
    name for name in dir() 
    if not name.startswith('_') and name != 'ClassStore'
]