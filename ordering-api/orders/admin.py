from django.contrib import admin
from .models import *

admin.site.register(Order)
admin.site.register(OrderedItem)
admin.site.register(StoreItem)
admin.site.register(Supplier)
admin.site.register(XMRExchangeRate)

