"""Testing module for :py:mod:`bot` module."""

import pytest
import asyncio
import discord
from unittest.mock import AsyncMock, MagicMock, patch, call
import sys
import signal

from bot import RewardsBot, bot, shutdown_bot, handle_signal, main


class TestRewardsBot:
    """Testing class for :py:class:`bot.RewardsBot`."""

    def test_rewards_bot_initialization(self):
        """Test bot initialization with correct parameters."""
        with patch('bot.commands.Bot.__init__') as mock_super_init:
            mock_super_init.return_value = None
            bot_instance = RewardsBot()
            
            mock_super_init.assert_called_once()
            call_args = mock_super_init.call_args
            
            # Verify bot configuration
            assert call_args.kwargs['command_prefix'] == '!'
            assert call_args.kwargs['status'] == discord.Status.online
            assert call_args.kwargs['activity'].type == discord.ActivityType.watching
            assert call_args.kwargs['activity'].name == "reward suggestions"
            
            # Verify bot attributes
            assert hasattr(bot_instance, 'api_service')
            assert bot_instance._shutting_down is False

    @pytest.mark.asyncio
    async def test_rewards_bot_setup_hook_success(self):
        """Test successful setup_hook execution."""
        bot_instance = RewardsBot()
        
        with patch.object(bot_instance, '_validate_config', new_callable=AsyncMock) as mock_validate, \
             patch.object(bot_instance, '_setup_commands', new_callable=AsyncMock) as mock_setup_commands, \
             patch.object(bot_instance, '_initialize_services', new_callable=AsyncMock) as mock_init_services:
            
            await bot_instance.setup_hook()
            
            mock_validate.assert_awaited_once()
            mock_setup_commands.assert_awaited_once()
            mock_init_services.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rewards_bot_setup_hook_config_validation_failure(self):
        """Test setup_hook when config validation fails."""
        bot_instance = RewardsBot()
        
        with patch.object(bot_instance, '_validate_config', new_callable=AsyncMock) as mock_validate:
            mock_validate.side_effect = ValueError("Invalid config")
            
            with pytest.raises(ValueError, match="Invalid config"):
                await bot_instance.setup_hook()

    @pytest.mark.asyncio
    async def test_rewards_bot_validate_config_success(self):
        """Test successful config validation."""
        bot_instance = RewardsBot()
        
        with patch('bot.config') as mock_config:
            mock_config.DISCORD_TOKEN = "test_token"
            mock_config.BASE_URL = "http://test.url"
            
            await bot_instance._validate_config()

    @pytest.mark.asyncio
    async def test_rewards_bot_validate_config_missing_token(self):
        """Test config validation with missing Discord token."""
        bot_instance = RewardsBot()
        
        with patch('bot.config') as mock_config:
            mock_config.DISCORD_TOKEN = None
            
            with pytest.raises(ValueError, match="DISCORD_TOKEN not found"):
                await bot_instance._validate_config()

    @pytest.mark.asyncio
    async def test_rewards_bot_setup_commands_success(self):
        """Test successful command setup and sync."""
        bot_instance = RewardsBot()
        bot_instance.tree = AsyncMock()
        bot_instance.tree.sync.return_value = [
            MagicMock(name='cmd1'), 
            MagicMock(name='cmd2')
        ]
        
        await bot_instance._setup_commands()
        
        bot_instance.tree.sync.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rewards_bot_initialize_services_success(self):
        """Test successful service initialization."""
        bot_instance = RewardsBot()
        bot_instance.api_service.initialize = AsyncMock()
        
        await bot_instance._initialize_services()
        
        bot_instance.api_service.initialize.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rewards_bot_on_ready_success(self):
        """Test on_ready event handler."""
        bot_instance = RewardsBot()
        bot_instance._shutting_down = False
        bot_instance.user = MagicMock()
        bot_instance.user.name = "TestBot"
        bot_instance.user.id = 12345
        bot_instance.guilds = [MagicMock(), MagicMock()]
        
        for i, guild in enumerate(bot_instance.guilds):
            guild.name = f"Guild{i}"
            guild.id = i
            guild.member_count = 100 + i
        
        bot_instance.tree = AsyncMock()
        bot_instance.tree.fetch_commands.return_value = [MagicMock(), MagicMock()]
        
        await bot_instance.on_ready()

    @pytest.mark.asyncio
    async def test_rewards_bot_on_ready_during_shutdown(self):
        """Test on_ready event handler when shutting down."""
        bot_instance = RewardsBot()
        bot_instance._shutting_down = True
        
        # Should return early without doing anything
        await bot_instance.on_ready()

    @pytest.mark.asyncio
    async def test_rewards_bot_close_success(self):
        """Test successful bot shutdown."""
        bot_instance = RewardsBot()
        bot_instance._shutting_down = False
        bot_instance.api_service.close = AsyncMock()
        
        with patch('bot.commands.Bot.close', new_callable=AsyncMock) as mock_super_close:
            await bot_instance.close()
            
            assert bot_instance._shutting_down is True
            bot_instance.api_service.close.assert_awaited_once()
            mock_super_close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rewards_bot_close_already_shutting_down(self):
        """Test bot shutdown when already shutting down."""
        bot_instance = RewardsBot()
        bot_instance._shutting_down = True
        bot_instance.api_service.close = AsyncMock()
        
        await bot_instance.close()
        
        # Should not call any close methods
        bot_instance.api_service.close.assert_not_called()


