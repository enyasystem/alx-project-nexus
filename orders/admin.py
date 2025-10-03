from django.contrib import admin
from .models import Address, Cart, CartItem, Order, OrderItem
from .models import PaymentRecord
from .models import StockReservation


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_cents', 'created_at')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'unit_price_cents', 'quantity')


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ('order', 'provider', 'provider_id', 'amount_cents', 'status', 'created_at')


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'quantity', 'owner_type', 'owner_id', 'status', 'expires_at', 'created_at')
    list_filter = ('status', 'owner_type')
