from django.http import request
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, Comment, Follow
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

User = get_user_model()


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator, }
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request,
                  "group.html",
                  {
                      "group": group,
                      "posts": posts,
                      "page": page,
                      'paginator': paginator,
                  }
                  )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("index")
    return render(request, "new_post.html", {"form": form})


def profile(request, username):
    is_following = False
    author = get_object_or_404(User, username=username)
    post_list = author.author_posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    subscribers = Follow.objects.filter(author=author).count()
    is_subscribed = Follow.objects.filter(user=author).count()
    if request.user.is_authenticated:
        following = Follow.objects.filter(user = request.user, author=author)
        is_following = True if following else False
    return render(request,
                  'profile.html',
                  {
                      'author': author,
                      'page': page,
                      'paginator': paginator,
                      'post_list': post_list,
                      'is_following': is_following,
                      'subscribers': subscribers,
                      'is_subscribed': is_subscribed,
                  }
                  )


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id, author__username=username)
    comments = post.comment.all()
    is_following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(user = request.user, author=author)
        is_following = True if following else False
    subscribers = Follow.objects.filter(author=author).count()
    is_subscribed = Follow.objects.filter(user=author).count()
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post_id = post_id
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request,
                  'post.html',
                  {
                      'author': post.author,
                      'post': post,
                      'comments': comments,
                      'form': form,
                      'subscribers': subscribers,
                      'is_subscribed': is_subscribed,
                      'is_following': is_following
                  }
                  )


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post_id = post_id
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'comments.html', {'form': form})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user != post.author:
        return redirect('post', usermame=username, post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request,
                  'new_post.html',
                  {
                      'post': post,
                      'update': True,
                      'form': form,
                      'author': post.author,
                  }
                  )


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)

@login_required
def follow_index(request):
    main_user = get_object_or_404(User, username=request.user)
    following = Follow.objects.filter(user=main_user)
    followed_authors = []
    for followed_author in following:
        followed_authors.append(followed_author.author)
    post_list = Post.objects.filter(author__in=followed_authors)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request,
                  'follow.html',
                  {
                    'page': page,
                    'paginator': paginator,
                    'post_list': post_list,
                  }
                  )


@login_required
def profile_follow(request, username):
    if username == request.user.username:
        return redirect('profile', username=username)
    main_user = request.user
    to_follow = User.objects.get(username=username)
    following = Follow.objects.filter(user = main_user, author = to_follow)
    is_following = True if following else False
    if is_following == False:
        Follow.objects.create(user=main_user, author=to_follow)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    main_user = request.user
    to_follow = User.objects.get(username=username)
    following = Follow.objects.filter(user = main_user, author = to_follow)
    is_following = True if following else False
    if is_following == True:
        Follow.objects.filter(user=main_user, author=to_follow).delete()
    return redirect('profile', username=username)
