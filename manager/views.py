from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import LoginForm, MemberForm, ProjectForm, SignupForm, StatusForm, TaskForm
from .models import Project, ProjectMember, Task
from .permissions import can_manage_project, can_manage_task, can_view_project, can_view_task, is_project_admin, project_membership


def _user_projects(user):
    if user.is_superuser:
        return Project.objects.all()
    return Project.objects.filter(memberships__user=user).distinct()


@login_required
def dashboard(request):
    projects = _user_projects(request.user).annotate(task_count=Count('tasks'))
    if request.user.is_superuser:
        tasks = Task.objects.select_related('project', 'assigned_to').all()
    else:
        tasks = Task.objects.select_related('project', 'assigned_to').filter(Q(project__in=projects) | Q(assigned_to=request.user)).distinct()
    stats = {
        'total_tasks': tasks.count(),
        'todo': tasks.filter(status=Task.STATUS_TODO).count(),
        'in_progress': tasks.filter(status=Task.STATUS_PROGRESS).count(),
        'done': tasks.filter(status=Task.STATUS_DONE).count(),
        'overdue': tasks.filter(due_date__lt=timezone.localdate()).exclude(status=Task.STATUS_DONE).count(),
    }
    tasks_by_user = tasks.values('assigned_to__first_name').annotate(total=Count('id')).order_by('-total')[:10]
    recent_tasks = tasks.order_by('-updated_at')[:5]
    return render(request, 'manager/dashboard.html', {
        'projects': projects,
        'stats': stats,
        'tasks_by_user': tasks_by_user,
        'recent_tasks': recent_tasks,
    })


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Account created successfully.')
        return redirect('dashboard')
    return render(request, 'manager/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, 'Logged in successfully.')
        return redirect('dashboard')
    return render(request, 'manager/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Logged out.')
    return redirect('login')


@login_required
def project_list(request):
    projects = _user_projects(request.user).annotate(task_count=Count('tasks'))
    return render(request, 'manager/project_list.html', {'projects': projects})


@login_required
def project_create(request):
    form = ProjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        project = form.save(commit=False)
        project.created_by = request.user
        project.save()
        ProjectMember.objects.create(project=project, user=request.user, role=ProjectMember.ROLE_ADMIN)
        messages.success(request, 'Project created.')
        return redirect('project_detail', project_id=project.id)
    return render(request, 'manager/project_form.html', {'form': form, 'title': 'Create Project'})


@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_view_project(request.user, project):
        return HttpResponseForbidden('You do not have access to this project.')
    membership = project_membership(request.user, project)
    is_admin = request.user.is_superuser or (membership and membership.role == ProjectMember.ROLE_ADMIN)
    if is_admin:
        tasks = project.tasks.select_related('assigned_to', 'created_by').all()
    else:
        tasks = project.tasks.select_related('assigned_to', 'created_by').filter(assigned_to=request.user)
    members = project.memberships.select_related('user').all()
    member_form = MemberForm()
    task_form = TaskForm()
    return render(request, 'manager/project_detail.html', {
        'project': project,
        'tasks': tasks,
        'members': members,
        'is_admin': is_admin,
        'member_form': member_form,
        'task_form': task_form,
        'status_choices': Task.STATUS_CHOICES,
    })


@login_required
def project_update(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_manage_project(request.user, project):
        return HttpResponseForbidden('Only admins can edit this project.')
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Project updated.')
        return redirect('project_detail', project_id=project.id)
    return render(request, 'manager/project_form.html', {'form': form, 'title': 'Edit Project'})


@login_required
def project_delete(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_manage_project(request.user, project):
        return HttpResponseForbidden('Only admins can delete this project.')
    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted.')
        return redirect('project_list')
    return render(request, 'manager/confirm_delete.html', {'object': project, 'type': 'project'})


@login_required
def add_member(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_manage_project(request.user, project):
        return HttpResponseForbidden('Only admins can manage members.')
    form = MemberForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip().lower()
        role = form.cleaned_data['role']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'No user found with that email.')
            return redirect('project_detail', project_id=project.id)
        membership, created = ProjectMember.objects.get_or_create(project=project, user=user, defaults={'role': role})
        if not created:
            membership.role = role
            membership.save()
        messages.success(request, 'Member added or updated.')
    return redirect('project_detail', project_id=project.id)


@login_required
def remove_member(request, project_id, membership_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_manage_project(request.user, project):
        return HttpResponseForbidden('Only admins can manage members.')
    ProjectMember.objects.filter(id=membership_id, project=project).delete()
    messages.success(request, 'Member removed.')
    return redirect('project_detail', project_id=project.id)


@login_required
def task_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not can_manage_project(request.user, project):
        return HttpResponseForbidden('Only admins can create tasks.')
    form = TaskForm(request.POST or None)
    form.fields['assigned_to'].queryset = User.objects.filter(project_memberships__project=project).distinct()
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.created_by = request.user
        task.save()
        messages.success(request, 'Task created.')
        return redirect('project_detail', project_id=project.id)
    return render(request, 'manager/task_form.html', {'form': form, 'title': 'Create Task', 'project': project})


@login_required
def task_update(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if not can_manage_project(request.user, task.project):
        return HttpResponseForbidden('Only admins can edit this task.')
    form = TaskForm(request.POST or None, instance=task)
    form.fields['assigned_to'].queryset = User.objects.filter(project_memberships__project=task.project).distinct()
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Task updated.')
        return redirect('project_detail', project_id=task.project.id)
    return render(request, 'manager/task_form.html', {'form': form, 'title': 'Edit Task', 'project': task.project})


@login_required
def task_status_update(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if not (can_manage_task(request.user, task) or can_manage_project(request.user, task.project)):
        return HttpResponseForbidden('You cannot update this task.')
    form = StatusForm(request.POST or None, instance=task)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Task status updated.')
        return redirect('project_detail', project_id=task.project.id)
    return render(request, 'manager/task_status_form.html', {'form': form, 'task': task})


@login_required
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if not can_manage_project(request.user, task.project):
        return HttpResponseForbidden('Only admins can delete tasks.')
    if request.method == 'POST':
        project_id = task.project.id
        task.delete()
        messages.success(request, 'Task deleted.')
        return redirect('project_detail', project_id=project_id)
    return render(request, 'manager/confirm_delete.html', {'object': task, 'type': 'task'})
