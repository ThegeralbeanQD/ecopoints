from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render, redirect
from datetime import datetime
from django.db.models.functions import ExtractMonth, ExtractDay
from django.http import JsonResponse
from django.utils import timezone
from django.db.models.functions import ExtractWeekDay
from django.db.models.functions import TruncDate
from ecopoints.models import CompletedTask, Category, Task, LikedCategory, UserProfile
from django.http import HttpResponse
from django.views import View
from collections import defaultdict
#from ecopoints.forms import UserProfileForm
from django.urls import reverse


def index(request):
    return render(request, 'ecopoints/index.html')


def calculate_points(user, start_date):
    return (
            CompletedTask.objects.filter(user=user, completed_at__gte=start_date)
            .aggregate(total=Sum('task__score'))['total']
            or 0
    )


def make_date_timezone_aware(date):
    return timezone.make_aware(datetime.combine(date, datetime.min.time()))


@login_required
def insights(request):
    user = request.user
    today = make_date_timezone_aware(datetime.now().date())
    current_month = datetime.now().strftime("%B")

    # using weekday() method to calculate the start of the week (Mon)
    # weekday() returns 0 for Mon and 6 for Sun
    start_of_week = today.replace(day=today.day - today.weekday())
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)

    if user.is_authenticated:
        daily_points = calculate_points(user, today)
        weekly_points = calculate_points(user, start_of_week)
        monthly_points = calculate_points(user, start_of_month)

        weekly_data = get_weekly_data(user)

        monthly_points_data = (
            CompletedTask.objects.filter(user=user, completed_at__gte=start_of_year)
            .annotate(month=ExtractMonth('completed_at'))
            .values('month')
            .annotate(total_points=Sum('task__score'))
            .order_by('month')
        )

        monthly_completed_tasks = CompletedTask.objects.filter(
            user=user,
            completed_at__month=start_of_month.month,
            completed_at__year=start_of_month.year
        )

        top_category_data = (
            monthly_completed_tasks
            .values('task__category__name')
            .annotate(total=Sum('task__score'))
            .order_by('-total')
            .first()
        )

        if top_category_data:
            top_category = top_category_data['task__category__name']
            top_category_points = top_category_data['total']
        else:
            top_category = "N/A"
            top_category_points = 0


        days_with_tasks = monthly_completed_tasks.values('completed_at__date').distinct().count()
        total_completed_tasks = monthly_completed_tasks.count()

        points_dict = defaultdict(lambda:0)
        for entry in monthly_points_data:
            points_dict[entry["month"]] = entry["total_points"]

        annual_points = [{"month": month, "points": points_dict[month]} for month in range(1, 13)]

        latest_month = (
            CompletedTask.objects.filter(user=user)
            .annotate(month=ExtractMonth('completed_at'))
            .values_list('month', flat=True)
            .order_by('-month')
            .first()
        )

        if latest_month:
            bubble_plot_data = (
                CompletedTask.objects.filter(user=user, completed_at__month=latest_month)
                .annotate(day=ExtractDay('completed_at'))  # Extract day instead of month
                .values('day', 'task__category__name')  # Group by day & category
                .annotate(total_points=Sum('task__score'))  # Sum points per category per day
                .order_by('day', 'task__category__name')
            )

            bubble_data = [
                {"day": entry["day"], "category": entry["task__category__name"], "points": entry["total_points"]}
                for entry in bubble_plot_data
            ]
        else:
            bubble_data = []

    else:
        daily_points = weekly_points = monthly_points = 0
        annual_points = []
        bubble_data = []

    context = {
        'daily_points': daily_points,
        'weekly_points': weekly_points,
        'monthly_points': monthly_points,
        'annual_points': annual_points,
        'bubble_data': bubble_data,
        'latest_month': latest_month,
        'weekly_data': weekly_data,
        'days_with_tasks': days_with_tasks,
        'total_completed_tasks': total_completed_tasks,
        'current_month' : current_month,
        'is_authenticated': user.is_authenticated,
        'top_category': top_category,
        'top_category_points': top_category_points
    }

    return render(request, 'ecopoints/insights.html', context)


def get_bubble_data_for_month(user, month):
    bubble_plot_data = (
        CompletedTask.objects.filter(user=user, completed_at__month=month)
        .annotate(day=ExtractDay('completed_at'))
        .values('day', 'task__category__name')
        .annotate(total_points=Sum('task__score'))
        .order_by('day', 'task__category__name')
    )

    return [
        {"day": entry["day"], "category": entry["task__category__name"], "points": entry["total_points"]}
        for entry in bubble_plot_data
    ]


