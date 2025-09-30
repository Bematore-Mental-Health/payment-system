"""
Django management command to create a superuser for Bematore Payment System
Usage: python manage.py create_admin_user
"""

import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import IntegrityError


class Command(BaseCommand):
    help = 'Create a superuser for Bematore Payment System'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the superuser (default: admin)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@bematore.com',
            help='Email for the superuser (default: admin@bematore.com)',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the superuser (will prompt if not provided)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force create superuser even if one already exists',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        force = options['force']

        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists() and not force:
            self.stdout.write(
                self.style.WARNING(
                    'A superuser already exists. Use --force to create another one.'
                )
            )
            return

        # Get password from environment or prompt
        if not password:
            password = os.getenv('ADMIN_PASSWORD')
            
        if not password:
            password = input('Enter password for superuser: ')

        if not password:
            self.stdout.write(
                self.style.ERROR('Password is required to create superuser.')
            )
            return

        try:
            # Create the superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created superuser "{username}" for Bematore Payment System'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Email: {email}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'You can now access the admin panel at /admin/'
                )
            )
            
        except IntegrityError:
            if force:
                # User exists, update it
                user = User.objects.get(username=username)
                user.set_password(password)
                user.email = email
                user.is_superuser = True
                user.is_staff = True
                user.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully updated superuser "{username}"'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'User "{username}" already exists. Use --force to update.'
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error creating superuser: {str(e)}'
                )
            )