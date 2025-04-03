
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, Profile
from .serializers import UserSerializer, ProfileSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        print(request.data, "----------------------------------")
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print(serializer.errors)  # Log the specific validation errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()

        Profile.objects.create(user=user)
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': serializer.data
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')
        
        user = authenticate(phone_number=phone_number, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'phone_number': user.phone_number,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Attempt to get or create the profile
            profile, created = Profile.objects.get_or_create(user=request.user)
            user_serializer = UserSerializer(request.user)
            profile_serializer = ProfileSerializer(profile)
            return Response({
                'user': user_serializer.data,
                'profile': profile_serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            # Catch any unexpected errors (e.g., database issues)
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request):
        try:
            print(request.data, "----------------------")
            # Attempt to get or create the profile
            profile, created = Profile.objects.get_or_create(user=request.user)
            serializer = ProfileSerializer(profile, data=request.data)
            
            # Validate and save the serializer
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except ObjectDoesNotExist:
            # This shouldn't happen with get_or_create, but included for robustness
            return Response(
                {"error": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            # Handle invalid data formats (e.g., bad JSON)
            return Response(
                {"error": f"Invalid data format: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Catch any other unexpected errors
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

