from .models import ProjectMember, Task


def project_membership(user, project):
    return ProjectMember.objects.filter(user=user, project=project).first()


def is_project_admin(user, project):
    membership = project_membership(user, project)
    return bool(membership and membership.role == ProjectMember.ROLE_ADMIN)


def can_view_project(user, project):
    return user.is_superuser or project_membership(user, project) is not None


def can_manage_project(user, project):
    return user.is_superuser or is_project_admin(user, project)


def can_view_task(user, task):
    if user.is_superuser or can_view_project(user, task.project):
        return True
    return task.assigned_to_id == user.id


def can_manage_task(user, task):
    return user.is_superuser or is_project_admin(user, task.project) or task.assigned_to_id == user.id
