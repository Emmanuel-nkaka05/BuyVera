from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth import get_user_model
from .forms import RegistrationForm
from .models import UserProfile
from django.contrib.auth.decorators import login_required
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
                first_name=first_name, 
                last_name=last_name, 
                email=email, 
                username=username, 
                phone_number=phone_number,
                password=password
            )
            
            # Set seller status based on selection
            if role == 'seller':
                user.is_seller = True
            else:
                user.is_seller = False
                
            user.save()
            
            if role == 'seller':
                messages.success(request, 'Seller account created! Please log in to upload your products.')
            else:
                messages.success(request, 'Buyer account created! Please log in to start shopping.')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login(request):
    if request.method == 'POST':
        email = request.POST.get('username') 
        password = request.POST.get('password')
        
        # Authenticate using email since USERNAME_FIELD = 'email'
        user = auth.authenticate(email=email, password=password)
        
        if user is not None:
            auth.login(request, user)
            messages.success(request, 'You are now logged in.')
            
            role = request.POST.get('role', 'buyer')
            
            if role == 'seller':
                return redirect('dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid login credentials. Please use your email address.')
            return redirect('login')
            
    return render(request, 'accounts/login.html')

def logout(request):
    auth.logout(request)
    messages.success(request, 'You are logged out.')
    return redirect('login')

def edit_profile(request):
    userprofile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.phone_number = request.POST.get('phone_number', request.user.phone_number)
        request.user.save()

        userprofile.address_line_1 = request.POST.get('address_line_1', '')
        userprofile.address_line_2 = request.POST.get('address_line_2', '')
        userprofile.city = request.POST.get('city', '')
        userprofile.state = request.POST.get('state', '')
        userprofile.country = request.POST.get('country', '')
        
        if 'profile_picture' in request.FILES:
            userprofile.profile_picture = request.FILES['profile_picture']
            
        userprofile.save()
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('edit_profile')

    context = {
        'userprofile': userprofile,
    }
    return render(request, 'accounts/edit_profile.html', context)
@login_required(login_url='login')
def upgrade_to_seller(request):
    if request.method == 'POST':
        # Change the user's status to seller
        user = request.user
        user.is_seller = True
        user.save()
        
        messages.success(request, 'Congratulations! Your account has been upgraded to a Seller.')
        return redirect('dashboard')
        
    return render(request, 'accounts/upgrade_seller.html')