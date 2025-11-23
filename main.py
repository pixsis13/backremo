#!/usr/bin/env python3
import os
import io
import requests
import asyncio
from datetime import datetime
from nicegui import ui, app
import base64
import uuid

# API Key برای Remove.bg
API_KEY = "m5M3G1DDPcEJTUg1Ciqmuy2Y"


class BackgroundRemover:
    def __init__(self):
        self.original_image = None
        self.processed_image = None
        self.uploaded_file = None
        self.file_name = ""

        # آمار استفاده - با استفاده از app.storage عمومی
        if 'stats' not in app.storage.general:
            app.storage.general['stats'] = {
                'processed_count': 0,
                'last_processed': None
            }

    async def handle_upload(self, e):
        """مدیریت آپلود فایل"""
        try:
            self.uploaded_file = e.content.read()
            self.file_name = e.name

            # اعتبارسنجی سایز فایل (5MB)
            if len(self.uploaded_file) > 5 * 1024 * 1024:
                ui.notify("حجم فایل نباید بیشتر از 5 مگابایت باشد", type='negative')
                return

            # اعتبارسنجی فرمت فایل
            valid_formats = ['.jpg', '.jpeg', '.png', '.gif']
            file_ext = os.path.splitext(self.file_name)[1].lower()
            if file_ext not in valid_formats:
                ui.notify("فرمت فایل باید JPG, PNG یا GIF باشد", type='negative')
                return

            # نمایش تصویر آپلود شده
            img_base64 = base64.b64encode(self.uploaded_file).decode()
            self.original_img.set_source(f"data:image/jpeg;base64,{img_base64}")
            self.original_img.set_visibility(True)

            # به‌روزرسانی اطلاعات فایل
            self.file_info.set_text(f"فایل: {self.file_name} | حجم: {len(self.uploaded_file) // 1024} KB")
            self.file_info.set_visibility(True)

            # فعال کردن دکمه پردازش
            self.process_btn.enabled = True
            self.result_area.set_visibility(False)

            ui.notify("✅ تصویر با موفقیت آپلود شد!", type='positive')

        except Exception as ex:
            ui.notify(f"❌ خطا در آپلود تصویر: {str(ex)}", type='negative')

    async def remove_background(self):
        """حذف پس‌زمینه با نمایش پیشرفت"""
        if not self.uploaded_file:
            ui.notify("⚠️ لطفا ابتدا یک تصویر آپلود کنید", type='warning')
            return

        try:
            # نمایش وضعیت پردازش
            self.progress.set_visibility(True)
            self.status_text.set_text("در حال ارسال به سرور...")
            self.process_btn.enabled = False

            # ارسال درخواست به API
            response = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': (self.file_name, self.uploaded_file)},
                data={'size': 'auto', 'format': 'png'},
                headers={'X-Api-Key': API_KEY},
                timeout=45
            )

            if response.status_code == 200:
                self.processed_image = response.content

                # نمایش تصویر پردازش شده
                processed_base64 = base64.b64encode(self.processed_image).decode()
                self.processed_img.set_source(f"data:image/png;base64,{processed_base64}")
                self.processed_img.set_visibility(True)

                # نمایش بخش نتیجه
                self.result_area.set_visibility(True)

                # به‌روزرسانی آمار
                app.storage.general['stats']['processed_count'] += 1
                app.storage.general['stats']['last_processed'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.update_stats()

                self.status_text.set_text("✅ پردازش با موفقیت انجام شد!")
                ui.notify("پس‌زمینه با موفقیت حذف شد!", type='positive')

            else:
                error_msg = self._handle_api_error(response)
                self.status_text.set_text("❌ خطا در پردازش")
                ui.notify(f"خطا در پردازش تصویر: {error_msg}", type='negative')

        except Exception as ex:
            self.status_text.set_text("❌ خطا در پردازش")
            ui.notify(f"خطا: {str(ex)}", type='negative')
        finally:
            self.progress.set_visibility(False)
            self.process_btn.enabled = True

    def _handle_api_error(self, response):
        """مدیریت خطاهای API"""
        error_messages = {
            400: "فایل تصویر معتبر نیست یا بسیار بزرگ است",
            402: "سهمیه API تمام شده است",
            403: "API Key نامعتبر است",
            429: "تعداد درخواست‌ها بیش از حد مجاز است"
        }
        return error_messages.get(response.status_code, f"خطای سرور: {response.status_code}")

    async def download_image(self):
        """دانلود تصویر پردازش شده"""
        if not self.processed_image:
            ui.notify("⚠️ تصویری برای دانلود وجود ندارد", type='warning')
            return

        try:
            # ایجاد فایل برای دانلود
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"no_bg_{timestamp}.png"

            # استفاده از قابلیت دانلود NiceGUI
            ui.download(self.processed_image, filename=filename)

            ui.notify(f"📥 تصویر آماده دانلود است", type='info')

        except Exception as ex:
            ui.notify(f"❌ خطا در ایجاد لینک دانلود: {str(ex)}", type='negative')

    def update_stats(self):
        """به‌روزرسانی آمار استفاده"""
        stats = app.storage.general['stats']
        self.stats_label.set_text(
            f"تعداد پردازش شده: {stats['processed_count']} | "
            f"آخرین پردازش: {stats['last_processed'] or '---'}"
        )

    def create_ui(self):
        """ایجاد رابط کاربری"""
        # هدر برنامه
        with ui.header().classes(
                'bg-gradient-to-r from-blue-600 to-purple-600 text-white justify-center items-center px-6 py-4'):
            with ui.row().classes('items-center gap-3'):
                ui.icon('auto_fix_high', size='2.5rem', color='white')
                ui.label('حذف کننده حرفه ای پس‌زمینه').classes('text-2xl font-bold')

        # محتوای اصلی
        with ui.column().classes('w-full max-w-6xl mx-auto p-6 gap-6'):
            # کارت آپلود
            with ui.card().classes('w-full shadow-xl rounded-2xl'):
                with ui.column().classes('w-full items-center gap-4 p-8'):
                    ui.label('آپلود تصویر').classes('text-2xl font-bold text-gray-800')

                    # منطقه آپلود
                    with ui.upload(
                            label=(
                                    '<div class="text-center">'
                                    '<i class="material-icons text-4xl text-blue-500">cloud_upload</i>'
                                    '<div class="text-lg font-medium mt-2">تصویر خود را اینجا رها کنید یا کلیک کنید</div>'
                                    '<div class="text-sm text-gray-500 mt-1">فرمت‌های مجاز: JPG, PNG, GIF | حداکثر حجم: 5MB</div>'
                                    '</div>'
                            ),
                            on_upload=self.handle_upload,
                            accepted_file_types=['image/*']
                    ).classes(
                        'w-full max-w-lg border-3 border-dashed border-blue-200 rounded-2xl p-8 hover:border-blue-400 transition-all') as upload:
                        upload.props('accept="image/*"')

                    self.file_info = ui.label().classes('text-sm text-gray-600 mt-2')
                    self.file_info.set_visibility(False)

            # بخش وضعیت و آمار
            with ui.row().classes('w-full justify-between items-center'):
                self.stats_label = ui.label().classes('text-sm text-gray-600')
                self.update_stats()

                self.status_text = ui.label('آماده برای آپلود').classes('text-lg font-semibold')
                self.progress = ui.linear_progress().classes('w-64')
                self.progress.set_visibility(False)

            # بخش تصاویر
            with ui.grid(columns=2).classes('w-full gap-8 mt-4'):
                # تصویر اصلی
                with ui.column().classes('items-center gap-3'):
                    ui.label('📷 تصویر اصلی').classes('text-xl font-semibold text-gray-700')
                    self.original_img = ui.image().classes(
                        'w-80 h-80 object-contain border-3 border-dashed border-gray-300 rounded-2xl shadow-lg')
                    self.original_img.set_visibility(False)

                # تصویر پردازش شده
                with ui.column().classes('items-center gap-3'):
                    ui.label('🎯 تصویر پردازش شده').classes('text-xl font-semibold text-gray-700')
                    self.processed_img = ui.image().classes(
                        'w-80 h-80 object-contain border-3 border-dashed border-green-300 rounded-2xl shadow-lg')
                    self.processed_img.set_visibility(False)

            # دکمه‌های کنترل
            with ui.row().classes('w-full justify-center gap-4 mt-6'):
                self.process_btn = ui.button(
                    'حذف پس‌زمینه',
                    on_click=self.remove_background,
                    icon='auto_fix_high'
                ).classes('bg-gradient-to-r from-green-500 to-green-600 text-white px-8 py-3 rounded-full shadow-lg')
                self.process_btn.enabled = False

                ui.button(
                    'پاک کردن همه',
                    on_click=self.reset_all,
                    icon='delete'
                ).classes('bg-red-500 text-white px-6 py-3 rounded-full')

            # بخش نتیجه
            with ui.column().classes('w-full items-center gap-4 mt-6') as self.result_area:
                self.result_area.set_visibility(False)

                ui.button(
                    'دانلود تصویر پردازش شده',
                    on_click=self.download_image,
                    icon='file_download'
                ).classes('bg-gradient-to-r from-blue-500 to-purple-500 text-white px-6 py-3 rounded-full')

        # فوتر
        with ui.footer().classes('bg-gray-100 text-center p-4'):
            ui.label('ساخته شده با NiceGUI | حذف کننده پس‌زمینه تصاویر').classes('text-gray-600')

    async def reset_all(self):
        """بازنشانی همه چیز"""
        self.original_image = None
        self.processed_image = None
        self.uploaded_file = None
        self.file_name = ""

        self.original_img.set_visibility(False)
        self.processed_img.set_visibility(False)
        self.file_info.set_visibility(False)
        self.result_area.set_visibility(False)
        self.process_btn.enabled = False
        self.status_text.set_text("آماده برای آپلود")

        ui.notify("همه چیز بازنشانی شد", type='info')


def main():
    """تابع اصلی"""
    # تنظیمات برنامه
    app.title = "حذف کننده پس‌زمینه تصاویر"

    # ایجاد نمونه برنامه
    remover = BackgroundRemover()
    remover.create_ui()


if __name__ == "__main__":
    # تنظیم پورت برای Render
    port = int(os.environ.get("PORT", 8080))

    # اجرای برنامه با تنظیمات مناسب برای Render
    ui.run(
        host="0.0.0.0",
        port=port,
        title="Background Remover",
        reload=False,
        show=False,
        storage_secret="BACKGROUND_REMOVER_SECRET_KEY_2024"  # کلید مخفی برای ذخیره‌سازی
    )