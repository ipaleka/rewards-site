"""Testing module for :py:mod:`core.models` module."""

from datetime import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import DataError, models
from django.http import Http404
from django.db.utils import IntegrityError
from django.utils import timezone

from core.models import (
    Contribution,
    Contributor,
    ContributorManager,
    Cycle,
    Handle,
    HandleManager,
    Reward,
    SocialProvider,
    _parse_full_handle,
)


class TestCoreCoreModelsHelpers:
    """Testing class for :py:mod:`core.models` helper functions."""

    # # _parse_full_handle
    @pytest.mark.parametrize(
        "full_handle,prefix,handle",
        [
            ("u/user1", "u/", "user1"),
            ("address", "", "address"),
            ("g@address", "g@", "address"),
            ("handle", "", "handle"),
            ("@handle", "@", "handle"),
            ("u/username", "u/", "username"),
            ("username", "", "username"),
            ("@address", "@", "address"),
            ("t@handle", "t@", "handle"),
            ("g@handle", "g@", "handle"),
        ],
    )
    def test_core_models_parse_full_handle_functionality(
        self, full_handle, prefix, handle
    ):
        assert _parse_full_handle(full_handle) == (prefix, handle)


class TestCoreContributorManager:
    """Testing class for :class:`core.models.ContributorManager` class."""

    # # from_full_handle

    @pytest.mark.django_db
    def test_core_contributormanager_from_full_handle_raises_error_for_no_provider(
        self,
    ):
        prefix, username = "h@", "username1"
        address, full_handle = "contributormanager1address", f"{prefix}{username}"
        with pytest.raises(Http404):
            Contributor.objects.from_full_handle(full_handle, address)

    @pytest.mark.django_db
    def test_core_contributormanager_from_full_handle_for_existing_handle(self, mocker):
        prefix, username = "c@", "username2"
        address, full_handle = "contributormanager2address", f"{prefix}{username}"
        contributor = Contributor.objects.create(name=full_handle, address=address)
        provider = SocialProvider.objects.create(
            name="contributormanagerprovider2", prefix=prefix
        )
        Handle.objects.create(
            contributor=contributor, provider=provider, handle=username
        )
        mocked_save = mocker.patch("core.models.Contributor.save")
        returned = Contributor.objects.from_full_handle(full_handle, address)
        assert returned == contributor
        mocked_save.assert_not_called()

    @pytest.mark.django_db
    def test_core_contributormanager_from_full_handle_creates_handle(self):
        prefix, username = "h@", "username3"
        address, full_handle = "contributormanager3address", f"{prefix}{username}"
        SocialProvider.objects.create(name="contributormanagerprovider3", prefix=prefix)
        assert Contributor.objects.count() == 0
        assert Handle.objects.count() == 0
        returned = Contributor.objects.from_full_handle(full_handle, address)
        assert isinstance(returned, Contributor)
        assert returned.name == full_handle
        assert returned.address == address
        assert Contributor.objects.count() == 1
        assert Handle.objects.count() == 1

    @pytest.mark.django_db
    def test_core_contributormanager_from_full_handle_for_no_address_provided(self):
        prefix, username = "h@", "username4"
        full_handle = f"{prefix}{username}"
        SocialProvider.objects.create(name="contributormanagerprovider4", prefix=prefix)
        assert Contributor.objects.count() == 0
        assert Handle.objects.count() == 0
        returned = Contributor.objects.from_full_handle(full_handle)
        assert isinstance(returned, Contributor)
        assert returned.name == full_handle
        assert returned.address is None
        assert Contributor.objects.count() == 1
        assert Handle.objects.count() == 1


