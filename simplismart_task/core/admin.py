from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Cluster, ResourceUsage, Deployment, Organization, OrganizationMembership

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff')
    search_fields = ('email', 'username')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )

@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'total_cpu', 'total_ram', 'total_gpu', 'available_cpu', 'available_ram', 'available_gpu', 'created_at')
    list_filter = ('owner', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('available_cpu', 'available_ram', 'available_gpu', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'owner')
        }),
        ('Resources', {
            'fields': ('total_cpu', 'total_ram', 'total_gpu')
        }),
        ('Available Resources', {
            'fields': ('available_cpu', 'available_ram', 'available_gpu'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ResourceUsage)
class ResourceUsageAdmin(admin.ModelAdmin):
    list_display = ('cluster', 'used_cpu', 'used_ram', 'used_gpu', 'created_at')
    list_filter = ('cluster', 'created_at')
    search_fields = ('cluster__name',)
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Resource Usage', {
            'fields': ('cluster', 'used_cpu', 'used_ram', 'used_gpu')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    list_display = ('name', 'cluster', 'docker_image', 'status', 'created_at')
    list_filter = ('status', 'cluster', 'created_at')
    search_fields = ('name', 'docker_image', 'cluster__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'cluster', 'docker_image', 'status')
        }),
        ('Resource Requirements', {
            'fields': ('required_cpu', 'required_ram', 'required_gpu')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'created_by__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__email', 'organization__name')
    readonly_fields = ('joined_at',)
    fieldsets = (
        ('Membership Details', {
            'fields': ('user', 'organization', 'role')
        }),
        ('Timestamps', {
            'fields': ('joined_at',),
            'classes': ('collapse',)
        }),
    ) 