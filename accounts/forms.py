from django import forms
from django.contrib.auth import get_user_model

# Use your custom Account model
User = get_user_model()

class RegistrationForm(forms.ModelForm):
    # Add a role choice field
    ROLE_CHOICES = (
        ('buyer', 'I want to buy items (Buyer)'),
        ('seller', 'I want to sell items (Seller)'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect, initial='buyer')

    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Enter Password', 'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'phone_number']

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter First Name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter Last Name'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter Email Address'
        self.fields['username'].widget.attrs['placeholder'] = 'Enter Username'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Enter Phone Number'
        
        # Add Bootstrap class to all fields except role
        for field in self.fields:
            if field != 'role':
                self.fields[field].widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError("Password does not match!")