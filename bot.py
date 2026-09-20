

        try:
            data=json.loads(file.read_text()); uid=int(file.stem); destinations.update(data.get("destinations", []))
            if mode in {"all", "users"}:
                await bot.copy_message(uid,message.chat.id,message.message_id); sent+=1
        except Exception: pass
    if mode in {"all", "channels"}:
        for target in destinations:
            try:
                chat = int(target) if str(target).startswith("-100") else target
                resolved = (await bot.get_chat(chat_id=chat)).id
                member = await bot.get_chat_member(resolved, (await bot.get_me()).id)
                if member.status in {"administrator", "creator"}:
                    await bot.copy_message(resolved, message.chat.id, message.message_id); channel_sent += 1
            except Exception: pass
    await state.clear(); await message.answer(deco(f"Broadcast complete. Mode: {mode}\nDM sent: {sent}\nChannel/group sent: {channel_sent}"),reply_markup=main_kb(True))


@router.callback_query(F.data == "posts")
async def posts(call: CallbackQuery):
    user=await store.load_user(call.from_user.id); total=len(user.get("posts",[])); await edit_ui(call.message, deco(f"<b>MY POSTS</b>\n\nSaved posts: {total}"), main_kb(call.from_user.id in OWNER_IDS))
@router.callback_query(F.data == "extract")
async def extract(call: CallbackQuery): await edit_ui(call.message, deco("<b>EMOJI EXTRACTOR</b>\n\nPremium emoji wale message ko forward karein ya custom emoji entity wala text bhejein. IDs ko owner panel se pool mein add kiya ja sakta hai."), main_kb(call.from_user.id in OWNER_IDS))
@router.callback_query(F.data == "help")
async def help_(call: CallbackQuery): await edit_ui(call.message, deco("<b>HELP</b>\n\nMake Post → media → button → design → preview → publish. Private channels/groups mein bot ko pehle admin karein."), main_kb(call.from_user.id in OWNER_IDS))
@router.callback_query(F.data == "back")
async def back(call: CallbackQuery):
    await call.answer()
    await edit_ui(call.message, deco(BRAND), main_kb(call.from_user.id in OWNER_IDS))
@router.callback_query(F.data == "noop")
async def noop(call: CallbackQuery): await call.answer()


async def main() -> None:
    if TOKEN == "PUT_BOT_TOKEN_HERE": raise RuntimeError("Set BOT_TOKEN in config.py")
    await store.initialize()
    persisted = await store.load_meta()
    OWNER_IDS.update(int(x) for x in persisted.get("owner_ids", []))
    bot=Bot(TOKEN,default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    global VALID_CUSTOM_EMOJI_IDS, CUSTOM_EMOJI_FALLBACKS
    try:
        for start in range(0, len(store.emoji_ids), 50):
            chunk = store.emoji_ids[start:start + 50]
            try:
                stickers = await bot.get_custom_emoji_stickers(custom_emoji_ids=chunk)
                for sticker in stickers:
                    if sticker.custom_emoji_id:
                        emoji_id = str(sticker.custom_emoji_id)
                        VALID_CUSTOM_EMOJI_IDS.add(emoji_id)
                        if sticker.emoji:
                            CUSTOM_EMOJI_FALLBACKS[emoji_id] = sticker.emoji
            except Exception:
                # An invalid ID can reject a whole request; isolate it without
                # preventing the remaining valid premium IDs from working.
                for emoji_id in chunk:
                    try:
                        stickers = await bot.get_custom_emoji_stickers(custom_emoji_ids=[emoji_id])
                        for sticker in stickers:
                            if sticker.custom_emoji_id:
                                emoji_id = str(sticker.custom_emoji_id)
                                VALID_CUSTOM_EMOJI_IDS.add(emoji_id)
                                if sticker.emoji:
                                    CUSTOM_EMOJI_FALLBACKS[emoji_id] = sticker.emoji
                    except Exception:
                        continue
    except Exception:
        VALID_CUSTOM_EMOJI_IDS = set()
    dp=Dispatcher(); dp.include_router(router)
    # Telegram rejects getUpdates while an old webhook is still active.
    # Remove stale deployment webhooks before switching to long polling and
    # preserve queued updates so a restart does not silently lose messages.
    await bot.delete_webhook(drop_pending_updates=False)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__": asyncio.run(main())
