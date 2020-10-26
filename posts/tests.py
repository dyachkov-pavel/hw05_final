from django import template
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls.base import reverse
from .models import Comment, Post, Group, Follow
from .forms import PostForm
from PIL import Image
from django.core.cache import cache
import tempfile


User = get_user_model()


class TestViewMethods(TestCase):
    def setUp(self):
        self.client = Client()
        self.unauthorized_client = Client()
        self.user = User.objects.create(username='user')
        self.client.force_login(self.user)
        self.group_1 = Group.objects.create(
            title='test_title',
            slug='test_slug'
        )

    def test_profile(self):
        url = reverse('profile', kwargs={'username': self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_new_post_authorized(self):
        original_text = 'test_text'
        url = reverse('new_post')
        self.client.post(
            url, {'text': original_text, 'group': self.group_1.id})
        post = Post.objects.first()
        self.assertEqual(original_text, post.text)
        self.assertEqual(self.user, post.author)
        self.assertEqual(self.group_1, post.group)
        self.assertEqual(Post.objects.count(), 1)

    def test_new_post_unauthorized(self):
        url = reverse('new_post')
        response = self.unauthorized_client.get(url)
        url_redirect = reverse('login') + '?next=' + reverse('new_post')
        self.assertEqual(Post.objects.count(), 0)
        self.assertRedirects(response, url_redirect)

    def check_posts(self, url, post, user):
        response = self.client.get(url)
        if 'page' in response.context:
            response_post = response.context['page'][0]
        else:
            response_post = response.context['post']
        self.assertEqual(response_post, post)
        self.assertEqual(response_post.author, user)
        self.assertEqual(response_post.group, post.group)

    def test_pages_contains_new_post(self):
        original_text = 'test_text'
        post = Post.objects.create(
            text=original_text,
            author=self.user,
            group=self.group_1
        )
        urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.user.username}),
            reverse('post', kwargs={
                    'username': self.user.username, 'post_id': post.id}),
            reverse('group_posts', kwargs={'slug': self.group_1.slug})
        ]
        for url in urls:
            self.check_posts(url, post, self.user)

    def test_post_edit(self):
        original_text = 'test_text'
        post = Post.objects.create(
            text=original_text,
            author=self.user,
            group=self.group_1
        )
        group_2 = Group.objects.create(
            title='test_title2',
            slug='test_slug2'
        )
        url_edit_post = reverse('post_edit',
                                kwargs={
                                    'username': self.user.username,
                                    'post_id': post.id}
                                )
        self.client.post(
            url_edit_post, {'text': 'test_text_updated', 'group': group_2.id})
        edited_post = Post.objects.last()
        urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.user.username}),
            reverse('post', kwargs={
                    'username': self.user.username, 'post_id': post.id}),
            reverse('group_posts', kwargs={'slug': group_2.slug}),
        ]
        for url in urls:
            self.check_posts(url, edited_post, self.user)
        response = self.client.get(
            reverse('group_posts', kwargs={'slug': self.group_1.slug}))
        self.assertEqual(response.context['paginator'].count, 0)

    def test_page_not_found(self):
        url_not_found = '/unknown_adress/22123/'
        response = self.client.get(url_not_found)
        self.assertEqual(response.status_code, 404)
    

    def test_add_comment_unauthorized(self):
        post = Post.objects.create(
            text='text',
            author=self.user,
            group=self.group_1
        )
        comment_url = reverse('add_comment', kwargs={'username': self.user.username,'post_id': post.id})
        response = self.unauthorized_client.get(comment_url)
        url_redirect = reverse('login') + '?next=' + comment_url
        self.assertEqual(Comment.objects.count(), 0)
        self.assertRedirects(response, url_redirect)
    
    def test_add_comment_authorized(self):
        post = Post.objects.create(
            text='test_text',
            author=self.user,
            group=self.group_1
        )
        comment_url = reverse('add_comment', kwargs={'username': self.user.username,'post_id': post.id})
        response = self.client.post(comment_url, 
                                   {'post': post.id,
                                    'author': self.user,
                                    'text': 'test_comm',}
                                   )
        self.assertEqual(Comment.objects.count(), 1)
        post_url = reverse('post', kwargs={
                    'username': self.user.username, 'post_id': post.id})
        comment = Comment.objects.last()
        response = self.client.get(post_url)
        self.assertEqual(response.context['comments'][0], comment)


class TestImg(TestCase): 
    def setUp(self): 
        self.client = Client() 
        self.user = User.objects.create(username='user') 
        self.client.force_login(self.user)
        self.group_1 = Group.objects.create(
            title='test_title',
            slug='test_slug'
        )
         
    def check_img_tag(self, url):
        response = self.client.get(url)
        self.assertContains(response, '<img')

    def test_img_tag(self):
        original_text = 'post without image'
        post = Post.objects.create(
            text=original_text,
            author=self.user,
            group=self.group_1
        )
        post_edit_url = reverse('post_edit',
                                kwargs={
                                'username': self.user.username,
                                'post_id': post.id}
                                )
        img = Image.new('RGB', (60, 30), color = 'red')
        img.save('red.png')
        with open('red.png','rb') as img:
            self.client.post(post_edit_url,
                        {'author': self.user,
                        'text': 'post with image',
                        'image': img,
                        'group': self.group_1.id}
                        )
        post_with_img = Post.objects.first()
        self.assertEqual(post_with_img.text, 'post with image')
        urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.user.username}),
            reverse('post', kwargs={'username': self.user.username, 'post_id': post.id}),
            reverse('group_posts', kwargs={'slug': self.group_1.slug})
        ]
        for url in urls:
            self.check_img_tag(url)
        self.assertEqual(Post.objects.count(), 1)

    def test_non_img_file(self):
        cache.clear()
        original_text = 'post without image'
        post = Post.objects.create(
            text=original_text,
            author=self.user,
            group=self.group_1
        )
        post_edit_url = reverse('post_edit',
                                kwargs={
                                'username': self.user.username,
                                'post_id': post.id}
                                )
        fp = tempfile.TemporaryFile()
        fp.write(b'Hello world!')
        with fp as fake_img:
            self.client.post(post_edit_url,
                            {'author': self.user,
                            'text': 'post with image',
                            'image': fake_img,
                            'group': self.group_1.id}
                            )
        response = self.client.get(reverse('index'))
        self.assertNotContains(response, '<img')


class TestFollow(TestCase): 
    def setUp(self): 
        self.client = Client() 
        self.main_user = User.objects.create(username='main_user')
        self.client.force_login(self.main_user)
        self.user_2 = User.objects.create(username='user_2')
        self.passive_user = User.objects.create(username='passive_user')
        self.group_1 = Group.objects.create(
            title='test_title',
            slug='test_slug'
        )
        self.post = Post.objects.create(text='test_text', author=self.user_2, group=self.group_1)

    
    def test_follow(self):
        follow_url = reverse('profile_follow', kwargs={'username':self.user_2.username})
        self.client.get(follow_url)
        self.assertEqual(Follow.objects.count(), 1)
        follow_index_url = reverse('follow_index')
        response_main_user = self.client.get(follow_index_url)
        self.assertEqual(response_main_user.context['page'][0], self.post)
        self.client.force_login(self.passive_user)
        response_passive_user = self.client.get(follow_index_url)
        self.assertEqual(response_passive_user.context['paginator'].count, 0)

    
    def test_unfollow(self):
        Follow.objects.create(user=self.main_user, author=self.user_2)
        unfollow_url = reverse('profile_unfollow', kwargs={'username':self.user_2.username})
        self.client.get(unfollow_url)
        self.assertEqual(Follow.objects.count(), 0)