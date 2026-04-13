from django.contrib.auth.base_user import BaseUserManager

class UtilisateurManager(BaseUserManager):

    def create_user(self, username, password=None, email=None, nom=None, prenom=None, **extra_fields):
        if not username:
            raise ValueError("Le username est obligatoire")

        email = self.normalize_email(email)

        user = self.model(
            username=username,
            email=email,
            nom=nom,
            prenom=prenom,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def get_by_natural_key(self, username):
        return self.get(username=username)

    def create_superuser(self, username, password=None, email=None, nom="Admin", prenom="Admin", **extra_fields):

        from .models import EntiteMetier
        from security.models import Role

        # IMPORTANT: get default objects
        entite = EntiteMetier.objects.first()
        role = Role.objects.first()

        if not entite:
            raise ValueError("Créer au moins une EntiteMetier avant")
        if not role:
            raise ValueError("Créer au moins un Role avant")

        # inject required fields
        extra_fields.setdefault("entite_metier", entite)
        extra_fields.setdefault("role", role)

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser doit avoir is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser doit avoir is_superuser=True")

        return self.create_user(
            username=username,
            password=password,
            email=email,
            nom=nom,
            prenom=prenom,
            **extra_fields
        )