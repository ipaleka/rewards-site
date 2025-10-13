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
    RewardType,
    SocialPlatform,
    _parse_full_handle,
)
from utils.constants.core import HANDLE_EXCEPTIONS


class TestCoreModelsHelpers:
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
    def test_core_contributormanager_from_full_handle_returns_from_handle(self, mocker):
        prefix, username = "d@", "usernamed2"
        address, full_handle = (
            "contributormanageraddressfromhandle",
            f"{prefix}{username}",
        )
        contributor = mocker.MagicMock()
        mocked_handle = mocker.patch(
            "core.models.ContributorManager.from_handle", return_value=contributor
        )
        mocked_get = mocker.patch("core.models.get_object_or_404")
        returned = Contributor.objects.from_full_handle(full_handle, address)
        assert returned == contributor
        mocked_handle.assert_called_once_with(username)
        mocked_get.assert_not_called()

    @pytest.mark.django_db
    def test_core_contributormanager_from_full_handle_raises_error_for_no_platform(
        self, mocker
    ):
        mocker.patch("core.models.ContributorManager.from_handle", return_value=None)
        prefix, username = "h@", "username1"
        address, full_handle = "contributormanager1address", f"{prefix}{username}"
        with pytest.raises(Http404):
            Contributor.objects.from_full_handle(full_handle, address)

    @pytest.mark.django_db
    def test_core_contributormanager_from_full_handle_for_existing_handle(self, mocker):
        mocker.patch("core.models.ContributorManager.from_handle", return_value=None)
        prefix, username = "c@", "username2"
        address, full_handle = "contributormanager2address", f"{prefix}{username}"
        contributor = Contributor.objects.create(name=full_handle, address=address)
        platform = SocialPlatform.objects.create(
            name="contributormanagerplatform2", prefix=prefix
        )
        Handle.objects.create(
            contributor=contributor, platform=platform, handle=username
        )
        mocked_save = mocker.patch("core.models.Contributor.save")
        returned = Contributor.objects.from_full_handle(full_handle, address)
        assert returned == contributor
        mocked_save.assert_not_called()

    @pytest.mark.django_db
    def test_core_contributormanager_from_full_handle_creates_handle(self, mocker):
        mocker.patch("core.models.ContributorManager.from_handle", return_value=None)
        prefix, username = "h@", "username3"
        address, full_handle = "contributormanager3address", f"{prefix}{username}"
        SocialPlatform.objects.create(name="contributormanagerplatform3", prefix=prefix)
        assert Contributor.objects.count() == 0
        assert Handle.objects.count() == 0
        returned = Contributor.objects.from_full_handle(full_handle, address)
        assert isinstance(returned, Contributor)
        assert returned.name == full_handle
        assert returned.address == address
        assert Contributor.objects.count() == 1
        assert Handle.objects.count() == 1

    @pytest.mark.django_db
    def test_core_contributormanager_from_full_handle_for_no_address_provided(
        self, mocker
    ):
        mocker.patch("core.models.ContributorManager.from_handle", return_value=None)
        prefix, username = "h@", "username4"
        full_handle = f"{prefix}{username}"
        SocialPlatform.objects.create(name="contributormanagerplatform4", prefix=prefix)
        assert Contributor.objects.count() == 0
        assert Handle.objects.count() == 0
        returned = Contributor.objects.from_full_handle(full_handle)
        assert isinstance(returned, Contributor)
        assert returned.name == full_handle
        assert returned.address is None
        assert Contributor.objects.count() == 1
        assert Handle.objects.count() == 1

    # # from_handle
    @pytest.mark.django_db
    def test_core_contributormanager_from_handle_returns_contributor_from_exact(self):
        handle = "handlefh"
        contributor = Contributor.objects.create(name=f"z@{handle}")
        platform = SocialPlatform.objects.create(name="zplatform", prefix="z@")
        Handle.objects.create(contributor=contributor, platform=platform, handle=handle)
        returned = Contributor.objects.from_handle(handle)
        assert returned == contributor

    @pytest.mark.django_db
    def test_core_contributormanager_from_handle_returns_contributor(self):
        handle = "handlefh"
        contributor = Contributor.objects.create(name=f"z@{handle}")
        platform = SocialPlatform.objects.create(name="zplatform", prefix="z@")
        Handle.objects.create(
            contributor=contributor, platform=platform, handle=f"some{handle}"
        )
        returned = Contributor.objects.from_handle(handle)
        assert returned == contributor

    @pytest.mark.django_db
    def test_core_contributormanager_from_handle_for_no_contributor_found(self):
        handle = "handle"
        contributor1 = Contributor.objects.create(name="w@foobar")
        contributor2 = Contributor.objects.create(name="w@bar")
        platform = SocialPlatform.objects.create(name="wplatform", prefix="w@")
        Handle.objects.create(
            contributor=contributor1, platform=platform, handle="foobar"
        )
        Handle.objects.create(contributor=contributor2, platform=platform, handle="bar")
        returned = Contributor.objects.from_handle(handle)
        assert returned is None

    @pytest.mark.django_db
    def test_core_contributormanager_from_handle_for_exceptions(self):
        handle = HANDLE_EXCEPTIONS[0]
        contributor1 = Contributor.objects.create(name="n1{handle}")
        contributor2 = Contributor.objects.create(name="n2{handle}")
        platform1 = SocialPlatform.objects.create(name="n1platform", prefix="n1")
        platform2 = SocialPlatform.objects.create(name="n2platform", prefix="n2")
        Handle.objects.create(
            contributor=contributor1, platform=platform1, handle=handle
        )
        Handle.objects.create(
            contributor=contributor2, platform=platform2, handle=handle
        )
        returned = Contributor.objects.from_handle(handle)
        assert returned is None

    @pytest.mark.django_db
    def test_core_contributormanager_from_handle_raises_for_multiple_contributors(self):
        handle = "handlemulti"
        contributor1 = Contributor.objects.create(name=f"u@{handle}")
        contributor2 = Contributor.objects.create(name=f"y@{handle}")
        platform1 = SocialPlatform.objects.create(name="uplatform", prefix="u@")
        platform2 = SocialPlatform.objects.create(name="yplatform", prefix="y@")
        Handle.objects.create(
            contributor=contributor1, platform=platform1, handle=handle
        )
        Handle.objects.create(
            contributor=contributor2, platform=platform2, handle=handle
        )
        with pytest.raises(AssertionError) as exception:
            Contributor.objects.from_handle(handle)
            assert "Can't locate a single contributor" in str(exception.value)


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
        contributor = Contributor(name="@user name")
        assert str(contributor) == "user name"

    # # get_absolute_url
    @pytest.mark.django_db
    def test_core_contributor_model_get_absolute_url(self):
        contributor = Contributor.objects.create(name="contributorurl")
        assert contributor.get_absolute_url() == "/contributor/{}".format(
            contributor.id
        )

    # # total_rewards
    @pytest.mark.django_db
    def test_core_contributor_model_total_rewards(self):
        amount1, amount2, amount3 = 50000, 15000, 10000
        contributor = Contributor.objects.create(name="MyNametr")
        contributor2 = Contributor.objects.create(name="OtherNametr")
        cycle1 = Cycle.objects.create(start=datetime(2025, 3, 3))
        cycle2 = Cycle.objects.create(start=datetime(2024, 3, 3))
        platform = SocialPlatform.objects.create(name="platformtr", prefix="tr")
        reward_type = RewardType.objects.create(label="t1", name="t1")
        reward1 = Reward.objects.create(type=reward_type, amount=amount1)
        Contribution.objects.create(
            contributor=contributor, cycle=cycle1, platform=platform, reward=reward1
        )
        reward2 = Reward.objects.create(type=reward_type, amount=amount2)
        Contribution.objects.create(
            contributor=contributor, cycle=cycle1, platform=platform, reward=reward2
        )
        reward3 = Reward.objects.create(type=reward_type, amount=amount3)
        Contribution.objects.create(
            contributor=contributor, cycle=cycle2, platform=platform, reward=reward3
        )
        Contribution.objects.create(
            contributor=contributor2, cycle=cycle2, platform=platform, reward=reward3
        )
        assert contributor.total_rewards == amount1 + amount2 + amount3


