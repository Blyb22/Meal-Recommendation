from .models import Profile
from django.shortcuts import render, redirect
from django.contrib import messages
import os
from django.conf import settings
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors

class Recommender:
    def __init__(self):
        self.df = pd.read_csv(os.path.join(settings.BASE_DIR, 'website', 'csvfile','dataset.csv'))
    
    def get_features(self):
        # Getting dummies of dataset
        nutrient_dummies = self.df.Nutrient.str.get_dummies()
        disease_dummies = self.df.Disease.str.get_dummies(sep=' ')
        diet_dummies = self.df.Diet.str.get_dummies(sep=' ')
        feature_df = pd.concat([nutrient_dummies, disease_dummies, diet_dummies], axis=1)
        return feature_df
    
    def k_neighbor(self, inputs):
        feature_df = self.get_features()
        
        # Initializing model with k=40 neighbors
        model = NearestNeighbors(n_neighbors=40, algorithm='ball_tree')
        
        # Fitting model with dataset features
        model.fit(feature_df)
        
        # Getting distance and indices for k nearest neighbor
        distances, indices = model.kneighbors(inputs)
        
        # Collect results in a list
        results = self.df.iloc[indices.flatten()].drop_duplicates(subset=['Name']).reset_index(drop=True
        )
        results = results[['Meal_Id', 'Name', 'catagory', 'Nutrient', 'Veg_Non', 'Price', 'Review', 'Diet', 'Disease', 'description']]
        return results

def Recommend(request):
    if request.user.is_authenticated:
        ob = Recommender()
        data = ob.get_features()
        
        total_features = data.columns
        d = {i: 0 for i in total_features}
        
        try:
            p = Profile.objects.get(number=request.user.username)  # Extract values from database where Table name is Profile
            diet = list(p.diet.split('++'))
            disease = list(p.disease.split('++'))
            nutrient = list(p.nutrient.split('++'))
        except Profile.DoesNotExist:
            messages.error(request, 'Profile not found.')
            return redirect('Home')

        Recommend_input = diet + disease + nutrient

        # Handle missing image safely
        image = p.image.url if p.image else 'path/to/default/image.png'  # Provide a default image path if none is set

        for i in Recommend_input:
            d[i] = 1
        final_input = list(d.values())
        
        results = ob.k_neighbor([final_input])  # Pass as a 2D array []
        
        data = dict(results)
        
        ids = list(data['Meal_Id'])
        n = list(data['Name'])
        c = list(data['catagory'])
        vn = list(data['Veg_Non'])
        r = list(data['Review'])
        nt = list(data['Nutrient'])  
        p = list(data['Price'])
        sc = c
        
        data = zip(n, ids, n, c, sc, vn, r, nt, p, p)
        
        return render(request, "website/recommend.html", {'data': data, 'image': image})

    else:
        messages.error(request, 'You must be logged in for meal recommendations.')
        return redirect('Home')