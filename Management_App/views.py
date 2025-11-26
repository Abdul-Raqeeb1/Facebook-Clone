from django.shortcuts import render,redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from .models import Account_Extra_Details, User_Posts
from .models import PostLike, PostComment
from django.contrib import messages
from django.db.models import Q
import json
from django.contrib.auth import login,logout,authenticate
from .forms import UserRegisterForm

# Create your views here.

# Registration Form
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been created!")
            return redirect('Login_Page')
        else:
            form = UserRegisterForm()  # error case me form reset
    else:
        form = UserRegisterForm()  # GET request ke liye empty form

    return render(request, 'Create_Account.html', {"form": form})

#create account 

def Create_Account(request):
        if request.method == 'POST':
            email = request.POST.get('email')
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered!")
                return redirect('RegisterAccount')
            
            # Create new user
            user = User()
            user.first_name = request.POST.get('first')
            user.last_name = request.POST.get('surname')
            user.email = email
            # Generate username from email (part before @)
            user.username = email.split('@')[0]
            
            # If username exists, append numbers until unique
            base_username = user.username
            counter = 1
            while User.objects.filter(username=user.username).exists():
                user.username = f"{base_username}{counter}"
                counter += 1
                
            user.set_password(request.POST.get('password'))
            user.save()
            
            # Create extra details
            gender = request.POST.get('gender')
            Account_Extra_Details.objects.create(user_id=user, gender=gender)

            messages.success(request, "Account created successfully!")
            return redirect('Homepage')

# Login Function

def Login_Page(request):
    if request.method == 'POST':
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email=email)   # ✅ Email find
        except User.DoesNotExist:
            messages.error(request,"Invalid email or password")
            return render(request,'Login_Page.html')

        user = authenticate(request, username=user_obj.username, password=password)  # ✅ Auth by username

        if user is not None:
            login(request, user)
            request.session["email"] = user.email
            messages.success(request, "Logged in successfully!")
            return redirect('Homepage')
        else:
            messages.error(request, "Invalid email or password")
            return render(request, 'Login_Page.html')

    return render(request, 'Login_Page.html')

# Logout Function

def Logout_Page(request):
    logout(request)
    messages.success(request,"Logged out successfully!")
    return redirect('Login_Page')

# Facebook home page

def Home_Page(request):
    # Fetch posts and mark if the attached file is a video so template can render correctly
    posts_qs = User_Posts.objects.all().order_by('-post_time')
    posts = []
    for p in posts_qs:
        is_video = False
        try:
            if p.post_image and hasattr(p.post_image, 'name'):
                name = p.post_image.name.lower()
                if name.endswith(('.mp4', '.webm', '.ogg')):
                    is_video = True
        except Exception:
            is_video = False
        # attach attribute for template convenience
        setattr(p, 'is_video', is_video)
        posts.append(p)

    return render(request, 'Facebook_Home.html', {'posts': posts})

# User Profile Page

def User_Profile(request):
    # Require login to view profile (simple check)
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to view your profile.")
        return redirect('Login_Page')
    
    # Ensure Account_Extra_Details exists for this user so template access won't fail
    try:
        Account_Extra_Details.objects.get_or_create(user_id=request.user, defaults={'gender': 'CU'})
    except Exception:
        # If creation fails, continue to render but warn in messages
        messages.warning(request, "Could not ensure profile details exist. Some profile features may be missing.")

    posts = User_Posts.objects.filter(post_id=request.user.id)
    return render(request,'User_Profile.html', { 'user': request.user,"user_posts":posts })

# Delete Account Function

def Delete_Account(request):
    # Deletes the currently logged-in user's account on POST
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to delete your account.")
            return redirect('Login_Page')
        user = request.user
        logout(request)
        # delete user record
        try:
            user.delete()
            messages.success(request, "Your account has been deleted.")
        except Exception as e:
            messages.error(request, "Could not delete account. Please contact support.")
        return redirect('Login_Page')
    # For non-POST requests, redirect back to profile
    return redirect('User_Profile')

