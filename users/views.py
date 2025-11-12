from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create UserProfile
            user_profile = user.userprofile
            user_profile.phone = form.cleaned_data.get('phone')
            user_profile.address = form.cleaned_data.get('address')
            user_profile.city = form.cleaned_data.get('city')
            user_profile.state = form.cleaned_data.get('state')
            user_profile.pincode = form.cleaned_data.get('pincode')
            user_profile.save()
            
            # Auto-create a basic DonorProfile
            from donations.models import DonorProfile
            DonorProfile.objects.create(
                user=user,
                organization_name=user.username,
                user_type='individual',
                phone=user_profile.phone,
                address=user_profile.address,
                city=user_profile.city,
                state=user_profile.state,
                pincode=user_profile.pincode
            )
            
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, instance=request.user.userprofile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.userprofile)
    
    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'users/profile.html', context)

from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages

def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')