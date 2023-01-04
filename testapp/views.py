from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.


def test_view(request):
    items = [1, 2, 34, 4, 6]
    test_v1 = any([item for item in items])
    return HttpResponse(f"Hello World")


def test_view2(user):
    val = ("Hello World",)
    return "%s %s %s" % (user.first_name, user.last_name, val)
