from django.contrib import admin

from .models import (
    Agent,
    ChatInquiry,
    ContactMessage,
    CounterPayRequest,
    PartialHome,
    PartialHomeFeature,
    PartialHomeImage,
    Property,
    PropertyFeature,
    PropertyImage,
)


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


class PropertyFeatureInline(admin.TabularInline):
    model = PropertyFeature
    extra = 1


class PartialHomeImageInline(admin.TabularInline):
    model = PartialHomeImage
    extra = 1


class PartialHomeFeatureInline(admin.TabularInline):
    model = PartialHomeFeature
    extra = 1


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("public_id", "name", "email", "phone")
    search_fields = ("public_id", "name", "email", "phone")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("public_id", "title", "city", "state", "property_type", "status", "price", "is_featured")
    list_filter = ("property_type", "status", "city", "state", "is_featured")
    search_fields = ("public_id", "title", "address", "city", "state")
    inlines = [PropertyImageInline, PropertyFeatureInline]


@admin.register(PartialHome)
class PartialHomeAdmin(admin.ModelAdmin):
    list_display = ("public_id", "title", "city", "state", "property_type", "percentage_paid", "remaining_amount", "is_active")
    list_filter = ("property_type", "city", "state", "is_active")
    search_fields = ("public_id", "title", "address", "city", "state", "payer_name")
    inlines = [PartialHomeImageInline, PartialHomeFeatureInline]


@admin.register(CounterPayRequest)
class CounterPayRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "partial_home", "email", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("email", "partial_home__title", "partial_home__public_id")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "email", "subject", "status", "created_at")
    list_filter = ("subject", "status", "created_at")
    search_fields = ("first_name", "last_name", "email", "message")


@admin.register(ChatInquiry)
class ChatInquiryAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "source", "created_at")
    list_filter = ("source", "created_at")
    search_fields = ("email", "message")