# Edit Profile Function
def Edit_Profile(request):
    # Handle profile edits: first_name, last_name, profile picture
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to edit your profile.")
            return redirect('Login_Page')

        first = request.POST.get('first_name', '').strip()
        last = request.POST.get('last_name', '').strip()
        pic = request.FILES.get('profile_pic')

        user = request.user
        if first:
            user.first_name = first
        if last:
            user.last_name = last
        try:
            user.save()
        except Exception:
            messages.error(request, "Could not update name. Please try again.")
            return redirect('User_Profile')

        # Update or create Account_Extra_Details and save picture if provided
        try:
            # If extra details don't exist, create with a safe default for required fields
            aed, created = Account_Extra_Details.objects.get_or_create(user_id=user, defaults={'gender': 'CU'})

            # Basic validation: limit file size to 5 MB
            if pic:
                max_size = 5 * 1024 * 1024
                if getattr(pic, 'size', 0) > max_size:
                    messages.error(request, "Profile picture is too large (max 5 MB).")
                    return redirect('User_Profile')

                # Optional: basic content-type check
                content_type = getattr(pic, 'content_type', '')
                if content_type and not content_type.startswith('image/'):
                    messages.error(request, "Uploaded file is not an image.")
                    return redirect('User_Profile')

                aed.profile_pic = pic

            aed.save()
        except Exception:
            messages.error(request, "Could not update profile details. Please try again.")
            return redirect('User_Profile')

        messages.success(request, "Profile updated successfully.")
        return redirect('User_Profile')

    return redirect('User_Profile')

# Create post (handles text or media posts)

