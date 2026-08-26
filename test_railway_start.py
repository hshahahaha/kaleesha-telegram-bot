import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import kaleesha_bot_railway as bot


class StartConfigurationTests(unittest.IsolatedAsyncioTestCase):
    def test_start_image_is_packaged(self):
        self.assertTrue(bot.START_IMAGE_PATH.is_file())

    async def test_start_sends_image_with_the_requested_instruction(self):
        message = SimpleNamespace(reply_photo=AsyncMock())
        update = SimpleNamespace(
            effective_user=SimpleNamespace(id=42, first_name="اختبار", username="test"),
            message=message,
        )
        context = SimpleNamespace(bot=SimpleNamespace())
        with patch.object(bot, "register_user", return_value=False), patch.object(bot, "has_follow_proof", return_value=True):
            await bot.start(update, context)
        message.reply_photo.assert_awaited_once()
        kwargs = message.reply_photo.await_args.kwargs
        self.assertEqual(kwargs["caption"], "اضغط على الزر الموجود على اليسار كما في الصورة.")
        self.assertNotIn("reply_markup", kwargs)

    async def test_follow_proof_is_forwarded_to_admin_and_saved(self):
        message = SimpleNamespace(chat_id=55, message_id=77, reply_text=AsyncMock())
        user = SimpleNamespace(id=42, first_name="اختبار", full_name="مستخدم اختبار", username="test")
        update = SimpleNamespace(effective_user=user, effective_message=message)
        context = SimpleNamespace(bot=SimpleNamespace(copy_message=AsyncMock(), send_message=AsyncMock()))
        with patch.object(bot, "register_user"), patch.object(bot, "has_follow_proof", return_value=False), patch.object(bot, "save_follow_proof") as saved:
            await bot.follow_proof(update, context)
        context.bot.copy_message.assert_awaited_once_with(chat_id=bot.ADMIN_ID, from_chat_id=55, message_id=77)
        saved.assert_called_once_with(42)
        message.reply_text.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
