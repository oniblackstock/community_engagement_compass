# Ngrok Setup & Troubleshooting Guide

## Problem: Wrong Format Response on Ngrok but Works on Localhost

This guide fixes response format issues when accessing the application through ngrok tunnels.

## Solution Applied

### 1. Created NgrokMiddleware

**File**: `config/middleware.py`

Handles:
- Ngrok forwarded protocol headers (`X-Forwarded-Proto`)
- Ngrok forwarded host headers (`X-Forwarded-Host`)
- Security headers for ngrok tunnel
- CORS headers when accessed via ngrok

### 2. Updated Settings

**File**: `config/settings/base.py`

Added `"config.middleware.NgrokMiddleware"` to MIDDLEWARE list.

### 3. Already Configured

ALLOWED_HOSTS already includes ngrok domain:
```python
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1", "your-ngrok-url.ngrok-free.dev"]
```

CSRF_TRUSTED_ORIGINS already configured:
```python
CSRF_TRUSTED_ORIGINS = ["https://your-ngrok-url.ngrok-free.dev"]
```

## How to Use Ngrok Properly

### Step 1: Update Your Ngrok URL

Edit `config/settings/local.py`:

```python
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1", "your-current-ngrok-url.ngrok-free.dev"]

CSRF_TRUSTED_ORIGINS = [
    "https://your-current-ngrok-url.ngrok-free.dev",
]
```

**Replace `your-current-ngrok-url` with your actual ngrok domain!**

### Step 2: Collect Static Files

```bash
cd /home/conovo-ai/Documents/knowledgeassistant
python manage.py collectstatic --noinput
```

### Step 3: Start Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

### Step 4: Start Ngrok Tunnel

In a new terminal:
```bash
ngrok http 8000
```

This will output something like:
```
Forwarding https://abc123def456.ngrok-free.dev -> http://localhost:8000
```

### Step 5: Access Through Ngrok

Use the HTTPS URL from ngrok output:
```
https://abc123def456.ngrok-free.dev
```

## What the Middleware Does

1. **Handles Protocol Forwarding**
   - Ensures HTTPS is recognized when using ngrok tunnel
   - Prevents "Not secure" warnings

2. **Handles Host Forwarding**
   - Ensures Django knows the correct domain
   - Prevents CSRF errors

3. **Sets Security Headers**
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: SAMEORIGIN`
   - `X-XSS-Protection: 1; mode=block`

4. **CORS Support**
   - Allows cross-origin requests when needed
   - Automatically detected for ngrok URLs

## Troubleshooting

### Issue 1: "Invalid HTTP_HOST header"

**Solution**: 
1. Get your ngrok URL: `ngrok http 8000` (see output)
2. Update `config/settings/local.py` with the exact domain
3. Restart Django server

### Issue 2: "CSRF verification failed"

**Solution**:
1. Ensure URL is in `CSRF_TRUSTED_ORIGINS`
2. Clear browser cookies
3. Reload the page

### Issue 3: CSS/JS not loading (blank page)

**Symptom**: Page loads but looks broken

**Solutions**:
1. Run `python manage.py collectstatic --noinput`
2. Check browser console (F12) for errors
3. Verify static files are serving:
   ```bash
   curl https://your-ngrok-url.ngrok-free.dev/static/css/project.css
   ```

### Issue 4: DOMPurify not loading (HTML not formatted)

**Symptom**: HTML tags visible in messages instead of formatted text

**Solutions**:
1. Check browser console for CDN errors
2. Wait for CDN to load
3. Try hard refresh (Ctrl+Shift+R)

### Issue 5: Still getting wrong format

**Debug Steps**:
1. Open browser DevTools (F12)
2. Go to Console tab
3. Check for error messages
4. Check Network tab for failed requests
5. Look for:
   - Failed CSS loads
   - Failed JS loads (including DOMPurify)
   - CORS errors
   - 404 errors

## Verify Everything Works

### Test 1: Static Files Loading

```bash
curl -I https://your-ngrok-url.ngrok-free.dev/static/css/project.css
```

Should return `200 OK`, not `404`.

### Test 2: JavaScript Loading

```bash
curl -I https://your-ngrok-url.ngrok-free.dev/static/js/project.js
```

Should return `200 OK`.

### Test 3: Form Submission

1. Go to chat page on ngrok URL
2. Send a message
3. Should display formatted response (not raw HTML tags)
4. Text should be white on purple background
5. Spacing should be clean

## Common Ngrok URLs

If your ngrok keeps changing, here are options:

### Option 1: Use Static Domain (Paid)
```bash
ngrok http 8000 --domain your-static-domain.ngrok.io
```

### Option 2: Save Domain
Create `~/.ngrok2/ngrok.yml`:
```yaml
authtoken: your-auth-token
```

Then use: `ngrok http 8000`

### Option 3: Update settings each time
Every ngrok session changes the URL. Update settings before testing.

## Using Ngrok with Docker (Alternative)

If using Docker for deployment:

```dockerfile
# In your Dockerfile
ENV ALLOWED_HOSTS=localhost,0.0.0.0,127.0.0.1,*.ngrok-free.dev
```

This allows any ngrok domain.

## Performance on Ngrok

- **Speed**: Slightly slower than localhost (network tunnel)
- **Stability**: Usually stable
- **Data**: Your data passes through ngrok tunnel (development only!)
- **Recommendations**:
  - Use ngrok for development/testing only
  - Don't expose sensitive data over ngrok
  - Regenerate auth token if sharing URLs

## Ngrok Plus Features (If Subscribed)

### Static Domains
```bash
ngrok http 8000 --domain my-api.ngrok.io
```

### Ngrok Dashboard
View all tunnels at: https://dashboard.ngrok.com

### Reserved Domains
Keep the same URL across sessions

## Quick Checklist

- [ ] Updated ALLOWED_HOSTS with your ngrok domain
- [ ] Updated CSRF_TRUSTED_ORIGINS with your ngrok domain
- [ ] Ran `collectstatic --noinput`
- [ ] Started Django: `python manage.py runserver 0.0.0.0:8000`
- [ ] Started ngrok: `ngrok http 8000`
- [ ] Tested chat functionality
- [ ] Verified HTML renders correctly
- [ ] Checked browser console for errors

## Support

If still having issues after these steps:

1. **Check exact error** in browser console
2. **Run Django in debug mode** to see backend errors
3. **Check middleware logs** for forwarding issues
4. **Verify ngrok tunnel** is active and connected

---

**Status**: ✅ Ngrok middleware implemented and configured
**Last Updated**: 2025-10-23
**Requirements**: Django running on 0.0.0.0:8000 + Ngrok installed
