from django.test import TestCase
from django.urls import reverse
from blog_app.models import Post
from django.utils import timezone

class PostModelTests(TestCase):
    def test_post_creation(self):
        post = Post.objects.create(
            title="Test Post",
            content="This is a test post.",
            publish_date=timezone.now()
        )
        self.assertEqual(post.title, "Test Post")
        self.assertEqual(post.content, "This is a test post.")
        self.assertIsNotNone(post.publish_date)

class PostViewTests(TestCase):
    def setUp(self):
        self.post = Post.objects.create(
            title="Test Post",
            content="This is a test post.",
            publish_date=timezone.now()
        )

    def test_post_display(self):
        url = reverse('post_detail', args=[self.post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.title)
        self.assertContains(response, self.post.content)

    def test_post_list_display(self):
        url = reverse('post_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.title)