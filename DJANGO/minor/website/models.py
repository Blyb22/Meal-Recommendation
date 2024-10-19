from django.db import models

# Contact model
class Contact(models.Model):
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=50)
    number = models.BigIntegerField()
    message = models.TextField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return self.name

# Profile model
class Profile(models.Model):
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=50)
    number = models.BigIntegerField(primary_key=True)
    gender = models.CharField(max_length=10)
    age = models.IntegerField()
    blood = models.CharField(max_length=10)
    weight = models.IntegerField()
    height = models.CharField(max_length=10)
    favfood = models.CharField(max_length=100)
    foodtype = models.CharField(max_length=15)
    diet = models.TextField(max_length=1500)
    nutrient = models.TextField(max_length=1500)
    disease = models.TextField(max_length=1500)
    cuisines = models.TextField(max_length=1500)
    medicalhistory = models.TextField(max_length=1500)
    
    # Use a relative path for the image field
    image = models.ImageField(upload_to='DJANGO/minor/media/website/images', default='DJANGO/minor/media/website/images/avtar.png', blank=True, null=True)
    
    # Correct boolean field default value
    second_time = models.BooleanField(default=False)

    def __str__(self):
        return self.name