from django.contrib import admin
from .models import (
    User, Category, Service, ServiceProduct, Professional, WorkingHour, 
    Appointment, Payment, Product, StockMovement, Review, LoyaltyPoints, Message,
    Notification, ActivityLog
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'user_type', 'is_active')
    list_filter = ('user_type', 'is_active')
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

class ServiceProductInline(admin.TabularInline):
    model = ServiceProduct
    extra = 1

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'duration_minutes', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_active')
    inlines = [ServiceProductInline]

class WorkingHourInline(admin.TabularInline):
    model = WorkingHour
    extra = 7

@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = ('name', 'commission_rate', 'is_active')
    list_editable = ('commission_rate', 'is_active')
    search_fields = ('name', 'bio')
    filter_horizontal = ('services',)
    inlines = [WorkingHourInline]

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'service', 'professional', 'date_time', 'status')
    list_filter = ('status', 'date_time', 'professional')
    search_fields = ('client__username', 'service__name')
    date_hierarchy = 'date_time'
    actions = ['mark_as_confirmed', 'mark_as_completed', 'mark_as_canceled']

    def mark_as_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
    mark_as_confirmed.short_description = "Marcar selecionados como Confirmado"

    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_as_completed.short_description = "Marcar selecionados como Concluído"

    def mark_as_canceled(self, request, queryset):
        queryset.update(status='canceled')
    mark_as_canceled.short_description = "Marcar selecionados como Cancelado"

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'amount', 'professional_commission', 'method', 'status', 'created_at')
    list_filter = ('method', 'status', 'created_at')
    readonly_fields = ('professional_commission',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'stock_quantity', 'cost_price', 'expiry_date')
    list_filter = ('category', 'expiry_date')
    search_fields = ('name', 'supplier')

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'quantity', 'created_at')
    list_filter = ('movement_type', 'created_at')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'rating', 'created_at')
    list_filter = ('rating',)

@admin.register(LoyaltyPoints)
class LoyaltyPointsAdmin(admin.ModelAdmin):
    list_display = ('client', 'points', 'last_updated')
    search_fields = ('client__username',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'notification_type', 'sent_at', 'status')
    list_filter = ('notification_type', 'status', 'sent_at')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'created_at', 'ip_address')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'action', 'details')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('subject', 'message', 'name')
