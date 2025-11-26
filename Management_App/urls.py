
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
    path('video_page', views.Video_Page, name='Video_Page'),
    path('message_page', views.Message_Page, name='Message_Page'),
    path('market_page', views.Market_Page, name='Market_Page'),
    path('friends_page', views.Friends_Page, name='Friends_Page'),
    path('requests_page', views.Requests_Page, name='Requests_Page'),
    # API endpoints for friend requests and messages
    path('api/send_request/', views.api_send_request, name='api_send_request'),
    path('api/list_requests/', views.api_list_requests, name='api_list_requests'),
    path('api/accept_request/', views.api_accept_request, name='api_accept_request'),
    path('api/delete_request/', views.api_delete_request, name='api_delete_request'),
    path('api/send_message/', views.api_send_message, name='api_send_message'),
    path('api/list_conversations/', views.api_list_conversations, name='api_list_conversations'),
    path('api/get_messages/', views.api_get_messages, name='api_get_messages'),
    path('api/check_friend_status/', views.api_check_friend_status, name='api_check_friend_status'),
    path('api/friend_status/', views.api_check_friend_status, name='api_friend_status'),
    # path('show_posts', views.Show_Posts, name='Show_Posts'),
]