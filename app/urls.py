from django.urls import path
from .views import (index, login_view, signup_view, logout_view, video_detail, premium_view, 
                    wallet_view, upload_view, profile_view, admin_dashboard, admin_action,
                    categories_view, search_view, like_video, video_stream_view)

urlpatterns = [
    path('', index, name='index'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('signup/', signup_view, name='signup'),
    path('video/<int:video_id>/', video_detail, name='video_detail'),
    path('video/<int:video_id>/like/', like_video, name='like_video'),
    path('video/<int:video_id>/stream/', video_stream_view, name='video_stream'),
    path('premium/', premium_view, name='premium'),
    path('wallet/', wallet_view, name='wallet'),
    path('upload/', upload_view, name='upload'),
    path('profile/', profile_view, name='profile'),
    path('admindash/', admin_dashboard, name='admin_dashboard'),
    path('admindash/action/', admin_action, name='admin_action'),
    path('categories/<str:category_name>/', categories_view, name='categories'),
    path('search/', search_view, name='search'),
]
