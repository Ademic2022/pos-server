import factory
from factory.django import DjangoModelFactory


class PermissionFactory(DjangoModelFactory):
    class Meta:
        model = "auth.Permission"
        django_get_or_create = ("codename", "content_type")

    name = factory.Sequence(lambda n: f"Permission {n}")
    codename = factory.Sequence(lambda n: f"perm_{n}")
    content_type = factory.SubFactory("django.contrib.contenttypes.models.ContentType")


class RoleFactory(DjangoModelFactory):
    class Meta:
        model = "accounts.Role"
        skip_postgeneration_save = True

    name = factory.Sequence(lambda n: f"Role {n}")
    description = factory.Faker("text", max_nb_chars=200)

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for permission in extracted:
                self.permissions.add(permission)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = "accounts.User"
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    phone = factory.Faker("phone_number")
    address = factory.Faker("address")
    employee_id = factory.Sequence(lambda n: f"EMP{n:04d}")
    salary = factory.Faker("pydecimal", left_digits=5, right_digits=2, positive=True)

    @factory.post_generation
    def set_password(self, create, extracted, **kwargs):
        if not create:
            return
        password = extracted or "testpass123"
        self.set_password(password)
        self.save()


class StaffUserFactory(UserFactory):
    is_staff = True


class SuperUserFactory(UserFactory):
    is_staff = True
    is_superuser = True


class UserSessionFactory(DjangoModelFactory):
    class Meta:
        model = "accounts.UserSession"

    user = factory.SubFactory(UserFactory)
    session_key = factory.Faker("uuid4")
    ip_address = factory.Faker("ipv4")
    user_agent = factory.Faker("user_agent")
    is_active = True


class ActivityLogFactory(DjangoModelFactory):
    class Meta:
        model = "accounts.ActivityLog"

    user = factory.SubFactory(UserFactory)
    action = factory.Faker(
        "random_element",
        elements=("create", "update", "delete", "view", "login", "logout"),
    )
    model_name = factory.Faker("word")
    object_id = factory.Faker("random_int", min=1, max=1000)
    object_repr = factory.Faker("sentence", nb_words=3)
    ip_address = factory.Faker("ipv4")
    user_agent = factory.Faker("user_agent")
