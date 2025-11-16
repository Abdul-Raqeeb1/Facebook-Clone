from django.contrib import admin
from .models import User_Posts, PostLike, PostComment


@admin.register(User_Posts)
class UserPostsAdmin(admin.ModelAdmin):
	list_display = ('id', 'post_id', 'title_post', 'post_time', 'post_image')
	readonly_fields = ('post_time',)
	search_fields = ('title_post', 'post_id__username', 'post_id__first_name')
	list_per_page = 50


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'post', 'created_at')
	search_fields = ('user__username', 'post__title_post')


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'post', 'created_at')
	search_fields = ('user__username', 'comment_text')


