from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserViewSet,
    CustomTokenObtainPairView,
    ClusterViewSet,
    ResourceUsageViewSet,
    DeploymentViewSet,
    OrganizationViewSet,
    GenerateInviteCodeView,
    JoinOrganizationView
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'clusters', ClusterViewSet)
router.register(r'resource-usage', ResourceUsageViewSet)
router.register(r'deployments', DeploymentViewSet)
router.register(r'organizations', OrganizationViewSet)

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('organizations/<int:organization_id>/invite/', GenerateInviteCodeView.as_view(), name='generate-invite'),
    path('join-organization/', JoinOrganizationView.as_view(), name='join-organization'),
    path('', include(router.urls)),
] 