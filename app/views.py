from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden, Http404, StreamingHttpResponse
from .forms import LoginForm, SignUpForm, VideoUploadForm, CommentForm
from .models import User, Video, Comment, WithdrawRequest, VideoLike, VideoView
from django.conf import settings
from utils import generate_btc_address_for_user, check_payments
import os

def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_banned:
        return render(request, 'banned.html')
    videos = Video.objects.all().order_by('-upload_date')
    return render(request, 'index.html', {'videos': videos})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.user
            login(request, user)
            return redirect('index')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def video_detail(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    if request.user.is_banned:
        return render(request, 'banned.html')

    comments = video.comments.all().order_by('-created_at')
    recommended = Video.objects.exclude(id=video.id).order_by('-upload_date')[:5]
    is_premium = request.user.is_premium
    # Premium videonun full izlenmesi video_stream_view içinde kontrol edilecek.
    # Burada sadece template render ediyoruz.

    # Free kullanıcı için overlay göstereceğiz. Premium için göstermeye gerek yok.
    show_overlay = (video.video_type == 'premium' and not is_premium)
    return render(request, 'video_detail.html', {
        'video': video,
        'comments': comments,
        'recommended': recommended,
        'is_premium': is_premium,
        'comment_form': CommentForm(),
        'show_overlay': show_overlay
    })

@login_required
def like_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    if not VideoLike.objects.filter(user=request.user, video=video).exists():
        VideoLike.objects.create(user=request.user, video=video)
        video.likes_count += 1
        video.save()
    return redirect('video_detail', video_id=video_id)

@login_required
def video_stream_view(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    if video.video_type == 'premium':
        if not request.user.is_premium:
            # Free kullanıcıya sadece önizleme sun.
            if not video.video_preview_file:
                raise Http404("Preview not available")
            file_path = video.video_preview_file.path
            if not os.path.exists(file_path):
                raise Http404("Preview not found.")

            def file_iterator():
                with open(file_path, 'rb') as f:
                    chunk = f.read(8192)
                    while chunk:
                        yield chunk
                        chunk = f.read(8192)
            # Free izleyici premium videoyu izleyince izlenme sayılmaz!
            return StreamingHttpResponse(file_iterator(), content_type='video/mp4')
        else:
            # Premium user tam videoyu izleyebilir
            if not video.video_file:
                raise Http404("Video file not found.")

            # İzlenme kaydı oluştur (kullanıcı bu videoyu ilk kez izliyorsa)
            if not VideoView.objects.filter(user=request.user, video=video).exists():
                video.views_count += 1
                video.save()
                VideoView.objects.create(user=request.user, video=video)

            file_path = video.video_file.path
            if not os.path.exists(file_path):
                raise Http404("Video not found.")

            def file_iterator():
                with open(file_path, 'rb') as f:
                    chunk = f.read(8192)
                    while chunk:
                        yield chunk
                        chunk = f.read(8192)
            return StreamingHttpResponse(file_iterator(), content_type='video/mp4')
    else:
        # Free video
        if not video.video_file:
            raise Http404("Video file not found.")
        # Free video izleme: Premium veya değil fark etmez ilk kez izliyorsa izlenme artar
        if not VideoView.objects.filter(user=request.user, video=video).exists():
            video.views_count += 1
            video.save()
            VideoView.objects.create(user=request.user, video=video)

        file_path = video.video_file.path
        if not os.path.exists(file_path):
            raise Http404("Video not found.")

        def file_iterator():
            with open(file_path, 'rb') as f:
                chunk = f.read(8192)
                while chunk:
                    yield chunk
                    chunk = f.read(8192)
        return StreamingHttpResponse(file_iterator(), content_type='video/mp4')

@login_required
def upload_view(request):
    if request.user.is_banned:
        return render(request, 'banned.html')
    is_premium = request.user.is_premium
    error = None
    if not is_premium:
        return render(request, 'upload.html', {'is_premium': False, 'error': 'Only premium users can upload videos.'})
    if request.method == 'POST':
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.owner = request.user
            video.size_in_bytes = request.FILES['video_file'].size
            video.save()
            # Eğer premium video ise 10sn preview oluşturun (shell komutları ile ffmpeg kullanarak)
            # Bu örnekte oluşturduğunuzu varsayıyoruz ve video_preview_file atıyorsunuz.
            # Gerçekte bu aşamada bir işlem yapmalı veya önceden oluşturulmuş bir preview atayın.

            return redirect('index')
        else:
            error = form.errors
    else:
        form = VideoUploadForm()
    return render(request, 'upload.html', {'form': form, 'is_premium': True, 'error': error})

@login_required
def profile_view(request):
    if request.user.is_banned:
        return render(request, 'banned.html')
    videos = Video.objects.filter(owner=request.user)
    return render(request, 'profile.html', {'videos': videos})

@login_required
def premium_view(request):
    """View to handle premium user subscription."""
    if request.user.is_banned:
        return render(request, 'banned.html')

    if request.user.btc_address is None:
        try:
            # Generate a unique Bitcoin address for the user
            request.user.btc_address = generate_btc_address_for_user(request.user.id)
            request.user.save()
        except Exception as e:
            return render(request, 'error.html', {"message": f"Error generating address: {str(e)}"})

    is_premium = request.user.is_premium
    price = 50  # Replace with your price logic

    return render(request, 'premium.html', {
        'is_premium': is_premium,
        'address': request.user.btc_address,
        'price': price
    })

@login_required
def wallet_view(request):
    if request.user.is_banned:
        return render(request, 'banned.html')
    is_premium = request.user.is_premium
    if request.method == 'POST' and is_premium:
        btc_address = request.POST.get('btc_address')
        amount = request.POST.get('amount')
        try:
            amt = float(amount)
        except:
            amt = 0
        if amt > 0:
            WithdrawRequest.objects.create(user=request.user, amount=amt, btc_address=btc_address)
            return redirect('wallet')

    withdraw_requests = WithdrawRequest.objects.filter(user=request.user)
    return render(request, 'wallet.html', {
        'is_premium': is_premium,
        'earnings': request.user.earnings,
        'withdraw_requests': withdraw_requests
    })

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('index')
    users = User.objects.all()
    videos = Video.objects.all()
    withdraws = WithdrawRequest.objects.all()
    return render(request, 'admin_dashboard.html', {
        'users': users,
        'videos': videos,
        'withdraws': withdraws
    })

@login_required
def admin_action(request):
    if not request.user.is_superuser:
        return redirect('index')
    action = request.POST.get('action')
    from .utils import check_payments
    if action == 'ban_user':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)
        user.is_banned = True
        user.save()
    elif action == 'unban_user':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)
        user.is_banned = False
        user.save()
    elif action == 'make_premium':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)
        user.is_premium = True
        user.save()
    elif action == 'delete_video':
        video_id = request.POST.get('video_id')
        video = get_object_or_404(Video, id=video_id)
        video.delete()
    elif action == 'pay_withdraw':
        wr_id = request.POST.get('withdraw_id')
        txid = request.POST.get('txid')
        wr = get_object_or_404(WithdrawRequest, id=wr_id)
        wr.is_paid = True
        wr.txid = txid
        wr.save()
    elif action == 'check_payments':
        check_payments()

    return redirect('admin_dashboard')

def categories_view(request, category_name):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_banned:
        return render(request, 'banned.html')
    videos = Video.objects.filter(category__iexact=category_name).order_by('-upload_date')
    return render(request, 'category_videos.html', {'videos': videos, 'category_name': category_name})

def search_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_banned:
        return render(request, 'banned.html')
    query = request.GET.get('q', '')
    videos = Video.objects.filter(Q(title__icontains=query) | Q(description__icontains=query)).order_by('-upload_date')
    return render(request, 'search_results.html', {'videos': videos, 'query': query})
