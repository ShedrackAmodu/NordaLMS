from django.core.management.base import BaseCommand
from django.core.management import call_command
import subprocess


class Command(BaseCommand):
    help = 'Deploy the application: install dependencies, run migrations, collect static files, create superuser, and load dummy data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting deployment process...'))

        # Install dependencies
        self.stdout.write('Installing dependencies...')
        try:
            subprocess.check_call(['pip', 'install', '-r', 'requirements/production.txt'])
            self.stdout.write(self.style.SUCCESS('Dependencies installed successfully.'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Failed to install dependencies: {e}'))
            return

        # Run makemigrations
        self.stdout.write('Running makemigrations...')
        try:
            call_command('makemigrations', interactive=False)
            self.stdout.write(self.style.SUCCESS('Makemigrations completed.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to run makemigrations: {e}'))
            return

        # Run migrate
        self.stdout.write('Running migrate...')
        try:
            call_command('migrate', interactive=False)
            self.stdout.write(self.style.SUCCESS('Migration completed.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to run migrate: {e}'))
            return

        # Collect static files
        self.stdout.write('Collecting static files...')
        try:
            call_command('collectstatic', '--noinput')
            self.stdout.write(self.style.SUCCESS('Static files collected.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to collect static files: {e}'))
            return

        # Create superuser if not exists
        self.stdout.write('Checking/creating superuser...')
        try:
            from accounts.models import User
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser('admin', 'admin@example.com', 'admin')
                self.stdout.write(self.style.SUCCESS('Superuser admin/admin created.'))
            else:
                self.stdout.write('Superuser admin already exists.')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to create superuser: {e}'))
            return

        # Load dummy data
        self.stdout.write('Loading dummy data...')
        try:
            from scripts.generate_fake_core_data import generate_fake_core_data
            generate_fake_core_data(num_news_and_events=10, num_sessions=5, num_semesters=10, num_activity_logs=20)

            from scripts.generate_fake_accounts_data import generate_fake_accounts_data
            generate_fake_accounts_data(num_programs=5, num_students=50, num_parents=20)

            from scripts.generate_fake_data import generate_fake_course_data, populate_course_allocation
            generate_fake_course_data(
                num_programs=5, num_courses=50, num_course_allocations=10,
                num_uploads=100, num_upload_videos=20, num_course_offers=10
            )
            populate_course_allocation(num_allocations=20)

            self.stdout.write(self.style.SUCCESS('Dummy data loaded.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to load dummy data: {e}'))
            return

        self.stdout.write(self.style.SUCCESS('Deployment completed successfully!'))
        self.stdout.write('You can now reload your PythonAnywhere web app.')
