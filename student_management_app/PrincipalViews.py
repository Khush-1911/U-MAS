from django.shortcuts import render
def principal_home(request):
    return render(request, "hod_template/home_content.html")
