
from django.urls import path
from Management_App import views

urlpatterns = [
    path('createaccount',views.Create_Account,name='CreateAccount'),
    path('register',views.register,name='RegisterAccount'),
    path('login',views.Login_Page,name='Login_Page'),
    path('logout',views.Logout_Page,name='Logout_Page'),
    path('homepage',views.Home_Page,name='Homepage'),
    path('create_post', views.Create_Post, name='Create_Post'),
    path('like_post', views.Like_Post, name='Like_Post'),
    path('add_comment', views.Add_Comment, name='Add_Comment'),
    path('userprofile',views.User_Profile,name='User_Profile'),
    path('edit_profile', views.Edit_Profile, name='Edit_Profile'),
    path('delete_account', views.Delete_Account, name='Delete_Account'),
    # path('show_posts', views.Show_Posts, name='Show_Posts'),
]