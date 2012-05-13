from django.db import models

class Post(models.Model):
    '''
    Any timely and short publication.
    '''
    timestamp = models.DateTimeField()

    class Meta:
        abstract = True


class News(Post):
    '''
    Any news item on the public website.
    '''
    headline = models.CharField(max_length=255)
    markup = models.TextField()

    class Meta:
        verbose_name = "news"
        verbose_name_plural = "news"
