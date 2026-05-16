from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from manager.api import AuthSignupAPIView, AuthLoginAPIView, AuthLogoutAPIView, DashboardAPIView, ProjectViewSet, TaskViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('manager.urls')),
    path('api/auth/signup/', AuthSignupAPIView.as_view(), name='api-signup'),
    path('api/auth/login/', AuthLoginAPIView.as_view(), name='api-login'),
    path('api/auth/logout/', AuthLogoutAPIView.as_view(), name='api-logout'),
    path('api/dashboard/', DashboardAPIView.as_view(), name='api-dashboard'),
    path('api/', include(router.urls)),
]
