from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Profile
from .forms import (LoginForm,
                    UserRegistrationForm,
                    UserEditForm,
                    ProfileEditForm)


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request=request,
                                username=cd['username'],
                                password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponse('Success auth')
                else:
                    return HttpResponse('Disabled account')
            return HttpResponse('Invalid login')
    return render(request, 'account/login.html', {'form': LoginForm()})


@login_required
def dashboard(request):
    return render(request,
                  'account/dashboard.xhtml',
                  {'section': 'dashboard'})


def register(request):
    form = UserRegistrationForm()
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password']) #set_password() method handles password hashing before storing the password in the database.
            user.save()
            Profile.objects.create(user=user)

            return render(request,
                          'account/register_done.xhtml',
                          {'new_user': user})
    return render(request,
                  'account/register.xhtml',
                  {'user_form': form})


@login_required
def edit(request):
    user_form = UserEditForm(instance=request.user)
    profile_form = ProfileEditForm(
        instance=request.user.profile)
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user,
                                 data=request.POST)
        profile_form = ProfileEditForm(
            instance=request.user.profile,
            data=request.POST,
            files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully')
        else:
            messages.error(request, 'Error updating your profile')
    return render(request,
                  'account/edit.xhtml',
                  {'user_form': user_form,
                   'profile_form': profile_form})