def Create_Post(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to create a post.")
            return redirect('Login_Page')

        title = request.POST.get('post_title', '').strip()
        image = request.FILES.get('post_image')

        # Create the post record (basic implementation)
        try:
            User_Posts.objects.create(
                post_id=request.user,
                title_post=title if title else (request.POST.get('quick_post_text') or ''),
                post_image=image
            )
            messages.success(request, "Your post was created.")
        except Exception as e:
            # Log/notify minimal info and continue
            messages.error(request, "Could not create post. Please try again.")

        return redirect('Homepage')

    return redirect('Homepage')

# def Show_Posts(request):

#     current_user = request.user
#     user_post = User_Posts.objects.filter(post_id=current_user).all

#     return render(request,"User_Profile.html",{'show_content':user_post})


def Like_Post(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to like posts.")
            return redirect('Login_Page')

        post_id = request.POST.get('post_id')
        try:
            post = User_Posts.objects.get(id=post_id)
        except User_Posts.DoesNotExist:
            messages.error(request, "Post not found.")
            return redirect('Homepage')

        # toggle like
        like_qs = PostLike.objects.filter(user=request.user, post=post)
        if like_qs.exists():
            like_qs.delete()
            # decrement count if field present
            try:
                post.post_likes = max(0, int(post.post_likes) - 1)
                post.save()
            except Exception:
                pass
            messages.info(request, "Like removed.")
        else:
            PostLike.objects.create(user=request.user, post=post)
            try:
                post.post_likes = int(post.post_likes or 0) + 1
                post.save()
            except Exception:
                pass
            messages.success(request, "Post liked.")

        return redirect('Homepage')


def Add_Comment(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to comment.")
            return redirect('Login_Page')

        post_id = request.POST.get('post_id')
        text = request.POST.get('comment_text', '').strip()
        if not text:
            messages.error(request, "Comment cannot be empty.")
            return redirect('Homepage')

        try:
            post = User_Posts.objects.get(id=post_id)
        except User_Posts.DoesNotExist:
            messages.error(request, "Post not found.")
            return redirect('Homepage')

        PostComment.objects.create(user=request.user, post=post, comment_text=text)
        messages.success(request, "Comment added.")
        return redirect('Homepage')

    return redirect('Homepage')


def Video_Page(request):
    return render(request, 'videos_section.html')   

def Message_Page(request):
    # Fetch all friends and their last messages
    if not request.user.is_authenticated:
        return render(request, 'message_section.html', {'friends': [], 'conversations': {}})
    
    from Management_App.models import Friendship, Message
    from django.db.models import Q
    
    # Get all friends (accepted friendships)
    friends_qs = Friendship.objects.filter(user=request.user).select_related('friend').order_by('friend__first_name')
    friends = [f.friend for f in friends_qs]
    
    # Get last message for each friend (in either direction)
    conversations = {}
    for friend in friends:
        last_msg = Message.objects.filter(
            Q(sender=request.user, recipient=friend) | Q(sender=friend, recipient=request.user)
        ).select_related('sender', 'recipient').order_by('-created_at').first()
        
        conversations[friend.id] = {
            'friend': friend,
            'last_message': last_msg.text if last_msg else '',
            'last_time': last_msg.created_at if last_msg else None,
        }
    
    return render(request, 'message_section.html', {
        'friends': friends,
        'conversations': conversations,
    })

def Market_Page(request):
    return render(request, 'Market_Section.html')

def Friends_Page(request):
    # Pass list of users to the template and the current friendship/request state
    users_qs = User.objects.all().order_by('username')
    if request.user.is_authenticated:
        users_qs = users_qs.exclude(id=request.user.id)

        from Management_App.models import Friendship, FriendRequest
        # accepted friends (user -> friend)
        friends_qs = Friendship.objects.filter(user=request.user).select_related('friend')
        friend_ids = set(f.friend.id for f in friends_qs)

        # outgoing pending requests (to_user ids)
        outgoing_ids = set(FriendRequest.objects.filter(from_user=request.user, accepted=False).values_list('to_user_id', flat=True))

        # incoming pending requests (from_user ids)
        incoming_qs = FriendRequest.objects.filter(to_user=request.user, accepted=False).select_related('from_user')
        incoming_ids = set(incoming_qs.values_list('from_user_id', flat=True))
        # map from_user -> friendrequest id for quick lookup in template
        incoming_map = { fr.from_user.id: fr.id for fr in incoming_qs }

        return render(request, 'Friends_Section.html', {
            'users': users_qs,
            'friend_ids': friend_ids,
            'outgoing_ids': outgoing_ids,
            'incoming_ids': incoming_ids,
            'incoming_map': incoming_map,
        })

    return render(request, 'Friends_Section.html', {'users': users_qs})

def Requests_Page(request):
    # Fetch incoming pending requests for the current user
    if not request.user.is_authenticated:
        return render(request, 'Request_Section.html', {'incoming_requests': []})
    
    from Management_App.models import FriendRequest
    incoming = FriendRequest.objects.filter(to_user=request.user, accepted=False).select_related('from_user').order_by('-created_at')
    return render(request, 'Request_Section.html', {'incoming_requests': incoming})


# API: send friend request
def api_send_request(request):
    # Create a friend request: ensure authenticated, prevent duplicates, prevent when already friends
    if request.method != 'POST':
        return JsonResponse({'status': 'method_not_allowed'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'unauthorized'}, status=401)

    to_id = request.POST.get('to_id')
    if not to_id:
        return JsonResponse({'status': 'error', 'message': 'to_id required'}, status=400)
    try:
        to_user = User.objects.get(id=to_id)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'user not found'}, status=404)

    if to_user == request.user:
        return JsonResponse({'status': 'error', 'message': 'cannot send to self'}, status=400)

    from Management_App.models import FriendRequest, Friendship, Notification

    # if already friends, do not create request
    if Friendship.objects.filter(user=request.user, friend=to_user).exists():
        return JsonResponse({'status': 'already_friends'}, status=400)

    # prevent duplicate pending requests in same direction
    existing = FriendRequest.objects.filter(from_user=request.user, to_user=to_user).first()
    if existing:
        return JsonResponse({'status': 'exists', 'fr_id': existing.id}, status=200)

    # if there is an incoming request from the other user, accept it automatically
    incoming = FriendRequest.objects.filter(from_user=to_user, to_user=request.user, accepted=False).first()
    if incoming:
        # accept incoming instead of creating duplicate
        incoming.accepted = True
        incoming.save()
        Friendship.objects.get_or_create(user=request.user, friend=to_user)
        Friendship.objects.get_or_create(user=to_user, friend=request.user)
        Notification.objects.create(user=to_user, actor=request.user, verb='accepted your friend request')
        return JsonResponse({'status': 'accepted_existing', 'fr_id': incoming.id}, status=200)

    # create a new FriendRequest
    fr = FriendRequest.objects.create(from_user=request.user, to_user=to_user)
    Notification.objects.create(user=to_user, actor=request.user, verb='sent you a friend request')
    return JsonResponse({'status': 'created', 'fr_id': fr.id}, status=201)


# API: list friend requests for current user
def api_list_requests(request):
    # Return only incoming pending friend requests for the current user
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'unauthorized'}, status=401)

    from Management_App.models import FriendRequest
    incoming = FriendRequest.objects.filter(to_user=request.user, accepted=False).select_related('from_user').order_by('-created_at')
    data = []
    for fr in incoming:
        from_u = fr.from_user
        data.append({
            'id': fr.id,
            'from_id': from_u.id,
            'name': from_u.get_full_name() or from_u.username,
            'username': from_u.username,
            'img': '',
            'mutual': 0,
            'created_at': fr.created_at.isoformat(),
            'outgoing': False,
        })
    return JsonResponse(data, safe=False)


