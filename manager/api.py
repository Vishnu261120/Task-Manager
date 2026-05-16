from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Project, ProjectMember, Task
from .permissions import can_manage_project, can_manage_task
from .serializers import ProjectSerializer, TaskSerializer, UserSerializer


def user_projects(user):
    return Project.objects.filter(memberships__user=user).distinct()


class AuthSignupAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        name = (request.data.get('name') or '').strip()
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''
        if not name or not email or not password:
            return Response({'detail': 'Name, email, and password are required.'}, status=400)
        if User.objects.filter(username=email).exists():
            return Response({'detail': 'A user with this email already exists.'}, status=400)
        user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
        login(request, user)
        return Response({'detail': 'Signup successful.', 'user': UserSerializer(user).data}, status=201)


class AuthLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''
        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({'detail': 'Invalid email or password.'}, status=400)
        login(request, user)
        return Response({'detail': 'Login successful.', 'user': UserSerializer(user).data})


class AuthLogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response({'detail': 'Logged out.'})


class DashboardAPIView(APIView):
    def get(self, request):
        projects = user_projects(request.user)
        tasks = Task.objects.filter(project__in=projects) if request.user.is_superuser else Task.objects.filter(Q(project__in=projects) | Q(assigned_to=request.user)).distinct()
        payload = {
            'total_tasks': tasks.count(),
            'tasks_by_status': {
                'todo': tasks.filter(status=Task.STATUS_TODO).count(),
                'in_progress': tasks.filter(status=Task.STATUS_PROGRESS).count(),
                'done': tasks.filter(status=Task.STATUS_DONE).count(),
            },
            'tasks_per_user': list(tasks.values('assigned_to__first_name').annotate(total=Count('id')).order_by('-total')),
            'overdue_tasks': tasks.filter(due_date__lt=timezone.localdate()).exclude(status=Task.STATUS_DONE).count(),
            'projects': ProjectSerializer(projects, many=True).data,
        }
        return Response(payload)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Project.objects.annotate(task_count=Count('tasks')).all()
        return Project.objects.filter(memberships__user=self.request.user).annotate(task_count=Count('tasks')).distinct()

    def perform_create(self, serializer):
        project = serializer.save(created_by=self.request.user)
        ProjectMember.objects.create(project=project, user=self.request.user, role=ProjectMember.ROLE_ADMIN)

    def update(self, request, *args, **kwargs):
        project = self.get_object()
        if not can_manage_project(request.user, project):
            return Response({'detail': 'Only admins can update this project.'}, status=403)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        if not can_manage_project(request.user, project):
            return Response({'detail': 'Only admins can delete this project.'}, status=403)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        project = self.get_object()
        if not can_manage_project(request.user, project):
            return Response({'detail': 'Only admins can manage members.'}, status=403)
        email = (request.data.get('email') or '').strip().lower()
        role = request.data.get('role') or ProjectMember.ROLE_MEMBER
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'No user found with that email.'}, status=404)
        membership, created = ProjectMember.objects.get_or_create(project=project, user=user, defaults={'role': role})
        if not created:
            membership.role = role
            membership.save()
        return Response({'detail': 'Member added.', 'member': membership.id})

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        project = self.get_object()
        if not can_manage_project(request.user, project):
            return Response({'detail': 'Only admins can manage members.'}, status=403)
        user_id = request.data.get('user_id')
        ProjectMember.objects.filter(project=project, user_id=user_id).delete()
        return Response({'detail': 'Member removed.'})


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Task.objects.select_related('project', 'assigned_to', 'created_by')
        projects = user_projects(self.request.user)
        return Task.objects.select_related('project', 'assigned_to', 'created_by').filter(Q(project__in=projects) | Q(assigned_to=self.request.user)).distinct()

    def perform_create(self, serializer):
        project_id = self.request.data.get('project')
        project = Project.objects.get(id=project_id)
        if not can_manage_project(self.request.user, project):
            raise PermissionDenied('Only admins can create tasks for the project.')
        serializer.save(created_by=self.request.user, project=project)

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        if not can_manage_task(request.user, task):
            return Response({'detail': 'You cannot update this task.'}, status=403)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        if not can_manage_project(request.user, task.project):
            return Response({'detail': 'Only admins can delete tasks.'}, status=403)
        return super().destroy(request, *args, **kwargs)
