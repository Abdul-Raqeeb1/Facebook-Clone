from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from .models import Account_Extra_Details, User_Posts
from .models import PostLike, PostComment
from django.contrib import messages
from django.contrib.auth import login,logout,authenticate
from .forms import UserRegisterForm

# Create your views here.

# Registration Form
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        print(form)
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

        print(email, password)

        try:
            user_obj = User.objects.get(email=email)   # ✅ Email find
        except User.DoesNotExist:
            messages.error(request,"Invalid email or password")
            return render(request,'Login_Page.html')

        user = authenticate(request, username=user_obj.username, password=password)  # ✅ Auth by username

        print(user)

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
    print(posts)
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
    return render(request, 'message_section.html')

def Market_Page(request):
    return render(request, 'Market_Section.html')

def Friends_Page(request):
    return render(request, 'Friends_Section.html')

def Requests_Page(request):
    User_get = User.objects.all()   
    return render(request, 'Request_Section.html', {'User_get': User_get})