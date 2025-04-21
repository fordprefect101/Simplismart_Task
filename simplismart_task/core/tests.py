from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Cluster, ResourceUsage
from .rabbitmq import RabbitMQPublisher
import json
from unittest.mock import patch, MagicMock
import pika

User = get_user_model()

class TestUserModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.check_password('testpass123'))

class TestClusterModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.cluster = Cluster.objects.create(
            name='Test Cluster',
            description='Test Description',
            total_cpu=4,
            total_ram=8,
            total_gpu=1,
            owner=self.user
        )

    def test_cluster_creation(self):
        self.assertEqual(self.cluster.name, 'Test Cluster')
        self.assertEqual(self.cluster.total_cpu, 4)
        self.assertEqual(self.cluster.available_cpu, 4)
        self.assertEqual(self.cluster.owner, self.user)

    def test_cluster_str_representation(self):
        self.assertEqual(str(self.cluster), f"{self.cluster.name} (Owner: {self.user.email})")

class TestResourceUsageModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.cluster = Cluster.objects.create(
            name='Test Cluster',
            description='Test Description',
            total_cpu=4,
            total_ram=8,
            total_gpu=1,
            owner=self.user
        )
        self.resource_usage = ResourceUsage.objects.create(
            cluster=self.cluster,
            used_cpu=2,
            used_ram=4,
            used_gpu=0
        )

    def test_resource_usage_creation(self):
        self.assertEqual(self.resource_usage.cluster, self.cluster)
        self.assertEqual(self.resource_usage.used_cpu, 2)
        self.assertEqual(self.resource_usage.used_ram, 4)
        self.assertEqual(self.resource_usage.used_gpu, 0)

    def test_resource_usage_str_representation(self):
        self.assertEqual(str(self.resource_usage), f"Resource usage for {self.cluster.name}")

class TestRabbitMQPublisher(TestCase):
    @patch('pika.BlockingConnection')
    def test_publisher_initialization(self, mock_connection):
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        
        publisher = RabbitMQPublisher()
        
        # Verify connection setup
        mock_connection.assert_called_once()
        mock_channel.exchange_declare.assert_called_once()
        mock_channel.queue_declare.assert_called_once()
        mock_channel.queue_bind.assert_called_once()

    @patch('pika.BlockingConnection')
    def test_publish_deployment(self, mock_connection):
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        
        publisher = RabbitMQPublisher()
        deployment_data = {
            'id': 1,
            'name': 'Test Deployment',
            'cluster': 1,
            'docker_image': 'test/image:latest',
            'required_cpu': 2.0,
            'required_ram': 4.0,
            'required_gpu': 0.5
        }
        
        result = publisher.publish_deployment(deployment_data)
        
        self.assertTrue(result)
        mock_channel.basic_publish.assert_called_once()

class TestAPIEndpoints(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.cluster = Cluster.objects.create(
            name='Test Cluster',
            description='Test Description',
            total_cpu=4,
            total_ram=8,
            total_gpu=1,
            owner=self.user
        )

    def test_create_cluster(self):
        url = reverse('cluster-list')
        data = {
            'name': 'New Cluster',
            'description': 'New Description',
            'total_cpu': 8.0,
            'total_ram': 16.0,
            'total_gpu': 2.0
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cluster.objects.count(), 2)

    def test_use_resources(self):
        url = reverse('cluster-use-resources', kwargs={'pk': self.cluster.id})
        data = {
            'used_cpu': 2,
            'used_ram': 4,
            'used_gpu': 0
        }
        
        response = self.client.post(url, data, format='json')
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify resource usage was created
        self.assertEqual(ResourceUsage.objects.count(), 1)
        resource_usage = ResourceUsage.objects.first()
        self.assertEqual(resource_usage.used_cpu, 2)
        self.assertEqual(resource_usage.used_ram, 4)
        self.assertEqual(resource_usage.used_gpu, 0)

    def test_get_cluster_resources(self):
        url = reverse('cluster-resources', kwargs={'pk': self.cluster.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_cpu'], 4)
        self.assertEqual(response.data['total_ram'], 8)
        self.assertEqual(response.data['total_gpu'], 1)
        self.assertEqual(response.data['available_cpu'], 4)
        self.assertEqual(response.data['available_ram'], 8)
        self.assertEqual(response.data['available_gpu'], 1)

    def test_unauthorized_access(self):
        self.client.force_authenticate(user=None)
        url = reverse('cluster-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) 