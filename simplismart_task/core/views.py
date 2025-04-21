from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import Cluster, ResourceUsage, Deployment, Organization, OrganizationMembership
from .serializers import (
    UserSerializer,
    ClusterSerializer,
    ClusterCreateSerializer,
    ResourceUsageSerializer,
    ResourceUsageCreateSerializer,
    DeploymentSerializer,
    DeploymentCreateSerializer,
    OrganizationSerializer,
    OrganizationCreateSerializer,
    OrganizationInviteSerializer
)
from rest_framework.views import APIView
from .rabbitmq import rabbitmq_publisher

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': serializer.data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def create_with_organization(self, request):
        user_serializer = self.get_serializer(data=request.data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            
            org_data = request.data.get('organization')
            if org_data:
                org_serializer = OrganizationCreateSerializer(data=org_data)
                if org_serializer.is_valid():
                    organization = user.create_organization(
                        name=org_data['name'],
                        description=org_data.get('description', '')
                    )
                    return Response({
                        'user': user_serializer.data,
                        'organization': OrganizationSerializer(organization).data
                    }, status=status.HTTP_201_CREATED)
                return Response(org_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(user_serializer.data, status=status.HTTP_201_CREATED)
        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(email=request.data['email'])
            response.data['user'] = {
                'id': user.id,
                'email': user.email,
                'username': user.username
            }
        return response

class ClusterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Cluster.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ClusterCreateSerializer
        return ClusterSerializer

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['get'])
    def resources(self, request, pk=None):
        cluster = self.get_object()
        return Response({
            'total_cpu': cluster.total_cpu,
            'total_ram': cluster.total_ram,
            'total_gpu': cluster.total_gpu,
            'available_cpu': cluster.available_cpu,
            'available_ram': cluster.available_ram,
            'available_gpu': cluster.available_gpu,
            'usage': ResourceUsageSerializer(
                cluster.resource_usage.all(),
                many=True
            ).data
        })

    @action(detail=True, methods=['post'])
    def use_resources(self, request, pk=None):
        cluster = self.get_object()
        serializer = ResourceUsageCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                usage = serializer.save(cluster=cluster)
                return Response(ResourceUsageSerializer(usage).data, 
                             status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({'error': str(e)}, 
                             status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResourceUsageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = ResourceUsage.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ResourceUsageCreateSerializer
        return ResourceUsageSerializer

    def get_queryset(self):
        return self.queryset.filter(cluster__owner=self.request.user)

class DeploymentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Deployment.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DeploymentCreateSerializer
        return DeploymentSerializer

    def get_queryset(self):
        return self.queryset.filter(cluster__owner=self.request.user)

    def perform_create(self, serializer):
        deployment = serializer.save()
        
        ResourceUsage.objects.create(
            cluster=deployment.cluster,
            used_cpu=deployment.required_cpu,
            used_ram=deployment.required_ram,
            used_gpu=deployment.required_gpu
        )
        
        deployment_data = DeploymentSerializer(deployment).data
        rabbitmq_publisher.publish_deployment(deployment_data)

    def perform_update(self, serializer):
        old_deployment = self.get_object()
        new_deployment = serializer.save()
        
        if (old_deployment.required_cpu != new_deployment.required_cpu or
            old_deployment.required_ram != new_deployment.required_ram or
            old_deployment.required_gpu != new_deployment.required_gpu):
            
            resource_usage = ResourceUsage.objects.get(
                cluster=new_deployment.cluster,
                used_cpu=old_deployment.required_cpu,
                used_ram=old_deployment.required_ram,
                used_gpu=old_deployment.required_gpu
            )
            resource_usage.used_cpu = new_deployment.required_cpu
            resource_usage.used_ram = new_deployment.required_ram
            resource_usage.used_gpu = new_deployment.required_gpu
            resource_usage.save()
        
        deployment_data = DeploymentSerializer(new_deployment).data
        rabbitmq_publisher.publish_deployment(deployment_data)

class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Organization.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return OrganizationCreateSerializer
        return OrganizationSerializer

    def get_queryset(self):
        return self.queryset.filter(members=self.request.user)

    def perform_create(self, serializer):
        organization = serializer.save(created_by=self.request.user)
        OrganizationMembership.objects.create(
            user=self.request.user,
            organization=organization,
            role='admin'
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        organization = serializer.instance
        response_serializer = OrganizationSerializer(organization)
        
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class GenerateInviteCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, organization_id):
        try:
            organization = Organization.objects.get(id=organization_id)
            if not request.user.is_member_of(organization):
                return Response(
                    {'error': 'You are not a member of this organization'},
                    status=status.HTTP_403_FORBIDDEN
                )
            invite_code = request.user.generate_invite_code(organization)
            return Response({'invite_code': invite_code})
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class JoinOrganizationView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        serializer = OrganizationInviteSerializer(data=request.data)
        if serializer.is_valid():
            try:
                organization = request.user.join_organization(
                    serializer.validated_data['invite_code']
                )
                return Response(OrganizationSerializer(organization).data)
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 