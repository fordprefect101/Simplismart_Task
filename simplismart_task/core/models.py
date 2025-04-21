from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def create_organization(self, name, description=""):
       
        organization = Organization.objects.create(
            name=name,
            description=description,
            created_by=self
        )
        OrganizationMembership.objects.create(
            user=self,
            organization=organization,
            role='admin'
        )
        return organization

    def join_organization(self, invite_code):  
        try:
            token = RefreshToken(invite_code)
            payload = token.payload
            
            organization_id = payload.get('organization_id')
            if not organization_id:
                raise ValueError("Invalid invite code: missing organization ID")
            
            organization = Organization.objects.get(id=organization_id)
            
            if self.is_member_of(organization):
                raise ValueError("You are already a member of this organization")
            
            OrganizationMembership.objects.create(
                user=self,
                organization=organization,
                role='member'
            )
            return organization
        except Exception as e:
            raise ValueError(f"Invalid invite code: {str(e)}")

    def generate_invite_code(self, organization):
        if not self.is_member_of(organization):
            raise ValueError("User is not a member of this organization")
        
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken()
        token['organization_id'] = organization.id
        return str(token)

    def is_member_of(self, organization):
        return OrganizationMembership.objects.filter(
            user=self,
            organization=organization
        ).exists()

    def is_admin_of(self, organization):
        return OrganizationMembership.objects.filter(
            user=self,
            organization=organization,
            role='admin'
        ).exists()

class Cluster(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clusters')
    
    total_cpu = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total CPU cores available in the cluster"
    )
    total_ram = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total RAM in GB available in the cluster"
    )
    total_gpu = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total GPU units available in the cluster"
    )
    
    @property
    def available_cpu(self):
        used = sum(res.used_cpu for res in self.resource_usage.all())
        return self.total_cpu - used

    @property
    def available_ram(self):
        used = sum(res.used_ram for res in self.resource_usage.all())
        return self.total_ram - used

    @property
    def available_gpu(self):
        used = sum(res.used_gpu for res in self.resource_usage.all())
        return self.total_gpu - used

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (Owner: {self.owner.email})"

    class Meta:
        ordering = ['-created_at']

class ResourceUsage(models.Model):
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE, related_name='resource_usage')
    
    used_cpu = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of CPU cores used"
    )
    used_ram = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Amount of RAM in GB used"
    )
    used_gpu = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of GPU units used"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Resource usage for {self.cluster.name}"

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.used_cpu > self.cluster.available_cpu:
            raise ValueError(f"Cannot use {self.used_cpu} CPU cores. Only {self.cluster.available_cpu} available.")
        if self.used_ram > self.cluster.available_ram:
            raise ValueError(f"Cannot use {self.used_ram} GB RAM. Only {self.cluster.available_ram} available.")
        if self.used_gpu > self.cluster.available_gpu:
            raise ValueError(f"Cannot use {self.used_gpu} GPU units. Only {self.cluster.available_gpu} available.")
        super().save(*args, **kwargs)

class Deployment(models.Model):
    name = models.CharField(max_length=255)
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE, related_name='deployments')
    docker_image = models.CharField(max_length=255)
    required_cpu = models.FloatField()
    required_ram = models.FloatField()
    required_gpu = models.FloatField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('stopped', 'Stopped'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.cluster.name})"

    def save(self, *args, **kwargs):
        if self.required_cpu < 0 or self.required_ram < 0 or self.required_gpu < 0:
            raise ValueError("Resource requirements cannot be negative")
        
        if (self.required_cpu > self.cluster.available_cpu or
            self.required_ram > self.cluster.available_ram or
            self.required_gpu > self.cluster.available_gpu):
            raise ValueError("Cluster does not have enough resources")
        
        super().save(*args, **kwargs)

class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_organizations')
    members = models.ManyToManyField(User, through='OrganizationMembership', related_name='organizations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

class OrganizationMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Admin'),
            ('member', 'Member')
        ],
        default='member'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'organization')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})" 