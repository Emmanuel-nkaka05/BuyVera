from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth import get_user_model
from .forms import RegistrationForm
from .models import UserProfile

User = get_user_model()

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            phone_number = form.cleaned_data['phone_number']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role']

            user = User.objects.create_user(
                first_name=first_name, last_name=last_name, email=email, 
                username=username, phone_number=phone_number, password=password
            )
            user.save()
            
            if role == 'seller':
                messages.success(request, 'Seller account created! Please log in.')
            else:
                messages.success(request, 'Buyer account created! Please log in.')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        
        if user is not None:
            auth.login(request, user)
            messages.success(request, 'You are now logged in.')
            role = request.POST.get('role', 'buyer')
            if role == 'seller':
                return redirect('dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid login credentials.')
            return redirect('login')
    return render(request, 'accounts/login.html')

def logout(request):
    auth.logout(request)
    messages.success(request, 'You are logged out.')
    return redirect('login')

def edit_profile(request):
    userprofile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        request.user.first_name = request.POST['first_name']
        request.user.last_name = request.POST['last_name']
        request.user.phone_number = request.POST['phone_number']
        request.user.save()

        userprofile.address_line_1 = request.POST['address_line_1']
        userprofile.address_line_2 = request.POST['address_line_2']
        userprofile.city = request.POST['city']
        userprofile.state = request.POST['state']
        userprofile.country = request.POST['country']
        
        if 'profile_picture' in request.FILES:
            userprofile.profile_picture = request.FILES['profile_picture']
            
        userprofile.save()
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('edit_profile')

    context = {'userprofile': userprofile}
    return render(request, 'accounts/edit_profile.html', context)