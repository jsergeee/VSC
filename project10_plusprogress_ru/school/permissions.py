# school/permissions.py
from rest_framework import permissions

class IsTeacherUser(permissions.BasePermission):
    """Права для учителей"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'teacher'


class IsStudentUser(permissions.BasePermission):
    """Права для учеников"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'


class IsOwnerOrAdmin(permissions.BasePermission):
    """Права на свои объекты или админ"""
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        
        # Проверяем, принадлежит ли объект пользователю
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'teacher') and hasattr(obj.teacher, 'user'):
            return obj.teacher.user == request.user
        if hasattr(obj, 'student') and hasattr(obj.student, 'user'):
            return obj.student.user == request.user
        
        return False