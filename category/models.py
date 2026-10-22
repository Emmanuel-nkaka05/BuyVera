from django.db import models

# Create your models here.

class Category(models.Model):
    Category_name = models.CharField(max_length=50, unique=True)
    #url of category
    slug = models.SlugField( max_length=100, unique = True)
    
    description = models.TextField(max_length= 255,blank=True)
    cat_image = models.ImageField(upload_to='photos/categories', blank = True)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.Category_name
    