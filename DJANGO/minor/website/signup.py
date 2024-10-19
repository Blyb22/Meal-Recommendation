# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.conf import settings
from .models import Profile
import os
import pandas as pd

def signup_user(request):
    if request.method == 'POST':
        fname = request.POST.get('fname', 'default')
        lname = request.POST.get('lname', 'default')
        number = request.POST.get('number', 'default')
        email = request.POST.get('email', 'default')
        passw = request.POST.get('passw', 'default')
        re_pass = request.POST.get('re_pass', 'default')

        if len(fname) < 3 or fname.isnumeric():
            messages.error(request, "First Name should be a string with more than 2 characters")
            return render(request, 'website/signup.html')
        if len(lname) < 3 or lname.isnumeric():
            messages.error(request, "Last Name should be a string with more than 2 characters")
            return render(request, 'website/signup.html')
        if len(passw) < 5:
            messages.error(request, 'Length of password must be greater or equal to 5')
            return render(request, 'website/signup.html')
        if not passw.isalnum():
            messages.error(request, 'Password must be alphanumeric')
            return render(request, 'website/signup.html')
        if passw != re_pass:
            messages.error(request, 'Error! Password does not match')
            return render(request, 'website/signup.html')
        if len(number) != 10:
            messages.error(request, 'Error! Number must contain 10 digits')
            return render(request, 'website/signup.html')

        try:
            myuser = User.objects.get(username=number)
            messages.error(request, 'Number :- ' + myuser.username + ' already exists! Please use another number')
            return render(request, 'website/signup.html')
        except User.DoesNotExist:
            myuser = User.objects.create_user(username=number, email=email, password=passw)
            myuser.first_name = fname
            myuser.last_name = lname
            myuser.save()

            user = authenticate(username=number, password=passw)
            login(request, user)
            messages.success(request, "User created successfully, now please complete your profile")
            params = {'name': fname + " " + lname, 'number': number, 'email': email}
            return render(request, 'website/profile.html', params)
    else:
        return render(request, 'website/signup.html')

def fill_CSV(user, lst):
    # Define the CSV file path
    filename = os.path.join(settings.BASE_DIR, 'website', 'csvfile', 'user_Profiles.csv')

    # Check if file exists, if not, create a new one with column headers
    if not os.path.exists(filename):
        df = pd.DataFrame(columns=['User_Id', 'FoodType', 'Nutrient', 'Disease', 'Diet'])
    else:
        df = pd.read_csv(filename)

    # Check if the user already exists in the CSV
    if user in df['User_Id'].values:
        # Remove the old entry if it exists
        df = df[df['User_Id'] != user]

    # Create a new DataFrame for the new user data
    new_row = pd.DataFrame([lst], columns=df.columns)

    # Concatenate the new data
    df = pd.concat([df, new_row], ignore_index=True)

    # Write back to the CSV
    df.to_csv(filename, index=False)

def create_profile(request):
    if request.method == 'POST':
        # Correct way to get the image file, with a default value of None if not provided
        image = request.FILES.get('image', None)
        
        # Getting other form fields
        name = request.POST.get('name')
        email = request.POST.get('email')
        number = request.POST.get('number')
        gender = request.POST.get('gender')
        age = request.POST.get('age')
        blood = request.POST.get('blood')
        weight = request.POST.get('weight')
        height = request.POST.get('height')
        favfood = request.POST.get('favfood')
        
        # Handling list fields
        ft = request.POST.getlist('food')
        foodtype = "++".join(ft)
        
        dt = request.POST.getlist('diet')
        diet = "++".join(dt)
        
        cs = request.POST.getlist('cuisines')
        cuisines = "++".join(cs)
        
        nrt = request.POST.getlist('nutrient')
        nutrient = "++".join(nrt)
        
        des = request.POST.getlist('disease')
        disease = "++".join(des)
        
        medicalhistory = request.POST.get('medicalHistory')
        
        # Creating the profile
        prfl = Profile(
            name=name,
            email=email,
            number=number,
            gender=gender,
            age=age,
            blood=blood,
            weight=weight,
            height=height,
            favfood=favfood,
            foodtype=foodtype,
            diet=diet,
            nutrient=nutrient,
            cuisines=cuisines,
            disease=disease,
            medicalhistory=medicalhistory,
            image=image  # Save the image if uploaded
        )
        prfl.save()
        
        # Assuming fill_CSV is defined elsewhere for saving profile details to a CSV
        fill_CSV(request.user.username, [
            request.user.username,
            " ".join(ft),
            nutrient.replace("++", " "),
            disease.replace("++", " "),
            diet.replace("++", " ")
        ])
        
        # Success message and redirect
        messages.success(request, 'Profile created successfully')
        return redirect('Home')
    
    else:
        try:
            # Safely check if the image exists before trying to access the URL
            profile = Profile.objects.get(number=request.user.username)
            img = profile.image.url if profile.image else ""
        except Profile.DoesNotExist:
            img = ""
        
        return render(request, 'website/profile.html', {'image': img})