def get_weekly_data(user):
    weekday_data = (
        CompletedTask.objects.filter(user=user, completed_at__week=timezone.now().isocalendar()[1])
        .annotate(weekday=ExtractWeekDay('completed_at'))  # 1=Sunday, 7=Saturday
        .values('weekday')
        .annotate(total_points=Sum('task__score'))
        .order_by('weekday')
    )
    return [{"day": d["weekday"], "points": d["total_points"]} for d in weekday_data]


def get_bubble_data(request, month):
    user = request.user
    if user.is_authenticated:
        bubble_data = get_bubble_data_for_month(user, month)
    else:
        bubble_data = []
    return JsonResponse({"bubble_data": bubble_data})


@login_required(login_url='/accounts/login/')
def dashboard(request):
    user = request.user
    today = make_date_timezone_aware(datetime.now().date())
    category_list = Category.objects.all()
    task_list = Task.objects.all()
    completed_tasks = CompletedTask.objects.filter(user=request.user).order_by('-completed_at')
    completed_today = CompletedTask.objects.filter(user=request.user, completed_at__date=today)

    # Get the 5 most recent completed tasks
    # sqlLite does not support DISTINCT
    unique_tasks = []
    seen_task_ids = set()

    # function to get the unique tasks
    for completed in completed_tasks:
        task = completed.task
        task_id = task.id
        if task_id not in seen_task_ids:
            # Attach the completion datetime to the Task instance
            formatted_time = completed.completed_at.strftime("%d/%m/%y %H:%M")
            task.completed_at = formatted_time
            unique_tasks.append(task)
            seen_task_ids.add(task_id)
        # max 5 unique tasks
        if len(unique_tasks) == 5:
            break

    completed_today_unique = []
    seen_tasks_ids = set()

    # Loop through completions for today
    for completed in completed_today:
        task = completed.task
        task_id = task.id

        if task_id not in seen_tasks_ids:
            formatted_time = completed.completed_at.strftime("%d/%m/%y %H:%M")
            task.completed_at = formatted_time
            task.counter = 1

            completed_today_unique.append(task)
            seen_tasks_ids.add(task_id)
        else:
            # Task already seen, update its counter and score
            for t in completed_today_unique:
                if t.id == task_id:
                    t.counter += 1
                    break

    total_score_today = calculate_points(user, today)

    finished = False
    if total_score_today >= 50:
        finished = True

    context_dict = {
        'categories': category_list,
        'tasks': task_list,
        'recent_tasks': unique_tasks,
        'completed_tasks_today': completed_today_unique,
        'total_score_today': total_score_today,
        'finished': finished
    }

    return render(request, 'ecopoints/dashboard.html', context=context_dict)


@login_required(login_url='/accounts/login/')
def categories(request):
    category_list = Category.objects.all()
    context_dict = {
        'categories': category_list
    }

    return render(request, 'ecopoints/categories.html', context=context_dict)


@login_required(login_url='/accounts/login/')
def show_category(request, category_slug):
    try:
        category = Category.objects.get(slug=category_slug)
        tasks = Task.objects.filter(category=category)
    except Category.DoesNotExist:
        category = Category.objects.none()
        tasks = Task.objects.none()

    #Logic to check if user has liked this page
    try:
        liked_category = LikedCategory.objects.filter(user=request.user, category=category)
    except LikedCategory.DoesNotExist:
        liked_category = LikedCategory.objects.none()

    context_dict = {
        'category': category,
        'tasks': tasks,
        'liked_category': liked_category
    }
    return render(request, 'ecopoints/category.html', context=context_dict)


@login_required(login_url='/accounts/login/')
def like_category(request):
    category_id = request.GET['category_id']
    try:
        category = Category.objects.get(id=int(category_id))
    except Category.DoesNotExist:
        return redirect('ecopoints:dashboard')
    except ValueError:
        return redirect('ecopoints:dashboard')
    category.likes = category.likes + 1
    category.save()
    # Create a LikedCategory record for the logged-in user
    LikedCategory.objects.create(user=request.user, category=category)
    return HttpResponse(category.likes)


@login_required(login_url='/accounts/login/')
def complete_task(request, task_id):
    if request.method == 'POST':
        if task_id:
            try:
                task = Task.objects.get(id=task_id)
            except Task.DoesNotExist:
                # Handle invalid task ID
                return redirect('ecopoints:dashboard')

            # Create a CompletedTask record for the logged-in user
            CompletedTask.objects.create(user=request.user, task=task)
        return redirect('ecopoints:dashboard')
    else:
        # If someone navigates here with GET, just redirect to dashboard
        return redirect('ecopoints:dashboard')


'''@login_required(login_url='/accounts/login/')
def register_profile(request):
    form = UserProfileForm()

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)

        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()

            return redirect(reverse('ecopoints:index'))
    else:
        print(form.errors)
    context_dict = {'form': form}
    return render(request, 'ecopoints/profile_registration.html', context_dict)'''




