# NordaLMS Deployment Guide - PythonAnywhere

This guide will help you deploy the NordaLMS application to PythonAnywhere.

## Prerequisites

- A PythonAnywhere account
- The NordaLMS code pushed to a Git repository (e.g., GitHub)

## Step 1: Create a PythonAnywhere Account and Web App

1. Go to [PythonAnywhere](https://pythonanywhere.com) and sign up for an account
2. Create a new web app under the "Web" tab
3. Select:
   - **Framework**: Manual configuration (custom WSGI configuration)
   - **Python version**: 3.8 or later
   - **Domain name**: Keep the default (yourusername.pythonanywhere.com) or use your domain

## Step 2: Clone Your Repository

```bash
# In bash console
mkdir LearningManagementSystem
cd LearningManagementSystem
git clone https://github.com/ShedrackAmodu/NordaLMS.git NordaLMS
cd NordaLMS
```

## Step 3: Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv myenv

# Activate it
source myenv/bin/activate

# Install production requirements
pip install -r requirements/production.txt
```

## Step 4: Configure Environment Variables

1. In the PythonAnywhere web dashboard, go to "Variables"
2. Add the following environment variables from your `.env.production` file:

```
DEBUG=False
SECRET_KEY=<your-secure-secret-key>
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_FROM_ADDRESS=NordaLMS <your-email@yourdomain.com>
EMAIL_HOST_USER=<your-email@yourdomain.com>
EMAIL_HOST_PASSWORD=<your-app-password>
STRIPE_SECRET_KEY=<your-stripe-secret-key>
STRIPE_PUBLISHABLE_KEY=<your-stripe-publishable-key>
STUDENT_ID_PREFIX=NDS
LECTURER_ID_PREFIX=LEC
```

## Step 5: Run Deployment Command

```bash
# Navigate to the project directory
cd ~/LearningManagementSystem/NordaLMS

# Activate virtual environment
source ../myenv/bin/activate

# Run the deployment command (runs migrations, collects static, creates superuser, loads sample data)
python manage.py deploy
```

## Step 6: Configure WSGI

1. In the PythonAnywhere web dashboard, go to "WSGI configuration file"
2. Edit the WSGI configuration file to point to our custom wsgi.py:

```python
import os
import sys

# Add the project directory to the sys.path
path = '/home/yourusername/LearningManagementSystem/NordaLMS'
if path not in sys.path:
    sys.path.insert(0, '/home/yourusername/LearningManagementSystem/NordaLMS')

# Activate virtualenv
activate_env=os.path.expanduser('/home/yourusername/LearningManagementSystem/myenv/bin/activate_this.py')
exec(open(activate_env).read(), {'__file__': activate_env})

from wsgi_pythonanywhere import application
```

**Note**: Replace `yourusername` with your actual PythonAnywhere username.

## Step 7: Static Files Configuration

1. In the PythonAnywhere web dashboard, go to "Static files"
2. Add a new static file entry:
   - URL: `/static/`
   - Directory: `/home/yourusername/LearningManagementSystem/NordaLMS/staticfiles`

## Step 8: Media Files (Optional)

If you need to serve media files, configure them under "Static files" section:
- URL: `/media/`
- Directory: `/home/yourusername/LearningManagementSystem/NordaLMS/media`

## Step 9: Test Your Deployment

1. Click the "Reload" button in the PythonAnywhere web dashboard
2. Visit your PythonAnywhere URL to test the application
3. Check that admin login works and static files are loading

## Step 10: Domain Configuration (Optional)

If you have a custom domain, configure it in the PythonAnywhere dashboard under "Web" > "Domain" tab.

## Performance Tips

- Use Whitenoise for static file serving (already configured)
- Consider upgrading to PythonAnywhere paid plan for better performance
- Set up log files and monitor them regularly

## Troubleshooting

- **500 Errors**: Check the error logs in PythonAnywhere dashboard
- **Static Files Not Loading**: Ensure static files were collected and the path is correct
- **Database Issues**: Run migrations and check database file permissions
- **Environment Variables**: Make sure all required environment variables are set

## Security Notes

- Keep your SECRET_KEY secure and unique
- Use HTTPS (enabled by default on PythonAnywhere)
- Update your Django version regularly
- Monitor for security updates in your dependencies