def api_accept_request(request):
    # Accept friend request - only recipient should accept
    if request.method != 'POST':
        return JsonResponse({'status': 'method_not_allowed'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'unauthorized'}, status=401)

    fr_id = request.POST.get('fr_id')
    if not fr_id:
        return JsonResponse({'status': 'error', 'message': 'fr_id required'}, status=400)

    from Management_App.models import FriendRequest, Friendship, Notification
    try:
        fr = FriendRequest.objects.select_related('from_user', 'to_user').get(id=fr_id)
    except FriendRequest.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)

    # Only the recipient can accept the request
    if fr.to_user != request.user:
        return JsonResponse({'status': 'forbidden'}, status=403)

    if fr.accepted:
        return JsonResponse({'status': 'already_accepted', 'fr_id': fr.id}, status=200)

    fr.accepted = True
    fr.save()

    # create mutual friendships (avoid duplicates)
    Friendship.objects.get_or_create(user=fr.to_user, friend=fr.from_user)
    Friendship.objects.get_or_create(user=fr.from_user, friend=fr.to_user)

    # notify the sender
    Notification.objects.create(user=fr.from_user, actor=request.user, verb='accepted your friend request')
    return JsonResponse({'status': 'accepted', 'fr_id': fr.id}, status=200)


# API: send message
def api_send_message(request):
    # Send a message - only allowed between accepted friends
    if request.method != 'POST':
        return JsonResponse({'status': 'method_not_allowed'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'unauthorized'}, status=401)

    to_id = request.POST.get('to_id')
    text = request.POST.get('text','').strip()
    if not to_id or not text:
        return JsonResponse({'status': 'error', 'message': 'to_id and text required'}, status=400)

    try:
        to_user = User.objects.get(id=to_id)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'user not found'}, status=404)

    from Management_App.models import Message, Notification, Friendship
    # check friendship exists (both directions stored)
    if not Friendship.objects.filter(user=request.user, friend=to_user).exists():
        return JsonResponse({'status': 'forbidden', 'message': 'can only message friends'}, status=403)

    m = Message.objects.create(sender=request.user, recipient=to_user, text=text)
    Notification.objects.create(user=to_user, actor=request.user, verb='sent you a message')
    return JsonResponse({'status': 'sent', 'message_id': m.id}, status=201)


