from .models import Profile
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import os
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from collections import Counter
import warnings

warnings.filterwarnings('ignore')

def Recommend(request):
    if request.user.is_authenticated:
        class Recommender:

            def __init__(self, profiles, recent_activity, dataset):
                self.df = dataset
                self.profiles = profiles
                self.recent_activity = recent_activity

            def get_features(self, dataframe):
                nutrient_dummies = dataframe.Nutrient.str.get_dummies()
                disease_dummies = dataframe.Disease.str.get_dummies(sep=' ')
                diet_dummies = dataframe.Diet.str.get_dummies(sep=' ')
                feature_df = pd.concat([nutrient_dummies, disease_dummies, diet_dummies], axis=1)
                return feature_df

            def find_neighbors(self, dataframe, features, k):
                features_df = self.get_features(dataframe)
                total_features = features_df.columns
                d = {i: 0 for i in total_features}
                for i in features:
                    d[i] = 1
                final_input = list(d.values())

                similar_neighbors = self.k_neighbor([final_input], features_df, dataframe, k)
                return similar_neighbors

            def k_neighbor(self, inputs, feature_df, dataframe, k):
                model = NearestNeighbors(n_neighbors=k, algorithm='ball_tree')
                model.fit(feature_df)

                results = []
                distances, indices = model.kneighbors(inputs)

                for i in list(indices):
                    results.append(dataframe.loc[i])
                df_results = pd.concat(results).reset_index(drop=True)
                return df_results

            def user_based(self, features, user_id):
                similar_users = self.find_neighbors(self.profiles, features, 10)
                users = list(similar_users.User_Id)

                results = self.recent_activity[self.recent_activity.User_Id.isin(users)]
                results = results[results['User_Id'] != user_id]

                meals = list(results.Meal_Id.unique())
                results = self.df[self.df.Meal_Id.isin(meals)]

                results = results.filter(['Meal_Id', 'Name', 'catagory', 'Nutrient', 'Veg_Non', 'description', 'Price', 'Review'])
                results = results.drop_duplicates(subset=['Name']).reset_index(drop=True)
                return results

            def recent_activity_based(self, user_id):
                recent_df = self.recent_activity[self.recent_activity['User_Id'] == user_id]
                meal_ids = list(recent_df.Meal_Id.unique())
                recent_data = self.df[self.df.Meal_Id.isin(meal_ids)][['Nutrient', 'catagory', 'Disease', 'Diet']].reset_index(drop=True)

                disease = []
                diet = []
                for i in range(recent_data.shape[0]):
                    disease.extend(recent_data.loc[i, 'Disease'].split())
                    diet.extend(recent_data.loc[i, 'Diet'].split())

                value_counts = recent_data.Nutrient.value_counts()
                m = recent_data.Nutrient.value_counts().mean()
                features = list(value_counts[value_counts > m].index)

                a = dict(Counter(disease))
                m = np.mean(list(a.values()))
                for i in a.items():
                    if i[1] > m:
                        features.append(i[0])

                a = dict(Counter(diet))
                m = np.mean(list(a.values()))
                for i in a.items():
                    if i[1] > m:
                        features.append(i[0])

                similar_neighbors = self.find_neighbors(self.df, features, 10)
                return similar_neighbors.filter(['Meal_Id', 'Name', 'Nutrient', 'Veg_Non', 'description', 'Price', 'Review'])

            def recommend(self, user_id):
                profile = self.profiles[self.profiles['User_Id'] == user_id]
                features = [profile['Nutrient'].values[0]]
                features.extend(profile['Disease'].values[0].split())
                features.extend(profile['Diet'].values[0].split())

                df1 = self.user_based(features, user_id)
                df2 = self.recent_activity_based(user_id)
                df = pd.concat([df1, df2]).drop_duplicates('description').reset_index(drop=True)
                return df

        user_id = request.user.username

        # Load datasets with error handling
        try:
            profiles = pd.read_csv(os.path.join(settings.BASE_DIR, 'website', 'csvfile', 'user_Profiles.csv'))
            recent_activity = pd.read_csv(os.path.join(settings.BASE_DIR, 'website', 'csvfile', 'recent_activity.csv'))
            dataset = pd.read_csv(os.path.join(settings.BASE_DIR, 'website', 'csvfile', 'dataset.csv'))
        except FileNotFoundError as e:
            messages.error(request, f"File not found: {str(e)}")
            return redirect('Home')

        recommender = Recommender(profiles, recent_activity, dataset)
        result = recommender.recommend(user_id)

        # Prepare data for rendering
        data = dict(result)

        ids = list(data['Meal_Id'])
        names = list(data['Name'])
        categories = list(data['catagory'])
        veg_non = list(data['Veg_Non'])
        reviews = list(data['Review'])
        nutrients = list(data['Nutrient'])
        prices = list(data['Price'])

        data = zip(names, ids, names, categories, categories, veg_non, reviews, nutrients, prices, prices)

        # Check for profile image safely
        try:
            profile = Profile.objects.get(number=request.user.username)
            image = profile.image.url if profile.image and hasattr(profile.image, 'url') else None
        except Profile.DoesNotExist:
            image = None

        return render(request, "website/recommend.html", {'data': data, 'image': image})

    else:
        messages.error(request, 'You must be logged in for meal recommendations.')
        return redirect('Home')