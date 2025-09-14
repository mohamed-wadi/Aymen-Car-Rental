from django.contrib import admin
from .models import Contact

# Register your models here.
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'car_title', 'city', 'rental_start_date', 'rental_end_date', 'total_rental_cost', 'status', 'create_date')
    list_display_links = ('id', 'first_name', 'last_name')
    search_fields = ('first_name', 'last_name', 'email', 'car_title')
    list_filter = ('status', 'rental_start_date', 'rental_end_date', 'create_date')
    readonly_fields = ('rental_days', 'total_rental_cost')
    list_per_page = 25

admin.site.register(Contact, ContactAdmin)
