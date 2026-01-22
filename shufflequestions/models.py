from django.db import models

# Create your models here.
class ScrambleLinks(models.Model):
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="rn_scramble_links",
        )
    link = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
