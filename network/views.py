from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
import json
from django.http import JsonResponse
from .models import User, Post, Follow, Like


def index(request):
    all_posts = Post.objects.all().order_by("id").reverse()

    pagintator = Paginator(all_posts, 10)
    page_number = request.GET.get('page')
    posts_on_page = pagintator.get_page(page_number)

    all_likes = Like.objects.all()
    posts_liked = []
    try:
        for like in all_likes:
            if like.user.id == request.user.id:
                posts_liked.append(like.post.id)
    except:
        posts_liked = []

    return render(request, "network/index.html", {
        'all_posts': all_posts,
        'posts_on_page': posts_on_page,
        'posts_liked': posts_liked
    })


def new_post(request):
    if request.method == 'POST':
        content = request.POST["content"]
        if content:
            user = User.objects.get(pk=request.user.id)
            post = Post(content=content, user=user)
            post.save()
            return HttpResponseRedirect(reverse(index))
        else:
            return render(request, "network/index.html", {
                "message": "Cannot submit blank post."
            })


def profile(request, user_id):
    user = User.objects.get(pk=user_id)
    all_posts = Post.objects.filter(user=user).order_by("id").reverse()

    pagintator = Paginator(all_posts, 10)
    page_number = request.GET.get('page')
    posts_on_page = pagintator.get_page(page_number)

    following = Follow.objects.filter(user=user)
    followers = Follow.objects.filter(user_followed=user)

    try:
        check_following = followers.filter(user=User.objects.get(pk=request.user.id))
        if len(check_following) != 0:
            is_following = True
        else:
            is_following = False
    except:
        is_following = False

    return render(request, "network/profile.html", {
        'all_posts': all_posts,
        'posts_on_page': posts_on_page,
        'username': user.username,
        'following': following,
        'followers': followers,
        'is_following': is_following,
        'user_profile': user
    })


def follow(request):
    user_follow = request.POST["user_follow"]
    current_user = User.objects.get(pk=request.user.id)
    user_follow_data = User.objects.get(username=user_follow)
    f = Follow(user=current_user, user_followed=user_follow_data)
    f.save()
    user_id = user_follow_data.id
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id}))


def unfollow(request):
    user_follow = request.POST["user_follow"]
    current_user = User.objects.get(pk=request.user.id)
    user_follow_data = User.objects.get(username=user_follow)
    f = Follow.objects.get(user=current_user, user_followed=user_follow_data)
    f.delete()
    user_id = user_follow_data.id
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id}))


def following(request):
    current_user = User.objects.get(pk=request.user.id)
    users_following = Follow.objects.filter(user=current_user)
    all_posts = Post.objects.all().order_by("id").reverse()
    posts_from_following = []

    for post in all_posts:
        for user in users_following:
            if user.user_followed == post.user:
                posts_from_following.append(post)

    all_likes = Like.objects.all()
    posts_liked = []
    try:
        for like in all_likes:
            if like.user.id == request.user.id:
                posts_liked.append(like.post.id)
    except:
        posts_liked = []

    pagintator = Paginator(posts_from_following, 10)
    page_number = request.GET.get('page')
    posts_on_page = pagintator.get_page(page_number)

    return render(request, "network/following.html", {
        'all_posts': all_posts,
        'posts_on_page': posts_on_page,
        'posts_liked': posts_liked
    })


def edit(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        edit_post = Post.objects.get(pk=post_id)
        edit_post.content = data["content"]
        edit_post.save()
        return JsonResponse({"message": "Change successful", "data": data["content"]})


def unlike(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    like = Like.objects.filter(user=user, post=post)
    like.delete()
    return JsonResponse({"message": "Like deleted"})


def like(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    new_like = Like(user=user, post=post)
    new_like.save()
    return JsonResponse({"message": "Like added"})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