def api_list_conversations(request):
    # List conversations: only include accepted friends and last message/time
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'unauthorized'}, status=401)

    from Management_App.models import Message, Friendship
    # find friends of current user
    friend_ids = Friendship.objects.filter(user=request.user).values_list('friend_id', flat=True)
    # gather latest message per friend (either direction)
    qs = Message.objects.filter((Q(sender=request.user) & Q(recipient__in=friend_ids)) | (Q(recipient=request.user) & Q(sender__in=friend_ids))).select_related('sender','recipient').order_by('-created_at')[:500]
    conv = {}
    for m in qs:
        other = m.recipient if m.sender == request.user else m.sender
        if other.id not in conv:
            conv[other.id] = {
                'id': other.id,
                'name': other.get_full_name() or other.username,
                'avatar': '',
                'last_message': m.text,
                'time': m.created_at.isoformat(),
            }
    # also include friends with no messages (optional: show them with empty last_message)
    for fid in friend_ids:
        if fid not in conv:
            try:
                u = User.objects.get(id=fid)
                conv[fid] = {'id': u.id, 'name': u.get_full_name() or u.username, 'avatar':'', 'last_message': '', 'time': ''}
            except User.DoesNotExist:
                continue

    return JsonResponse(list(conv.values()), safe=False)


def api_delete_request(request):
    if request.method == 'POST' and request.user.is_authenticated:
        fr_id = request.POST.get('fr_id')
        from Management_App.models import FriendRequest
        try:
            fr = FriendRequest.objects.get(id=fr_id)
        except FriendRequest.DoesNotExist:
            return HttpResponse('Not found', status=404)
        # allow either sender or receiver to delete
        if fr.from_user == request.user or fr.to_user == request.user:
            fr.delete()
            return HttpResponse('Deleted', status=200)
        return HttpResponse('Forbidden', status=403)
    return HttpResponse('Unauthorized', status=401)


# API: check friendship/request status between current user and another user
def api_check_friend_status(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'unauthenticated'}, status=401)

    user_id = request.GET.get('user_id')
    if not user_id:
        return JsonResponse({'status': 'error', 'message': 'user_id required'}, status=400)
    try:
        other = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'user not found'}, status=404)

    from Management_App.models import Friendship, FriendRequest

    # check friendship
    is_friend = Friendship.objects.filter(user=request.user, friend=other).exists()
    if is_friend:
        return JsonResponse({'status': 'friend'})

    # check outgoing pending
    pending_out = FriendRequest.objects.filter(from_user=request.user, to_user=other, accepted=False).first()
    if pending_out:
        return JsonResponse({'status': 'pending', 'fr_id': pending_out.id})

    # check incoming pending
    pending_in = FriendRequest.objects.filter(from_user=other, to_user=request.user, accepted=False).first()
    if pending_in:
        return JsonResponse({'status': 'incoming', 'fr_id': pending_in.id})

    return JsonResponse({'status': 'none'})


# API: get messages with a friend
def api_get_messages(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'unauthorized'}, status=401)
    
    friend_id = request.GET.get('friend_id')
    if not friend_id:
        return JsonResponse({'status': 'error', 'message': 'friend_id required'}, status=400)
    
    try:
        friend = User.objects.get(id=friend_id)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'friend not found'}, status=404)
    
    from Management_App.models import Message, Friendship
    from django.db.models import Q
    
    # Check if they are friends
    if not Friendship.objects.filter(user=request.user, friend=friend).exists():
        return JsonResponse({'status': 'forbidden', 'message': 'not friends'}, status=403)
    
    # Fetch messages (both directions)
    messages = Message.objects.filter(
        Q(sender=request.user, recipient=friend) | Q(sender=friend, recipient=request.user)
    ).select_related('sender', 'recipient').order_by('created_at')
    
    data = []
    for m in messages:
        data.append({
            'id': m.id,
            'from_me': m.sender == request.user,
            'text': m.text,
            'time': m.created_at.strftime('%H:%M'),
        })
    
    return JsonResponse(data, safe=False)