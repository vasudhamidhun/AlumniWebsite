# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.contrib.auth.models import User
# from .models import RegisterModel
#
# @receiver(post_save, sender=User)
# def create_register_for_superuser(sender, instance, created, **kwargs):
#     if created and instance.is_superuser:
#         # Create matching RegisterModel entry
#         RegisterModel.objects.create(
#             username=instance.username,
#             college_id="ADMIN",
#             email=instance.email,
#             password=instance.password   # Not used for login, but stored anyway
#         )
