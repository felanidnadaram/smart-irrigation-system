PERSIAN_MESSAGES = {
    "user_not_found": "کاربر یافت نشد",
    "field_not_found": "مزرعه یافت نشد",
    "unauthorized": "شما دسترسی به این بخش ندارید",
    "invalid_token": "توکن نامعتبر است",
    "token_expired": "توکن منقضی شده است",
    "invalid_credentials": "نام کاربری یا رمز عبور اشتباه است",
    "field_created": "مزرعه با موفقیت ایجاد شد",
    "field_updated": "مزرعه با موفقیت بروزرسانی شd",
    "field_deleted": "مزرعه با موفقیت حذف شد",
    "data_generated": "داده جدید با موفقیت تولید شد",
    "user_created": "کاربر با موفقیت ایجاد شد",
    "user_updated": "کاربر با موفقیت بروزرسانی شد",
    "user_deleted": "کاربر با موفقیت حذف شد",
    "decision_resolved": "تصمیم با موفقیت حل شد",
    "thresholds_updated": "آستانه‌ها با موفقیت بروزرسانی شدند",
    "system_started": "سیستم با موفقیت راه‌اندازی شد",
    "no_data": "داده‌ای موجود نیست",
    "insufficient_data": "داده کافی برای پیش‌بینی موجود نیست",
}


def persian_response(message_key: str, **kwargs) -> dict:
    message = PERSIAN_MESSAGES.get(message_key, message_key)
    for k, v in kwargs.items():
        message = message.replace(f"{{{k}}}", str(v))
    return {"message": message}


def persian_error(status_code: int, detail: str) -> dict:
    return {"detail": detail, "status_code": status_code}