class TestBotCommands:
    """Testing class for bot command handlers."""

    @pytest.mark.asyncio
    async def test_rewards_cycle_current_command_success(self):
        """Test successful execution of rewards cycle current command."""
        mock_interaction = AsyncMock()
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        
        mock_bot = MagicMock()
        mock_bot.api_service = "api_service"
        mock_interaction.client = mock_bot
        
        with patch('bot.CycleService.current_cycle_info', new_callable=AsyncMock) as mock_service:
            mock_service.return_value = "Cycle info"
            
            from bot import rewards_cycle_current
            await rewards_cycle_current(mock_interaction)
            
            mock_interaction.response.defer.assert_awaited_once_with(thinking=True)
            mock_service.assert_awaited_once_with("api_service")
            mock_interaction.followup.send.assert_awaited_once_with("Cycle info")

    @pytest.mark.asyncio
    async def test_rewards_cycle_current_command_error(self):
        """Test rewards cycle current command with error."""
        mock_interaction = AsyncMock()
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        
        mock_bot = MagicMock()
        mock_bot.api_service = "api_service"
        mock_interaction.client = mock_bot
        
        with patch('bot.CycleService.current_cycle_info', new_callable=AsyncMock) as mock_service:
            mock_service.side_effect = Exception("API error")
            
            from bot import rewards_cycle_current
            await rewards_cycle_current(mock_interaction)
            
            mock_interaction.followup.send.assert_awaited_once_with(
                "❌ Failed to get current cycle info.", ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_rewards_cycle_date_command_success(self):
        """Test successful execution of rewards cycle date command."""
        mock_interaction = AsyncMock()
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        
        mock_bot = MagicMock()
        mock_interaction.client = mock_bot
        
        with patch('bot.CycleService.cycle_end_date', new_callable=AsyncMock) as mock_service:
            mock_service.return_value = "End date info"
            
            from bot import rewards_cycle_date
            await rewards_cycle_date(mock_interaction)
            
            mock_service.assert_awaited_once_with(mock_bot.api_service)
            mock_interaction.followup.send.assert_awaited_once_with("End date info")

    @pytest.mark.asyncio
    async def test_rewards_contributions_tail_command_success(self):
        """Test successful execution of rewards contributions tail command."""
        mock_interaction = AsyncMock()
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        
        mock_bot = MagicMock()
        mock_interaction.client = mock_bot
        
        with patch('bot.CycleService.contributions_tail', new_callable=AsyncMock) as mock_service:
            mock_service.return_value = "Contributions tail"
            
            from bot import rewards_contributions_tail
            await rewards_contributions_tail(mock_interaction)
            
            mock_service.assert_awaited_once_with(mock_bot.api_service)
            mock_interaction.followup.send.assert_awaited_once_with("Contributions tail")

    @pytest.mark.asyncio
    async def test_rewards_cycle_specific_command_success(self):
        """Test successful execution of rewards cycle specific command."""
        mock_interaction = AsyncMock()
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        
        mock_bot = MagicMock()
        mock_interaction.client = mock_bot
        
        with patch('bot.CycleService.cycle_info', new_callable=AsyncMock) as mock_service:
            mock_service.return_value = "Cycle 5 info"
            
            from bot import rewards_cycle_specific
            await rewards_cycle_specific(mock_interaction, number=5)
            
            mock_service.assert_awaited_once_with(mock_bot.api_service, 5)
            mock_interaction.followup.send.assert_awaited_once_with("Cycle 5 info")

    @pytest.mark.asyncio
    async def test_rewards_cycle_specific_command_invalid_number(self):
        """Test rewards cycle specific command with invalid cycle number."""
        mock_interaction = AsyncMock()
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        
        from bot import rewards_cycle_specific
        await rewards_cycle_specific(mock_interaction, number=0)
        
        mock_interaction.followup.send.assert_awaited_once_with(
            "❌ Cycle number must be positive."
        )

    @pytest.mark.asyncio
    async def test_rewards_user_command_success(self):
        """Test successful execution of rewards user command."""
        mock_interaction = AsyncMock()
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        
        mock_bot = MagicMock()
        mock_interaction.client = mock_bot
        
        with patch('bot.UserService.user_summary', new_callable=AsyncMock) as mock_service:
            mock_service.return_value = "User summary"
            
            from bot import rewards_user
            await rewards_user(mock_interaction, username="testuser")
            
            mock_service.assert_awaited_once_with(mock_bot.api_service, "testuser")
            mock_interaction.followup.send.assert_awaited_once_with("User summary")

    @pytest.mark.asyncio
    async def test_rewards_suggest_command_success(self):
        """Test successful execution of rewards suggest command."""
        mock_interaction = AsyncMock()
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        
        from bot import rewards_suggest
        await rewards_suggest(mock_interaction, username="testuser", reason="Great work!")
        
        mock_interaction.followup.send.assert_awaited_once_with(
            "✅ Reward suggestion recorded for testuser: Great work!"
        )


class TestBotEventHandlers:
    """Testing class for bot event handlers."""

    @pytest.mark.asyncio
    async def test_on_app_command_error_cooldown(self):
        """Test app command error handler for cooldown errors."""
        mock_interaction = AsyncMock()
        mock_interaction.command.name = "test_command"
        mock_interaction.user = "test_user"
        mock_interaction.guild = None
        mock_interaction.response.is_done.return_value = False
        mock_interaction.response.send_message = AsyncMock()
        
        error = discord.app_commands.CommandOnCooldown(retry_after=5.0)
        
        from bot import on_app_command_error
        await on_app_command_error(mock_interaction, error)
        
        mock_interaction.response.send_message.assert_awaited_once()
        call_args = mock_interaction.response.send_message.call_args
        assert "cooldown" in call_args[0][0]
        assert "5.0" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_on_app_command_error_missing_permissions(self):
        """Test app command error handler for missing permissions."""
        mock_interaction = AsyncMock()
        mock_interaction.command.name = "test_command"
        mock_interaction.response.is_done.return_value = True
        mock_interaction.followup.send = AsyncMock()
        
        error = discord.app_commands.MissingPermissions(["administrator"])
        
        from bot import on_app_command_error
        await on_app_command_error(mock_interaction, error)
        
        mock_interaction.followup.send.assert_awaited_once_with(
            "❌ You don't have permission to use this command.", ephemeral=True
        )

    @pytest.mark.asyncio
    async def test_on_interaction_application_command(self):
        """Test interaction logging for application commands."""
        mock_interaction = AsyncMock()
        mock_interaction.type = discord.InteractionType.application_command
        mock_interaction.command.name = "test_command"
        mock_interaction.user = "test_user"
        mock_interaction.user.id = 123
        mock_interaction.guild = MagicMock()
        mock_interaction.guild.name = "Test Guild"
        mock_interaction.guild.id = 456
        
        from bot import on_interaction
        await on_interaction(mock_interaction)
        
        # Should log the interaction but not raise errors

    @pytest.mark.asyncio
    async def test_suggest_reward_context_success(self):
        """Test successful context menu execution."""
        mock_interaction = AsyncMock()
        mock_interaction.response.send_modal = AsyncMock()
        
        mock_message = MagicMock()
        mock_message.author.bot = False
        mock_message.author = MagicMock()
        mock_message.author != mock_interaction.user
        mock_message.id = 123
        
        with patch('bot.SuggestRewardModal') as mock_modal_class:
            mock_modal = MagicMock()
            mock_modal_class.return_value = mock_modal
            
            from bot import suggest_reward_context
            await suggest_reward_context(mock_interaction, mock_message)
            
            mock_modal_class.assert_called_once_with(target_message=mock_message)
            mock_interaction.response.send_modal.assert_awaited_once_with(mock_modal)

    @pytest.mark.asyncio
    async def test_suggest_reward_context_bot_message(self):
        """Test context menu with bot message."""
        mock_interaction = AsyncMock()
        mock_interaction.response.send_message = AsyncMock()
        
        mock_message = MagicMock()
        mock_message.author.bot = True
        
        from bot import suggest_reward_context
        await suggest_reward_context(mock_interaction, mock_message)
        
        mock_interaction.response.send_message.assert_awaited_once_with(
            "❌ Cannot suggest rewards for bot messages.", ephemeral=True
        )


class TestBotUtilities:
    """Testing class for bot utility functions."""

    @pytest.mark.asyncio
    async def test_shutdown_bot_success(self):
        """Test successful bot shutdown."""
        mock_bot = AsyncMock()
        
        with patch('bot.bot', mock_bot):
            await shutdown_bot()
            
            mock_bot.close.assert_awaited_once()

    def test_handle_signal(self):
        """Test signal handler function."""
        mock_signal = MagicMock()
        mock_signal.name = "SIGTERM"
        
        with patch('bot.asyncio.create_task') as mock_create_task:
            handle_signal(mock_signal)
            
            mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_success(self):
        """Test successful main execution."""
        with patch('bot.config') as mock_config, \
             patch('bot.RewardsBot') as mock_bot_class, \
             patch('bot.asyncio.get_running_loop') as mock_loop, \
             patch('bot.signal') as mock_signal:
            
            mock_config.DISCORD_TOKEN = "test_token"
            mock_config.BASE_URL = "http://test.url"
            
            mock_bot_instance = AsyncMock()
            mock_bot_class.return_value = mock_bot_instance
            
            mock_loop_instance = MagicMock()
            mock_loop.return_value = mock_loop_instance
            
            # Mock context manager behavior
            mock_bot_instance.__aenter__ = AsyncMock(return_value=mock_bot_instance)
            mock_bot_instance.__aexit__ = AsyncMock(return_value=None)
            mock_bot_instance.start = AsyncMock()
            
            result = await main()
            
            assert result == 0
            mock_bot_instance.start.assert_awaited_once_with("test_token")

    @pytest.mark.asyncio
    async def test_main_login_failure(self):
        """Test main execution with login failure."""
        with patch('bot.config') as mock_config, \
             patch('bot.RewardsBot') as mock_bot_class:
            
            mock_config.DISCORD_TOKEN = "test_token"
            
            mock_bot_instance = AsyncMock()
            mock_bot_class.return_value = mock_bot_instance
            mock_bot_instance.__aenter__ = AsyncMock(return_value=mock_bot_instance)
            mock_bot_instance.__aexit__ = AsyncMock(return_value=None)
            mock_bot_instance.start.side_effect = discord.LoginFailure("Invalid token")
            
            result = await main()
            
            assert result == 1

    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt(self):
        """Test main execution with keyboard interrupt."""
        with patch('bot.config') as mock_config, \
             patch('bot.RewardsBot') as mock_bot_class:
            
            mock_config.DISCORD_TOKEN = "test_token"
            
            mock_bot_instance = AsyncMock()
            mock_bot_class.return_value = mock_bot_instance
            mock_bot_instance.__aenter__ = AsyncMock(return_value=mock_bot_instance)
            mock_bot_instance.__aexit__ = AsyncMock(return_value=None)
            mock_bot_instance.start.side_effect = KeyboardInterrupt()
            
            result = await main()
            
            assert result == 0

    @pytest.mark.asyncio
    async def test_clear_all_commands_success(self):
        """Test successful command clearing."""
        mock_bot = AsyncMock()
        mock_bot.user.id = 12345
        mock_bot.http.bulk_upsert_global_commands = AsyncMock()
        
        from bot import clear_all_commands
        await clear_all_commands(mock_bot)
        
        mock_bot.http.bulk_upsert_global_commands.assert_awaited_once_with(12345, [])