class TestCoreContributorModel:
    """Testing class for :class:`core.models.Contributor` model."""

    # # field characteristics
    @pytest.mark.parametrize(
        "name,typ",
        [
            ("name", models.CharField),
            ("address", models.CharField),
            ("created_at", models.DateTimeField),
            ("updated_at", models.DateTimeField),
        ],
    )
    def test_core_contributor_model_fields(self, name, typ):
        assert hasattr(Contributor, name)
        assert isinstance(Contributor._meta.get_field(name), typ)

    @pytest.mark.django_db
    def test_core_contributor_model_name_is_not_optional(self):
        with pytest.raises(ValidationError):
            Contributor().full_clean()

    @pytest.mark.django_db
    def test_core_contributor_model_cannot_save_too_long_name(self):
        contributor = Contributor(name="a" * 100)
        with pytest.raises(DataError):
            contributor.save()
            contributor.full_clean()

    @pytest.mark.django_db
    def test_core_contributor_model_cannot_save_too_long_address(self):
        contributor = Contributor(address="a" * 100)
        with pytest.raises(DataError):
            contributor.save()
            contributor.full_clean()

    def test_core_contributor_objects_is_contributormanager_instance(self):
        assert isinstance(Contributor.objects, ContributorManager)

    # # Meta
    @pytest.mark.django_db
    def test_core_contributor_model_ordering(self):
        contributor1 = Contributor.objects.create(name="Abcde", address="address1")
        contributor2 = Contributor.objects.create(name="aabcde", address="address2")
        contributor3 = Contributor.objects.create(name="bcde", address="address3")
        contributor4 = Contributor.objects.create(name="Bcde", address="address4")
        assert list(Contributor.objects.all()) == [
            contributor2,
            contributor1,
            contributor3,
            contributor4,
        ]

    # # save
    @pytest.mark.django_db
    def test_core_contributor_model_save_duplicate_name_is_invalid(self):
        Contributor.objects.create(name="name1")
        with pytest.raises(IntegrityError):
            contributor = Contributor(name="name1")
            contributor.save()

    @pytest.mark.django_db
    def test_core_contributor_model_save_duplicate_address_is_invalid(self):
        Contributor.objects.create(address="address1")
        with pytest.raises(IntegrityError):
            contributor = Contributor(address="address1")
            contributor.save()

    # # __str__
    @pytest.mark.django_db
    def test_core_contributor_model_string_representation_is_contributor_name(self):
        contributor = Contributor(name="user name")
        assert str(contributor) == "user name"


class TestCoreSocialProviderModel:
    """Testing class for :class:`core.models.SocialProvider` model."""

    # # field characteristics
    @pytest.mark.parametrize(
        "name,typ",
        [
            ("name", models.CharField),
            ("prefix", models.CharField),
        ],
    )
    def test_core_socialprovider_model_fields(self, name, typ):
        assert hasattr(SocialProvider, name)
        assert isinstance(SocialProvider._meta.get_field(name), typ)

    @pytest.mark.django_db
    def test_core_socialprovider_model_name_is_not_optional(self):
        with pytest.raises(ValidationError):
            SocialProvider().full_clean()

    @pytest.mark.django_db
    def test_core_socialprovider_model_cannot_save_too_long_name(self):
        social_provider = SocialProvider(name="a" * 100)
        with pytest.raises(DataError):
            social_provider.save()
            social_provider.full_clean()

    @pytest.mark.django_db
    def test_core_socialprovider_model_cannot_save_too_long_prefix(self):
        social_provider = SocialProvider(prefix="abc")
        with pytest.raises(DataError):
            social_provider.save()
            social_provider.full_clean()

    # # Meta
    @pytest.mark.django_db
    def test_core_socialprovider_model_ordering(self):
        social_provider1 = SocialProvider.objects.create(name="Abcde", prefix="1")
        social_provider2 = SocialProvider.objects.create(name="aabcde", prefix="5")
        social_provider3 = SocialProvider.objects.create(name="bcde", prefix="a")
        social_provider4 = SocialProvider.objects.create(name="Bcde", prefix="c")
        assert list(SocialProvider.objects.all()) == [
            social_provider2,
            social_provider1,
            social_provider3,
            social_provider4,
        ]

    # # save
    @pytest.mark.django_db
    def test_core_socialprovider_model_save_duplicate_name_is_invalid(self):
        SocialProvider.objects.create(name="name1", prefix="a")
        with pytest.raises(IntegrityError):
            social_provider = SocialProvider(name="name1", prefix="b")
            social_provider.save()

    @pytest.mark.django_db
    def test_core_socialprovider_model_save_duplicate_prefix_is_invalid(self):
        SocialProvider.objects.create(name="name8", prefix="p1")
        with pytest.raises(IntegrityError):
            social_provider = SocialProvider(name="name9", prefix="p1")
            social_provider.save()

    # # __str__
    @pytest.mark.django_db
    def test_core_socialprovider_model_string_representation_is_social_provider_name(
        self,
    ):
        social_provider = SocialProvider(name="social name")
        assert str(social_provider) == "social name"


