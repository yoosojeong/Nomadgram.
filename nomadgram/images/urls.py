from django.conf.urls import url
from . import views

urlpatterns = [
    url(
        regex=r'^$',
        view=views.Feed.as_view(),
        name='feed',
    ),
    url(
        regex=r'(?P<image_id>[0-9]+)/like',
        view=views.LikeImage.as_view(),
        name='like_image'
    )
]

#/images/3/like/

#1.url, view 생성
#2.url에서 id 가져오기
#3.해당 id의 이미지 가져오기 (이를 통해 이미지 존재 확인)
#4.이미지 좋아요 생성