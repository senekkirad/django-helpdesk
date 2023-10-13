#from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, reverse, redirect
from django.http import HttpResponseRedirect, HttpResponse
from .admin import  AddUserForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
# Create your views here.

def signup_view(request):
    if request.method == 'POST':
        form = AddUserForm(data=request.POST)
        if form.is_valid():
            user =  form.save()
            return redirect('login')
    else:
        form = AddUserForm()
        args = {'form' : form}
        return render(request, 'signup.html', args)

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(username=email, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse('list_tickets'))
        else:
            return HttpResponse("Invalid login details")
    else:
        return render(request, 'login.html', {})

@login_required(login_url='/user/login/')
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))