class TestCoreHandleManager:
    """Testing class for :class:`core.models.HandleManager` class."""

    # # from_address_and_full_handle
    @pytest.mark.django_db
    def test_core_handlemanager_from_address_and_full_handle_for_existing_contributor(
        self, mocker
    ):
        prefix, username = "h@", "username1"
        address, full_handle = "handlemanager1address", f"{prefix}{username}"
        contributor = Contributor.objects.create(name=full_handle, address=address)
        provider = SocialProvider.objects.create(
            name="handlemanagerprovider1", prefix=prefix
        )
        mocked_save = mocker.patch("core.models.Contributor.save")
        returned = Handle.objects.from_address_and_full_handle(address, full_handle)
        assert isinstance(returned, Handle)
        assert returned.contributor == contributor
        assert returned.provider == provider
        assert returned.handle == username
        mocked_save.assert_not_called()

    @pytest.mark.django_db
    def test_core_handlemanager_from_address_and_full_handle_creates_contributor(self):
        prefix, username = "h@", "username2"
        address, full_handle = "handlemanager2address", f"{prefix}{username}"
        provider = SocialProvider.objects.create(
            name="handlemanagerprovider1", prefix=prefix
        )
        assert Contributor.objects.count() == 0
        returned = Handle.objects.from_address_and_full_handle(address, full_handle)
        contributor = Contributor.objects.get(address=address)
        assert isinstance(returned, Handle)
        assert returned.contributor == contributor
        assert returned.provider == provider
        assert returned.handle == username

    @pytest.mark.django_db
    def test_core_handlemanager_from_address_and_full_handle_raises_error_for_no_provider(
        self,
    ):
        prefix, username = "h@", "username3"
        address, full_handle = "handlemanager3address", f"{prefix}{username}"
        Contributor.objects.create(name=full_handle, address=address)
        with pytest.raises(Http404):
            Handle.objects.from_address_and_full_handle(address, full_handle)


