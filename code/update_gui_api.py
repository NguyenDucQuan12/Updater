import requests
import sys
import psutil
import json
import os
import hashlib
import zipfile
import logging
from pyuac import main_requires_admin
import pyuac
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from packaging import version
import time
import datetime

today = str(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")) #chua ngay thang nam cung voi gio phut giay
date_today = str(datetime.datetime.now().strftime("%d-%m-%y")) # chỉ chứa ngày tháng năm


# Lấy đường dẫn đến thư mục AppData/Roaming của người dùng
appdata_dir = os.getenv('APPDATA')

def resource_path(relative_path):
    """ Trả về đường dẫn đến file tài nguyên khi đóng gói với PyInstaller """
    try:
        # Khi chạy ứng dụng từ file .exe
        base_path = sys._MEIPASS
    except Exception:
        # Khi chạy từ mã nguồn Python
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

json_filename = "data\\config.json"

# Lấy các thông tin ban đầu để khởi tạo cho phần mềm
with open(json_filename, 'r') as inside:
    data = json.load(inside)

    # Cấu hình API
    API_SERVER = data['Update_app']["server"]
    LATEST_VERSION_ENDPOINT = data['Update_app']["api_get_version"]
    MAIN_APP = data['Update_app']["main_app_name"]
    UPDATE_ZIP_NAME = data['Update_app']["update_zip_name"]
    CURRENT_VERSION = data['Update_app']["current_version"]

# Tạo thư mục nhật kí trong Roaming theo ngày tháng năm, nếu thư mục đã tồn tại thì không tạo nữa
save_dir_log = os.path.join(appdata_dir, "SmartParking", "update", date_today)
os.makedirs(save_dir_log, exist_ok=True)

log_file_path = os.path.join(save_dir_log, "log.txt")

def get_real_app_dir():
    """
    Trả về đường dẫn thực sự của ứng dụng, kể cả khi chạy từ thư mục tạm _MEI khi sử dụng PyInstaller.  
    Khi đóng gói ứng dụng bằng PyInstall, sau đó khởi chạy ứng dụng thì nó sẽ tạo một thư mục tạm, thường bắt đầu bằng _MEIxxxx, để khởi chạy phần mềm  
    Vì vậy nếu sử dụng `os.path.dirname(os.path.abspath(__file__))` thì nó sẽ trả về đường dẫn thư mục tạm chứ không phải thư mục chứa tệp exe: `C:\Program File\My_app`  
    """
    if getattr(sys, 'frozen', False):
        # Ứng dụng đang chạy dưới dạng một file đóng gói bởi PyInstaller thì biến sys.frozen = True
        app_dir = sys._MEIPASS  # Trả về thư mục tạm _MEI

        # Trả về thư mục của ứng dụng thực thi (có thể là Program Files)
        return os.path.dirname(os.path.abspath(sys.executable))
    
    else:
        # Khi chạy trực tiếp từ mã nguồn Python (không phải PyInstaller)
        app_dir = os.path.dirname(os.path.abspath(__file__))

        return app_dir
    
# Đường dẫn ứng dụng chính
APP_DIR = get_real_app_dir()
APP_EXE_PATH = os.path.join(APP_DIR, MAIN_APP)
UPDATE_ZIP_PATH = os.path.join(APP_DIR, UPDATE_ZIP_NAME)

# @main_requires_admin
class UpdateApp:
    """
    Ứng dụng cập nhật phần mềm cho một `ứng dụng khác`, cần đặt ứng dụng này cùng vị trí với ứng dụng chính  
    Khi ứng dụng chính được cài đặt trong thư mục `Program Files` trên `Windows`, việc ghi đè tệp trong thư mục này yêu cầu quyền quản trị viên, vì vậy cần chạy ứng dụng này với quyền quản trị viên  
    Phần mềm này `(updater)` sẽ được phần mềm chính gọi và chạy trong nền để kiểm tra xem có bản cập nhật nào mới từ server hay không  
    `Updater` sẽ truy vấn thông tin từ thư mục `data/config.json` để lấy các thông tin cần thiết và tải về một tệp `zip` chứa `file exe`, `thư mục`, `tệp tin` khác cần thiết để thay thế cho các tệp tin cũ  
    Sau khi `ghi đè` các tệp tin cũ thì `Updater` tự động xóa tệp zip đã tải về và khởi chạy phần mềm chính   
    """
    def __init__(self, root, current_version = "1.0.0"):
        self.root = root
        self.root.title("Cập nhật phần mềm")
        self.root.iconbitmap(resource_path("assets\\image\\Update_ico.ico"))
        self.root.geometry("500x300")
        self.root.resizable(True, True)  # Cho phép cửa sổ có thể thay đổi kích thước

        self.current_version =current_version

        # Các thành phần giao diện
        self.file_label = tk.Label(root, text="File: Chưa tải", font=("Arial", 10))
        self.file_label.pack(pady=5)

        self.note_label = tk.Label(root, text="Nội dung phiên bản mới", font=("Arial", 10), wraplength=480, justify="left")
        self.note_label.pack(pady=5)

        self.speed_label = tk.Label(root, text="Speed: 0 KB/s", font=("Arial", 10))
        self.speed_label.pack(pady=5)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

        # Label hiển thị tệp đang giải nén
        self.current_file_label = tk.Label(root, text="Đang giải nén: Chưa bắt đầu", font=("Arial", 10))
        self.current_file_label.pack(pady=5)

        self.extract_progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.extract_progress.pack(pady=10)
        # self.extract_progress.pack_forget()  # Ẩn thanh tiến trình giải nén ban đầu

        self.get_information_from_server()

        self.status_label = tk.Label(root, text="Nhấn 'Start' để bắt đầu cập nhật.", font=("Arial", 10))
        self.status_label.pack(pady=5)

        self.start_button = tk.Button(root, text="Start Download and Extract", command=self.update_application, bg="#4CAF50", fg="white")
        self.start_button.pack(pady=10)

        # Khi đóng chương trình bằng nút "X" thì chạy hàm on_closing
        self.root.protocol("WM_DELETE_WINDOW", self.close_updater)

    def adjust_window_size(self):
        """
        Điều chỉnh kích thước cửa sổ dựa trên nội dung của `note_label`.
        """
        self.root.update_idletasks()
        self.root.geometry(f"{self.note_label.winfo_width() + 100}x{self.note_label.winfo_height() + 300}")

    def get_information_from_server(self):

        # Lấy thông tin phiên bản mới nhất
        try:
            response = requests.get(LATEST_VERSION_ENDPOINT)
            response.raise_for_status()

            # Lấy thông tin nội dung từ api
            version_info = response.json()
            # Lấy thông tin phiên bản mới nhất
            self.latest_version = version_info.get("latest_version")
            # Lấy địa chỉ api để download tệp zip chứa file exe và các thư mục khác đi kèm
            self.download_url = version_info.get("download_url")
            # Lấy thông tin nội dung của phiên bản cập nhật
            release_notes = version_info.get("release_notes")
            # Lấy thông tin checksum của tệp zip, để đổi chiếu sau khi tải xong có trùng hay không
            self.expected_checksum = version_info.get("checksum")

            # Hiển thị tên tệp và nội dung cập nhật mới
            # long_text = "Đây là nội dung cập nhật rất dài. " * 10
            self.file_label.config(text=f"File: {UPDATE_ZIP_NAME} Version: {self.latest_version}")
            self.note_label.config(text=release_notes)

            # Điều chỉnh kích thước cửa sổ sau khi đặt nội dung dài
            self.adjust_window_size()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tìm thấy phiên bản mới: {e}")
            self.close_updater()
            return

    def calculate_checksum(self, file_path):
        """
        Tính toán checksum SHA256 của một tập tin.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def verify_checksum(self, file_path, expected_checksum):
        """
        So sánh checksum của tệp tin với checksum được cung cấp từ server.
        """
        calculated_checksum = self.calculate_checksum(file_path)
        if calculated_checksum == expected_checksum:
            return True
        else:
            logger.info(f"Checksum tính toán: {calculated_checksum}")
            logger.info(f"Checksum mong đợi: {expected_checksum}")
            return False

    def download_file(self, url, save_path, progress_callback=None, speed_callback=None):
        """
        Tải về tệp tin từ URL với hỗ trợ cập nhật tiến trình và tốc độ tải.
        """
        logger.info(f"Tải tệp tin từ server và lưu vào: {save_path}")
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                total_length = int(r.headers.get('content-length', 0))
                with open(save_path, 'wb') as f:
                    downloaded = 0
                    start_time = time.time()
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_length > 0:
                                percent = int(downloaded * 100 / total_length)
                                progress_callback(percent)
                            
                            # Tính toán tốc độ tải
                            elapsed_time = time.time() - start_time
                            speed = downloaded / 1024 / elapsed_time if elapsed_time > 0 else 0
                            speed_callback(f"{speed:.2f} KB/s")
            return True
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False

    def extract_zip(self, zip_path, extract_to, progress_callback=None):
        """
        Giải nén tệp zip với hỗ trợ cập nhật tiến trình.
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                files = zip_ref.namelist()
                total_files = len(files)
                for i, file in enumerate(files, 1):
                    # Cập nhật label với tên tệp hiện tại
                    self.current_file_label.config(text=f"Đang giải nén: {file}")
                    zip_ref.extract(member=file, path=extract_to)
                    if progress_callback and total_files > 0:
                        percent = int(i * 100 / total_files)
                        progress_callback(percent)
            return True
        except Exception as e:
            logger.error(f"Error extracting zip file: {e}")
            return False

    def launch_app(self):
        """
        Khởi động ứng dụng chính (app.exe).
        """
        if os.path.exists(APP_EXE_PATH):
            subprocess.Popen([APP_EXE_PATH])
        else:
            messagebox.showerror("Lỗi", f"Không thể tìm thấy ứng dụng: {APP_EXE_PATH}")

    def close_updater(self):
        """
        Đóng cửa sổ updater.
        """
        self.root.destroy()
        sys.exit(0)

    def update_application(self):
        """
        Bắt đầu quá trình cập nhật trong một luồng riêng.
        """
        
        threading.Thread(target=self.start_update, args=(self.current_version, self.latest_version, self.download_url, self.expected_checksum), daemon=True).start()

    def start_update(self, current_version, latest_version, download_url, expected_checksum):
        """
        Quá trình cập nhật chính: kiểm tra phiên bản, tải về, kiểm tra checksum, giải nén và khởi động ứng dụng mới.
        """

        if version.parse(latest_version) > version.parse(current_version):
            self.status_label.config(text=f"Đang tải về phiên bản: {latest_version} ...")
            
            # Tải về tệp cập nhật
            success = self.download_file(
                download_url,
                UPDATE_ZIP_PATH,
                progress_callback=lambda p: self.progress.config(value=p),
                speed_callback=lambda s: self.speed_label.config(text=f"Speed: {s}")
            )
            if success:
                self.status_label.config(text="Đã tải về thành công.\nĐang kiểm tra tính toàn vẹn...")
                
                # Kiểm tra checksum
                if self.verify_checksum(UPDATE_ZIP_PATH, expected_checksum):
                    self.status_label.config(text="Checksum hợp lệ.\nĐang giải nén và cập nhật...")
                    self.extract_progress.pack(pady=10)  # Hiển thị thanh tiến trình giải nén

                    # Giải nén tệp
                    success = self.extract_zip(
                        UPDATE_ZIP_PATH,
                        APP_DIR,
                        progress_callback=lambda p: self.extract_progress.config(value=p)
                    )
                    if success:
                        self.status_label.config(text="Cập nhật thành công.\nKhởi động ứng dụng mới...")
                        # self.extract_progress.pack_forget()  # Ẩn thanh tiến trình giải nén

                        # Viết lại phiên bản mới vào tệp json
                        data['Update_app']["current_version"] = latest_version
                        with open(json_filename, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                        
                        # Khởi động ứng dụng mới
                        self.launch_app()
                        
                        # Xóa tệp zip đã tải về
                        os.remove(UPDATE_ZIP_PATH)
                        
                        # Đóng updater sau 2 giây
                        self.root.after(2000, self.close_updater)
                    else:
                        messagebox.showerror("Lỗi", "Giải nén tệp cập nhật thất bại. Hãy thử lại hoặc liên hệ với bộ phận IT")
                        self.close_updater()
                else:
                    messagebox.showerror("Lỗi checksum", "Checksum không hợp lệ. Cập nhật bị hủy.")
                    os.remove(UPDATE_ZIP_PATH)
                    self.close_updater()
            else:
                messagebox.showerror("Lỗi", "Tải về tệp cập nhật thất bại.")
                self.close_updater()
        else:
            # messagebox.showinfo("Thông Báo", "Bạn đang sử dụng phiên bản mới nhất.")
            self.close_updater()

    def close_main_app():
        """Đóng ứng dụng chính nếu nó đang chạy"""
        try:
            for proc in psutil.process_iter():
                if MAIN_APP in proc.name():
                    proc.terminate()
                    proc.wait(timeout=5)  # Đợi quá trình dừng hẳn trong 5 giây
                    return True
        except Exception as e:
            logger.error(f"Không thể đóng ứng dụng chính: {e}")
            return False
        return True

if __name__ == "__main__":

    "Để chạy Updater với quyền quản trị, ta sử dụng 2 thư viện là pywin32 và pyuac: pip install pypiwin32 và pip install pyuac"
    """
    Cách 1: Sử dụng trình trang trí `decorator` thì mặc định khi gọi hàm đó sẽ yêu cầu quyền quản trị viên, có thể sử dụng `decorator` cho class:
    @main_requires_admin
    def main():
        print("Do stuff here that requires being run as an admin.")
        # The window will disappear as soon as the program exits!
        input("Press enter to close the window. >")

    if __name__ == "__main__":
        main()
    """
    # root = tk.Tk()
    # app = UpdateApp(root, current_version= CURRENT_VERSION)
    # root.mainloop()

    """
    Cách 2: Gọi trực tiếp quyền admin ngay từ ban đầu. Kiểm tra xem phần mềm có chạy với quyền admin không, nếu không thì chạy lại với quyền admin
    """
    try:
        if not pyuac.isUserAdmin():
            pyuac.runAsAdmin()
        else:

            logger = logging.getLogger()
            # Dòng dưới sẽ ngăn chặn việc có những log không mong muốn từ thư viện PILLOW
            # ví dụ: 2020-12-16 15:21:30,829 - DEBUG - PngImagePlugin - STREAM b'PLTE' 41 768
            logging.getLogger("PIL.PngImagePlugin").propagate = False

            logging.basicConfig(filename=log_file_path, filemode= 'a',
                                format='%(asctime)s %(levelname)s:\t %(filename)s: %(funcName)s()-Line: %(lineno)d\t message: %(message)s',
                                datefmt='%d/%m/%Y %I:%M:%S %p', encoding = 'utf-8', force=True)

            # Mức độ lưu nhật ký, DEBUG chỉ dành cho trong quá trình DEBUG, nếu không sẽ có nhiều log thừa thãi
            logger.setLevel(logging.INFO)


            root = tk.Tk()
            app = UpdateApp(root, current_version= CURRENT_VERSION)
            root.mainloop()
    except Exception as e:
        logger.error(f"Có lỗi khi khởi chạy ứng dụng Updater: {e}")

