from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from .models import Contact, Profile
import os
import datetime
import pandas as pd

def index(request):
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(number=request.user.username)
            # Check if the profile has an associated image
            img = profile.image.url if profile.image else ""
        except Profile.DoesNotExist:
            img = ""
        
        return render(request, 'website/home.html', {'image': img})
    else:
        return render(request, 'website/home.html')


def login_user(request):
    if request.method == 'POST':
        number = request.POST.get('number', 'default')
        passw = request.POST.get('passw', 'default')

        if len(number) != 10:
            messages.error(request, 'Number must contain 10 digits')
        else:
            user = authenticate(username=number, password=passw)
            if user:
                login(request, user)
                messages.success(request, 'Successfully Logged in')
                return redirect('Home')
            else:
                messages.error(request, 'Error: Invalid Credentials, Please try again')
                return redirect('login')

    return render(request, 'website/login.html')

def logout_user(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Successfully Logged out')
        return redirect('Home')

def decider(request):
    if request.user.is_authenticated:
        v = Profile.objects.get(number=request.user.username).second_time
        return redirect('recommend' if not v else 'SecondRecommend')
    messages.error(request, 'You must be logged in for meal')
    return redirect('Home')


def buy(request):
    if request.method == 'POST':
        a = request.POST.get('product_buy', '')
        if not a:
            messages.error(request, "No product selected")
            return redirect('Home')

        l = list(a.split())
        
        filename = os.path.join(settings.BASE_DIR, 'website', 'csvfile', 'recent_activity.csv')
        
        try:
            df2 = pd.read_csv(filename)
        except FileNotFoundError:
            messages.error(request, "Recent activity file not found.")
            return redirect('Home')

        currentDT = datetime.datetime.now()
        new_rows = []

        for meal_id in l:
            new_row = [request.user.username, meal_id, 0, 0, 0, 1, currentDT.strftime("%m/%d/%Y %I:%M:%S %p")]
            new_rows.append(new_row)

        # Create a DataFrame from the new rows and append to the existing DataFrame
        new_df = pd.DataFrame(new_rows, columns=df2.columns)
        df2 = pd.concat([df2, new_df], ignore_index=True)
        
        df2.to_csv(filename, index=False)
        
        Profile.objects.filter(number=request.user.username).update(second_time=True)
        
    return redirect('Home')

def order(request):
    if request.user.is_authenticated:
        try:
            # Get user profile
            profile = Profile.objects.get(number=request.user.username)
            if not profile.second_time:
                messages.info(request, 'You have not ordered anything.')
                return render(request, 'website/orders.html')

            # Define file paths
            recent_activity_path = os.path.join(settings.BASE_DIR, 'website', 'csvfile', 'recent_activity.csv')
            dataset_path = os.path.join(settings.BASE_DIR, 'website', 'csvfile', 'dataset.csv')

            # Read CSV files
            try:
                recent_activity_df = pd.read_csv(recent_activity_path)
                dataset_df = pd.read_csv(dataset_path)
            except FileNotFoundError:
                messages.error(request, "Required files not found.")
                return redirect('Home')

            # Filter recent activity for the logged-in user
            user_activity = recent_activity_df.loc[recent_activity_df["User_Id"] == request.user.username]
            user_activity = user_activity.sort_values(by='Timestamp', ascending=False).drop_duplicates(subset=user_activity.columns.difference(['Timestamp']), keep="last")
            meal_ids = user_activity["Meal_Id"].unique()

            # Filter dataset based on meal ids
            data = dataset_df.loc[dataset_df["Meal_Id"].isin(meal_ids)].drop_duplicates(subset='Meal_Id', keep="first")

            # Prepare data for rendering
            if not data.empty and not user_activity.empty:
                # Make sure all required columns are present
                expected_columns = ['Name', 'Meal_Id', 'catagory', 'Veg_Non', 'Review', 'Nutrient', 'Price']
                if all(col in data.columns for col in expected_columns):
                    # Extract data into lists
                    names = data['Name'].tolist()
                    meal_ids = data['Meal_Id'].tolist()
                    categories = data['catagory'].tolist()
                    veg_non = data['Veg_Non'].tolist()
                    reviews = data['Review'].tolist()
                    nutrients = data['Nutrient'].tolist()
                    prices = data['Price'].tolist()

                    # Extract user activity data
                    likes = user_activity['Liked'].tolist()
                    rates = user_activity['Rated'].tolist()
                    timestamps = user_activity['Timestamp'].tolist()

                    # Zip the data together, ensuring we are unpacking correctly
                    data_zip = zip(names, meal_ids, categories, veg_non, reviews, nutrients, prices, likes, rates, timestamps)

                    # Handle image retrieval safely
                    img = profile.image.url if profile.image else None

                    return render(request, 'website/orders.html', {'data': data_zip, 'image': img})

            # If no data found
            messages.info(request, 'No orders found for your account.')
            return render(request, 'website/orders.html')

        except Profile.DoesNotExist:
            messages.error(request, "Profile does not exist.")
            return redirect('Home')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('Home')

    messages.error(request, 'You must be logged in to view orders.')
    return redirect('Home')

def LikeRate(request):
    if request.method == 'POST':
        ids = request.POST.get('idsinp', '').split(',')
        likes = request.POST.get('likeinp', '').split(',')
        rates = request.POST.get('rateinp', '').split(',')

        # Path to the CSV file
        filename = os.path.join(settings.BASE_DIR, 'website', 'csvfile', 'recent_activity.csv')

        try:
            df = pd.read_csv(filename)
        except FileNotFoundError:
            messages.error(request, "Recent activity file not found.")
            return redirect('Home')

        # Ensure data lengths match
        if not (len(ids) == len(likes) == len(rates)):
            messages.error(request, "Mismatch in input data lengths.")
            return redirect('Home')

        currentDT = datetime.datetime.now()

        # Loop through each ID and update the DataFrame
        for i, meal_id in enumerate(ids):
            # Remove existing entries for the user and meal
            df = df[~((df['User_Id'] == request.user.username) & (df['Meal_Id'] == meal_id))]

            # Create the new row with the correct number of columns (match this with your CSV structure)
            new_row = pd.Series({
                'User_Id': request.user.username,
                'Meal_Id': meal_id,
                'Rate': rates[i],
                'Like': likes[i],
                'DateTime': currentDT.strftime("%m/%d/%Y %I:%M:%S %p")
            })

            # Append the new row
            df = pd.concat([df, new_row.to_frame().T], ignore_index=True)

        # Write the updated DataFrame back to the CSV
        df.to_csv(filename, index=False)

        return redirect('Home')