class TestCoreHandleModel:
    """Testing class for :class:`core.models.Handle` model."""

    # # field characteristics
    @pytest.mark.parametrize(
        "name,typ",
        [
            ("contributor", models.ForeignKey),
            ("provider", models.ForeignKey),
            ("handle", models.CharField),
            ("created_at", models.DateTimeField),
            ("updated_at", models.DateTimeField),
        ],
    )
    def test_core_handle_model_fields(self, name, typ):
        assert hasattr(Handle, name)
        assert isinstance(Handle._meta.get_field(name), typ)

    @pytest.mark.django_db
    def test_core_handle_model_handle_is_not_optional(self):
        contributor = Contributor.objects.create(
            name="myhandlecontr8", address="addressfoocontrl2"
        )
        provider = SocialProvider.objects.create(name="Provider58", prefix="ah")
        with pytest.raises(ValidationError):
            Handle(contributor=contributor, provider=provider).full_clean()

    @pytest.mark.django_db
    def test_core_handle_model_cannot_save_too_long_name(self):
        contributor = Contributor.objects.create(
            name="myhandlecontr9", address="addressfoocontrl3"
        )
        provider = SocialProvider.objects.create(name="Provider47", prefix="a3")
        handle = Handle(handle="a" * 100, contributor=contributor, provider=provider)
        with pytest.raises(DataError):
            handle.save()
            handle.full_clean()

    @pytest.mark.django_db
    def test_core_handle_model_is_related_to_contributor(self):
        contributor = Contributor.objects.create(
            name="myhandlecontr", address="addressfoocontrl"
        )
        provider = SocialProvider.objects.create(name="Provider1", prefix="55")
        handle = Handle(provider=provider, handle="handle1")
        handle.contributor = contributor
        handle.save()
        assert handle in contributor.handle_set.all()

    @pytest.mark.django_db
    def test_core_handle_model_is_related_to_provider(self):
        contributor = Contributor.objects.create(
            name="myhandleprov", address="addressfooprov"
        )
        provider = SocialProvider.objects.create(name="Provider2", prefix="56")
        handle = Handle(contributor=contributor, handle="handle2")
        handle.provider = provider
        handle.save()
        assert handle in provider.handle_set.all()

    def test_core_handle_objects_is_handlemanager_instance(self):
        assert isinstance(Handle.objects, HandleManager)

    # # Meta
    @pytest.mark.django_db
    def test_core_handle_model_ordering(self):
        contributor1 = Contributor.objects.create(
            name="myhandlecontr78a", address="addressfoocontr3"
        )
        provider1 = SocialProvider.objects.create(name="Provider3", prefix="57")
        contributor2 = Contributor.objects.create(
            name="myhandlecontr582", address="addressfoocontr4"
        )
        provider2 = SocialProvider.objects.create(name="Provider4", prefix="-7")
        handle1 = Handle.objects.create(
            handle="Abcde", contributor=contributor1, provider=provider1
        )
        handle2 = Handle.objects.create(
            handle="aabcde", contributor=contributor2, provider=provider2
        )
        handle3 = Handle.objects.create(
            handle="bcde", contributor=contributor1, provider=provider2
        )
        handle4 = Handle.objects.create(
            handle="Bcde", contributor=contributor2, provider=provider1
        )
        assert list(Handle.objects.all()) == [
            handle2,
            handle1,
            handle3,
            handle4,
        ]

    # # save
    @pytest.mark.django_db
    def test_core_handle_model_save_duplicate_provider_handle_is_invalid(self):
        contributor = Contributor.objects.create(
            name="myhandleprov", address="addressfooprov"
        )
        contributor1 = Contributor.objects.create(
            name="myhandleprov1", address="addressfooprov1"
        )
        provider = SocialProvider.objects.create(name="Provider2", prefix="56")
        Handle.objects.create(
            handle="namehandle", contributor=contributor, provider=provider
        )
        with pytest.raises(IntegrityError):
            handle = Handle(
                handle="namehandle", contributor=contributor1, provider=provider
            )
            handle.save()

    @pytest.mark.django_db
    def test_core_handle_model_save_duplicate_handle_other_provider_is_valid(self):
        contributor = Contributor.objects.create(
            name="myhandleprov", address="addressfooprov"
        )
        contributor1 = Contributor.objects.create(
            name="myhandleprov1", address="addressfooprov1"
        )
        provider = SocialProvider.objects.create(name="Provider5", prefix="56")
        provider1 = SocialProvider.objects.create(name="Provider6", prefix="2")
        Handle.objects.create(
            handle="namehandle2", contributor=contributor, provider=provider
        )
        handle = Handle(
            handle="namehandle2", contributor=contributor1, provider=provider1
        )
        handle.save()

    # # __str__
    @pytest.mark.django_db
    def test_core_handle_model_string_representation_is_handle_name(self):
        contributor = Contributor.objects.create(
            name="myhandlestr1", address="addressfoostr1"
        )
        provider = SocialProvider.objects.create(name="Provider8", prefix="9")
        handle = Handle(
            handle="handle name", contributor=contributor, provider=provider
        )
        assert str(handle) == "handle name@Provider8"


class TestCoreCycleModel:
    """Testing class for :class:`core.models.Cycle` model."""

    # # field characteristics
    @pytest.mark.parametrize(
        "name,typ",
        [
            ("start", models.DateField),
            ("end", models.DateField),
            ("created_at", models.DateTimeField),
            ("updated_at", models.DateTimeField),
        ],
    )
    def test_core_cycle_model_fields(self, name, typ):
        assert hasattr(Cycle, name)
        assert isinstance(Cycle._meta.get_field(name), typ)

    @pytest.mark.django_db
    def test_core_cycle_model_start_is_not_optional(self):
        with pytest.raises(ValidationError):
            Cycle().full_clean()

    @pytest.mark.django_db
    def test_core_cycle_model_created_at_datetime_field_set(self):
        cycle = Cycle.objects.create(start=datetime(2025, 3, 22))
        assert cycle.created_at <= timezone.now()

    @pytest.mark.django_db
    def test_core_cycle_model_updated_at_datetime_field_set(self):
        cycle = Cycle.objects.create(start=datetime(2025, 3, 22))
        assert cycle.updated_at <= timezone.now()

    # # Meta
    @pytest.mark.django_db
    def test_core_cycle_model_ordering(self):
        cycle1 = Cycle.objects.create(start=datetime(2025, 3, 25))
        cycle2 = Cycle.objects.create(start=datetime(2025, 3, 22))
        cycle3 = Cycle.objects.create(start=datetime(2024, 4, 22))
        assert list(Cycle.objects.all()) == [cycle3, cycle2, cycle1]

    # # __str__
    @pytest.mark.django_db
    def test_core_cycle_model_string_representation_for_end(self):
        cycle = Cycle.objects.create(
            start=datetime(2025, 3, 25), end=datetime(2025, 4, 25)
        )
        assert str(cycle) == "25-03-25 - 25-04-25"

    @pytest.mark.django_db
    def test_core_cycle_model_string_representation_without_end(self):
        cycle = Cycle.objects.create(start=datetime(2025, 3, 25))
        assert str(cycle) == ""


