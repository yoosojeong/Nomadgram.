from . import models
from . import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from nomadgram.users import models as user_models
from nomadgram.users import serializers as user_serializers
from nomadgram.notifications import views as notification_views


class Images(APIView):

    def get(self, request, format=None):

        # user = request.user

        # following_users = user.following.all()

        # first_image = models.Image.objects.all().first()
        # # count_likes = first_image.count_likes
        # # print (first_image.count_likes)
        
        # image_list = []

        # for following_user in following_users:
            
        #     user_images = following_user.images.all()[:2]

        #     for image in user_images:

        #         image_list.append(image)

        # sorted_list = sorted(image_list, key=lambda image: image.created_at, reverse=True)
        # # Image.objects.filter(creator=following_user)

        # serializer = serializers.imageSerializer(sorted_list, many=True)

        # return Response(serializer.data)

        user = request.user
        
        following_users = user.following.all()

        image_list = []
        
        for following_user in following_users:

            user_images = following_user.images.all()[:2]

            for image in user_images:

                image_list.append(image)
            
        my_images = user.images.all()[:2]

        for image in my_images:
            
            image_list.append(image)

        sorted_list = sorted(image_list, key=lambda images: images.created_at, reverse=True)
        
        serializer = serializers.imageSerializer(sorted_list, many=True)
        
        return Response(serializer.data)
    
    def post(self, request, format=None):

        user = request.user

        serializer = serializers.InputImageSerializer(data=request.data)

        if serializer.is_valid():

            serializer.save(creator=user)

            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LikeImage(APIView):

    def get(self, request, image_id, format=None):

        likes = models.Like.objects.filter(image__id=image_id)

        like_creators_ids = likes.values('creator_id')    

        users = user_models.User.objects.filter(id__in=like_creators_ids)

        serializer = user_serializers.ListUserSerializer(users, many=True)
        
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        
    def post(self, request, image_id, format=None):
        
        user = request.user
         
         # create notification for like 

        try: 
            found_image = models.Image.objects.get(id=image_id)

        except models.Image.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            preexisiting_like = models.Like.objects.get(
                creator=user,
                image=found_image
            )
            return Response(status=status.HTTP_304_NOT_MODIFIED)

        except models.Like.DoesNotExist:

            new_like = models.Like.objects.create(
                creator=user,
                image=found_image
            )

            new_like.save()

            notification_views.create_notification(user, found_image.creator, 'like', found_image)

            return Response(status=status.HTTP_201_CREATED)

class UnLikeImage(APIView):
    
    def delete(self, request, image_id, format=None):

        user = request.user
        
        try:
            found_image = models.Image.objects.get(id=image_id)

        except models.Image.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            preexisiting_like = models.Like.objects.get(
                creator=user,
                image=found_image
            )

            preexisiting_like.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except models.Like.DoesNotExist:

            return Response(status=status.HTTP_304_NOT_MODIFIED)

class CommentOnImage(APIView):

    def post(self, request, image_id, format=None):

        user = request.user

        # create notification for comment

        try:
            found_image = models.Image.objects.get(id=image_id)

        except models.Image.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = serializers.CommentSerializer(data=request.data)

        if serializer.is_valid():
            
            serializer.save(creator=user, image=found_image)

            notification_views.create_notification(user, found_image.creator, 'comment', found_image, serializer.data['message'])

            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class Comment(APIView):

    def delete(self, request, comment_id, format=None):
        
        # 자기 댓글 삭제

        user = request.user

        try:
            comment = models.Comment.objects.get(id=comment_id, creator=user)
            comment.delete()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except models.Comment.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

class Search(APIView):

    def get(self, request, format=None):

        # print(request)

        # print(request.query_params)
        
        hashtags = request.query_params.get('hashtags', None).split(",")
        
        if hashtags is not None:
            images = models.Image.objects.filter(tags__name__in=hashtags).distinct()

            serializer = serializers.CountImageSerializer(images, many=True)

            return Response(data=serializer.data,status=status.HTTP_200_OK)

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class ModerateComments(APIView):

    # 자기 이미지에 있는 댓글 삭제

    def delete(self, request, image_id, comment_id, format=None):

        print("dd0")
        user = request.user
        
        try:
            comment_to_delete = models.Comment.objects.get(
                id=comment_id, image__id=image_id, image__creator=user)

            comment_to_delete.delete()

        except models.Comment.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)

class ImageDetail(APIView):
    
    def find_image(self, image_id):
        
        try:
            image = models.Image.objects.get(id=image_id)
            return image

        except models.Image.DoesNotExist:
            return None
    
    def find_own_image(self, image_id, user):

        try:
            image = models.Image.objects.get(id=image_id, creator=user)
            return image

        except models.Image.DoesNotExist:
            return None
            
    def get(self, request, image_id, format=None):

        user = request.user

        image = self.find_image(image_id)

        serializer = serializers.imageSerializer(image)

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def put(self, request, image_id, format=None):

        user = request.user

        image = self.find_own_image(image_id, user)

        if image is None:

            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = serializers.InputImageSerializer(image, data=request.data, partial=True)

        if serializer.is_valid():

            serializer.save(creator=user)

            return Response(data=serializer.data, status=status.HTTP_204_NO_CONTENT)
        
        else:

            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, image_id, format=None):
    
        user = request.user 
        
        image = self.find_own_image(image_id, user)

        if image is None:

            return Response(status=status.HTTP_401_UNAUTHORIZED)
    
        image.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

