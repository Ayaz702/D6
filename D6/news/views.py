from django.shortcuts import render, reverse, redirect
from django.views.generic import ListView, UpdateView, CreateView, DetailView, DeleteView
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin

from .models import *
from .filters import NewsFilter
from .forms import NewsForm

class NewsList(ListView):
  model = Post
  template_name = 'news.html'
  context_object_name = 'news'
  paginate_by = 10
  form_class = NewsForm

  def get_context_data(self, **kwargs): 
    context = super().get_context_data(**kwargs)
    context['filter'] = NewsFilter(self.request.GET, queryset=self.get_queryset())
    return context
    
class NewsSearch(ListView):
  model = Post
  template_name = 'news_filter.html'
  context_object_name = 'news'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['filter'] = NewsFilter(self.request.GET, queryset=self.get_queryset())
    return context

class NewsDetailView(DetailView):
    template_name = 'news_detail.html'
    queryset = Post.objects.all()


class NewsCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    permission_required = ('news.add_post', )
    template_name = 'news_add.html'
    form_class = NewsForm

    def post(self, request, *args, **kwargs):
        form = NewsForm(request.POST)
        post_category_pk = request.POST['postCategory']
        sub_text = request.POST.get('text')
        sub_title = request.POST.get('title')
        post_category = Category.objects.get(pk=post_category_pk)
        subscribers = post_category.subscribers.all()
        host = request.META.get('HTTP_HOST')
    

        if form.is_valid():
            news = form.save(commit=False)
            news.save()
    

        for subscriber in subscribers:
            html_content = render_to_string(
                'mail.html', {'user': subscriber, 'text': sub_text[:50], 'post': news, 'title': sub_title, 'host': host}
            )
    

            msg = EmailMultiAlternatives(
                subject=f'Здравствуй, {subscriber.username}! Новая статья в вашем любимом разделе!',
                body=f'{sub_text[:50]}',
                from_email='mailForSkillfactory@yandex.ru',
                to=[subscriber.email],
            )

            msg.attach_alternative(html_content, "text/html")
            msg.send()
        return redirect('/news/')


class NewsUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    permission_required = ('news.change_post', )
    template_name = 'news_edit.html'
    form_class = NewsForm

    def get_object(self, **kwargs):
      id = self.kwargs.get('pk')
      return Post.objects.get(pk=id)

class NewsDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    permission_required = ('news.delete_post', )
    template_name = 'news_delete.html'
    queryset = Post.objects.all()
    success_url = '/news/'
    
# D6
class CategoryList(ListView):
    model = Category
    template_name = 'category_list.html'
    context_object_name = 'categories'


class CategoryDetail(DetailView):
    template_name = 'category_subscription.html'
    model = Category

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_id = self.kwargs.get('pk')
        category_subscribers = Category.objects.filter(pk=category_id).values("subscribers__username")
        context['is_not_subscribe'] = not category_subscribers.filter(subscribers__username=self.request.user).exists()
        context['is_subscribe'] = category_subscribers.filter(subscribers__username=self.request.user).exists()
        return context


@login_required
def add_subscribe(request, **kwargs):
    pk = request.GET.get('pk', )
    print('Пользователь', request.user, 'добавлен в подписчики категории:', Category.objects.get(pk=pk))
    Category.objects.get(pk=pk).subscribers.add(request.user)
    return redirect('/news/categories')


@login_required
def del_subscribe(request, **kwargs):
    pk = request.GET.get('pk', )
    print('Пользователь', request.user, 'удален из подписчиков категории:', Category.objects.get(pk=pk))
    Category.objects.get(pk=pk).subscribers.remove(request.user)
    return redirect('/news/categories')