class TestCoreContributionModel:
    """Testing class for :class:`core.models.Contribution` model."""

    # # field characteristics
    @pytest.mark.parametrize(
        "name,typ",
        [
            ("contributor", models.ForeignKey),
            ("cycle", models.ForeignKey),
            ("platform", models.CharField),
            ("url", models.CharField),
            ("type", models.CharField),
            ("level", models.IntegerField),
            ("percentage", models.DecimalField),
            ("reward", models.DecimalField),
            ("comment", models.CharField),
            ("confirmed", models.BooleanField),
            ("created_at", models.DateTimeField),
            ("updated_at", models.DateTimeField),
        ],
    )
    def test_core_contribution_model_fields(self, name, typ):
        assert hasattr(Contribution, name)
        assert isinstance(Contribution._meta.get_field(name), typ)

    @pytest.mark.django_db
    def test_core_contribution_model_is_related_to_contributor(self):
        contributor = Contributor.objects.create(
            name="mynamecontr", address="addressfoocontr"
        )
        cycle = Cycle.objects.create(start=datetime(2025, 3, 22))
        contribution = Contribution(cycle=cycle)
        contribution.contributor = contributor
        contribution.save()
        assert contribution in contributor.contribution_set.all()

    @pytest.mark.django_db
    def test_core_contribution_model_is_related_to_cycle(self):
        contributor = Contributor.objects.create(
            name="mynamecycle", address="addresscycle"
        )
        cycle = Cycle.objects.create(start=datetime(2025, 3, 22))
        contribution = Contribution(contributor=contributor)
        contribution.cycle = cycle
        contribution.save()
        assert contribution in cycle.contribution_set.all()

    @pytest.mark.django_db
    def test_core_contribution_model_cannot_save_too_long_platform(self):
        contributor = Contributor.objects.create()
        contribution = Contribution(contributor=contributor, platform="*" * 100)
        with pytest.raises(DataError):
            contribution.save()
            contribution.full_clean()

    @pytest.mark.django_db
    def test_core_contribution_model_cannot_save_too_long_url(self):
        contributor = Contributor.objects.create()
        contribution = Contribution(contributor=contributor, url="xyz" * 200)
        with pytest.raises(DataError):
            contribution.save()
            contribution.full_clean()

    @pytest.mark.django_db
    def test_core_contribution_model_cannot_save_too_long_type(self):
        contributor = Contributor.objects.create()
        contribution = Contribution(contributor=contributor, type="a" * 50)
        with pytest.raises(DataError):
            contribution.save()
            contribution.full_clean()

    @pytest.mark.django_db
    def test_core_contribution_model_cannot_save_too_big_percentage(self):
        contributor = Contributor.objects.create()
        contribution = Contribution(contributor=contributor, percentage=10e6)
        with pytest.raises(DataError):
            contribution.save()
            contribution.full_clean()

    @pytest.mark.django_db
    def test_core_contribution_model_cannot_save_too_big_reward(self):
        contributor = Contributor.objects.create()
        contribution = Contribution(contributor=contributor, percentage=10e12)
        with pytest.raises(DataError):
            contribution.save()
            contribution.full_clean()

    @pytest.mark.django_db
    def test_core_contribution_model_cannot_save_too_long_comment(self):
        contributor = Contributor.objects.create()
        contribution = Contribution(contributor=contributor, comment="abc" * 100)
        with pytest.raises(DataError):
            contribution.save()
            contribution.full_clean()

    @pytest.mark.django_db
    def test_core_contribution_model_created_at_datetime_field_set(self):
        contributor = Contributor.objects.create(
            name="mynamecreated", address="addressfoocreated"
        )
        cycle = Cycle.objects.create(start=datetime(2025, 3, 22))
        contribution = Contribution.objects.create(
            contributor=contributor, cycle=cycle, platform="platform"
        )
        assert contribution.created_at <= timezone.now()

    @pytest.mark.django_db
    def test_core_contribution_model_updated_at_datetime_field_set(self):
        contributor = Contributor.objects.create(
            name="mynameupd", address="addressfooupd"
        )
        cycle = Cycle.objects.create(start=datetime(2025, 3, 22))
        contribution = Contribution.objects.create(
            contributor=contributor, cycle=cycle, platform="platform"
        )
        assert contribution.updated_at <= timezone.now()

    # # Meta
    @pytest.mark.django_db
    def test_core_contribution_model_contributions_ordering(self):
        cycle1 = Cycle.objects.create(start=datetime(2025, 3, 22))
        cycle2 = Cycle.objects.create(start=datetime(2025, 4, 20))
        cycle3 = Cycle.objects.create(start=datetime(2025, 5, 20))
        contributor1 = Contributor.objects.create(name="myname", address="addressfoo")
        contributor2 = Contributor.objects.create(name="myname2", address="addressfoo2")
        contribution1 = Contribution.objects.create(
            contributor=contributor1, cycle=cycle1
        )
        contribution2 = Contribution.objects.create(
            contributor=contributor2, cycle=cycle2
        )
        contribution3 = Contribution.objects.create(
            contributor=contributor2, cycle=cycle1
        )
        contribution4 = Contribution.objects.create(
            contributor=contributor1, cycle=cycle3
        )
        contribution5 = Contribution.objects.create(
            contributor=contributor1, cycle=cycle2
        )
        assert list(Contribution.objects.all()) == [
            contribution1,
            contribution3,
            contribution2,
            contribution5,
            contribution4,
        ]

    # #  __str__
    @pytest.mark.django_db
    def test_core_contribution_model_string_representation(self):
        contributor = Contributor.objects.create(name="MyName")
        cycle = Cycle.objects.create(start=datetime(2025, 3, 22))
        contribution = Contribution.objects.create(
            contributor=contributor, cycle=cycle, platform="platform2"
        )
        assert "/".join(str(contribution).split("/")[:2]) == "MyName/platform2"


