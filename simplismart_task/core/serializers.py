from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Cluster, ResourceUsage, Deployment, Organization

User = get_user_model()

class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model"""
    class Meta:
        model = Organization
        fields = ['id', 'name', 'description', 'created_by', 'members', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating organizations"""
    class Meta:
        model = Organization
        fields = ['name', 'description']

class OrganizationInviteSerializer(serializers.Serializer):
    """Serializer for organization invite codes"""
    invite_code = serializers.CharField()

class UserSerializer(serializers.ModelSerializer):
    """Modified User serializer to include organization info"""
    organizations = OrganizationSerializer(many=True, read_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'organizations', 'is_active', 'is_staff', 'date_joined']
        read_only_fields = ['is_active', 'is_staff', 'date_joined']

    def create(self, validated_data):
        """Create user with optional organization"""
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user

class ResourceUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceUsage
        fields = ('id', 'cluster', 'used_cpu', 'used_ram', 'used_gpu', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

class ResourceUsageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceUsage
        fields = ('used_cpu', 'used_ram', 'used_gpu')

class ClusterSerializer(serializers.ModelSerializer):
    available_cpu = serializers.IntegerField(read_only=True)
    available_ram = serializers.IntegerField(read_only=True)
    available_gpu = serializers.IntegerField(read_only=True)
    resource_usage = ResourceUsageSerializer(many=True, read_only=True)

    class Meta:
        model = Cluster
        fields = (
            'id', 'name', 'description', 'owner',
            'total_cpu', 'total_ram', 'total_gpu',
            'available_cpu', 'available_ram', 'available_gpu',
            'resource_usage', 'created_at', 'updated_at'
        )
        read_only_fields = ('owner', 'created_at', 'updated_at')

class ClusterCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cluster
        fields = ('id', 'name', 'description', 'total_cpu', 'total_ram', 'total_gpu')
        read_only_fields = ('id',)

    def validate(self, data):
        # Validate that resource values are non-negative
        if data['total_cpu'] < 0:
            raise serializers.ValidationError("Total CPU cannot be negative")
        if data['total_ram'] < 0:
            raise serializers.ValidationError("Total RAM cannot be negative")
        if data['total_gpu'] < 0:
            raise serializers.ValidationError("Total GPU cannot be negative")
        return data

class DeploymentSerializer(serializers.ModelSerializer):
    """Serializer for Deployment model"""
    class Meta:
        model = Deployment
        fields = ['id', 'name', 'cluster', 'docker_image', 'required_cpu', 
                 'required_ram', 'required_gpu', 'status', 'created_at', 'updated_at']
        read_only_fields = ['status', 'created_at', 'updated_at']

class DeploymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating deployments"""
    class Meta:
        model = Deployment
        fields = ['name', 'cluster', 'docker_image', 'required_cpu', 
                 'required_ram', 'required_gpu']

    def validate(self, data):
        """Validate resource requirements"""
        if (data['required_cpu'] < 0 or 
            data['required_ram'] < 0 or 
            data['required_gpu'] < 0):
            raise serializers.ValidationError("Resource requirements cannot be negative")
        return data 