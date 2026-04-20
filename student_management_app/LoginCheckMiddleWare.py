from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class LoginCheckMiddleWare(MiddlewareMixin):

    def process_view(self,request,view_func,view_args,view_kwargs):
        modulename=view_func.__module__
        user=request.user
        if user.is_authenticated:
            if str(user.user_type) == "1": # Owner
                if modulename in ["student_management_app.OwnerViews", "student_management_app.views", "django.views.static", "django.contrib.auth.views", "django.contrib.admin.sites"]:
                    pass
                else:
                    return HttpResponseRedirect(reverse("owner_home"))
            elif str(user.user_type) == "2": # Staff
                if modulename in ["student_management_app.StaffViews", "student_management_app.EditResultVIewClass", "student_management_app.views", "django.views.static"]:
                    pass
                else:
                    return HttpResponseRedirect(reverse("staff_home"))
            elif str(user.user_type) == "3": # Student
                if modulename in ["student_management_app.StudentViews", "django.views.static", "student_management_app.views"]:
                    pass
                else:
                    return HttpResponseRedirect(reverse("student_home"))
            elif str(user.user_type) == "4": # Superuser
                if modulename in ["student_management_app.SuperuserViews", "django.views.static", "student_management_app.views"]:
                    pass
                else:
                    return HttpResponseRedirect(reverse("superuser_home"))
            elif str(user.user_type) == "5": # Principal
                if modulename in ["student_management_app.PrincipalViews", "django.views.static", "student_management_app.views"]:
                    pass
                else:
                    return HttpResponseRedirect(reverse("principal_home"))
            elif str(user.user_type) == "6": # College Admin
                if modulename in ["student_management_app.CollegeAdminViews", "django.views.static", "student_management_app.views"]:
                    pass
                else:
                    return HttpResponseRedirect(reverse("collegeadmin_home"))
            elif str(user.user_type) == "7": # HOD
                if modulename in ["student_management_app.HodViews", "django.views.static", "student_management_app.views"]:
                    pass
                else:
                    return HttpResponseRedirect(reverse("hod_home"))
            else:
                return HttpResponseRedirect(reverse("show_login"))

        else:
            if request.path == reverse("show_login") or request.path == reverse("do_login") or modulename == "django.contrib.auth.views" or modulename =="django.contrib.admin.sites" or modulename=="student_management_app.views":
                pass
            else:
                return HttpResponseRedirect(reverse("show_login"))