class TestCoreRewardModel:
    """Testing class for :class:`core.models.Reward` model."""

    # # field characteristics
    @pytest.mark.parametrize(
        "name,typ",
        [
            ("type", models.CharField),
            ("level", models.IntegerField),
            ("reward", models.DecimalField),
            ("description", models.CharField),
            ("general_description", models.TextField),
            ("created_at", models.DateTimeField),
            ("updated_at", models.DateTimeField),
        ],
    )
    def test_core_reward_model_fields(self, name, typ):
        assert hasattr(Reward, name)
        assert isinstance(Reward._meta.get_field(name), typ)

    def test_core_reward_model_default_level(self):
        reward = Reward()
        assert reward.level == 1

    @pytest.mark.django_db
    def test_core_contribution_model_cannot_save_too_long_type(self):
        reward = Reward(type="*" * 50)
        with pytest.raises(DataError):
            reward.save()
            reward.full_clean()

    @pytest.mark.django_db
    def test_core_contribution_model_cannot_save_too_big_reward(self):
        reward = Reward(reward=10e12)
        with pytest.raises(DataError):
            reward.save()
            reward.full_clean()

    @pytest.mark.django_db
    def test_core_contribution_model_cannot_save_too_long_description(self):
        reward = Reward(reward="*" * 500)
        with pytest.raises(ValidationError):
            reward.save()
            reward.full_clean()

    @pytest.mark.django_db
    def test_core_reward_model_created_at_datetime_field_set(self):
        reward = Reward.objects.create()
        assert reward.created_at <= timezone.now()

    @pytest.mark.django_db
    def test_core_reward_model_updated_at_datetime_field_set(self):
        reward = Reward.objects.create()
        assert reward.updated_at <= timezone.now()

    # # Meta
    @pytest.mark.django_db
    def test_core_reward_model_ordering(self):
        reward1 = Reward.objects.create(type="type2", level=2)
        reward2 = Reward.objects.create(type="type1", level=2)
        reward3 = Reward.objects.create(type="type2", level=1)
        assert list(Reward.objects.all()) == [reward2, reward3, reward1]

    # save
    @pytest.mark.django_db
    def test_core_reward_model_model_save_duplicate_type_and_level_combination(self):
        Reward.objects.create(type="type1", level=2)
        with pytest.raises(IntegrityError):
            contributor = Reward(type="type1", level=2)
            contributor.save()

    # # __str__
    @pytest.mark.django_db
    def test_core_reward_model_string_representation(self):
        reward = Reward.objects.create(type="type2", level=1)
        assert str(reward) == "type2 1"
