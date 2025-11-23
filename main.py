#!/usr/bin/env python3
import os
import requests
from datetime import datetime
from nicegui import ui, app
import base64

# API Key برای Remove.bg
API_KEY = "m5M3G1DDPcEJTUg1Ciqmuy2Y"


class BackgroundRemover:
    def __init__(self):
        self.uploaded_file = None
        self.file_name = ""
        self.processed_image = None

        # آمار عمومی
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

            # اعتبارسنجی سایز فایل
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
            self.original_img.visible = True

            # به‌روزرسانی اطلاعات فایل
            self.file_info.set_text(f"فایل: {self.file_name} | حجم: {len(self.uploaded_file) // 1024} KB")
            self.file_info.visible = True

            # فعال کردن دکمه پردازش
            self.process_btn.enabled = True
            self.result_area.visible = False

            ui.notify("✅ تصویر با موفقیت آپلود شد!", type='positive')

        except Exception as ex:
            ui.notify(f"❌ خطا در آپلود تصویر: {str(ex)}", type='negative')

    async def remove_background(self):
        """حذف پس‌زمینه"""
        if not self.uploaded_file:
            ui.notify("⚠️ لطفا ابتدا یک تصویر آپلود کنید", type='warning')
            return

        try:
            # نمایش وضعیت پردازش
            self.progress.visible = True
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
                self.processed_img.visible = True

                # نمایش بخش نتیجه
                self.result_area.visible = True

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
            self.progress.visible = False
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

    def download_image(self):
        """دانلود تصویر پردازش شده"""
        if not self.processed_image:
            ui.notify("⚠️ تصویری برای دانلود وجود ندارد", type='warning')
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"no_bg_{timestamp}.png"

            # استفاده از قابلیت دانلود NiceGUI
            ui.download(self.processed_image, filename=filename)

            ui.notify("📥 تصویر آماده دانلود است", type='info')

        except Exception as ex:
            ui.notify(f"❌ خطا در ایجاد لینک دانلود: {str(ex)}", type='negative')

    def update_stats(self):
        """به‌روزرسانی آمار استفاده"""
        stats = app.storage.general['stats']
        self.stats_label.set_text(
            f"تعداد پردازش شده: {stats['processed_count']} | "
            f"آخرین پردازش: {stats['last_processed'] or '---'}"
        )

    def reset_all(self):
        """بازنشانی همه چیز"""
        self.uploaded_file = None
        self.file_name = ""
        self.processed_image = None

        self.original_img.visible = False
        self.processed_img.visible = False
        self.file_info.visible = False
        self.result_area.visible = False
        self.process_btn.enabled = False
        self.status_text.set_text("آماده برای آپلود")

        ui.notify("همه چیز بازنشانی شد", type='info')

    def create_ui(self):
        """ایجاد رابط کاربری"""
        # هدر برنامه
        with ui.header().classes('bg-blue-600 text-white justify-center items-center px-6 py-4'):
            with ui.row().classes('items-center gap-3'):
                ui.icon('brush', size='2.5rem').classes('text-white')
                ui.label('حذف کننده پس‌زمینه تصاویر').classes('text-2xl font-bold text-white')

        # محتوای اصلی
        with ui.column().classes('w-full max-w-4xl mx-auto p-4 gap-4'):
            # کارت آپلود
            with ui.card().classes('w-full'):
                with ui.column().classes('w-full items-center gap-4 p-6'):
                    ui.label('آپلود تصویر').classes('text-xl font-bold')

                    # منطقه آپلود با پارامترهای صحیح
                    upload = ui.upload(
                        on_upload=self.handle_upload,
                        multiple=False
                    ).classes('w-full')
                    upload.props('accept="image/*"')

                    # محتوای منطقه آپلود با المان‌های ساده NiceGUI
                    with upload:
                        with ui.column().classes(
                                'items-center gap-2 p-8 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer'):
                            ui.icon('folder_open', size='xl').classes('text-4xl text-blue-500')
                            ui.label('تصویر خود را اینجا رها کنید یا کلیک کنید').classes('text-lg font-medium')
                            ui.label('فرمت‌های مجاز: JPG, PNG, GIF').classes('text-sm text-gray-500')
                            ui.label('حداکثر حجم: 5MB').classes('text-sm text-gray-500')

                    self.file_info = ui.label().classes('text-sm text-gray-600 mt-2')
                    self.file_info.visible = False

            # بخش وضعیت و آمار
            with ui.row().classes('w-full justify-between items-center'):
                self.stats_label = ui.label().classes('text-sm text-gray-600')
                self.update_stats()

                self.status_text = ui.label('آماده برای آپلود').classes('text-lg font-semibold')
                self.progress = ui.spinner(size='lg')
                self.progress.visible = False

            # بخش تصاویر
            with ui.row().classes('w-full justify-around items-start gap-8 mt-4'):
                # تصویر اصلی
                with ui.column().classes('items-center gap-3'):
                    ui.label('📷 تصویر اصلی').classes('text-lg font-semibold')
                    self.original_img = ui.image().classes(
                        'w-64 h-64 object-contain border-2 border-dashed border-gray-300 rounded-lg')
                    self.original_img.visible = False

                # تصویر پردازش شده
                with ui.column().classes('items-center gap-3'):
                    ui.label('🎯 تصویر پردازش شده').classes('text-lg font-semibold')
                    self.processed_img = ui.image().classes(
                        'w-64 h-64 object-contain border-2 border-dashed border-green-300 rounded-lg')
                    self.processed_img.visible = False

            # دکمه‌های کنترل
            with ui.row().classes('w-full justify-center gap-4 mt-6'):
                self.process_btn = ui.button(
                    'حذف پس‌زمینه',
                    on_click=self.remove_background,
                    icon='auto_fix_high'
                ).classes('bg-green-500 text-white')
                self.process_btn.enabled = False

                ui.button(
                    'پاک کردن همه',
                    on_click=self.reset_all,
                    icon='delete'
                ).classes('bg-red-500 text-white')

            # بخش نتیجه
            with ui.column().classes('w-full items-center gap-4 mt-6') as self.result_area:
                self.result_area.visible = False

                ui.button(
                    'دانلود تصویر پردازش شده',
                    on_click=self.download_image,
                    icon='download'
                ).classes('bg-blue-500 text-white')

        # فوتر
        with ui.footer().classes('bg-gray-100 text-center p-4'):
            ui.label('ساخته شده با NiceGUI | حذف کننده پس‌زمینه تصاویر').classes('text-gray-600')


# صفحه اصلی
@ui.page('/')
def main_page():
    remover = BackgroundRemover()
    remover.create_ui()


if __name__ == "__main__":
    # تنظیم پورت برای Render
    port = int(os.environ.get("PORT", 8080))

    # اجرای برنامه با تنظیمات مناسب
    ui.run(
        host="0.0.0.0",
        port=port,
        title="Background Remover",
        reload=False,
        show=False,
        storage_secret=os.environ.get("STORAGE_SECRET", "DEFAULT_SECRET_KEY_FOR_DEVELOPMENT"),
        favicon="🎨"
    )