class TestCoreSocialPlatformModel:
    """Testing class for :class:`core.models.SocialPlatform` model."""

    # # field characteristics
    @pytest.mark.parametrize(
        "name,typ",
        [
            ("name", models.CharField),
            ("prefix", models.CharField),
        ],
    )
    def test_core_socialplatform_model_fields(self, name, typ):
        assert hasattr(SocialPlatform, name)
        assert isinstance(SocialPlatform._meta.get_field(name), typ)

    @pytest.mark.django_db
    def test_core_socialplatform_model_name_is_not_optional(self):
        with pytest.raises(ValidationError):
            SocialPlatform().full_clean()

    @pytest.mark.django_db
    def test_core_socialplatform_model_cannot_save_too_long_name(self):
        social_platform = SocialPlatform(name="a" * 100)
        with pytest.raises(DataError):
            social_platform.save()
            social_platform.full_clean()

    @pytest.mark.django_db
    def test_core_socialplatform_model_cannot_save_too_long_prefix(self):
        social_platform = SocialPlatform(prefix="abc")
        with pytest.raises(DataError):
            social_platform.save()
            social_platform.full_clean()

    # # Meta
    @pytest.mark.django_db
    def test_core_socialplatform_model_ordering(self):
        social_platform1 = SocialPlatform.objects.create(name="Abcde", prefix="1")
        social_platform2 = SocialPlatform.objects.create(name="aabcde", prefix="5")
        social_platform3 = SocialPlatform.objects.create(name="bcde", prefix="a")
        social_platform4 = SocialPlatform.objects.create(name="Bcde", prefix="c")
        assert list(SocialPlatform.objects.all()) == [
            social_platform2,
            social_platform1,
            social_platform3,
            social_platform4,
        ]

    # # save
    @pytest.mark.django_db
    def test_core_socialplatform_model_save_duplicate_name_is_invalid(self):
        SocialPlatform.objects.create(name="name1", prefix="a")
        with pytest.raises(IntegrityError):
            social_platform = SocialPlatform(name="name1", prefix="b")
            social_platform.save()

    @pytest.mark.django_db
    def test_core_socialplatform_model_save_duplicate_prefix_is_invalid(self):
        SocialPlatform.objects.create(name="name8", prefix="p1")
        with pytest.raises(IntegrityError):
            social_platform = SocialPlatform(name="name9", prefix="p1")
            social_platform.save()

    # # __str__
    @pytest.mark.django_db
    def test_core_socialplatform_model_string_representation_is_social_platform_name(
        self,
    ):
        social_platform = SocialPlatform(name="social name")
        assert str(social_platform) == "social name"


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
        platform = SocialPlatform.objects.create(
            name="handlemanagerplatform1", prefix=prefix
        )
        mocked_save = mocker.patch("core.models.Contributor.save")
        returned = Handle.objects.from_address_and_full_handle(address, full_handle)
        assert isinstance(returned, Handle)
        assert returned.contributor == contributor
        assert returned.platform == platform
        assert returned.handle == username
        mocked_save.assert_not_called()

    @pytest.mark.django_db
    def test_core_handlemanager_from_address_and_full_handle_creates_contributor(self):
        prefix, username = "h@", "username2"
        address, full_handle = "handlemanager2address", f"{prefix}{username}"
        platform = SocialPlatform.objects.create(
            name="handlemanagerplatform1", prefix=prefix
        )
        assert Contributor.objects.count() == 0
        returned = Handle.objects.from_address_and_full_handle(address, full_handle)
        contributor = Contributor.objects.get(address=address)
        assert isinstance(returned, Handle)
        assert returned.contributor == contributor
        assert returned.platform == platform
        assert returned.handle == username

    @pytest.mark.django_db
    def test_core_handlemanager_from_address_and_full_handle_raises_error_for_no_platform(
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
            ("platform", models.ForeignKey),
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
        platform = SocialPlatform.objects.create(name="Provider58", prefix="ah")
        with pytest.raises(ValidationError):
            Handle(contributor=contributor, platform=platform).full_clean()

    @pytest.mark.django_db
    def test_core_handle_model_cannot_save_too_long_name(self):
        contributor = Contributor.objects.create(
            name="myhandlecontr9", address="addressfoocontrl3"
        )
        platform = SocialPlatform.objects.create(name="Provider47", prefix="a3")
        handle = Handle(handle="a" * 100, contributor=contributor, platform=platform)
        with pytest.raises(DataError):
            handle.save()
            handle.full_clean()

    @pytest.mark.django_db
    def test_core_handle_model_is_related_to_contributor(self):
        contributor = Contributor.objects.create(
            name="myhandlecontr", address="addressfoocontrl"
        )
        platform = SocialPlatform.objects.create(name="Provider1", prefix="55")
        handle = Handle(platform=platform, handle="handle1")
        handle.contributor = contributor
        handle.save()
        assert handle in contributor.handle_set.all()

    @pytest.mark.django_db
    def test_core_handle_model_is_related_to_platform(self):
        contributor = Contributor.objects.create(
            name="myhandleprov", address="addressfooprov"
        )
        platform = SocialPlatform.objects.create(name="Provider2", prefix="56")
        handle = Handle(contributor=contributor, handle="handle2")
        handle.platform = platform
        handle.save()
        assert handle in platform.handle_set.all()

    def test_core_handle_objects_is_handlemanager_instance(self):
        assert isinstance(Handle.objects, HandleManager)

    # # Meta
    @pytest.mark.django_db
    def test_core_handle_model_ordering(self):
        contributor1 = Contributor.objects.create(
            name="myhandlecontr78a", address="addressfoocontr3"
        )
        platform1 = SocialPlatform.objects.create(name="Provider3", prefix="57")
        contributor2 = Contributor.objects.create(
            name="myhandlecontr582", address="addressfoocontr4"
        )
        platform2 = SocialPlatform.objects.create(name="Provider4", prefix="-7")
        handle1 = Handle.objects.create(
            handle="Abcde", contributor=contributor1, platform=platform1
        )
        handle2 = Handle.objects.create(
            handle="aabcde", contributor=contributor2, platform=platform2
        )
        handle3 = Handle.objects.create(
            handle="bcde", contributor=contributor1, platform=platform2
        )
        handle4 = Handle.objects.create(
            handle="Bcde", contributor=contributor2, platform=platform1
        )
        assert list(Handle.objects.all()) == [
            handle2,
            handle1,
            handle3,
            handle4,
        ]

    # # save
    @pytest.mark.django_db
    def test_core_handle_model_save_duplicate_platform_handle_is_invalid(self):
        contributor = Contributor.objects.create(
            name="myhandleprov", address="addressfooprov"
        )
        contributor1 = Contributor.objects.create(
            name="myhandleprov1", address="addressfooprov1"
        )
        platform = SocialPlatform.objects.create(name="Provider2", prefix="56")
        Handle.objects.create(
            handle="namehandle", contributor=contributor, platform=platform
        )
        with pytest.raises(IntegrityError):
            handle = Handle(
                handle="namehandle", contributor=contributor1, platform=platform
            )
            handle.save()

    @pytest.mark.django_db
    def test_core_handle_model_save_duplicate_handle_other_platform_is_valid(self):
        contributor = Contributor.objects.create(
            name="myhandleprov", address="addressfooprov"
        )
        contributor1 = Contributor.objects.create(
            name="myhandleprov1", address="addressfooprov1"
        )
        platform = SocialPlatform.objects.create(name="Provider5", prefix="56")
        platform1 = SocialPlatform.objects.create(name="Provider6", prefix="2")
        Handle.objects.create(
            handle="namehandle2", contributor=contributor, platform=platform
        )
        handle = Handle(
            handle="namehandle2", contributor=contributor1, platform=platform1
        )
        handle.save()

    # # __str__
    @pytest.mark.django_db
    def test_core_handle_model_string_representation_is_handle_name(self):
        contributor = Contributor.objects.create(
            name="myhandlestr1", address="addressfoostr1"
        )
        platform = SocialPlatform.objects.create(name="Provider8", prefix="9")
        handle = Handle(
            handle="handle name", contributor=contributor, platform=platform
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

    # # get_absolute_url
    @pytest.mark.django_db
    def test_core_cycle_model_get_absolute_url(self):
        cycle = Cycle.objects.create(start=datetime(2021, 10, 1))
        assert cycle.get_absolute_url() == "/cycle/{}".format(cycle.id)

    # # total_rewards
    @pytest.mark.django_db
    def test_core_cycle_model_total_rewards(self):
        amount1, amount2, amount3 = 250000, 15000, 10000
        contributor = Contributor.objects.create(name="MyNamecytr")
        contributor2 = Contributor.objects.create(name="OtherNametcyr")
        cycle = Cycle.objects.create(start=datetime(2025, 3, 3))
        cycle2 = Cycle.objects.create(start=datetime(2024, 3, 3))
        platform = SocialPlatform.objects.create(name="platformcy", prefix="tc")
        reward_type = RewardType.objects.create(label="c2", name="c2")
        reward1 = Reward.objects.create(type=reward_type, amount=amount1)
        Contribution.objects.create(
            contributor=contributor, cycle=cycle, platform=platform, reward=reward1
        )
        reward2 = Reward.objects.create(type=reward_type, amount=amount2)
        Contribution.objects.create(
            contributor=contributor, cycle=cycle, platform=platform, reward=reward2
        )
        reward3 = Reward.objects.create(type=reward_type, amount=amount3)
        Contribution.objects.create(
            contributor=contributor, cycle=cycle2, platform=platform, reward=reward3
        )
        Contribution.objects.create(
            contributor=contributor2, cycle=cycle2, platform=platform, reward=reward3
        )
        assert cycle.total_rewards == amount1 + amount2


class TestCoreRewardTypeModel:
    """Testing class for :class:`core.models.RewardType` model."""

    # # field characteristics
    @pytest.mark.parametrize(
        "name,typ",
        [
            ("label", models.CharField),
            ("name", models.CharField),
            ("created_at", models.DateTimeField),
            ("updated_at", models.DateTimeField),
        ],
    )
    def test_core_reward_model_fields(self, name, typ):
        assert hasattr(RewardType, name)
        assert isinstance(RewardType._meta.get_field(name), typ)

    @pytest.mark.django_db
    def test_core_reward_type_model_cannot_save_too_long_label(self):
        reward_type = RewardType(label="*" * 10)
        with pytest.raises(DataError):
            reward_type.save()
            reward_type.full_clean()

    @pytest.mark.django_db
    def test_core_reward_type_model_cannot_save_too_long_name(self):
        reward_type = RewardType(name="*" * 100)
        with pytest.raises(DataError):
            reward_type.save()
            reward_type.full_clean()

    @pytest.mark.django_db
    def test_core_reward_type_model_created_at_datetime_field_set(self):
        reward_type = RewardType.objects.create()
        assert reward_type.created_at <= timezone.now()

    @pytest.mark.django_db
    def test_core_reward_type_model_updated_at_datetime_field_set(self):
        reward_type = RewardType.objects.create()
        assert reward_type.updated_at <= timezone.now()

    # # Meta
    @pytest.mark.django_db
    def test_core_reward_type_model_ordering(self):
        reward_type1 = RewardType.objects.create(name="name2", label="n2")
        reward_type2 = RewardType.objects.create(name="name3", label="n3")
        reward_type3 = RewardType.objects.create(name="name1", label="n1")
        assert list(RewardType.objects.all()) == [
            reward_type3,
            reward_type1,
            reward_type2,
        ]

    # save
    @pytest.mark.django_db
    def test_core_reward_type_model_model_save_duplicate_label(self):
        RewardType.objects.create(label="type1", name="nametype1")
        with pytest.raises(IntegrityError):
            reward_type = RewardType(label="type1", name="nametype10")
            reward_type.save()

    @pytest.mark.django_db
    def test_core_reward_type_model_model_save_duplicate_name(self):
        RewardType.objects.create(label="type3", name="nametype4")
        with pytest.raises(IntegrityError):
            reward_type = RewardType(label="type1", name="nametype4")
            reward_type.save()

    # # __str__
    @pytest.mark.django_db
    def test_core_reward_type_model_string_representation(self):
        reward_type = RewardType.objects.create(label="T5", name="rewardtype1")
        assert str(reward_type) == "[T5] rewardtype1"


class TestCoreRewardModel:
    """Testing class for :class:`core.models.Reward` model."""

    # # field characteristics
    @pytest.mark.parametrize(
        "name,typ",
        [
            ("type", models.ForeignKey),
            ("level", models.IntegerField),
            ("amount", models.IntegerField),
            ("description", models.CharField),
            ("general_description", models.TextField),
            ("active", models.BooleanField),
            ("created_at", models.DateTimeField),
            ("updated_at", models.DateTimeField),
        ],
    )
    def test_core_reward_model_fields(self, name, typ):
        assert hasattr(Reward, name)
        assert isinstance(Reward._meta.get_field(name), typ)

    @pytest.mark.django_db
    def test_core_reward_model_is_related_to_rewardtype(self):
        reward_type = RewardType.objects.create(label="LR", name="Test Reward")
        reward = Reward()
        reward.type = reward_type
        reward.save()
        assert reward in reward_type.reward_set.all()

    def test_core_reward_model_default_level(self):
        reward = Reward()
        assert reward.level == 1

    def test_core_reward_model_default_active(self):
        reward = Reward()
        assert reward.active

    @pytest.mark.django_db
    def test_core_reward_model_cannot_save_too_big_amount(self):
        reward_type = RewardType.objects.create(label="RT1", name="Test Reward1")
        reward = Reward(type=reward_type, amount=10e12)
        with pytest.raises(DataError):
            reward.save()
            reward.full_clean()

    @pytest.mark.django_db
    def test_core_reward_model_cannot_save_too_long_description(self):
        reward_type = RewardType.objects.create(label="RT2", name="Test Reward2")
        reward = Reward(type=reward_type, description="*" * 500)
        with pytest.raises(DataError):
            reward.save()
            reward.full_clean()

    @pytest.mark.django_db
    def test_core_reward_model_created_at_datetime_field_set(self):
        reward_type = RewardType.objects.create(label="RT3", name="Test Reward3")
        reward = Reward.objects.create(type=reward_type)
        assert reward.created_at <= timezone.now()

    @pytest.mark.django_db
    def test_core_reward_model_updated_at_datetime_field_set(self):
        reward_type = RewardType.objects.create(label="RT4", name="Test Reward4")
        reward = Reward.objects.create(type=reward_type)
        assert reward.updated_at <= timezone.now()

    # # Meta
    @pytest.mark.django_db
    def test_core_reward_model_ordering(self):
        reward_type1 = RewardType.objects.create(label="T2", name="type2")
        reward_type2 = RewardType.objects.create(label="T1", name="type1")
        reward1 = Reward.objects.create(type=reward_type1, level=2)
        reward2 = Reward.objects.create(type=reward_type2, level=2)
        reward3 = Reward.objects.create(type=reward_type2, level=1)
        assert list(Reward.objects.all()) == [reward3, reward2, reward1]

    # save
    @pytest.mark.django_db
    def test_core_reward_model_model_save_duplicate_type_level_and_amount_combination(
        self,
    ):
        reward_type = RewardType.objects.create(label="a2", name="atype2")
        Reward.objects.create(
            type=reward_type, level=2, amount=50000, description="foo"
        )
        with pytest.raises(IntegrityError):
            contributor = Reward(
                type=reward_type, level=2, amount=50000, description="bar"
            )
            contributor.save()

    # # __str__
    @pytest.mark.django_db
    def test_core_reward_model_string_representation(self):
        reward_type = RewardType.objects.create(label="TS", name="Task")
        reward = Reward.objects.create(type=reward_type, level=1, amount=20000)
        assert str(reward) == "[TS] Task 1: 20,000"


class TestCoreContributionModel:
    """Testing class for :class:`core.models.Contribution` model."""

    # # field characteristics
    @pytest.mark.parametrize(
        "name,typ",
        [
            ("contributor", models.ForeignKey),
            ("cycle", models.ForeignKey),
            ("platform", models.ForeignKey),
            ("reward", models.ForeignKey),
            ("percentage", models.DecimalField),
            ("url", models.CharField),
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
        platform = SocialPlatform.objects.create(
            name="contributioncontributor", prefix="cr"
        )
        reward_type = RewardType.objects.create(label="co", name="rewardco")
        reward = Reward.objects.create(type=reward_type)
        contribution = Contribution(cycle=cycle, platform=platform, reward=reward)
        contribution.contributor = contributor
        contribution.save()
        assert contribution in contributor.contribution_set.all()

    @pytest.mark.django_db
    def test_core_contribution_model_is_related_to_cycle(self):
        contributor = Contributor.objects.create(
            name="mynamecycle", address="addresscycle"
        )
        cycle = Cycle.objects.create(start=datetime(2025, 3, 22))
        platform = SocialPlatform.objects.create(name="contributioncycle", prefix="cy")
        reward_type = RewardType.objects.create(label="L1", name="Name1")
        reward = Reward.objects.create(type=reward_type)
        contribution = Contribution(
            contributor=contributor, platform=platform, reward=reward
        )
        contribution.cycle = cycle
        contribution.save()
        assert contribution in cycle.contribution_set.all()

    @pytest.mark.django_db
    def test_core_contribution_model_is_related_to_socialplatform(self):
        contributor = Contributor.objects.create(
            name="mynamecycle", address="addresscycle"
        )
        cycle = Cycle.objects.create(start=datetime(2025, 1, 1))
        platform = SocialPlatform.objects.create(
            name="contributionplatform", prefix="cf"
        )
        reward_type = RewardType.objects.create(label="s", name="rewards")
        reward = Reward.objects.create(type=reward_type)
        contribution = Contribution(contributor=contributor, cycle=cycle, reward=reward)
        contribution.platform = platform
        contribution.save()
        assert contribution in platform.contribution_set.all()

    @pytest.mark.django_db
    def test_core_contribution_model_is_related_to_reward(self):
        contributor = Contributor.objects.create(
            name="mynamecycle", address="addresscycle"
        )
        cycle = Cycle.objects.create(start=datetime(2025, 1, 1))
        platform = SocialPlatform.objects.create(
            name="contributionplatform", prefix="cf"
        )
        reward_type = RewardType.objects.create(label="r", name="rewardr")
        reward = Reward.objects.create(type=reward_type)
        contribution = Contribution(
            contributor=contributor, cycle=cycle, platform=platform
        )
        contribution.reward = reward
        contribution.save()
        assert contribution in reward.contribution_set.all()

    @pytest.mark.django_db
    def test_core_contribution_model_cannot_save_too_long_url(self):
        contributor = Contributor.objects.create()
        cycle = Cycle.objects.create(start=datetime(2024, 1, 1))
        platform = SocialPlatform.objects.create(
            name="contributionplatform1", prefix="c1"
        )
        reward_type = RewardType.objects.create(label="9", name="reward9")
        reward = Reward.objects.create(type=reward_type)
        contribution = Contribution(
            contributor=contributor,
            cycle=cycle,
            platform=platform,
            reward=reward,
            url="xyz" * 200,
        )
        with pytest.raises(DataError):
            contribution.save()
            contribution.full_clean()

    @pytest.mark.django_db
    def test_core_contribution_model_cannot_save_too_big_percentage(self):
        contributor = Contributor.objects.create()
        cycle = Cycle.objects.create(start=datetime(2023, 1, 1))
        platform = SocialPlatform.objects.create(
            name="contributionplatform2", prefix="c2"
        )
        reward_type = RewardType.objects.create(label="90", name="reward90")
        reward = Reward.objects.create(type=reward_type)
        contribution = Contribution(
            contributor=contributor,
            cycle=cycle,
            platform=platform,
            reward=reward,
            percentage=10e6,
        )
        with pytest.raises(DataError):
            contribution.save()
            contribution.full_clean()

    @pytest.mark.django_db
    def test_core_contribution_model_cannot_save_too_long_comment(self):
        contributor = Contributor.objects.create()
        cycle = Cycle.objects.create(start=datetime(2022, 1, 1))
        platform = SocialPlatform.objects.create(
            name="contributionplatform3", prefix="c3"
        )
        reward_type = RewardType.objects.create(label="80", name="reward80")
        reward = Reward.objects.create(type=reward_type)
        contribution = Contribution(
            contributor=contributor,
            cycle=cycle,
            platform=platform,
            reward=reward,
            comment="abc" * 100,
        )
        with pytest.raises(DataError):
            contribution.save()
            contribution.full_clean()

    @pytest.mark.django_db
    def test_core_contribution_model_created_at_datetime_field_set(self):
        contributor = Contributor.objects.create(
            name="mynamecreated", address="addressfoocreated"
        )
        cycle = Cycle.objects.create(start=datetime(2025, 3, 22))
        platform = SocialPlatform.objects.create(
            name="contributioncreated", prefix="dc"
        )
        reward_type = RewardType.objects.create(label="70", name="reward70")
        reward = Reward.objects.create(type=reward_type)
        contribution = Contribution.objects.create(
            contributor=contributor, cycle=cycle, platform=platform, reward=reward
        )
        assert contribution.created_at <= timezone.now()

    @pytest.mark.django_db
    def test_core_contribution_model_updated_at_datetime_field_set(self):
        contributor = Contributor.objects.create(
            name="mynameupd", address="addressfooupd"
        )
        cycle = Cycle.objects.create(start=datetime(2025, 3, 22))
        platform = SocialPlatform.objects.create(
            name="contributionupdated", prefix="du"
        )
        reward_type = RewardType.objects.create(label="71", name="reward71")
        reward = Reward.objects.create(type=reward_type)
        contribution = Contribution.objects.create(
            contributor=contributor, cycle=cycle, platform=platform, reward=reward
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
        platform = SocialPlatform.objects.create(
            name="contributionorderingplatform", prefix="co"
        )
        reward_type = RewardType.objects.create(label="50", name="reward50")
        reward = Reward.objects.create(type=reward_type)
        contribution1 = Contribution.objects.create(
            contributor=contributor1, cycle=cycle1, platform=platform, reward=reward
        )
        contribution2 = Contribution.objects.create(
            contributor=contributor2, cycle=cycle2, platform=platform, reward=reward
        )
        contribution3 = Contribution.objects.create(
            contributor=contributor2, cycle=cycle1, platform=platform, reward=reward
        )
        contribution4 = Contribution.objects.create(
            contributor=contributor1, cycle=cycle3, platform=platform, reward=reward
        )
        contribution5 = Contribution.objects.create(
            contributor=contributor1, cycle=cycle2, platform=platform, reward=reward
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
        platform = SocialPlatform.objects.create(name="platformstr", prefix="st")
        reward_type = RewardType.objects.create(label="40", name="reward40")
        reward = Reward.objects.create(type=reward_type)
        contribution = Contribution.objects.create(
            contributor=contributor, cycle=cycle, platform=platform, reward=reward
        )
        assert "/".join(str(contribution).split("/")[:2]) == "MyName/platformstr"

    # # get_absolute_url
    @pytest.mark.django_db
    def test_core_contribution_model_get_absolute_url(self):
        contributor = Contributor.objects.create(name="MyName1")
        cycle = Cycle.objects.create(start=datetime(2025, 3, 23))
        platform = SocialPlatform.objects.create(name="platforms1", prefix="s1")
        reward_type = RewardType.objects.create(label="41", name="reward41")
        reward = Reward.objects.create(type=reward_type)
        contribution = Contribution.objects.create(
            contributor=contributor, cycle=cycle, platform=platform, reward=reward
        )
        assert contribution.get_absolute_url() == "/contribution/{}".format(
            contribution.id
        )
