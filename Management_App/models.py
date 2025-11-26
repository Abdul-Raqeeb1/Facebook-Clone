from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date

# Create your models here.

def validate_age(value):
    today = date.today()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if age < 13:
        raise ValidationError("User must be at least 13 years old.")

class Account_Extra_Details(models.Model):

    user_id = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True
    )

    gender_choice = [
        ('FE','Female'),
        ('MA','Male'),
        ('CU','Custom'),
    ]

    gender = models.CharField(max_length=10,choices=gender_choice)

    date_of_birth = models.DateField(validators=[validate_age], null=True, blank=True)
    profile_pic = models.ImageField(upload_to='post_images/', null=True, blank=True)


class User_Posts(models.Model):

    post_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    title_post = models.CharField(max_length=200)

    post_time = models.DateTimeField(auto_created=True,auto_now_add=True)

    post_image = models.ImageField(upload_to='post_images/', null=True, blank=True) 

    post_likes = models.DecimalField(max_digits=9999,max_length=9,decimal_places=0,default=0,null=True)

    post_views = models.DecimalField(max_digits=9999,max_length=9,decimal_places=0,default=0,null=True)


class PostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(User_Posts, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} likes {self.post.id}"


class PostComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(User_Posts, on_delete=models.CASCADE, related_name='comments')
    comment_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.id}: {self.comment_text[:20]}"


class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({'accepted' if self.accepted else 'pending'})"


class Friendship(models.Model):
    user = models.ForeignKey(User, related_name='friendships', on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name='friends_of', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'friend')

    def __str__(self):
        return f"{self.user.username} <-> {self.friend.username}"


class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.text[:20]}"


class Notification(models.Model):
    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    actor = models.ForeignKey(User, related_name='actor_notifications', on_delete=models.SET_NULL, null=True, blank=True)
    verb = models.CharField(max_length=200)
    unread = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.verb}"

    


