from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.db.models import Count
from django.contrib.postgres.search import (SearchVector,
                                            SearchQuery,
                                            SearchRank,
                                            TrigramSimilarity)

from .models import Post
from .forms import EmailPostForm, CommentForm, SearchForm
from django.views.generic import ListView
from django.views.decorators.http import require_POST
from taggit.models import Tag


# class PostListView(ListView):
#     model = Post
#     context_object_name = 'posts'
#     paginate_by = 3
#     template_name = 'blog/post/list.xhtml'

def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    if tag_slug is not None:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])

    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        posts = paginator.page(1)
    return render(request, 'blog/post/list.xhtml',
                  {'posts': posts, 'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    comments = post.comments.filter(active=True)
    form = CommentForm
    # [(1,), (2,), (3,)] ==>  [1, 2, 3] flat
    post_tags_ids = post.tags.values_list('id', flat=True)

    similar_posts = (Post.published.filter(tags__in=post_tags_ids)
                     .exclude(id=post.id))

    similar_posts = (similar_posts.annotate(same_tags=Count('tags'))
                     .order_by('-same_tags', 'publish'))

    return render(request, 'blog/post/detail.xhtml',
                  {'post': post,
                   'comments': comments,
                   'form': form,
                   'similar_posts': similar_posts
                   })


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False
    match request.method:
        case "POST":
            form = EmailPostForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                post_url = request.build_absolute_uri(post.get_absolute_path())
                subject = f"{cd['name']} recommends you read {post.title}"
                message = f"Read {post.title} at {post_url}\n\n" \
                          f"{cd['name']}\'s comments: {cd['comments']}"
                if send_mail(subject, message, 'iljavaleev@gmail.com',
                             [cd['to']]):
                    sent = True
        case _:
            form = EmailPostForm()
    return render(request, 'blog/post/share.xhtml',
                  {'post': post, 'form': form, 'sent': sent})


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    form = CommentForm(data=request.POST)
    comment = None
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
    return render(request,
                  'blog/post/comment.xhtml',
                  {'post': post, 'form': form, 'comment': comment})


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            # search_query = SearchQuery(query)
            # search_vector = (SearchVector('title', weight='A')
            #                  + SearchVector('body', weight='B'))
            # results = Post.published.annotate(
            #     search=search_vector,
            #     rank=SearchRank(search_vector, search_query)
            # ).filter(rank_gte=0.3).order_by('-rank')
            results = Post.published.annotate(
                similarity=TrigramSimilarity('title', query),
            ).filter(similarity__gt=0.1).order_by('-similarity')
    return render(request,
                  'blog/post/search.xhtml',
                  {'form': form,
                   'query': query,
                   'results': results})
