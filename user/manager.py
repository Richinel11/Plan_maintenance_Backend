from django.contrib.auth.base_user import BaseUserManager

class UtilisateurManager(BaseUserManager):
    
    def _create_user(self, username, email, is_staff, is_superuser, password, **extra_fields):
        if not username :
            raise ValueError("username required")
        # email = self.normalize_email(email)
        user = self.model(username=username, email=email, is_staff=is_staff, is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)
        
        return user

    def create_user(self, username, email, password, **extra_fields):
        return self._create_user(username, email, False, False, password, **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        return self._create_user(username,email,True, True, password,**extra_fields)